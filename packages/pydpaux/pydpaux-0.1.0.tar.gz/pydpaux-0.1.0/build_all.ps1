# ! For package maintainers only !
# Build script for pydpaux with all Python versions
# Usage: .\build_all.ps1

# Define Python versions to build
$PYTHON_VERSIONS = @('3.9', '3.10', '3.11', '3.12', '3.13', '3.14')
#$PYTHON_VERSIONS = @('3.9')

Write-Host "[*] Starting multi-version build process..." -ForegroundColor Cyan
Write-Host ""

# Loop through each Python version
foreach ($pythonVersion in $PYTHON_VERSIONS) {
    Write-Host "============================================================" -ForegroundColor Yellow
    Write-Host "[BUILD] Python $pythonVersion" -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Yellow
    Write-Host ""
    
    $venvDir = "venvs\.venv$pythonVersion"
    
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
    
    if (-not (Test-Path $venvDir)) {
        Write-Host "[2] Creating virtual environment..."
        & $pythonPath -m venv $venvDir
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] Failed to create virtual environment for Python $pythonVersion" -ForegroundColor Red
            exit 1
        }
        Write-Host "[2] Virtual environment created successfully"
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] Failed to install build package for Python $pythonVersion" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "[2] Virtual environment already exists"
    }
    Write-Host ""
    
    # Activate virtual environment and build
    Write-Host "[3] Activating virtual environment..."
    $activateScript = "$venvDir\Scripts\Activate.ps1"
    
    & $activateScript

    Write-Host  "Python executable in venv:"
    Write-Host (Get-Command python).Path -ForegroundColor Green

    #Write-Host "[*] Press any key to continue with the build..." -ForegroundColor Cyan
    #$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

    Write-Host "[4] Installing build package..."
    python -m pip install --upgrade pip build

    Write-Host ""
  
    # Build project
    Write-Host "[5] Building project with Python $pythonVersion..."

    python -m build

    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Build failed for Python $pythonVersion" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "[SUCCESS] Build completed for Python $pythonVersion" -ForegroundColor Green
    Write-Host ""
}

Write-Host "============================================================" -ForegroundColor Yellow
Write-Host "[SUCCESS] All builds completed successfully!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Yellow
exit 0

