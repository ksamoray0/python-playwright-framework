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

  environment {
    PW_IMAGE = 'mcr.microsoft.com/playwright/python:v1.58.0-jammy'
    PIP_CACHE_DIR = "${WORKSPACE}/.pip-cache"
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
          def suiteArgs = (params.SUITE == 'all')
            ? ""
            : "-m ${params.SUITE}"

          def pytestArgs = "${suiteArgs} --browser ${params.BROWSER} --slowmo ${params.SLOWMO}"

          def traceEnv = params.PW_TRACE ? "PW_TRACE=1" : "PW_TRACE=0"

            // Ensure image exists (silent)
            sh """
              set -e
              docker image inspect ${env.PW_IMAGE} >/dev/null 2>&1 || docker pull ${env.PW_IMAGE}
            """

          docker.image(env.PW_IMAGE).inside {
            sh """
              set -e
              mkdir -p reports artifacts

              ${params.DEBUG ? 'echo "--- debug ---"; pwd; ls -la; echo "--- debug end ---"' : ''}

              echo '--- python ---'
              python --version

              echo '--- install deps ---'
              export PIP_DISABLE_PIP_VERSION_CHECK=1
              export PATH="/home/pwuser/.local/bin:$PATH"
              python -m pip install --cache-dir "${env.PIP_CACHE_DIR}" --user -r requirements.txt

              echo '--- run tests ---'
              ${traceEnv} python -m pytest ${pytestArgs} --junitxml=reports/junit.xml --html=reports/report.html --self-contained-html
            """
          }
        }
      }
    }
  }

  post {
    always {
      junit allowEmptyResults: true, testResults: 'reports/junit.xml'
      archiveArtifacts allowEmptyArchive: true, artifacts: 'reports/**/*, artifacts/**/*, .pip-cache/**/*'
    }
  }
}
