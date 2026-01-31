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
    // persistent cache location in Jenkins home (shared via volumes-from)
    PIP_CACHE_DIR = '/var/jenkins_home/.cache/pip'
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

          // Detect the current Jenkins container id (works for Docker-in-Docker style setups)
          def jenkinsCid = sh(
            returnStdout: true,
            script: '''
              set -e
              # common: /docker/<id>
              CID="$(cat /proc/1/cpuset 2>/dev/null | sed -n 's#.*/docker/\\([0-9a-f]\\{12,64\\}\\).*#\\1#p')"
              if [ -z "$CID" ]; then
                # fallback
                CID="$(hostname | tr -d '\\n')"
              fi
              echo "$CID"
            '''
          ).trim()

          sh """
            set -e

            # Ensure cache dir exists (inside Jenkins container filesystem)
            mkdir -p "${PIP_CACHE_DIR}"
            chmod -R a+rwx "${PIP_CACHE_DIR}" || true

            # Pull only if missing (keeps output clean)
            docker image inspect ${env.PW_IMAGE} >/dev/null 2>&1 || docker pull ${env.PW_IMAGE}

            # Run Playwright container sharing Jenkins container volumes (workspace + jenkins_home)
            docker run --rm \\
              --volumes-from ${jenkinsCid} \\
              -u 1000:1000 \\
              -w "${WORKSPACE}" \\
              -e ${traceEnv} \\
              -e PIP_DISABLE_PIP_VERSION_CHECK=1 \\
              -e PIP_CACHE_DIR="${PIP_CACHE_DIR}" \\
              ${env.PW_IMAGE} \\
              bash -lc '
                set -e
                mkdir -p reports artifacts

                if [ "${params.DEBUG}" = "true" ]; then
                  echo "--- debug ---"
                  pwd
                  ls -la
                  echo "--- debug end ---"
                fi

                echo "--- python ---"
                python --version

                echo "--- install deps ---"
                export PATH="/home/pwuser/.local/bin:$PATH"
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
