Changelog
=========

0.7.1 (2020-12-17)
------------------
- ISSUE-035: Added upload CLI option, increased mem to 20% (0189eb3) [JustAddRobots]
- ISSUE-035: Added slackSend for build start. (46a3de7) [JustAddRobots]

0.7.0 (2020-12-17)
------------------
- ISSUE-018: Removed unnecessary core/batch parameters. (fd85366) [JustAddRobots]

0.6.3 (2020-12-16)
------------------
- ISSUE-030: Disabled delete tag stage. (fc01c33) [JustAddRobots]
- ISSUE-030: Disabled delete tag stage. (51ba4cb) [JustAddRobots]

0.6.1 (2020-12-15)
------------------
- ISSUE-020: Added Jenkins/python venv workaround. (b292ae9) [JustAddRobots]

0.6.0 (2020-12-15)
------------------
- Stage: Added delete tags stage for main branch. (c95ca38) [JustAddRobots]
- Stage: Cleaned up. (00c1d99) [JustAddRobots]
- Stage: Added absolute path for runkubejobs. (2709780) [JustAddRobots]
- Stage: Added pip version check. (57e7281) [JustAddRobots]
- Stage: Added Deploy Key. (88c8e7a) [JustAddRobots]
- Stage: Added --user for pip install. (0221391) [JustAddRobots]
- Stage: Fixed env var name. (b06fbd2) [JustAddRobots]
- Stage: Added python scripting bits using withCredentials. (862850d) [JustAddRobots]
- ISSUE-020: Added engcommon @ git+https, fixed env var names. (267e4d1) [JustAddRobots]
- ISSUE-020: Added bits for autodeployment of RC. (1a2c570) [JustAddRobots]
- ISSUE-020: Added Jenkinsfile. (e63e840) [JustAddRobots]
- ISSUE-024: Updated engcommon link. (8a2d0d3) [JustAddRobots]
- ISSUE-022: Added License, updated setup.py. (fc5a0b3) [JustAddRobots]
- ISSUE-022: Added README. (c5c03d7) [JustAddRobots]

0.5.0 (2020-12-11)
------------------
- Stage: Re-fixed Node Not Ready exception output. (58052b9) [JustAddRobots]
- Stage: Changed exception handler output for Node Not Ready. (be5d2c5) [JustAddRobots]
- Stage: Updated exception handling for Node Not Ready. (f30249e) [JustAddRobots]
- Stage: Changed to logger.exception for Node Not Ready Error. (38bd2a8) [JustAddRobots]
- Stage: Renamed get_task_nodes() (e206275) [JustAddRobots]
- Stage: Fixed positional argument for get_test_nodes() (9a08bef) [JustAddRobots]
- ISSUE-002: Updated for INI_URL, node check. (db70bb2) [JustAddRobots]

0.4.0 (2020-11-19)
------------------
- Stage: Removed commented out KUBECONFIG env var. (c04138f) [JustAddRobots]
- Stage: Added explicit kube config file path. (92b2815) [JustAddRobots]
- Stage: Reverted back to load_kube_config, added config in root. (25a52ce) [JustAddRobots]
- Stage: Added loading kubernetes config from within cluster. (3f8515c) [JustAddRobots]
- LOAD-011: Disabled master node scheduling. (e6876ca) [JustAddRobots]

0.3.0 (2020-11-17)
------------------
- Stage: Added pod toleration to run on master node. (4d44a6e) [JustAddRobots]
- ISSUE-007: Removed master node from scheduler ignore. (67d4a33) [JustAddRobots]

0.2.0 (2020-11-17)
------------------
- ISSUE-004: Added pre-commit flake8 fixes. (b47b8e1) [JustAddRobots]
- ISSUE-001: Added minor fixes. (8e0fbf1) [JustAddRobots]
- ISSUE-001: Added file dump for updates. (fae6712) [JustAddRobots]
- Initial commit. (06733fb) [JustAddRobots]
