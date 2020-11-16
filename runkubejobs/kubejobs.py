#!/usr/bin/env python3

"""
This module implements a custom Kubernetes Job controller.

This fills the gap between the Kubernetes Job and DaemonSet controllers.
It runs *once* on multiple nodes (almost) simultaneously and does not
restart regardless of success or failure.
"""

import datetime
import logging
import sys
import threading
import time
import yaml

from dateutil.tz import tzutc
import kubernetes.client as client
import kubernetes.utils as kubeutils
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)


class kubeJob:
    """
    A class for spawning Kubernetes jobs on worker nodes.

    This class is really only used to facilitate spawning the jobs. It requires
    organised instantiation using CLI options parsed into a Kubernetes YAML 
    template. After the job is spawned, the generic non-class functions in this 
    module administer the job through the Kubernetes API.

    Attributes:
        core (CoreV1Api): Kubernetes API.
        batch (BatchV1Api): Kubernetes API.
        worker_yaml (dict): Dict of Kubernetes YAML with runtime substitutions.
        job (V1Job): Job spawned from worker_yaml.
    """
    def __init__(self, tmpl, task, node, log_id, image, core, batch, q, w):
        """
        Init with CLI options

        Args:
            tmpl (str): Filename of YAML template.
            task (str): Job task to run (e.g. runxhpl).
            node (str): Name of worker node.
            log_id (str): log_id (unique ID) of run.
            image (str): Docker image to run on worker node.
            core (CoreV1Api): Kubernetes API.
            batch (BatchV1Api): Kubernetes API.
            q (Queue): Queue for Kubernetes event stream.
            w (Watch): Kubernetes Watch object that genereates the event stream.
        """
        self.core = core
        self.batch = batch
        self.worker_yaml = get_dict_from_yaml(task, node, tmpl, log_id, image)
        self.job = self.spawn_job(task, node, batch)

    def job_exists(self):
        """
        Check if Kubernetes job exists in the default namespace.

        Args:
            None

        Returns:
            tuple(
                exists (bool):  Whether the job esists.
                job: (V1Job or None): Queried job.
            )

        Raises:
            ApiException: An error occured reading the job.
        """
        try:
            job = self.batch.read_namespaced_job(
                self.worker_yaml["metadata"]["name"],
                "default",
            )
        except ApiException as e: 
            if e.reason == "Not Found":
                exists = False
                job = None
            else:
                raise e
        else:
            exists = True
        return (exists, job)

    def wait_for_delete(self):
        """Wait for Kubernetes job deletion."""
        while (self.job_exists())[0]:
            time.sleep(1)
        return None

    def spawn_job(self, task, node, batch):
        """
        Spawn a Kubernetes job on a Kubernetes node.

        If a job with the same name already exists, delete it.

        Args:
            task (str): Type of job to run (e.g. runxhpl).
            node (str): Name of the node on which to run the job.
            batch (BatchV1Api): Kubernetes API.

        Returns:
            job (V1Job): Spawned job.

        Raises:
            FailToCreateError: An error occured creating the job.
        """
        job = None
        kube_client = client.api_client.ApiClient()
        (exists, job) = self.job_exists()
        if exists:
            logger.info("Found existing job: {0}".format(job.metadata.name))
            delete_obj(job, batch)
            self.wait_for_delete()

        logger.info("Creating worker: {0}-{1}".format(task, node))
        if isinstance(self.worker_yaml, dict):
            try:
                kubeutils.create_from_dict(kube_client, self.worker_yaml)
            except FailToCreateError as e:  # list(ApiException)
                raise e
            else:
                job = get_job(
                    self.worker_yaml["metadata"]["name"],
                    batch,
                )
        return job


def delete_obj(obj, api):
    """
    Delete Kubernetes object (job or pod) in the default namespace.

    Args:
        obj (V1Job or V1Pod): Object to delete.
        api (BatchV1Api or CoreV1Api): Kubernetes API.

    Returns:
        None

    Raises:
        ApiException: An error occured deleting the object.
    """
    logger.info("Deleting obj: {0}".format(obj.metadata.name))
    fn = "delete_namespaced_{0}".format(obj.kind.lower())
    params = (
        obj.metadata.name,
        "default",
    )
    kw_params = {
        "propagation_policy": "Foreground",
    }
    try:
        r = getattr(api, fn)(*params, **kw_params)
    except ApiException as e:
        raise e
    return None
    

def get_stream(w, core):
    """
    Get Kubernetes Watch event stream in the default namespace.

    Args:
        w (Kubernetes Watch object): Kubernetes Watch.
        core (CoreV1Api): Kubernetes API.

    Returns:
        stream (V1EventList): event stream list.
    """
    fn_dict = {
        "core.list_namespaced_event": core.list_namespaced_event,
    }
    fn = "core.list_namespaced_event"
    stream = getattr(w, "stream")(
        fn_dict[fn],
        "default",
    )
    return stream


