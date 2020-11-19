#!/usr/bin/env python3

"""
This module implements the command-line interface for package.
"""

import argparse
import atexit
import logging
import os
import pkg_resources
import queue
import sys
import threading
import traceback
from argparse import ArgumentError

import kubernetes.config as config
import kubernetes.client as client
import kubernetes.watch as watch

from engcommon import clihelper
from runkubejobs import kubejobs


def csv_str(vstr, sep = ","):
    """
    Parse comma-separated value string for "nodes" option.

    Args:
        vstr (str): Value string from CLI, including commas.
        sep (str): String separator.

    Returns:
        values (list): List of nodes.

    Raises:
        ArgumentError: Non-string value detected.
        ArgumentError: Value does not exist in allowed choices.
    """
    values = []
    choices = [
        "all",
        "brisket",
        "flatiron",
        "porterhouse",
        "ribeye",
        "silverside",
        "slimjim",
        "sweetbreads",
    ]
    for v in vstr.split(sep):
        try:
            v = str(v)
        except ValueError:
            raise ArgumentError("Invalid value: {0}, must be string".format(v))
        else:
            v = v.strip(" ,")
            if v not in choices:
                try:
                    raise ArgumentError("Invalid value: {0}, not in {1}".format(v, choices))
                except ArgumentError:
                    raise
            else:
                values.append(v)
    return values


def get_command(args):
    """
    Parse command argument list into dict.

    Parameters:
        args (list): Argument list (typically sys.argv[1:]).

    Returns:
        args (dict): Argument dict.
    """
    parser = argparse.ArgumentParser(description = "Spawn kubernetes job on nodes")
    parser.add_argument(
        "-d", "--debug",
        action = "store_true",
        help = "print debug information",
        required = False,
    )
    parser.add_argument(
        "--debug-api",
        action = "store_true",
        help = "print kubernetes API debug information",
        required = False,
    )
    parser.add_argument(
        "-i", "--image",
        action = "store",
        type = str,
        help = "set container image for task",
        required = False,
    )
    parser.add_argument(
        "-l", "--logid",
        action = "store",
        type = str,
        help = "set log_id for run",
        required = False,
    )
    parser.add_argument(
        "-n", "--nodes",
        action = "store",
        type = csv_str,
        help = "set nodes for task (comma separated)",
        required = False,
    )
    parser.add_argument(
        "-p", "--prefix",
        action = "store",
        type = str,
        help = "set prefix directory",
        default = "/tmp/logs",
        required = False,
    )
    parser.add_argument(
        "-t", "--task",
        action = "store",
        help = "set task to run",
        choices = [
            "runxhpl",
        ],
        required = True,
    )
    parser.add_argument(
        "--tmpl",
        action = "store",
        type = str,
        help = "set template file",
        required = False,
    )
    parser.add_argument(
        "-v", "--version",
        action = "version",
        version = pkg_resources.get_distribution(parser.prog).version
    )
    args = vars(parser.parse_args(args))
    return args


def clean_up(workers, batch, core, my_cli):
    """
    Clean up failed Kubernetes jobs on worker nodes.

    Args:
        workers (dict): Dict of KubeJob instances, keyed by node name.
        batch (BatchV1Api): Kubernetes API.
        core (CoreV1Api): Kubernetes API.
        logger (Logger): Logger default.
        logger_noformat(Logger): Logger with no timestamp prefixes.

    Returns:
        None
    """
    logger = my_cli.logger
    logger_noformat = my_cli.logger_noformat
    # Add handler to write failed pod logs to "console" with "noformat"
    kh = logging.StreamHandler(logger.handlers[1].stream)  # console
    kh.setFormatter(logger_noformat.handlers[0].formatter)  # noformat
    kh.setLevel(logging.DEBUG)
    logger_noformat.addHandler(kh)
    logger.info("Cleaning up")

    for node, kjobs in workers.items():
        j = kjobs.job
        p = kubejobs.get_pod(j, core)
        if j.status:
            if j.status.failed or p.status.phase == "Failed":
                logger_noformat.debug("\n{0}".format(
                    (
                        " Failed pod log: "
                        + p.metadata.name
                        + " "
                    ).center(80, "*")
                ))
                s = kubejobs.get_pod_log(p.metadata.name, core)
                logger_noformat.debug(s)
            else:
                kubejobs.delete_obj(j, batch)
    my_cli.print_logdir()
    return None


def run(d):
    """
    Run package.

    Args:
        d (dict): Dict of command-line options.

    Returns:
        None

    Raises:
        Exception: An error occured in the child event stream processing thread.
    """
    project_name = (os.path.dirname(__file__).split("/")[-1])
    if d["debug_api"]:
        d["debug"] = True
        client.rest.logger.setLevel(logging.DEBUG)
    elif not d["debug_api"]:
        client.rest.logger.setLevel(logging.WARNING)

    my_cli = clihelper.CLI(project_name, d)
    log_id = my_cli.log_id
    logger = my_cli.logger
    my_cli.print_versions()

    # Setup Kubernetes config and API
    # config.load_kube_config()
    config.load_incluster_config()
    core = client.CoreV1Api()
    batch = client.BatchV1Api()
    w = watch.Watch()
    q_watch = queue.Queue()  # Queue for event stream
    q_exc = queue.Queue()  # Queue for thread exceptions

    # Setup stream and child thread(s) of Kubernetes events
    task = d["task"]
    nodes = d["nodes"]
    image = d["image"]
    tmpl = d["tmpl"]
    if not tmpl:
        tmpl = pkg_resources.resource_stream(
            __name__,
            "kube-job-tmpl-{0}.yaml".format(task)
        ).name

    logger.info("Creating Watch() thread")
    stream = kubejobs.get_stream(w, core)
    t_watch = kubejobs.get_thread(q_watch, stream)
    t_watch.start()

    # Start main thread
    m = threading.Thread(
        target = kubejobs.parse_queue,
        args = (q_watch, q_exc, batch, core,),
        name = "thread.main",
        daemon = True,
    )
    m.start()

    logger.info("Creating workers")
    workers = {}
    if "all" in nodes:
        nodes = kubejobs.get_ready_nodes(core)

    for node in nodes:
        workers[node] = kubejobs.kubeJob(tmpl, task, node, log_id, image, core, batch, q_watch, w)

    # Register cleanup, handle exception queue from child threads
    atexit.register(clean_up, workers, batch, core, my_cli)
    try:
        m.join()
    except KeyboardInterrupt:
        logger.info("CTRL-C receved")
        sys.exit(1)
    else:
        if not q_exc.empty():
            exc_type, exc_obj, exc_tb = q_exc.get()
            exc = "".join(traceback.format_exception(exc_type, exc_obj, exc_tb))
            try:
                raise exc_type(exc)
            except exc_type:
                logger.error(exc)
                raise


def main():
    args = sys.argv[1:]
    d = get_command(args)
    run(d)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logging.exception("Exceptions Found")
        logging.critical("Exiting.")
        sys.exit(1)
