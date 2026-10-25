#requires -Version 7.0
param(
  [Parameter(Mandatory=$true)][int]$GrantEvent,
  [Parameter(Mandatory=$true)][string]$PreparedManifest,
  [Parameter(Mandatory=$true)][string]$NextOwner,
  [ValidateRange(90,240)][int]$MaxSeconds=240
)
$ErrorActionPreference='Stop'
$jsonWindowRoot='D:/MyNewProjects/qfli_json'
$jsonWindowId=[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')+'-'+[Guid]::NewGuid().ToString('N').Substring(0,8)
$jsonWindowOut="$jsonWindowRoot/build/native-window-artifacts/$jsonWindowId"
$jsonWindowClock=[Diagnostics.Stopwatch]::StartNew()
$jsonWindowPwsh=Join-Path $PSHOME 'pwsh.exe'
$jsonWindowChildScript="$jsonWindowRoot/.trellis/.runtime/run_json_ohos_release.ps1"
$jsonWindowRecord=[ordered]@{schemaVersion=1;grant=$GrantEvent;nextOwner=$NextOwner;startedUtc=[DateTime]::UtcNow.ToString('o');scope='isolated unsigned x64 package validation; no device';maxSeconds=$MaxSeconds;exit=1;terminal=$false;handoffReady=$false;handoffMeaning='ownership only; not runtime acceptance';finalGatePassed=$false;error=$null;rows=@();childResult=$null;childExit=$null;childGatePassed=$false;identityDrift=@();budgetExceeded=$false}
function Get-JsonWindowSha([string]$Path){
  $stream=[IO.File]::OpenRead($Path);$sha=[Security.Cryptography.SHA256]::Create()
  try{return ([BitConverter]::ToString($sha.ComputeHash($stream))).Replace('-','').ToLowerInvariant()}
  finally{$sha.Dispose();$stream.Dispose()}
}
function Save-JsonWindow {
  [IO.File]::WriteAllText("$jsonWindowOut/result.json",($jsonWindowRecord | ConvertTo-Json -Depth 14),[Text.UTF8Encoding]::new($false))
}
function Invoke-JsonWindowOwned([string]$Name,[string]$Program,[string[]]$Arguments,[int]$WaitMilliseconds){
  if($WaitMilliseconds -le 0){throw "No remaining wait budget for $Name"}
  $row=[ordered]@{name=$Name;started=$false;pid=$null;exit=$null;treeEmpty=$null;timedOut=$false;residualCleanup=$false;error=$null;allowedWaitMilliseconds=$WaitMilliseconds;elapsedMilliseconds=$null;observedProcessIds=@()}
  $jsonWindowRecord.rows+= $row
  $watch=[Diagnostics.Stopwatch]::StartNew()
  $callback=[Action[int]]{param($ownedPid);$row.pid=$ownedPid;Save-JsonWindow;Write-Host "JSON WINDOW LIVE $Name PID=$ownedPid"}
  $row.started=$true
  $run=[QfliLuaAudit.BoundedProcess]::Run($Program,$Arguments,$jsonWindowRoot,"$jsonWindowOut/$Name.log","$jsonWindowOut/$Name.stderr.log",$WaitMilliseconds,$callback)
  $row.pid=$run.RootProcessId;$row.exit=$run.RootExitCode;$row.treeEmpty=$run.TreeEmpty;$row.timedOut=$run.TimedOut;$row.residualCleanup=$run.ResidualTreeTerminated;$row.error=$run.Error;$row.observedProcessIds=@($run.ObservedProcessIds);$row.elapsedMilliseconds=$watch.ElapsedMilliseconds
  Save-JsonWindow
  return $row
}
function Invoke-JsonWindowMessage([string]$Name,[string]$Message,[int]$WaitMilliseconds){
  $textPath="$jsonWindowOut/$Name.txt"
  [IO.File]::WriteAllText($textPath,$Message,[Text.UTF8Encoding]::new($false))
  $tool=(Get-Command trellis -ErrorAction Stop).Source.Replace("'","''")
  $escapedText=$textPath.Replace("'","''")
  $command="& '$tool' channel send qfli-core-release-sync --scope global --as json-offline-1022 --text-file '$escapedText'; exit `$LASTEXITCODE"
  $encoded=[Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($command))
  return Invoke-JsonWindowOwned $Name $jsonWindowPwsh ([string[]]@('-NoProfile','-NonInteractive','-EncodedCommand',$encoded)) $WaitMilliseconds
}
function Test-JsonWindowRow($Row){return $Row -and $Row.exit -eq 0 -and $Row.treeEmpty -eq $true -and !$Row.timedOut -and !$Row.error}
try {
  [IO.Directory]::CreateDirectory($jsonWindowOut) | Out-Null
  if($PSVersionTable.PSEdition -ne 'Core' -or !(Test-Path -LiteralPath $jsonWindowPwsh -PathType Leaf)){throw 'PowerShell Core executable required.'}
  Add-Type -Path "$jsonWindowRoot/.trellis/.runtime/json-bounded-process.cs"
  $jsonWindowIdentityPaths=@($PSCommandPath,$jsonWindowChildScript,"$jsonWindowRoot/.trellis/.runtime/json-bounded-process.cs",(Resolve-Path -LiteralPath $PreparedManifest).Path,$jsonWindowPwsh)
  $jsonWindowRecord.identities=[ordered]@{}
  foreach($path in $jsonWindowIdentityPaths){$jsonWindowRecord.identities[$path]=Get-JsonWindowSha $path}
  Save-JsonWindow
  $accept=Invoke-JsonWindowMessage 'acceptance' "JSON ACCEPT fresh grant$GrantEvent; same-invocation observer started. Exact successor=$NextOwner. No historical grant replay. Total window<=${MaxSeconds}s, including owned cleanup and final relay. Frozen isolated unsigned x64 harness+normal only; no device/ARM64/signing claim. Observer evidence=$jsonWindowOut/result.json." 5000
  if(!(Test-JsonWindowRow $accept)){throw 'Acceptance transport was not confirmed terminal and successful; validation not started.'}
  # One current-job cleanup (10s), final relay/wait+cleanup (15s), and IO margin (5s).
  $mainWait=[int](($MaxSeconds-30)*1000-$jsonWindowClock.ElapsedMilliseconds)
  $childMax=[int][Math]::Floor($mainWait/1000)-10
  if($childMax -lt 90){throw 'Too little budget remains to start validation.'}
  $childArgs=[string[]]@('-NoProfile','-NonInteractive','-File',$jsonWindowChildScript,'-GrantEvent',"$GrantEvent",'-PreparedManifest',$PreparedManifest,'-NextOwner',$NextOwner,'-MaxSeconds',"$childMax")
  $jsonWindowRecord.childCommand=@{program=$jsonWindowPwsh;arguments=$childArgs;waitMilliseconds=$mainWait}
  $validation=Invoke-JsonWindowOwned 'validation' $jsonWindowPwsh $childArgs $mainWait
  $jsonWindowRecord.childExit=$validation.exit
  if($validation.timedOut){throw 'Child validation timed out; owned cleanup status is recorded separately.'}
  if($validation.treeEmpty -ne $true){throw 'Validation root or an owned descendant remains unconfirmed; HOLD.'}
  $matches=@(Select-String -LiteralPath "$jsonWindowOut/validation.log" -Pattern '^JSON OHOS result=(.+)$')
  if($matches.Count -ne 1){throw 'Missing or ambiguous child result path.'}
  $childPath=[IO.Path]::GetFullPath($matches[0].Matches[0].Groups[1].Value.Trim())
  $allowedPrefix=[IO.Path]::GetFullPath("$jsonWindowRoot/build/native-release-artifacts/")
  if(!$childPath.StartsWith($allowedPrefix,[StringComparison]::OrdinalIgnoreCase)){throw 'Child evidence path is outside the intended artifact directory.'}
  if((Get-Item -LiteralPath $childPath).Length -gt 4MB){throw 'Child result exceeds evidence size limit.'}
  $child=Get-Content -LiteralPath $childPath -Raw | ConvertFrom-Json
  $jsonWindowRecord.childResult=@{path=$childPath;sha256=(Get-JsonWindowSha $childPath);gateExit=$child.exit;terminal=$child.terminal;artifacts=@($child.artifacts).Count;sourceDrift=@($child.sourceDrift);publication=$child.publication}
  foreach($path in $jsonWindowIdentityPaths){if((Get-JsonWindowSha $path) -ne $jsonWindowRecord.identities[$path]){$jsonWindowRecord.identityDrift+= $path}}
  $jsonWindowRecord.childGatePassed=(Test-JsonWindowRow $validation) -and $child.exit -eq 0 -and $child.terminal -eq $true -and @($child.artifacts).Count -eq 2 -and @($child.sourceDrift).Count -eq 0 -and $jsonWindowRecord.identityDrift.Count -eq 0
  if(!$jsonWindowRecord.childGatePassed){throw 'Child validation failed, timed out or drifted; inspect exact retained result and logs.'}
  $jsonWindowRecord.exit=0
} catch {
  $jsonWindowRecord.exit=1;$jsonWindowRecord.error=$_.Exception.ToString()
} finally {
  $jsonWindowRecord.terminal=@($jsonWindowRecord.rows | Where-Object {$_.started -and $_.treeEmpty -ne $true}).Count -eq 0
  $jsonWindowRecord.finishedUtc=[DateTime]::UtcNow.ToString('o')
  $jsonWindowRecord.elapsedSeconds=[Math]::Round($jsonWindowClock.Elapsed.TotalSeconds,3)
  $saved=$false
  try {Save-JsonWindow;$saved=$true}
  catch {$jsonWindowRecord.exit=1;$jsonWindowRecord.error="$($jsonWindowRecord.error) Result persistence failed; HOLD/manual reconciliation required.";[Console]::Error.WriteLine(($jsonWindowRecord | ConvertTo-Json -Depth 14 -Compress))}
  if($saved -and $jsonWindowRecord.terminal){
    try {
      $relayWait=[int][Math]::Min(5000,$MaxSeconds*1000-$jsonWindowClock.ElapsedMilliseconds-11000)
      if($relayWait -le 0){throw 'No bounded final-relay budget remains; manual handoff required.'}
      $message="JSON grant$GrantEvent FINAL VALIDATION TERMINAL RELEASE to $NextOwner. Retained validation wrapper/root and all its descendant Jobs, including its pending publisher, are now terminal+active0. SDKValidationExit=$($jsonWindowRecord.exit), childGatePassed=$($jsonWindowRecord.childGatePassed). Evidence=$jsonWindowOut/result.json. This relay is coordination only. Final window budget/pass verdict is ONLY in the completed result.json; verify handoffReady/relay treeEmpty before next execution. No device/ARM64/signed-release claim."
      $relay=Invoke-JsonWindowMessage 'final-relay' $message $relayWait
      if(!(Test-JsonWindowRow $relay)){throw 'Final relay not confirmed successful and empty; manual reconciliation required.'}
      $jsonWindowRecord.handoffReady=$true
    } catch {$jsonWindowRecord.exit=1;$jsonWindowRecord.error="$($jsonWindowRecord.error) $($_.Exception.Message)"}
  }
  $jsonWindowRecord.terminal=@($jsonWindowRecord.rows | Where-Object {$_.started -and $_.treeEmpty -ne $true}).Count -eq 0
  $jsonWindowRecord.budgetExceeded=$jsonWindowClock.Elapsed.TotalSeconds -gt $MaxSeconds
  if($jsonWindowRecord.budgetExceeded){$jsonWindowRecord.exit=1;$jsonWindowRecord.error="$($jsonWindowRecord.error) Actual total window budget exceeded."}
  $jsonWindowRecord.finalGatePassed=$jsonWindowRecord.exit -eq 0 -and $jsonWindowRecord.childGatePassed -and $jsonWindowRecord.handoffReady -and !$jsonWindowRecord.budgetExceeded
  $jsonWindowRecord.finishedUtc=[DateTime]::UtcNow.ToString('o');$jsonWindowRecord.elapsedSeconds=[Math]::Round($jsonWindowClock.Elapsed.TotalSeconds,3)
  try {Save-JsonWindow}
  catch {$jsonWindowRecord.exit=1;$jsonWindowRecord.handoffReady=$false;$jsonWindowRecord.finalGatePassed=$false;[Console]::Error.WriteLine(($jsonWindowRecord | ConvertTo-Json -Depth 14 -Compress))}
  Write-Host "JSON WINDOW result=$jsonWindowOut/result.json"
}
exit $jsonWindowRecord.exit
