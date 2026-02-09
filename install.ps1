# Prometheux MCP Server - Installation Script for Windows
# PowerShell script for automated installation

$ErrorActionPreference = "Stop"

Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Blue
Write-Host "║   Prometheux MCP Server - Installation Script             ║" -ForegroundColor Blue
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Blue
Write-Host ""

# Step 1: Check/Install pipx
Write-Host "[Step 1/5] Checking for pipx..." -ForegroundColor Blue

if (Get-Command pipx -ErrorAction SilentlyContinue) {
    Write-Host "✓ pipx is already installed" -ForegroundColor Green
} else {
    Write-Host "⚠ pipx not found. Installing pipx..." -ForegroundColor Yellow
    python -m pip install --user pipx
    python -m pipx ensurepath
    Write-Host "✓ pipx installed successfully" -ForegroundColor Green
    Write-Host "⚠ Please restart your terminal and run this script again" -ForegroundColor Yellow
    exit 0
}

Write-Host ""

# Step 2: Install prometheux-mcp
Write-Host "[Step 2/5] Installing prometheux-mcp package..." -ForegroundColor Blue

$pipxList = pipx list 2>&1 | Out-String
if ($pipxList -match "prometheux-mcp") {
    Write-Host "⚠ prometheux-mcp is already installed. Upgrading..." -ForegroundColor Yellow
    pipx upgrade prometheux-mcp
    if ($LASTEXITCODE -ne 0) {
        pipx install prometheux-mcp --force
    }
} else {
    pipx install prometheux-mcp
}

Write-Host "✓ prometheux-mcp installed successfully" -ForegroundColor Green
Write-Host ""

# Step 3: Collect credentials
Write-Host "[Step 3/5] Please provide your Prometheux credentials..." -ForegroundColor Blue
Write-Host ""

$PROMETHEUX_URL = Read-Host "Prometheux API URL (press Enter for default: https://api.prometheux.ai)"
if ([string]::IsNullOrWhiteSpace($PROMETHEUX_URL)) {
    $PROMETHEUX_URL = "https://api.prometheux.ai"
}

do {
    $PROMETHEUX_USERNAME = Read-Host "Username"
    if ([string]::IsNullOrWhiteSpace($PROMETHEUX_USERNAME)) {
        Write-Host "Username is required" -ForegroundColor Red
    }
} while ([string]::IsNullOrWhiteSpace($PROMETHEUX_USERNAME))

do {
    $PROMETHEUX_ORGANIZATION = Read-Host "Organization"
    if ([string]::IsNullOrWhiteSpace($PROMETHEUX_ORGANIZATION)) {
        Write-Host "Organization is required" -ForegroundColor Red
    }
} while ([string]::IsNullOrWhiteSpace($PROMETHEUX_ORGANIZATION))

do {
    $PROMETHEUX_TOKEN = Read-Host "Authentication Token" -AsSecureString
    $PROMETHEUX_TOKEN_PLAIN = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($PROMETHEUX_TOKEN))
    if ([string]::IsNullOrWhiteSpace($PROMETHEUX_TOKEN_PLAIN)) {
        Write-Host "Token is required" -ForegroundColor Red
    }
} while ([string]::IsNullOrWhiteSpace($PROMETHEUX_TOKEN_PLAIN))

Write-Host ""
Write-Host "✓ Credentials collected" -ForegroundColor Green
Write-Host ""

# Step 4: Configure Claude Desktop
Write-Host "[Step 4/5] Configuring Claude Desktop..." -ForegroundColor Blue

$CONFIG_DIR = "$env:APPDATA\Claude"
$CONFIG_FILE = "$CONFIG_DIR\claude_desktop_config.json"

# Create directory if it doesn't exist
if (-not (Test-Path $CONFIG_DIR)) {
    New-Item -ItemType Directory -Path $CONFIG_DIR | Out-Null
}

