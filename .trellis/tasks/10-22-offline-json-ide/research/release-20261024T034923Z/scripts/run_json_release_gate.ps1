param(
  [Parameter(Mandatory=$true)][int]$GrantEvent,
  [Parameter(Mandatory=$true)][int]$PublicationEvent,
  [Parameter(Mandatory=$true)][string]$CoreCommit,
  [Parameter(Mandatory=$true)][string]$NextOwner,
  [ValidateRange(45,110)][int]$MaxSeconds=110
)
$ErrorActionPreference='Stop'
$jsonRoot='D:/MyNewProjects/qfli_json'
$jsonOut="$jsonRoot/.trellis/tasks/10-22-offline-json-ide/research/release-$([DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ'))"
[IO.Directory]::CreateDirectory($jsonOut) | Out-Null
$jsonWatch=[Diagnostics.Stopwatch]::StartNew()
$jsonRecord=[ordered]@{grant=$GrantEvent;publicationEvent=$PublicationEvent;coreCommit=$CoreCommit;nextOwner=$NextOwner;scope='full JSON host suite on exact published core and captured owned report fix';startedUtc=[DateTime]::UtcNow.ToString('o');phases=@();sourceDrift=@();error=$null;exit=1;terminal=$false}
$jsonDart='D:/ProgramFiles/flutter_ohos/bin/cache/dart-sdk/bin/dart.exe'
$jsonFlutter='D:/ProgramFiles/flutter_ohos/bin/cache/flutter_tools.snapshot'
$jsonPython=(Get-Command python).Source
$jsonManifest=$null
$jsonReady=$false
$jsonRecord.runnerHashes=[ordered]@{}
foreach($jsonHelper in @($PSCommandPath,"$jsonRoot/.trellis/.runtime/prepare_json_release_gate.py","$jsonRoot/.trellis/.runtime/json-bounded-process.cs",$jsonDart,$jsonFlutter)){
  $jsonRecord.runnerHashes[$jsonHelper]=(Get-FileHash -LiteralPath $jsonHelper -Algorithm SHA256).Hash.ToLowerInvariant()
}
function Save-JsonRelease {
  [IO.File]::WriteAllText("$jsonOut/result.json",($jsonRecord | ConvertTo-Json -Depth 15),[Text.UTF8Encoding]::new($false))
}
function Invoke-JsonPhase([string]$Name,[string]$Program,[string[]]$Arguments,[string]$Directory,[int]$Seconds) {
  $jsonRemaining=[int][Math]::Min($Seconds*1000,($MaxSeconds-12)*1000-$jsonWatch.ElapsedMilliseconds)
  if($jsonRemaining -le 0){throw 'Shared host deadline exhausted; later phases unrun.'}
  $jsonRow=[ordered]@{name=$Name;pid=$null;exit=$null;treeEmpty=$null;timedOut=$false;residualCleanup=$false;observedProcessIds=@();error=$null}
  $jsonRecord.phases+= $jsonRow
  $jsonCallback=[Action[int]]{param($jsonPid);$jsonRow.pid=$jsonPid;Save-JsonRelease;Write-Host "JSON LIVE $Name PID=$jsonPid"}
  $jsonRun=[QfliLuaAudit.BoundedProcess]::Run($Program,$Arguments,$Directory,"$jsonOut/$Name.log","$jsonOut/$Name.stderr.log",$jsonRemaining,$jsonCallback)
  $jsonRow.pid=$jsonRun.RootProcessId;$jsonRow.exit=$jsonRun.RootExitCode;$jsonRow.treeEmpty=$jsonRun.TreeEmpty;$jsonRow.timedOut=$jsonRun.TimedOut;$jsonRow.residualCleanup=$jsonRun.ResidualTreeTerminated;$jsonRow.error=$jsonRun.Error
  $jsonRow.observedProcessIds=@($jsonRun.ObservedProcessIds)
  Save-JsonRelease
  if(!$jsonRun.TreeEmpty -or $jsonRun.TimedOut -or $jsonRun.Error){throw "Owned $Name process failed its containment/deadline gate."}
  return $jsonRun.RootExitCode
}
try {
  Add-Type -Path "$jsonRoot/.trellis/.runtime/json-bounded-process.cs"
  $jsonReady=$true
  $jsonOwned=@('lib/json/json_verification_report.dart','lib/json/json_verification_page.dart','test/json_verification_report_test.dart')
  $jsonExit=Invoke-JsonPhase 'format-owned' $jsonDart (@('format')+$jsonOwned) $jsonRoot 8
  if($jsonExit -ne 0){throw 'Owned formatting failed.'}
  $jsonPrepare=@("$jsonRoot/.trellis/.runtime/prepare_json_release_gate.py",'--core-commit',$CoreCommit,'--publication-event',"$PublicationEvent")
  foreach($jsonPath in $jsonOwned){$jsonPrepare+=@('--owned-overlay',$jsonPath)}
  $jsonExit=Invoke-JsonPhase 'prepare' $jsonPython $jsonPrepare $jsonRoot 12
  if($jsonExit -ne 0){throw 'Exact-source snapshot preparation failed.'}
  $jsonManifest=(Get-Content "$jsonOut/prepare.log" -Raw | ConvertFrom-Json).manifest
  Copy-Item -LiteralPath $jsonManifest -Destination "$jsonOut/source-before.json"
  $jsonInputs=Get-Content $jsonManifest -Raw | ConvertFrom-Json
  $jsonRecord.manifest=$jsonManifest
  $jsonRecord.appCommit=$jsonInputs.appCommit
  $jsonRecord.coreTree=$jsonInputs.coreTree
  $jsonPhases=@(
    @{name='format-check';program=$jsonDart;arguments=@('format','--output=none','--set-exit-if-changed','lib','test');seconds=8},
    @{name='content';program=$jsonPython;arguments=@('tool/build_json_content.py','--check');seconds=8},
    @{name='test';program=$jsonDart;arguments=@($jsonFlutter,'--suppress-analytics','test','--no-pub','--concurrency=1','--reporter=expanded','--timeout','30s');seconds=60},
    @{name='analyze';program=$jsonDart;arguments=@('analyze','lib','test');seconds=20}
  )
  foreach($jsonPhase in $jsonPhases){
    $jsonExit=Invoke-JsonPhase $jsonPhase.name $jsonPhase.program $jsonPhase.arguments $jsonInputs.appSnapshot $jsonPhase.seconds
    if($jsonExit -eq 0 -and $jsonPhase.name -eq 'test' -and !(Select-String -LiteralPath "$jsonOut/test.log" -SimpleMatch 'All tests passed!' -Quiet)){throw 'Test root returned success without its final success marker.'}
    if($jsonExit -eq 0 -and $jsonPhase.name -eq 'analyze' -and !(Select-String -LiteralPath "$jsonOut/analyze.log" -SimpleMatch 'No issues found!' -Quiet)){throw 'Analyzer root returned success without its final success marker.'}
  }
  $jsonRecord.exit=0
} catch {
  $jsonRecord.error=$_.Exception.ToString()
} finally {
  if($jsonManifest){
    try {
      $jsonCapture=@("$jsonRoot/.trellis/.runtime/prepare_json_release_gate.py",'--core-commit',$CoreCommit,'--publication-event',"$PublicationEvent",'--manifest',$jsonManifest,'--capture',"$jsonOut/source-after.json")
      $jsonCaptureResult=[QfliLuaAudit.BoundedProcess]::Run($jsonPython,$jsonCapture,$jsonRoot,"$jsonOut/capture.log","$jsonOut/capture.stderr.log",4000,$null)
      $jsonRecord.capture=@{pid=$jsonCaptureResult.RootProcessId;exit=$jsonCaptureResult.RootExitCode;treeEmpty=$jsonCaptureResult.TreeEmpty;timedOut=$jsonCaptureResult.TimedOut;residualCleanup=$jsonCaptureResult.ResidualTreeTerminated;error=$jsonCaptureResult.Error}
      if($jsonCaptureResult.RootExitCode -ne 0 -or !$jsonCaptureResult.TreeEmpty -or $jsonCaptureResult.TimedOut -or $jsonCaptureResult.Error){throw 'Final source capture failed.'}
      $jsonBefore=(Get-Content "$jsonOut/source-before.json" -Raw | ConvertFrom-Json -AsHashtable).files
      $jsonAfter=(Get-Content "$jsonOut/source-after.json" -Raw | ConvertFrom-Json -AsHashtable).files
      foreach($jsonKey in @(@($jsonBefore.Keys)+@($jsonAfter.Keys) | Sort-Object -Unique)){
        if(!$jsonBefore.ContainsKey($jsonKey) -or !$jsonAfter.ContainsKey($jsonKey) -or $jsonBefore[$jsonKey].sha256 -ne $jsonAfter[$jsonKey].sha256){$jsonRecord.sourceDrift+= $jsonKey}
      }
    } catch {$jsonRecord.error="$($jsonRecord.error) Final source check: $($_.Exception.Message)";$jsonRecord.exit=1}
  }
  if(@($jsonRecord.phases | Where-Object {$_.exit -ne 0}).Count -gt 0 -or $jsonRecord.sourceDrift.Count -gt 0 -or $jsonRecord.error){$jsonRecord.exit=1}
  $jsonRecord.finishedUtc=[DateTime]::UtcNow.ToString('o')
  $jsonRecord.elapsedSeconds=[Math]::Round($jsonWatch.Elapsed.TotalSeconds,3)
  $jsonRecord.terminal=@($jsonRecord.phases | Where-Object {$_.pid -and $_.treeEmpty -ne $true}).Count -eq 0
  if($jsonRecord.Contains('capture') -and $jsonRecord.capture.treeEmpty -ne $true){$jsonRecord.terminal=$false}
  Save-JsonRelease
  $jsonDisposition=if($jsonRecord.terminal){"Explicit RELEASE to $NextOwner."}else{'HOLD: owned tree not confirmed empty.'}
  $jsonMessage="JSON$GrantEvent full host gate terminal exit=$($jsonRecord.exit); $jsonDisposition Core=$CoreCommit. Phases=$($jsonRecord.phases | ConvertTo-Json -Compress -Depth 4); drift=$($jsonRecord.sourceDrift.Count); evidence=$jsonOut/result.json. Exact snapshot host evidence only; no native/HAP/device claim."
  [IO.File]::WriteAllText("$jsonOut/release.txt",$jsonMessage,[Text.UTF8Encoding]::new($false))
  if($jsonReady){
    $jsonTrellis=(Get-Command trellis).Source.Replace("'","''")
    $jsonPublish="& '$jsonTrellis' channel send qfli-core-release-sync --scope global --as json-offline-1022 --text-file '$jsonOut/release.txt'; exit `$LASTEXITCODE"
    $jsonEncoded=[Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($jsonPublish))
    $jsonPublisher=[QfliLuaAudit.BoundedProcess]::Run((Get-Process -Id $PID).Path,[string[]]@('-NoProfile','-NonInteractive','-EncodedCommand',$jsonEncoded),$jsonRoot,"$jsonOut/publication.log","$jsonOut/publication.stderr.log",5000,$null)
    $jsonRecord.publication=@{pid=$jsonPublisher.RootProcessId;exit=$jsonPublisher.RootExitCode;treeEmpty=$jsonPublisher.TreeEmpty;timedOut=$jsonPublisher.TimedOut;residualCleanup=$jsonPublisher.ResidualTreeTerminated;error=$jsonPublisher.Error}
    if(!$jsonPublisher.TreeEmpty){$jsonRecord.terminal=$false}
    if($jsonPublisher.RootExitCode -ne 0 -or !$jsonPublisher.TreeEmpty -or $jsonPublisher.TimedOut -or $jsonPublisher.Error){
      $jsonRecord.exit=1
      $jsonRecord.error="$($jsonRecord.error) Automatic release publication was not confirmed; coordinate HOLD/manual release."
      Write-Host 'HOLD/manual reconciliation required: release publisher failed its terminal gate.'
    }
    Save-JsonRelease
  }
  Write-Output "JSON result=$jsonOut/result.json"
}
Get-Content -LiteralPath "$jsonOut/test.log" -Tail 12 -ErrorAction SilentlyContinue
Get-Content -LiteralPath "$jsonOut/analyze.log" -Tail 10 -ErrorAction SilentlyContinue
exit $jsonRecord.exit
