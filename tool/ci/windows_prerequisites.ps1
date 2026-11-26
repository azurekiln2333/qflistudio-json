# Cloud inspection only. Do not install or modify Visual Studio on a local PC.
$ErrorActionPreference = 'Stop'
if ($env:GITHUB_ACTIONS -ne 'true') { throw 'cloud-only: Windows prerequisites require GitHub Actions' }
$vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
if (-not (Test-Path $vswhere)) { throw 'dependency-blocked: vswhere is missing' }
$vs = & $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 Microsoft.VisualStudio.Component.VC.ATL -property installationPath
if ($LASTEXITCODE -ne 0 -or -not $vs) { throw 'dependency-blocked: Visual Studio x64 C++ tools and ATL component are required' }
$atl = Get-ChildItem (Join-Path $vs 'VC/Tools/MSVC/*/atlmfc/include/atlbase.h') -File -ErrorAction SilentlyContinue
if (-not $atl) { throw 'dependency-blocked: ATL headers are missing' }
$redist = Get-ChildItem (Join-Path $vs 'VC/Redist/MSVC/*/x64/Microsoft.VC143.CRT') -Directory -ErrorAction SilentlyContinue | Sort-Object FullName | Select-Object -Last 1
if (-not $redist) { throw 'dependency-blocked: redistributable VC143 x64 runtime directory is missing' }
"QFLI_MSVC_REDIST=$($redist.FullName)" | Out-File -FilePath $env:GITHUB_ENV -Encoding utf8 -Append
New-Item -ItemType Directory -Force 'build/ci-state' | Out-Null
@{ visual_studio = $vs; atl_header_present = $true; msvc_redist = $redist.FullName; inno_setup_present = (Test-Path "${env:ProgramFiles(x86)}/Inno Setup 6/ISCC.exe") } | ConvertTo-Json | Set-Content -Encoding utf8 'build/ci-state/windows-prerequisites.json'
