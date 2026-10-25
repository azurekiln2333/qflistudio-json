param([Parameter(Mandatory=$true)][string]$Config)
$ErrorActionPreference='Stop'
$jsonBuild=Get-Content -LiteralPath $Config -Raw | ConvertFrom-Json
Set-Location -LiteralPath $jsonBuild.cwd
$jsonArguments=[string[]]$jsonBuild.arguments
& $jsonBuild.executable @jsonArguments
exit $LASTEXITCODE
