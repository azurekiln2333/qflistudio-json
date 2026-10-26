#requires -Version 7.0
param(
  [Parameter(Mandatory=$true)][int]$GrantEvent,
  [Parameter(Mandatory=$true)][string]$PreparedManifest,
  [Parameter(Mandatory=$true)][string]$NextOwner,
  [ValidateRange(90,120)][int]$MaxSeconds=120
)
$ErrorActionPreference='Stop'
$jsonWindowRoot='D:/MyNewProjects/qfli_json'
$jsonWindowId=[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')+'-'+[Guid]::NewGuid().ToString('N').Substring(0,8)
$jsonWindowOut="$jsonWindowRoot/build/retention-window-artifacts/$jsonWindowId"
$jsonWindowClock=[Diagnostics.Stopwatch]::StartNew()
$jsonWindowPwsh=Join-Path $PSHOME 'pwsh.exe'
$jsonWindowChildScript="$jsonWindowRoot/.trellis/.runtime/run_json_retention_controls.ps1"
$jsonWindowRecord=[ordered]@{schemaVersion=1;grant=$GrantEvent;nextOwner=$NextOwner;startedUtc=[DateTime]::UtcNow.ToString('o');scope='isolated synthetic host retention controls; no SDK/native/device';maxSeconds=$MaxSeconds;exit=1;terminal=$false;handoffReady=$false;handoffMeaning='ownership only; not runtime acceptance';finalGatePassed=$false;error=$null;rows=@();childResult=$null;childExit=$null;childGatePassed=$false;identityDrift=@();budgetExceeded=$false}
function Get-JsonWindowSha([string]$Path){
  $stream=[IO.File]::OpenRead($Path);$sha=[Security.Cryptography.SHA256]::Create()
  try{return ([BitConverter]::ToString($sha.ComputeHash($stream))).Replace('-','').ToLowerInvariant()}
  finally{$sha.Dispose();$stream.Dispose()}
}
function Save-JsonWindow {
  [IO.File]::WriteAllText("$jsonWindowOut/result.json",($jsonWindowRecord | ConvertTo-Json -Depth 14),[Text.UTF8Encoding]::new($false))
}
function Invoke-JsonWindowOwned([string]$Name,[string]$Program,[string[]]$Arguments,[int]$WaitMilliseconds,[bool]$Custodian=$false){
  if($WaitMilliseconds -le 0){throw "No remaining wait budget for $Name"}
  $row=[ordered]@{name=$Name;started=$false;pid=$null;exit=$null;treeEmpty=$null;timedOut=$false;residualCleanup=$false;error=$null;allowedWaitMilliseconds=$WaitMilliseconds;elapsedMilliseconds=$null;observedProcessIds=@()}
  $jsonWindowRecord.rows+= $row
  $watch=[Diagnostics.Stopwatch]::StartNew()
  $callback=[Action[int]]{param($ownedPid);$row.pid=$ownedPid;Save-JsonWindow;Write-Host "JSON WINDOW LIVE $Name PID=$ownedPid"}
  $row.started=$true
  if($Custodian){
    $run=[QfliLuaAudit.BoundedProcess]::RunCustodian($Program,$Arguments,$jsonWindowRoot,"$jsonWindowOut/$Name.log","$jsonWindowOut/$Name.stderr.log",$WaitMilliseconds,$callback)
  } else {
    $run=[QfliLuaAudit.BoundedProcess]::Run($Program,$Arguments,$jsonWindowRoot,"$jsonWindowOut/$Name.log","$jsonWindowOut/$Name.stderr.log",$WaitMilliseconds,$callback)
  }
  $row.rootCreationFileTime=$run.RootCreationFileTime;$row.rootTerminal=$run.RootTerminal;$row.jobActiveZero=$run.JobActiveZero;$row.handlesClosed=$run.HandlesClosed;$row.holdEntered=$run.HoldEntered;$row.holdEvidencePath=$run.HoldEvidencePath;$row.cleanupError=$run.CleanupError;$row.custodian=$Custodian
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
function Test-JsonWindowRow($Row){return $Row -and $Row.exit -eq 0 -and $Row.treeEmpty -eq $true -and $Row.rootTerminal -eq $true -and $Row.jobActiveZero -eq $true -and $Row.handlesClosed -eq $true -and !$Row.holdEntered -and !$Row.cleanupError -and !$Row.timedOut -and !$Row.error}
try {
  [IO.Directory]::CreateDirectory($jsonWindowOut) | Out-Null
  if($PSVersionTable.PSEdition -ne 'Core' -or !(Test-Path -LiteralPath $jsonWindowPwsh -PathType Leaf)){throw 'PowerShell Core executable required.'}
  $reviewed=Get-Content -LiteralPath $PreparedManifest -Raw|ConvertFrom-Json
  if($reviewed.schemaVersion -ne 1 -or $reviewed.kind -ne 'json-retention-controls-source-freeze' -or $reviewed.executionAuthorized -ne $false){throw 'Wrong controls freeze manifest.'}
  $reviewedNames=@($reviewed.files.PSObject.Properties.Name)
  $required=@($PSCommandPath,$jsonWindowChildScript,"$jsonWindowRoot/.trellis/.runtime/json-bounded-process.cs","$jsonWindowRoot/.trellis/.runtime/run_json_ohos_window.ps1","$jsonWindowRoot/.trellis/.runtime/run_json_ohos_release.ps1",$jsonWindowPwsh)
  $required=@($required | ForEach-Object {[IO.Path]::GetFullPath($_)})
  if($reviewedNames.Count -ne $required.Count){throw 'Wrong reviewed controls file set.'}
  foreach($path in $required){
    $id=$reviewed.files.$path
    if(!$id -or (Get-Item -LiteralPath $path).Length -ne $id.bytes -or (Get-JsonWindowSha $path) -ne $id.sha256){throw "Reviewed controls input drift: $path"}
  }
  Add-Type -Path "$jsonWindowRoot/.trellis/.runtime/json-bounded-process.cs"
  $jsonWindowIdentityPaths=@($PSCommandPath,$jsonWindowChildScript,"$jsonWindowRoot/.trellis/.runtime/json-bounded-process.cs",(Resolve-Path -LiteralPath $PreparedManifest).Path,$jsonWindowPwsh)
  $jsonWindowRecord.identities=[ordered]@{}
  foreach($path in $jsonWindowIdentityPaths){$jsonWindowRecord.identities[$path]=Get-JsonWindowSha $path}
  Save-JsonWindow
  $accept=Invoke-JsonWindowMessage 'acceptance' "JSON ACCEPT fresh grant$GrantEvent; same-invocation observer started. Exact successor=$NextOwner. No historical grant replay. Total window<=${MaxSeconds}s, including owned cleanup and final relay. Synthetic host retention controls only; no SDK/native/device/core changes. Observer evidence=$jsonWindowOut/result.json." 5000
  if(!(Test-JsonWindowRow $accept)){throw 'Acceptance transport was not confirmed terminal and successful; validation not started.'}
  # One current-job cleanup (10s), final relay/wait+cleanup (15s), and IO margin (5s).
  $mainWait=[int](($MaxSeconds-30)*1000-$jsonWindowClock.ElapsedMilliseconds)
  $childMax=[int][Math]::Floor($mainWait/1000)-10
  if($childMax -lt 30){throw 'Too little budget remains to start validation.'}
  $childArgs=[string[]]@('-NoProfile','-NonInteractive','-File',$jsonWindowChildScript,'-GrantEvent',"$GrantEvent",'-MaxSeconds',"$childMax")
  $jsonWindowRecord.childCommand=@{program=$jsonWindowPwsh;arguments=$childArgs;waitMilliseconds=$mainWait}
  $validation=Invoke-JsonWindowOwned 'validation' $jsonWindowPwsh $childArgs $mainWait $true
  $jsonWindowRecord.childExit=$validation.exit
  if($validation.timedOut){throw 'Child validation timed out; owned cleanup status is recorded separately.'}
  if($validation.treeEmpty -ne $true){throw 'Validation root or an owned descendant remains unconfirmed; HOLD.'}
  $matches=@(Select-String -LiteralPath "$jsonWindowOut/validation.log" -Pattern '^JSON RETENTION CONTROLS result=(.+)$')
  if($matches.Count -ne 1){throw 'Missing or ambiguous child result path.'}
  $childPath=[IO.Path]::GetFullPath($matches[0].Matches[0].Groups[1].Value.Trim())
  $allowedPrefix=[IO.Path]::GetFullPath("$jsonWindowRoot/build/native-retention-controls/")
  if(!$childPath.StartsWith($allowedPrefix,[StringComparison]::OrdinalIgnoreCase)){throw 'Child evidence path is outside the intended artifact directory.'}
  if((Get-Item -LiteralPath $childPath).Length -gt 4MB){throw 'Child result exceeds evidence size limit.'}
  $child=Get-Content -LiteralPath $childPath -Raw | ConvertFrom-Json
  $jsonWindowRecord.childResult=@{path=$childPath;sha256=(Get-JsonWindowSha $childPath);gateExit=$child.exit;allReturnedOwnershipVerified=$child.allReturnedOwnershipVerified;allControlsPassed=$child.allControlsPassed;cases=@($child.cases).Count;finalGatePassed=$child.finalGatePassed}
  foreach($path in $jsonWindowIdentityPaths){if((Get-JsonWindowSha $path) -ne $jsonWindowRecord.identities[$path]){$jsonWindowRecord.identityDrift+= $path}}
  $jsonWindowRecord.childGatePassed=(Test-JsonWindowRow $validation) -and $child.exit -eq 0 -and $child.allReturnedOwnershipVerified -eq $true -and $child.allControlsPassed -eq $true -and $child.finalGatePassed -eq $true -and @($child.cases).Count -eq 7 -and $jsonWindowRecord.identityDrift.Count -eq 0
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
      $message="JSON grant$GrantEvent FINAL VALIDATION TERMINAL RELEASE to $NextOwner. Retained controls wrapper/root and all owned case Jobs are now terminal+active0. ControlsExit=$($jsonWindowRecord.exit), childGatePassed=$($jsonWindowRecord.childGatePassed). Evidence=$jsonWindowOut/result.json. This relay is coordination only. Final window budget/pass verdict is ONLY in the completed result.json; verify handoffReady/relay treeEmpty before next execution. No SDK/native/device/core changes."
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
  Write-Host "JSON RETENTION WINDOW result=$jsonWindowOut/result.json"
}
exit $jsonWindowRecord.exit
