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
  }

  stages {

    stage('Environment check') {
      steps {
        script {
          if (isUnix()) {
            sh '''
              echo "Running on Linux agent"
              which python3 || (echo "ERROR: python3 not found on agent" && exit 1)
              python3 --version
            '''
          } else {
            powershell '''
              Write-Host "Running on Windows agent"
              where python || (Write-Error "Python not found on agent"; exit 1)
              python --version
            '''
          }
        }
      }
    }

    stage('Setup venv') {
      steps {
        script {
          if (isUnix()) {
            sh '''
              set -e
              python3 -m venv .venv
              . .venv/bin/activate
              python -m pip install --upgrade pip
              python -m pip install pytest pytest-html playwright pytest-xdist
              python -m playwright install
            '''
          } else {
            powershell '''
              $ErrorActionPreference = "Stop"

              python -m venv .venv
              .\\.venv\\Scripts\\Activate.ps1

              python -m pip install --upgrade pip
              python -m pip install pytest pytest-html playwright pytest-xdist
              python -m playwright install
            '''
          }
        }
      }
    }

stage('Run tests (Docker)') {
  steps {
    sh '''
      set -e

      mkdir -p reports artifacts

      # Build command for pytest suite selection
      if [ "${SUITE}" = "all" ]; then
        PYTEST_ARGS="--browser ${BROWSER} --slowmo ${SLOWMO}"
      else
        PYTEST_ARGS="-m ${SUITE} --browser ${BROWSER} --slowmo ${SLOWMO}"
      fi

      # Trace toggle
      if [ "${PW_TRACE}" = "true" ]; then
        export PW_TRACE=1
      else
        unset PW_TRACE || true
      fi

      docker run --rm \
        -e BROWSER="${BROWSER}" \
        -e SLOWMO="${SLOWMO}" \
        -e SUITE="${SUITE}" \
        -e PW_TRACE="${PW_TRACE}" \
        -e PW_TRACE=1 \
        -v "$PWD:/work" \
        -w /work \
        mcr.microsoft.com/playwright/python:v1.50.0-jammy \
        bash -lc "
          python --version
          pip install -U pip
          pip install -r requirements.txt
          pytest -q ${PYTEST_ARGS} --junitxml=reports/junit.xml
        "
    '''
  }
}


  } // end stages

  post {
    always {
      junit allowEmptyResults: true, testResults: 'reports/junit.xml'
      archiveArtifacts allowEmptyArchive: true, artifacts: 'reports/**/*, artifacts/**/*'
    }
  }
}