def queue_event(q, stream):
    """
    Add recent events from Kubernetes event stream to Queue.

    Args:
        q (Queue): Queue that will be used to process event stream.
        stream (V1EventList): Event stream that will be processed.

    Returns:
        None
    """
    current_time = datetime.datetime.now(tzutc())
    for event in stream:
        e = event["object"]
        if e.last_timestamp:
            if e.last_timestamp > current_time:
                q.put(event)
    return None


def get_thread(q, stream):
    """
    Create and return thread for single asynchronous Kubernetes event stream.

    The event stream gets a dedicated thread. Each event is filtered by
    timestamp and put on the queue to be processed. This allows mutiple
    event streams to be processed asynchronously by the main thread (e.g.
    processing event streams from a different task or namespace).

    The following is an diagram with multiple event streams:

      /----------------------\      -----
      | runxhpl event stream | ---> |   |
      \----------------------/      |   |      ===============
                                    | Q | <=== | Main thread |
      /--------------------\        |   |      ===============
      | other event stream | -----> |   |
      \--------------------/        -----

    Args:
        q (Queue): Queue for processing events by main thread.
        stream (V1EventList): Event stream to process.

    Returns:
        t (Thread): Thread containing event stream.
    """
    t = threading.Thread(
        target = queue_event,
        args = (q, stream),
        name = "thread.watch",
        daemon = True,
    )
    t.start()
    return t

def get_job(name, batch):
    """
    Get Kubernetes job in the default namespace.

    Args:
        name (str): Name of the job.
        batch (BatchV1Api): Kubernetes API.

    Returns:
        j (V1Job): Queried job

    Raises:
        ApiException: An error occured reading the job.
    """
    try:
        j = batch.read_namespaced_job(
            name,
            "default", 
        )
    except ApiException as e:
        raise e
    return j


def get_pod(obj, core):
    """
    Get Kubernetes pod in the default namespace.

    Args:
        obj (str or V1Job): Name of the pod or its V1Job parent.
        core (CoreV1Api): Kubernetes API.

    Returns:
        p (V1Pod): Queried pod.

    Raises:
        ApiException: An error occured listing the job.
        ApiException: An error occured reading the pod.
    """
    if isinstance(obj, client.models.v1_job.V1Job):
        job = obj
        try:
            l = core.list_namespaced_pod(
                "default",
                label_selector = "job-group={0}".format(job.metadata.name),
            )
        except ApiException as e:
            raise e
        else:
            p = l.items[0]
    elif isinstance(obj, str):
        name = obj
        try:
            p = core.read_namespaced_pod(
                name,
                "default",
            )
        except ApiException as e:
            raise e
    return p


def get_pod_log(p, core):
    """
    Get the log of a Kubernetes Pod.

    Args:
        p (str): Name of the pod.
        core (CoreV1Api): Kubernetes API.

    Returns:
        s (str): pod log

    Raises:
        ApiException: An error occured reading the pod log
    """
    try:
        s = core.read_namespaced_pod_log(p, "default")
    except ApiException as e:
        raise e
    return s


def get_like_objs(obj, api):
    """
    Get similar Kubernetes objects (jobs/pods) according to metadata labels.

    This is useful for grouping together objects with similar task (e.g. runxhpl)
    and log-id with to of the target object.

    Args:
        obj (V1Job or V1Pod): Queried object.
        api (BatchV1Api or CoreV1Api): Kubernetes API.

    Returns:
        l.items (list V1Job or V1Pod): list of objects like target object.
    """
    fn = "list_namespaced_{0}".format(obj.kind.lower())
    params = (
        "default",
    )
    kw_params = {
        "label_selector": "task={0},log-id={1}".format(
            obj.metadata.labels["task"],
            obj.metadata.labels["log-id"]
        ),
    }
    l = getattr(api, fn)(*params, **kw_params)
    return l.items


def gen_like_job_status(job, batch):
    """
    Generate the statuses of similar Kubernetes jobs.

    This is useful for getting the status of jobs with similar task
    (e.g. runxhpl) and log-id as that of the target job. This facilitates
    checking a group of runs for failure/success.

    Args:
        job (V1Job): Query object.
        batch (BatchV1Api): Kubernetes API.

    Yields:
        status (generator): Job statusues generator object.
    """
    status = ""
    for j in get_like_objs(job, batch):
        if j.status:
            if j.status.failed:
                status = "Failed"
            elif j.status.succeeded:
                status = "Succeeded"
            else:
                status = ""
            yield status

       
def log_event(e):
    """
    Log the Kubernetes event using the logger.

    Uses the debug logger and includes a warning if the event is of type 
    "Warning".

    Args:
        e (V1Event): Kubernetes event 

    Returns:
        None
    """
    log_vars = {}
    format_vars = ""
    o = e.involved_object
    o_meta = e.metadata
    if e.type:
        e_type = "WWW" if e.type == "Warning" else "..."
        log_vars.update({"type": e_type})
        format_vars += "{type:<4}"
    if o.name:
        log_vars.update({"o_name": o.name})
        format_vars += "{o_name:<25}"
    if e.reason:
        log_vars.update({"reason": e.reason})
        format_vars += "{reason:<25}"
    if format_vars:
        logger.debug(format_vars.format(**log_vars))
    return None


