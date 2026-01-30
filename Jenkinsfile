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
        sh '''
          set -e

          mkdir -p reports artifacts

          if [ "${SUITE}" = "all" ]; then
            PYTEST_ARGS="--browser ${BROWSER} --slowmo ${SLOWMO}"
          else
            PYTEST_ARGS="-m ${SUITE} --browser ${BROWSER} --slowmo ${SLOWMO}"
          fi

          # PW_TRACE is a Jenkins booleanParam; in shell it appears as "true"/"false"
          if [ "${PW_TRACE}" = "true" ]; then
            export PW_TRACE=1
          else
            unset PW_TRACE || true
          fi
          echo '--- on jenkins agent: pwd ---'
          pwd
          echo '--- on jenkins agent: ls -la ---'
          ls -la
          docker run --rm \
            -e PW_TRACE="${PW_TRACE:-}" \
            -v "/workspace/python-playwright-framework:/work" \
            -w /work \
            mcr.microsoft.com/playwright/python:v1.50.0-jammy \
            bash -lc "
              echo '--- inside container: pwd ---'
              pwd
              echo '--- inside container: ls -la ---'
              ls -la
              echo '--- inside container: find requirements ---'
              find . -maxdepth 3 -iname 'requirements*.txt' -print
              echo '--- python version ---'
              python --version
              echo '--- installing ---'
              pip install -U pip
              pip install -r requirements.txt
              pytest ${PYTEST_ARGS}
            "
        '''
      }
    }
  }

post {
  always {
    junit allowEmptyResults: true, testResults: '/workspace/python-playwright-framework/reports/junit.xml'
    archiveArtifacts allowEmptyArchive: true, artifacts: '/workspace/python-playwright-framework/reports/**/*, /workspace/python-playwright-framework/artifacts/**/*'
  }
}

}
