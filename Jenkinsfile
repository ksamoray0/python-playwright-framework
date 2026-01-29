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

    stage('Run tests') {
      steps {
        script {
          if (isUnix()) {
            sh '''
              set -e
              . .venv/bin/activate

              if [ "${PW_TRACE}" = "true" ]; then
                export PW_TRACE=1
              else
                unset PW_TRACE || true
              fi

              if [ "${SUITE}" = "all" ]; then
                python -m pytest --browser ${BROWSER} --slowmo ${SLOWMO}
              else
                python -m pytest -m ${SUITE} --browser ${BROWSER} --slowmo ${SLOWMO}
              fi
            '''
          } else {
            powershell '''
              $ErrorActionPreference = "Stop"

              .\\.venv\\Scripts\\Activate.ps1

              if ("${env:PW_TRACE}" -eq "true") {
                $env:PW_TRACE = "1"
              } else {
                Remove-Item Env:PW_TRACE -ErrorAction SilentlyContinue
              }

              $args = @("--browser", "${env:BROWSER}", "--slowmo", "${env:SLOWMO}")

              if ("${env:SUITE}" -ne "all") {
                $args += @("-m", "${env:SUITE}")
              }

              python -m pytest @args
            '''
          }
        }
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
