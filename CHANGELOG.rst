Changelog
=========

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
