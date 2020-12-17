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
❯ runkubejobs --debug --task runxhpl --prefix /var/lib/jenkins/workspace/logs --nodes all --image hosaka.local:5000/runxhpl:0.10.0-5851277-x86_64
2020-12-16 20:01:04 - INFO [clihelper]: runkubejobs v: 0.7.2
2020-12-16 20:01:04 - DEBUG [clihelper]: engcommon v: 0.6.2
2020-12-16 20:01:04 - DEBUG [clihelper]: {'debug': True,
 'debug_api': False,
 'image': 'hosaka.local:5000/runxhpl:0.10.0-5851277-x86_64',
 'log_id': None,
 'nodes': ['all'],
 'prefix': '/tmp/logs',
 'task': 'runxhpl',
 'tmpl': None}
2020-12-16 20:01:04 - INFO [cli]: Creating Watch() thread
2020-12-16 20:01:04 - INFO [cli]: Creating workers
2020-12-16 20:01:04 - INFO [kubejobs]: Creating worker: runxhpl-ono
2020-12-16 20:01:04 - INFO [kubejobs]: Creating worker: runxhpl-sendai
2020-12-16 20:01:05 - DEBUG [kubejobs]: ... runxhpl-ono-kbg7j        Pulling
2020-12-16 20:01:05 - DEBUG [kubejobs]: ... runxhpl-sendai-ttf8p     Pulling
2020-12-16 20:01:09 - DEBUG [kubejobs]: ... runxhpl-ono-kbg7j        Pulled
2020-12-16 20:01:09 - DEBUG [kubejobs]: ... runxhpl-ono-kbg7j        Created
2020-12-16 20:01:09 - DEBUG [kubejobs]: ... runxhpl-ono-kbg7j        Started
2020-12-16 20:01:13 - DEBUG [kubejobs]: ... runxhpl-sendai-ttf8p     Pulled
2020-12-16 20:01:13 - DEBUG [kubejobs]: ... runxhpl-sendai-ttf8p     Created
2020-12-16 20:01:13 - DEBUG [kubejobs]: ... runxhpl-sendai-ttf8p     Started
2020-12-16 20:01:58 - DEBUG [kubejobs]: ... runxhpl-sendai           Completed
2020-12-16 20:02:21 - DEBUG [kubejobs]: ... runxhpl-ono              Completed
2020-12-16 20:02:21 - INFO [cli]: Cleaning up
2020-12-16 20:02:21 - INFO [kubejobs]: Deleting obj: runxhpl-ono
2020-12-16 20:02:21 - INFO [kubejobs]: Deleting obj: runxhpl-sendai
2020-12-16 20:02:21 - INFO [clihelper]: LOGS: /tmp/logs/hosaka/keenly-bursal-ashtray/runkubejobs.2020.12.16-200104

