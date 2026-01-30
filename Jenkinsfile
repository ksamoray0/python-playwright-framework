pipeline {
  agent any

  options {
    timestamps()
    ansiColor('xterm')
  }

  parameters {
    choice(
      name: 'BROWSER',
      choices: ['chromium', 'firefox', 'webkit'],
      description: 'Playwright browser engine'
    )
    booleanParam(
      name: 'PW_TRACE',
      defaultValue: false,
      description: 'Enable Playwright tracing'
    )
    string(
      name: 'SLOWMO',
      defaultValue: '0',
      description: 'Slow down Playwright actions in ms'
    )
    choice(
      name: 'SUITE',
      choices: ['smoke', 'e2e', 'all'],
      description: 'Which test suite to run'
    )
    booleanParam(
      name: 'DEBUG',
      defaultValue: false,
      description: 'Print extra debug info (pwd/ls) from inside the container'
    )
  }

  stages {
    stage('Environment check') {
      steps {
        sh '''
          set -e
          echo "Running on Linux agent (Jenkins container)"
          docker --version
          docker ps >/dev/null
        '''
      }
    }

    stage('Run tests (Docker)') {
      steps {
        script {
          def pytestArgs = (params.SUITE == 'all')
            ? "--browser ${params.BROWSER} --slowmo ${params.SLOWMO}"
            : "-m ${params.SUITE} --browser ${params.BROWSER} --slowmo ${params.SLOWMO}"

          // Pull/run inside Playwright Python image; Docker Pipeline will mount Jenkins workspace automatically
          docker.image('mcr.microsoft.com/playwright/python:v1.50.0-jammy').inside {
            sh '''
              set -e
              mkdir -p reports artifacts
              python --version
              pip install -U pip
              pip install -r requirements.txt
            '''

            if (params.DEBUG) {
              sh '''
                echo "--- inside container debug ---"
                pwd
                ls -la
              '''
            }

            if (params.PW_TRACE) {
              sh "PW_TRACE=1 python -m pytest ${pytestArgs}"
            } else {
              sh "python -m pytest ${pytestArgs}"

            }
          }
        }
      }
    }
  }

  post {
    always {
      junit allowEmptyResults: true, testResults: 'reports/junit.xml'
      archiveArtifacts allowEmptyArchive: true, artifacts: 'reports/**/*, artifacts/**/*'
    }
  }
}
