# runkubejobs
Custom Kubernetes Job Controller

## About

Kubernetes is great. Its one of my favourite workflow tools. Unfortunately the
native workload controllers are not best suited for HPC QA on baremetal computes. 

I needed a job controller that can run an app (e.g. runxhpl) simultaneously on all 
nodes to completion and not respawn regardless of whether the pod succeeded or failed. 
The Job and DaemonSet controllers were close, but neither could do exactly what I needed.

This project seeks to fill that gap. Though, there are already several great HPC job
controllers, Kubernetes is just so accessible. Not to mention the 
[API](https://kubernetes.io/docs/concepts/overview/kubernetes-api/) is just lovely 
and the [Python client](https://github.com/kubernetes-client/python) is easy to use.

This project is part of a CI/CD proof-of-concept and is **not supported**.

## Features

* Run task on node list or all workers
* Custom task via YAML
* CLI YAML template override
* Full API debug output 

## Installing

## Usage

```
usage: runkubejobs [-h] [-d] [--debug-api] [-i IMAGE] [-l LOGID] [-n NODES]
                   [-p PREFIX] -t {runxhpl} [--tmpl TMPL] [-v]

Spawn kubernetes job on nodes

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           print debug information
  --debug-api           print kubernetes API debug information
  -i IMAGE, --image IMAGE
                        set container image for task
  -l LOGID, --logid LOGID
                        set log_id for run
  -n NODES, --nodes NODES
                        set nodes for task (comma separated)
  -p PREFIX, --prefix PREFIX
                        set prefix directory
  -t {runxhpl}, --task {runxhpl}
                        set task to run
  --tmpl TMPL           set template file
  -v, --version         show program's version number and exit
```

Kubernetes cluster topoplgy:
```
❯ kubectl get node
NAME     STATUS   ROLES    AGE   VERSION
hosaka   Ready    master   23d   v1.19.4
ono      Ready    <none>   23d   v1.19.3
sendai   Ready    <none>   23d   v1.19.3
```

Run task on selected nodes
```
❯ runkubejobs --debug --task runxhpl --nodes ono,sendai --image hosaka.local:5000/runxhpl:0.7.3-10e1187-x86_64
2020-12-11 00:41:29 - INFO [clihelper]: runkubejobs v: 0.5.0
2020-12-11 00:41:29 - DEBUG [clihelper]: engcommon v: 0.5.2
2020-12-11 00:41:29 - DEBUG [clihelper]: {'debug': True,
 'debug_api': False,
 'image': 'hosaka.local:5000/runxhpl:0.7.3-10e1187-x86_64',
 'log_id': None,
 'nodes': ['ono', 'sendai'],
 'prefix': '/tmp/logs',
 'task': 'runxhpl',
 'tmpl': None}
2020-12-11 00:41:29 - INFO [cli]: Creating Watch() thread
2020-12-11 00:41:29 - INFO [cli]: Creating workers
2020-12-11 00:41:29 - INFO [kubejobs]: Creating worker: runxhpl-ono
2020-12-11 00:41:29 - INFO [kubejobs]: Creating worker: runxhpl-sendai
2020-12-11 00:41:30 - DEBUG [kubejobs]: ... runxhpl-ono-9k6w7        Pulling
2020-12-11 00:41:30 - DEBUG [kubejobs]: ... runxhpl-ono-9k6w7        Pulled
2020-12-11 00:41:30 - DEBUG [kubejobs]: ... runxhpl-ono-9k6w7        Created
2020-12-11 00:41:30 - DEBUG [kubejobs]: ... runxhpl-sendai-nxsc8     Pulling
2020-12-11 00:41:30 - DEBUG [kubejobs]: ... runxhpl-ono-9k6w7        Started
2020-12-11 00:41:30 - DEBUG [kubejobs]: ... runxhpl-sendai-nxsc8     Pulled
2020-12-11 00:41:30 - DEBUG [kubejobs]: ... runxhpl-sendai-nxsc8     Created
2020-12-11 00:41:30 - DEBUG [kubejobs]: ... runxhpl-sendai-nxsc8     Started
2020-12-11 00:41:41 - DEBUG [kubejobs]: ... runxhpl-sendai           Completed
2020-12-11 00:42:10 - DEBUG [kubejobs]: ... runxhpl-ono              Completed
2020-12-11 00:42:10 - INFO [cli]: Cleaning up
2020-12-11 00:42:10 - INFO [kubejobs]: Deleting obj: runxhpl-ono
2020-12-11 00:42:10 - INFO [kubejobs]: Deleting obj: runxhpl-sendai
2020-12-11 00:42:10 - INFO [clihelper]: LOGS: /tmp/logs/hosaka/cleverly-buttery-amphibia/runkubejobs.2020.12.11-004129
```

Task logs are saved to each node.

node: ono
```
❯ cat /tmp/logs/ono/cleverly-buttery-amphibia/runxhpl.2020.12.11-004130/runxhpl.debug.1.log
2020-12-11 00:41:30 - INFO [clihelper]: runxhpl v: 0.7.3
2020-12-11 00:41:30 - DEBUG [clihelper]: engcommon v: 0.5.2
2020-12-11 00:41:30 - DEBUG [clihelper]: {'debug': True, 'log_id': 'cleverly-buttery-amphibia', 'mem': 10, 'prefix': '/tmp/logs', 'runs': 2, 'upload': None}
2020-12-11 00:41:30 - DEBUG [xhpl]: CORES: 4, MEM: 16 GB
2020-12-11 00:41:30 - DEBUG [xhpl]: MEM_PERCENT: 10, RUNS: 2
2020-12-11 00:41:30 - DEBUG [xhpl]: MEM_XHPL: 1 GB
2020-12-11 00:41:30 - DEBUG [xhpl]: Generating HPL.dat
2020-12-11 00:41:30 - DEBUG [xhpl]: {'N': 14784, 'NB': 336, 'P': 1, 'Q': 4}
2020-12-11 00:41:30 - DEBUG [xhpl]: HPL.dat: /usr/local/lib/python3.6/site-packages/runxhpl/bin/HPL.dat
2020-12-11 00:41:30 - DEBUG [xhpl]: 'mpirun --allow-run-as-root -mca btl_vader_single_copy_mechanism none -np 4 xhpl-x86_64'
2020-12-11 00:41:30 - INFO [xhpl]: Starting XHPL
2020-12-11 00:41:30 - INFO [xhpl]: STATUS     TEST     RUN TIME      GFLOPS
2020-12-11 00:41:30 - INFO [xhpl]: STARTED    xhpl      #1
2020-12-11 00:41:49 - INFO [xhpl]: PASSED     xhpl      #1 15.31     1.407e+02
2020-12-11 00:41:50 - INFO [xhpl]: STARTED    xhpl      #2
2020-12-11 00:42:09 - INFO [xhpl]: PASSED     xhpl      #2 15.23     1.415e+02
2020-12-11 00:42:09 - INFO [cli]: Status: PASSED
2020-12-11 00:42:09 - INFO [cli]: Mean Gflops: 141.1
2020-12-11 00:42:09 - INFO [clihelper]: LOGS: /tmp/logs/ono/cleverly-buttery-amphibia/runxhpl.2020.12.11-004130
2020-12-11 00:42:09 - INFO [cli]: Done.
```

node: sendai
```
❯ cat /tmp/logs/sendai/cleverly-buttery-amphibia/runxhpl.2020.12.11-004131/runxhpl.debug.1.log
2020-12-11 00:41:31 - INFO [clihelper]: runxhpl v: 0.7.3
2020-12-11 00:41:31 - DEBUG [clihelper]: engcommon v: 0.5.2
2020-12-11 00:41:31 - DEBUG [clihelper]: {'debug': True, 'log_id': 'cleverly-buttery-amphibia', 'mem': 10, 'prefix': '/tmp/logs', 'runs': 2, 'upload': None}
2020-12-11 00:41:31 - DEBUG [xhpl]: CORES: 4, MEM: 3 GB
2020-12-11 00:41:31 - DEBUG [xhpl]: MEM_PERCENT: 10, RUNS: 2
2020-12-11 00:41:31 - DEBUG [xhpl]: MEM_XHPL: 0 GB
2020-12-11 00:41:31 - DEBUG [xhpl]: Generating HPL.dat
2020-12-11 00:41:31 - DEBUG [xhpl]: {'N': 6144, 'NB': 256, 'P': 1, 'Q': 4}
2020-12-11 00:41:31 - DEBUG [xhpl]: HPL.dat: /usr/local/lib/python3.6/site-packages/runxhpl/bin/HPL.dat
2020-12-11 00:41:31 - DEBUG [xhpl]: 'mpirun --allow-run-as-root -mca btl_vader_single_copy_mechanism none -np 4 xhpl-x86_64'
2020-12-11 00:41:31 - INFO [xhpl]: Starting XHPL
2020-12-11 00:41:31 - INFO [xhpl]: STATUS     TEST     RUN TIME      GFLOPS
2020-12-11 00:41:31 - INFO [xhpl]: STARTED    xhpl      #1
2020-12-11 00:41:35 - INFO [xhpl]: PASSED     xhpl      #1 2.91      5.314e+01
2020-12-11 00:41:36 - INFO [xhpl]: STARTED    xhpl      #2
2020-12-11 00:41:41 - INFO [xhpl]: PASSED     xhpl      #2 2.87      5.388e+01
2020-12-11 00:41:41 - INFO [cli]: Status: PASSED
2020-12-11 00:41:41 - INFO [cli]: Mean Gflops: 53.510000000000005
2020-12-11 00:41:41 - INFO [clihelper]: LOGS: /tmp/logs/sendai/cleverly-buttery-amphibia/runxhpl.2020.12.11-004131
2020-12-11 00:41:41 - INFO [cli]: Done.
```

## License

Licensed under GNU GPL v3. See **LICENSE.md**.