```

Task logs are saved to each node.

node: ono
```
❯ cat  /tmp/logs/ono/keenly-bursal-ashtray/runxhpl.2020.12.16-200109/runxhpl.debug.1.log
2020-12-16 20:01:09 - INFO [clihelper]: runxhpl v: 0.10.0
2020-12-16 20:01:09 - DEBUG [clihelper]: engcommon v: 0.6.2
2020-12-16 20:01:09 - DEBUG [clihelper]: {'debug': True, 'log_id': 'keenly-bursal-ashtray', 'mem': 10, 'prefix': '/tmp/logs', 'runs': 2, 'upload': 'http://hosaka.local:3456/v1/machines'}
2020-12-16 20:01:09 - DEBUG [xhpl]: CORES: 4, MEM: 27 GB
2020-12-16 20:01:09 - DEBUG [xhpl]: MEM_PERCENT: 10, RUNS: 2
2020-12-16 20:01:09 - DEBUG [xhpl]: MEM_XHPL: 2 GB
2020-12-16 20:01:09 - DEBUG [xhpl]: Generating HPL.dat
2020-12-16 20:01:09 - DEBUG [xhpl]: {'N': 18816, 'NB': 336, 'P': 1, 'Q': 4}
2020-12-16 20:01:09 - DEBUG [xhpl]: HPL.dat: /usr/local/lib/python3.6/site-packages/runxhpl/bin/HPL.dat
2020-12-16 20:01:09 - DEBUG [xhpl]: 'mpirun --allow-run-as-root -mca btl_vader_single_copy_mechanism none -np 4 xhpl-x86_64'
2020-12-16 20:01:09 - INFO [xhpl]: Starting XHPL
2020-12-16 20:01:09 - INFO [xhpl]: STATUS     TEST     RUN TIME      GFLOPS
2020-12-16 20:01:09 - INFO [xhpl]: STARTED    xhpl      #1
2020-12-16 20:01:44 - INFO [xhpl]: PASSED     xhpl      #1 29.85     1.488e+02
2020-12-16 20:01:45 - INFO [xhpl]: STARTED    xhpl      #2
2020-12-16 20:02:20 - INFO [xhpl]: PASSED     xhpl      #2 30.13     1.474e+02
2020-12-16 20:02:20 - INFO [cli]: Status: PASSED
2020-12-16 20:02:20 - INFO [cli]: Mean Gflops: 148.10000000000002
2020-12-16 20:02:20 - INFO [clihelper]: LOGS: /tmp/logs/ono/keenly-bursal-ashtray/runxhpl.2020.12.16-200109
2020-12-16 20:02:20 - INFO [cli]: Uploading to Database
2020-12-16 20:02:20 - DEBUG [connectionpool]: Starting new HTTP connection (1): hosaka.local:3456
2020-12-16 20:02:20 - DEBUG [connectionpool]: http://hosaka.local:3456 "POST /v1/machines HTTP/1.1" 200 0
2020-12-16 20:02:20 - INFO [cli]: Done.
```

node: sendai
```
❯ cat /tmp/logs/sendai/keenly-bursal-ashtray/runxhpl.2020.12.16-200114/runxhpl.debug.1.log
2020-12-16 20:01:14 - INFO [clihelper]: runxhpl v: 0.10.0
2020-12-16 20:01:14 - DEBUG [clihelper]: engcommon v: 0.6.2
2020-12-16 20:01:14 - DEBUG [clihelper]: {'debug': True, 'log_id': 'keenly-bursal-ashtray', 'mem': 10, 'prefix': '/tmp/logs', 'runs': 2, 'upload': 'http://hosaka.local:3456/v1/machines'}
2020-12-16 20:01:14 - DEBUG [xhpl]: CORES: 4, MEM: 9 GB
2020-12-16 20:01:14 - DEBUG [xhpl]: MEM_PERCENT: 10, RUNS: 2
2020-12-16 20:01:14 - DEBUG [xhpl]: MEM_XHPL: 0 GB
2020-12-16 20:01:14 - DEBUG [xhpl]: Generating HPL.dat
2020-12-16 20:01:14 - DEBUG [xhpl]: {'N': 10240, 'NB': 256, 'P': 1, 'Q': 4}
2020-12-16 20:01:14 - DEBUG [xhpl]: HPL.dat: /usr/local/lib/python3.6/site-packages/runxhpl/bin/HPL.dat
2020-12-16 20:01:14 - DEBUG [xhpl]: 'mpirun --allow-run-as-root -mca btl_vader_single_copy_mechanism none -np 4 xhpl-x86_64'
2020-12-16 20:01:14 - INFO [xhpl]: Starting XHPL
2020-12-16 20:01:14 - INFO [xhpl]: STATUS     TEST     RUN TIME      GFLOPS
2020-12-16 20:01:14 - INFO [xhpl]: STARTED    xhpl      #1
2020-12-16 20:01:29 - INFO [xhpl]: PASSED     xhpl      #1 12.13     5.901e+01
2020-12-16 20:01:30 - INFO [xhpl]: STARTED    xhpl      #2
2020-12-16 20:01:58 - INFO [xhpl]: PASSED     xhpl      #2 22.47     3.186e+01
2020-12-16 20:01:58 - INFO [cli]: Status: PASSED
2020-12-16 20:01:58 - INFO [cli]: Mean Gflops: 45.435
2020-12-16 20:01:58 - INFO [clihelper]: LOGS: /tmp/logs/sendai/keenly-bursal-ashtray/runxhpl.2020.12.16-200114
2020-12-16 20:01:58 - INFO [cli]: Uploading to Database
2020-12-16 20:01:58 - DEBUG [connectionpool]: Starting new HTTP connection (1): hosaka.local:3456
2020-12-16 20:01:58 - DEBUG [connectionpool]: http://hosaka.local:3456 "POST /v1/machines HTTP/1.1" 200 0
2020-12-16 20:01:58 - INFO [cli]: Done.
```

## Todo

Rewrite in golang. ;)

## License

Licensed under GNU GPL v3. See **LICENSE.md**.