# Get the full path to prometheux-mcp
$PROMETHEUX_MCP_PATH = (Get-Command prometheux-mcp -ErrorAction SilentlyContinue).Source
if ([string]::IsNullOrWhiteSpace($PROMETHEUX_MCP_PATH)) {
    $PROMETHEUX_MCP_PATH = "$env:USERPROFILE\.local\bin\prometheux-mcp.exe"
}

# Escape backslashes for JSON
$PROMETHEUX_MCP_PATH = $PROMETHEUX_MCP_PATH -replace '\\', '\\'

# Create or update config file
if (Test-Path $CONFIG_FILE) {
    Write-Host "⚠ Config file already exists. Creating backup..." -ForegroundColor Yellow
    $backupFile = "$CONFIG_FILE.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Copy-Item $CONFIG_FILE $backupFile
    
    # Read existing config
    $config = Get-Content $CONFIG_FILE -Raw | ConvertFrom-Json
    
    # Ensure mcpServers exists
    if (-not $config.mcpServers) {
        $config | Add-Member -MemberType NoteProperty -Name "mcpServers" -Value @{} -Force
    }
    
    # Add/Update prometheux entry
    $prometheuxConfig = @{
        command = $PROMETHEUX_MCP_PATH
        args = @("--url", $PROMETHEUX_URL)
        env = @{
            PROMETHEUX_TOKEN = $PROMETHEUX_TOKEN_PLAIN
            PROMETHEUX_USERNAME = $PROMETHEUX_USERNAME
            PROMETHEUX_ORGANIZATION = $PROMETHEUX_ORGANIZATION
        }
    }
    
    $config.mcpServers | Add-Member -MemberType NoteProperty -Name "prometheux" -Value $prometheuxConfig -Force
    
    $config | ConvertTo-Json -Depth 10 | Set-Content $CONFIG_FILE
    Write-Host "✓ Configuration updated" -ForegroundColor Green
} else {
    # Create new config file
    $config = @{
        mcpServers = @{
            prometheux = @{
                command = $PROMETHEUX_MCP_PATH
                args = @("--url", $PROMETHEUX_URL)
                env = @{
                    PROMETHEUX_TOKEN = $PROMETHEUX_TOKEN_PLAIN
                    PROMETHEUX_USERNAME = $PROMETHEUX_USERNAME
                    PROMETHEUX_ORGANIZATION = $PROMETHEUX_ORGANIZATION
                }
            }
        }
    }
    
    $config | ConvertTo-Json -Depth 10 | Set-Content $CONFIG_FILE
    Write-Host "✓ Configuration file created" -ForegroundColor Green
}

Write-Host ""

# Step 5: Final instructions
Write-Host "[Step 5/5] Installation complete!" -ForegroundColor Blue
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                 Installation Successful! 🎉                ║" -ForegroundColor Green
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  1. Restart Claude Desktop completely (Right-click → Quit, then reopen)"
Write-Host "  2. Look for the 🔨 (hammer) icon in Claude Desktop"
Write-Host "  3. Verify 'Prometheux Knowledge Graph' appears in the tools list"
Write-Host "  4. Test by asking Claude: 'List my Prometheux concepts'"
Write-Host ""
Write-Host "Configuration saved to:" -ForegroundColor Blue
Write-Host "  $CONFIG_FILE"
Write-Host ""
if (Test-Path "$CONFIG_FILE.backup.*") {
    Write-Host "Backup created:" -ForegroundColor Blue
    Write-Host "  $(Get-ChildItem "$CONFIG_FILE.backup.*" | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Select-Object -ExpandProperty FullName)"
}
Write-Host ""
Write-Host "Troubleshooting:" -ForegroundColor Yellow
Write-Host "  • If tools don't appear, check Claude Desktop logs"
Write-Host "  • Windows logs: %APPDATA%\Claude\logs\"
Write-Host ""
Write-Host "For support: davben@prometheux.co.uk, teodoro.baldazzi@prometheux.co.uk, support@prometheux.co.uk" -ForegroundColor Green
Write-Host ""
