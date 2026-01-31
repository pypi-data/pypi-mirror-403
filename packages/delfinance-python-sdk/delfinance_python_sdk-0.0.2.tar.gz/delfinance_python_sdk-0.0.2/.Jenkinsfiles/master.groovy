def pipelineRoll() {

    stage('Checkout') {
        withCredentials([usernamePassword(credentialsId: 'giteauth', usernameVariable: 'GIT_USERNAME', passwordVariable: 'GIT_PASSWORD')]) {
            echo '---------------------GitHub Checkout started!----------------------'
            sh '''
              apt-get update
              apt-get install -y git ca-certificates
            '''
            sh 'rm -rf ${GIT_REPO_NAME}'
            sh 'git clone https://${GIT_USERNAME}:${GIT_PASSWORD}@git.delbank.srv.br/DelbankDev/${GIT_REPO_NAME}.git'

                dir("${GIT_REPO_NAME}") {
                sh "git checkout ${env.BRANCH_NAME}"
                sh 'git fetch --all --tags'
                def tagged = sh(
                                script: 'git tag --points-at HEAD',
                                returnStdout: true
                            ).trim()

                def tag = sh(
                            script: 'git describe --tags --abbrev=0 2>/dev/null || echo 0.0.0',
                            returnStdout: true
                            ).trim()

                if (tagged) {
                    env.VERSION = "${tag}"
                } else {
                    def sha = sh(
                            script: 'git rev-parse --short HEAD',
                            returnStdout: true
                            ).trim()

                    env.VERSION = "${tag}b${TAG}"    
                }
            }
            echo '---------------------GitHub Checkout finished!---------------------'
        }
    }

    stage('Generating Artifact') {
        echo "Python artifact will be generated"
        sh 'git tag $VERSION'
        sh 'rm -rf /dist'
        sh 'pip install -U pip setuptools wheel'
        sh 'pip install -r requirements.txt'
        sh """
            python setup.py sdist bdist_wheel
            """
        sh 'pip install -U pip twine'
    }

    stage('Publish to Gitea') {
        withCredentials([
            string(credentialsId: 'gitea-package-publisher', variable: 'GITEA_TOKEN')
        ]) {
            sh """
                export TWINE_USERNAME=__token__
                export TWINE_PASSWORD=$GITEA_TOKEN
              
                twine upload   --repository-url $GITEA_PYPI_SOURCE dist/delfinance_python_sdk-$VERSION*
            """
        }
    }

}

return this

