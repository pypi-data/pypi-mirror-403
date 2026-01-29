```bash
# Build
dotnet build

# Run all tests
dotnet test

# Run tests with coverage
rm -rf ./TestResults
dotnet test --collect:"XPlat Code Coverage" --results-directory ./TestResults
reportgenerator -reports:"./TestResults/*/coverage.cobertura.xml" -targetdir:"./TestResults/CoverageReport" -reporttypes:TextSummary
cat ./TestResults/CoverageReport/Summary.txt

# Run single test class
dotnet test --filter "ClassName"

# Run single test method
dotnet test --filter "ClassName.MethodName"

# Run specific test project
dotnet test tests/Project.Tests

# Format code
dotnet format

# Watch mode
dotnet watch --project src/Project
```