def is_failed(e_type, job, pod, batch, q_exc):
    """
    Check if Kubernetes Job/Pod in Kubernetes Event has failed.

    Pass RuntimeErrors from the event stream thread to the main thread
    via the exception queue.

    Args:
        e_type (str): type of event, from V1Event.type.
        job (V1Job): Query job.
        pod (V1Pod): Query pod.
        batch (BatchV1Api): Kubernetes API.
        q_exc (Queue): Queue to pass job/pod exceptions to main thread.

    Return:
        failed (bool): Whether the job/pod in the event has failed.

    Raises:
        RuntimeError: Pod hangs in "Pending" phase.
        RuntimeError: Pod enters "Failed" phase.
        RuntimeError: Job has Pods in "Failed" phase.
    """
    failed = False
    if pod.status.start_time:
        time_current = datetime.datetime.now(tzutc())
        time_elapsed = (time_current - pod.status.start_time).total_seconds()
        if (
            e_type == "Warning"
            and pod.status.phase == "Pending"
            and time_elapsed > 60
        ):
            try:
                raise RuntimeError("Pending Timeout Exceeded", pod.metadata.name)
            except RuntimeError as e:
                failed = True
                q_exc.put(sys.exc_info())

    if pod.status:
        if pod.status.phase == "Failed":
            try:
                raise RuntimeError("Pod Failed", pod.metadata.name)
            except RuntimeError as e:
                failed = True
                q_exc.put(sys.exc_info())
    elif job.status:
        if job.status.failed:
            try:
                raise RuntimeError("Job Failed", job.metadata.name)
            except RuntimeError as e:
                failed = True
                q_exc.put(sys.exc_info())
    return failed


def is_completed(job, batch):
    """
    Check if Kubernetes Job is completed.

    All similar jobs (task and log-id) must complete successfully for this
    to return True. In other words, this checks the success of a group run
    of a task (e.g. runxhpl).

    Args:
        job (V1Job): Query job.
        batch (BatchV1Api): Kubernetes API.

    Returns:
        completed (bool): Whether the job is completed.
    """
    completed = False

    like_job_status = list(gen_like_job_status(job, batch))
    if all(list(i == "Succeeded" for i in like_job_status)):
        completed = True
    return completed


def parse_queue(q_watch, q_exc, batch, core):
    """
    Parse a Kubernetes event stream.

    For each event in the stream, log it then analyse whether the Kubernetes
    Job that generated it has completed or failed. Stop if either all jobs
    in the group have succeeded or any have failed.

    A separate exception queue is necessary because threads have their own
    stack separate from the main thread.

    Args:
        q_watch (Queue): Queue to receive async Kubernetes Watch events.
        q_exc (Queue): Queue to pass exceptions to main thread.
        batch (BatchV1Api): Kubernetes API.
        core (CoreV1Api): Kubernetes API.

    Return:
        None
    """
    while True:
        if not q_watch.empty():
            w_event = q_watch.get()
            event_type = w_event["type"]
            e = w_event["object"]
            log_event(e)
            obj = e.involved_object
            if obj.kind.lower() == "job":
                job = get_job(obj.name, batch)
                pod = get_pod(job, core)
            elif obj.kind.lower() == "pod":
                pod = get_pod(obj.name, core)
                job = get_job(pod.metadata.name.rsplit("-", 1)[0], batch)

            if (
                is_completed(job, batch)
                or is_failed(e.type, job, pod, batch, q_exc)
            ):
                break
    return None


def get_ready_nodes(core):
    """
    Get a list of nodes ready to schedule jobs.

    Ignore the master node or any nodes drained / cordoned.

    Args:
        core (CoreV1Api): Kubernetes API.

    Returns:
        ready_nodes (list): Node list.
    """
    ready_nodes = []
    l = core.list_node()
    for i in l.items:
        if not (
            "node-role.kubernetes.io/master" in i.metadata.labels.keys()
            or i.spec.unschedulable
            ):
            # Sort condition list by timestamp
            conds = sorted(
                i.status.conditions,
                key = lambda condition: condition.last_transition_time
            )
            for c in conds:
                if c.type == "Ready" and c.status == "True":
                    ready_nodes.append(i.metadata.name)
    return ready_nodes


def get_dict_from_yaml(task, worker, filename, log_id, image):
    """
    Create a dictionary from a Kubernetes YAML template that will be used to
    spawn jobs on worker nodes.

    Args:
        task (str): Job task to run (e.g. runxhpl).
        worker (str): Name of worker node.
        filename (str): Filename of YAML template.
        log_id (str): log_id (unique ID) of run.
        image (str): Docker image to run on worker node.

    Returns:
        d (dict): Dictionary of YAML with substituted vars
    """
    d = {}
    image_dict = {
        "runxhpl": "hosaka.local:5000/runxhpl:default-x86_64"
    }
    img = image if image else image_dict[task]
    with open(filename) as f:
        blob = f.read()

    d = yaml.safe_load(
        blob.replace(
            "$WORKER", worker
        ).replace(
            "$TASK", task
        ).replace(
            "$LOGID", log_id
        ).replace(
            "$IMAGE", img
        )
    )
    return d

