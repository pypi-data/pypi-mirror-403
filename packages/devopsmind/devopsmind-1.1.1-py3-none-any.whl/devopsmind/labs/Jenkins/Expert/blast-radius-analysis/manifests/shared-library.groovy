def buildApp() {
  sh 'mvn clean package'
}

def runTests() {
  error 'Test framework misconfiguration'
}
