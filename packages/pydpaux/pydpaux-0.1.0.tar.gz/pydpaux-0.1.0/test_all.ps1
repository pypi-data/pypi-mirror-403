# ! For package maintainers only !
# Test script for pydpaux with all Python versions
# Usage: .\test_all.ps1

# Define Python versions to test
$PYTHON_VERSIONS = @('3.9', '3.10', '3.11', '3.12', '3.13', '3.14')
#$PYTHON_VERSIONS = @('3.9')

Write-Host "[*] Starting multi-version test process..." -ForegroundColor Cyan
Write-Host ""

$testDir = "test_venvs"
if (Test-Path $testDir) {
    remove-item "$testDir" -Recurse -Force
} 

New-Item -ItemType Directory -Path $testDir | Out-Null

# Retrieve module version from *.tar.gz file
$tarGzFile = Get-ChildItem -Path "dist" -Filter "*.tar.gz" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($tarGzFile) {
    # Extract version from filename (e.g., pydpaux-0.1.0.tar.gz -> 0.1.0)
    if ($tarGzFile.Name -match ".*-(\d+\.\d+\.\d+)\.tar\.gz") {
        $moduleVersion = $matches[1]
        Write-Host "[*] Module version: $moduleVersion" -ForegroundColor Green
    }
}
else{
    Write-Host "[ERROR] No .tar.gz file found in dist directory" -ForegroundColor Red
    exit 1
}


# Loop through each Python version
foreach ($pythonVersion in $PYTHON_VERSIONS) {
    Write-Host "============================================================" -ForegroundColor Yellow
    Write-Host "[TEST] Python $pythonVersion" -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Yellow
    Write-Host ""
    
    $venvDir = "$testDir\.venv$pythonVersion"
    
    # Set Python version using pyenv
    Write-Host "[1] Setting Python $pythonVersion as local version..."
    pyenv local $pythonVersion
    
    # Get the Python executable path from pyenv
    $pythonPath = pyenv which python 2>&1 | Out-String    
    
    $pythonPath = $pythonPath.Trim()
    if (-not $pythonPath) {
        Write-Host "[ERROR] Could not find Python $pythonVersion in pyenv" -ForegroundColor Red
        exit 1
    }
    else {
        #Write-Host "[1] Python executable path from pyenv: $pythonPath"
    }
    
    # Verify Python version
    Write-Host "[1] Verifying Python $pythonVersion is available..."
    $versionOutput = & $pythonPath --version 2>&1 | Out-String    
    $versionOutput = $versionOutput.Trim()
    Write-Host $versionOutput
    
    # Extract and check version - match format "Python X.Y.Z"
    if ($versionOutput -match "Python (\d+\.\d+)") {
        $detectedVersion = $matches[1]
        if ($detectedVersion -ne $pythonVersion) {
            Write-Host "[ERROR] Python version mismatch! Expected $pythonVersion but got $detectedVersion" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "[ERROR] Could not parse Python version from: $versionOutput" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "[1] Python version verified: $versionOutput" -ForegroundColor Green
    Write-Host "Python executable path: $pythonPath" -ForegroundColor Green
    
    # Check and create virtual environment
    Write-Host "[2] Checking virtual environment at $venvDir..."
    
    
    Write-Host "[2] Creating virtual environment..."
    & $pythonPath -m venv $venvDir
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to create virtual environment for Python $pythonVersion" -ForegroundColor Red
        exit 1
    }
    Write-Host "[2] Virtual environment created successfully"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to install test package for Python $pythonVersion" -ForegroundColor Red
        exit 1
    }

    Write-Host ""
    
    # Activate virtual environment and test
    Write-Host "[3] Activating virtual environment..."
    $activateScript = "$venvDir\Scripts\Activate.ps1"
    
    & $activateScript

    Write-Host  "Python executable in venv:"
    Write-Host (Get-Command python).Path -ForegroundColor Green

    Write-Host "[4] Installing target package..."
    pip install --find-links=dist pydpaux==$moduleVersion

    Write-Host ""
  
    # Run test and capture output
    $testOutput = python test\test.py 2>&1 | Out-String
    Write-Host $testOutput
    
    # Check if test passed by looking for "Test result OK" in output
    if ($testOutput -match "Test result OK.") {
        Write-Host "[SUCCESS] Test passed for Python $pythonVersion - 'Test result OK' found in output" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Test failed for Python $pythonVersion - 'Test result OK' not found in output" -ForegroundColor Red
        exit 1
    }

    #Write-Host "[*] Press any key to continue with the test..." -ForegroundColor Cyan
    #$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

    
    Write-Host "[SUCCESS] Test completed for Python $pythonVersion" -ForegroundColor Green
    Write-Host ""
}

remove-item "$testDir" -Recurse -Force

Write-Host "============================================================" -ForegroundColor Yellow
Write-Host "[SUCCESS] All tests completed successfully!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Yellow
exit 0

