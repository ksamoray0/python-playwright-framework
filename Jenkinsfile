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
    PIP_CACHE_DIR = '.pip-cache'
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
          def suiteArgs = (params.SUITE == 'all') ? '' : "-m ${params.SUITE}"
          def pytestArgs = "${suiteArgs} --browser ${params.BROWSER} --slowmo ${params.SLOWMO}"
          def traceEnv = params.PW_TRACE ? 'PW_TRACE=1' : 'PW_TRACE=0'

          // Pull only if missing (silent)
          sh """
            set -e
            docker image inspect ${env.PW_IMAGE} >/dev/null 2>&1 || docker pull ${env.PW_IMAGE}
          """

          sh """
            set -e
            mkdir -p reports artifacts ${env.PIP_CACHE_DIR}

            docker run --rm \\
              -u 1000:1000 \\
              -w /work \\
              -e ${traceEnv} \\
              -e PIP_DISABLE_PIP_VERSION_CHECK=1 \\
              -e PIP_CACHE_DIR=/work/${env.PIP_CACHE_DIR} \\
              -v "\$PWD:/work" \\
              ${env.PW_IMAGE} \\
              bash -lc '
                if [ "${params.DEBUG}" = "true" ]; then
                  echo "--- debug ---"
                  pwd
                  ls -la
                  echo "--- debug end ---"
                fi

                echo "--- python ---"
                python --version

                echo "--- install deps ---"
                export PATH="/home/pwuser/.local/bin:\$PATH"
                python -m pip install --user -r requirements.txt

                echo "--- run tests ---"
                python -m pytest ${pytestArgs} --junitxml=reports/junit.xml --html=reports/report.html --self-contained-html
              '
          """
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
