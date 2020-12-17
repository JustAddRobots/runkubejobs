#!/usr/bin/env groovy

// This Jenkinsfile automatically buids the repos tagged commits
// (releases/candidates/etc.)

def HASHLONG
def HASHSHORT
def TAG
def TAG_HASH
def MMP
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
                    env.TAG_HASH = "${env.TAG}-${env.HASHSHORT}-${env.ARCH}"
                }
                echo "ARCH: ${env.ARCH}"
                echo "COMMIT: ${env.GIT_COMMIT}"
                echo "HASHLONG: ${env.HASHLONG}"
                echo "HASHSHORT: ${env.HASHSHORT}"
                echo "TAG: ${env.TAG}"
                echo "TAG_HASH: ${env.TAG_HASH}"
                slackSend(
                    message: """\
                        STARTED ${env.JOB_NAME} #${env.BUILD_NUMBER},
                        v${env.TAG_HASH} (<${env.BUILD_URL}|Open>)
                    """.stripIndent()
                )
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
                withCredentials([usernamePassword(
                    credentialsId: 'github-runxhpl-multibranch-stage',
                    passwordVariable: 'GIT_PASSWORD',
                    usernameVariable: 'GIT_USERNAME'
                )]){
                    sh("""mkdir venv
                        python3 -m venv venv
                        source venv/bin/activate
                        python3 -m pip install --upgrade pip
                        python3 -m pip install --force-reinstall git+ssh://runkubejobs.github.com/JustAddRobots/runkubejobs.git@${env.HASHSHORT}
                        runkubejobs \
                            --debug --task runxhpl \
                            --prefix /var/lib/jenkins/workspace/logs \
                            --nodes all --image ${IMG}
                    """.stripIndent())
                }
            }
        }
        stage('Delete RC Tags') {
            when {
                branch 'foo'  // disabled for now, See ISSUE-030.
            }
            steps {
                script {
                    (mmp, _) = "${env.TAG}".tokenize("-") // Major Minor Patch
                    env.MMP = "${mmp}"
                    echo "TAG: ${env.TAG}"
                    echo "MMP: ${env.MMP}"
                    withCredentials([usernamePassword(
                        credentialsId: 'github-runxhpl-multibranch-stage',
                        passwordVariable: 'GIT_PASSWORD',
                        usernameVariable: 'GIT_USERNAME'
                    )]){
                        sh("""git push --delete https://${env.GIT_USERNAME}:${env.GIT_PASSWORD}@github.com/JustAddRobots/runkubejobs.git \$(git tag -l "${env.MMP}-rc*")""")
                        sh("""git tag -d \$(git tag -l "${env.MMP}-rc*")""")
                    }
                }
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
