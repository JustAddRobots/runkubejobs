#!/usr/bin/env groovy

// This Jenkinsfile automatically buids the repos tagged commits
// (releases/candidates/etc.)

def HASHLONG
def HASHSHORT
def TAG
def TAG_HASH
def BRANCH

def DOCKERHOST
def KUBECONFIG

// Requires "Pipeline Utility Steps" plugin
def loadProperties() {
    def resp = httpRequest "http://hosaka.local/ini/builder.json"
    def content = resp.getContent()
    echo "${content}"
    def props = readJSON text: "${content}"
    echo "${props}"
    env.DOCKERHOST = props["dockerhost"]
    env.KUBECONFIG = props["kubeconfig"]
}

pipeline {
    agent any
    environment {
        ARCH = sh(returnStdout: true, script: 'uname -m').trim()
    }
    stages {
        stage ('Read INI') {
            steps {
                loadProperties()
            }
        }
        stage ('Create Tag Hash') {
            steps {
                script {
                    env.HASHLONG = sh(
                        returnStdout: true,
                        script: "git log -1 --pretty=%H --no-merges"
                    ).trim()
                    env.HASHSHORT = sh(
                        returnStdout: true,
                        script: "git log -1 --pretty=%h --no-merges"
                    ).trim()
                    env.TAG = sh(
                        returnStdout: true,
                        script: "git describe --tags --abbrev=0"
                    ).trim()
                    env.TAG_HASH = "${TAG}-${HASHSHORT}-${ARCH}"
                }
                echo "ARCH: ${env.ARCH}"
                echo "COMMIT: ${env.GIT_COMMIT}"
                echo "HASHLONG: ${env.HASHLONG}"
                echo "HASHSHORT: ${env.HASHSHORT}"
                echo "TAG: ${env.TAG}"
                echo "TAG_HASH: ${env.TAG_HASH}"
            }
        }
        stage ('Deploy to Kubernetes Cluster') {
            steps {
                script {
                    IMG = ("""\
                        ${env.DOCKERHOST}/runxhpl:default-x86_64
                    """.stripIndent().replaceAll("\\s","")
                    )
                }
                sh("""mkdir venv""")
                sh("""python3 -m venv venv""")
                sh("""activate""")
                sh("""python3 -m pip install --upgrade pip setuptools""")
                sh("""python3 -m pip install --force-reinstall git+https://github.com/JustAddRobots/engcommon.git""")
                sh("""\
                        python3 runkubejobs \
                        -d -t runxhpl \
                        -p /var/lib/jenkins/workspace/logs \
                        -n all -i ${IMG}
                    """.stripIndent()
                )
            }
        }
    }        
    post {
        success {
            slackSend(
                color: "good",
                message: """\
                    SUCCESS ${env.JOB_NAME} #${env.BUILD_NUMBER},
                    v${env.TAG_HASH}, Took: ${currentBuild.durationString.replace(
                        ' and counting', ''
                    )} (<${env.BUILD_URL}|Open>)
                """.stripIndent()
            )
        }
        failure {
            slackSend(
                color: "danger",
                message: """\
                    FAILURE ${env.JOB_NAME} #${env.BUILD_NUMBER},
                    v${env.TAG_HASH}, Took: ${currentBuild.durationString.replace(
                        ' and counting', ''
                    )} (<${env.BUILD_URL}|Open>)
                """.stripIndent()
            )
        }
    }
}
