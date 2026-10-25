#requires -Version 7.0
param(
  [Parameter(Mandatory=$true)][int]$GrantEvent,
  [Parameter(Mandatory=$true)][string]$PreparedManifest,
  [Parameter(Mandatory=$true)][string]$NextOwner,
  [ValidateRange(90,240)][int]$MaxSeconds=240
)
$ErrorActionPreference='Stop'
$jsonRoot='D:/MyNewProjects/qfli_json'
$jsonId=[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')+'-'+[Guid]::NewGuid().ToString('N').Substring(0,8)
$jsonPackages="$jsonRoot/build/native-release-artifacts/$jsonId"
$jsonOut="$jsonPackages/evidence"
$jsonWatch=[Diagnostics.Stopwatch]::StartNew()
$jsonRecord=[ordered]@{grant=$GrantEvent;nextOwner=$NextOwner;scope='isolated published-core unsigned x64 harness and normal HAP builds; no device';workCutoffSeconds=($MaxSeconds-50);cleanupReserveSeconds=50;budgetExceeded=$false;startedUtc=[DateTime]::UtcNow.ToString('o');phases=@();artifacts=@();sourceDrift=@();error=$null;exit=1;terminal=$false}
$jsonPython=$null
$jsonPowerShell=Join-Path $PSHOME 'pwsh.exe'
$jsonReady=$false
$jsonCaptureReady=$false
$jsonCaptureIdentityArgs=@()
$jsonPrepared=$null
function Save-JsonNative {
  [IO.File]::WriteAllText("$jsonOut/result.json",($jsonRecord | ConvertTo-Json -Depth 16),[Text.UTF8Encoding]::new($false))
}
function Get-JsonNativeSha256([string]$Path) {
  $jsonStream=[IO.File]::OpenRead($Path)
  $jsonSha=[Security.Cryptography.SHA256]::Create()
  try {return ([BitConverter]::ToString($jsonSha.ComputeHash($jsonStream))).Replace('-','').ToLowerInvariant()}
  finally {$jsonSha.Dispose();$jsonStream.Dispose()}
}
# Reserve current-job cleanup (10s), final capture/cleanup (17s), publisher/cleanup (15s), and serialization margin.
function Invoke-JsonNativePhase([string]$Name,[string]$Program,[string[]]$Arguments,[string]$Directory,[int]$Seconds) {
  $jsonRemaining=[int][Math]::Min($Seconds*1000,($MaxSeconds-50)*1000-$jsonWatch.ElapsedMilliseconds)
  if($jsonRemaining -le 0){throw 'Native shared host work deadline exhausted.'}
  $jsonRow=[ordered]@{name=$Name;pid=$null;exit=$null;treeEmpty=$null;timedOut=$false;residualCleanup=$false;observedProcessIds=@();error=$null;started=$false;allowedWaitMilliseconds=$jsonRemaining;elapsedMilliseconds=$null}
  $jsonRecord.phases+= $jsonRow
  $jsonCallback=[Action[int]]{param($jsonPid);$jsonRow.pid=$jsonPid;Save-JsonNative;Write-Host "JSON OHOS LIVE $Name PID=$jsonPid"}
  $jsonPhaseWatch=[Diagnostics.Stopwatch]::StartNew()
  $jsonRow.started=$true
  $jsonRun=[QfliLuaAudit.BoundedProcess]::Run($Program,$Arguments,$Directory,"$jsonOut/$Name.log","$jsonOut/$Name.stderr.log",$jsonRemaining,$jsonCallback)
  $jsonRow.elapsedMilliseconds=$jsonPhaseWatch.ElapsedMilliseconds
  $jsonRow.pid=$jsonRun.RootProcessId;$jsonRow.exit=$jsonRun.RootExitCode;$jsonRow.treeEmpty=$jsonRun.TreeEmpty;$jsonRow.timedOut=$jsonRun.TimedOut;$jsonRow.residualCleanup=$jsonRun.ResidualTreeTerminated;$jsonRow.observedProcessIds=@($jsonRun.ObservedProcessIds);$jsonRow.error=$jsonRun.Error
  Save-JsonNative
  if(!$jsonRun.TreeEmpty -or $jsonRun.TimedOut -or $jsonRun.Error -or $jsonRun.RootExitCode -ne 0){throw "Native $Name phase failed; later build phases unrun."}
}
try {
  [IO.Directory]::CreateDirectory($jsonOut) | Out-Null
  $jsonPython=(Get-Command python -ErrorAction Stop).Source
  if($PSVersionTable.PSVersion.Major -lt 7 -or $PSVersionTable.PSEdition -ne 'Core' -or !(Test-Path -LiteralPath $jsonPowerShell -PathType Leaf)){throw 'Native wrapper requires PowerShell 7+ Core and its matching pwsh.exe.'}
  $jsonRecord.powerShell=@{version=$PSVersionTable.PSVersion.ToString();path=$jsonPowerShell;sha256=(Get-JsonNativeSha256 $jsonPowerShell)}
  Add-Type -Path "$jsonRoot/.trellis/.runtime/json-bounded-process.cs"
  $jsonReady=$true
  $jsonPrepared=Get-Content -LiteralPath $PreparedManifest -Raw | ConvertFrom-Json
  if($jsonPrepared.prepared -ne $true){throw 'Native snapshot was not prepared.'}
  Copy-Item -LiteralPath $PreparedManifest -Destination "$jsonOut/prepared.json"
  $jsonRecord.coreCommit=$jsonPrepared.coreCommit
  $jsonRecord.appRoot=$jsonPrepared.appRoot
  $jsonRecord.coreRoot=$jsonPrepared.coreRoot
  $jsonRecord.runnerHashes=[ordered]@{}
  $jsonRunners=[ordered]@{
    wrapper=$PSCommandPath
    hvigorPhase="$jsonRoot/.trellis/.runtime/json_hvigor_phase.ps1"
    prepare="$jsonRoot/.trellis/.runtime/prepare_json_ohos_inputs.py"
    inspector="$jsonRoot/.trellis/.runtime/inspect_json_release_hap.py"
    boundedProcess="$jsonRoot/.trellis/.runtime/json-bounded-process.cs"
  }
  foreach($jsonHelper in $jsonRunners.Values){
    $jsonRecord.runnerHashes[$jsonHelper]=Get-JsonNativeSha256 $jsonHelper
  }
  $jsonHvigor='D:/ProgramFiles/Huawei/DevEco Studio/tools/hvigor/bin/hvigorw.bat'
  $jsonTools=[ordered]@{python=$jsonPython;powerShell=$jsonPowerShell;hvigor=$jsonHvigor;hvigorWrapper=(Join-Path (Split-Path $jsonHvigor) 'hvigorw.js');node=(Get-Command node -CommandType Application).Source}
  foreach($jsonKey in $jsonRunners.Keys){$jsonCaptureIdentityArgs+= @('--runner',"$jsonKey=$($jsonRunners[$jsonKey])")}
  foreach($jsonKey in $jsonTools.Keys){$jsonCaptureIdentityArgs+= @('--tool',"$jsonKey=$($jsonTools[$jsonKey])")}
  $jsonCommands=[ordered]@{}
  foreach($jsonMode in @('harness','normal')){
    $jsonDefines=if($jsonMode -eq 'harness'){'UUZMSV9WRVJJRllfQ0FUQUxPRz10cnVl'}else{''}
    $jsonCommand=[ordered]@{
      executable=$jsonHvigor
      cwd=(Join-Path $jsonPrepared.appRoot 'ohos')
      arguments=@('--mode','module','-p','module=entry@default','-p','product=default','-p','buildMode=debug','-p','FLUTTER_TARGET=lib/main.dart','-p','TARGET_PLATFORM=ohos-x64','-p',"DART_DEFINES=$jsonDefines",'-p','TRACK_WIDGET_CREATION=true','-p','TREE_SHAKE_ICONS=false','-c','properties.enableSignTask=false','--no-daemon','--no-parallel','assembleHap')
    }
    $jsonCommands[$jsonMode]=$jsonCommand
    [IO.File]::WriteAllText("$jsonOut/$jsonMode-command.json",($jsonCommand | ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
    $jsonCaptureIdentityArgs+= @('--runner',"$jsonMode-config=$jsonOut/$jsonMode-command.json",'--build-parameter',"$jsonMode.command=$($jsonCommand | ConvertTo-Json -Depth 5 -Compress)")
  }
  $jsonCaptureArgs=@("$jsonRoot/.trellis/.runtime/prepare_json_ohos_inputs.py",'--host-manifest',$jsonPrepared.hostManifest,'--app-root',$jsonPrepared.appRoot,'--core-root',$jsonPrepared.coreRoot,'--output',"$jsonOut/source-before.json")+$jsonCaptureIdentityArgs
  Invoke-JsonNativePhase 'capture-before' $jsonPython $jsonCaptureArgs $jsonRoot 8
  $jsonCaptureReady=$true
  $jsonHap=Join-Path $jsonPrepared.appRoot 'ohos/entry/build/default/outputs/default/entry-default-unsigned.hap'
  if(Test-Path -LiteralPath $jsonHap){throw 'Fresh isolated native root already contains an output HAP.'}
  foreach($jsonMode in @('harness','normal')){
    $jsonCommand=$jsonCommands[$jsonMode]
    $jsonBuildArgs=@('-NoProfile','-NonInteractive','-File',"$jsonRoot/.trellis/.runtime/json_hvigor_phase.ps1",'-Config',"$jsonOut/$jsonMode-command.json")
    Invoke-JsonNativePhase "$jsonMode-build" $jsonPowerShell $jsonBuildArgs $jsonCommand.cwd 100
    if(!(Select-String -LiteralPath "$jsonOut/$jsonMode-build.log" -SimpleMatch 'BUILD SUCCESSFUL' -Quiet)){throw 'Hvigor returned0 without its final successful build marker.'}
    $jsonInspectArgs=@("$jsonRoot/.trellis/.runtime/inspect_json_release_hap.py",'--hap',$jsonHap,'--app-root',$jsonPrepared.appRoot,'--core-root',$jsonPrepared.coreRoot,'--mode',$jsonMode,'--output',"$jsonOut/$jsonMode-artifact.json",'--copy-to',"$jsonPackages/json-$jsonMode-unsigned.hap")
    Invoke-JsonNativePhase "$jsonMode-inspect" $jsonPython $jsonInspectArgs $jsonRoot 10
    $jsonArtifact=Get-Content -LiteralPath "$jsonOut/$jsonMode-artifact.json" -Raw | ConvertFrom-Json
    if($jsonArtifact.passed -ne $true){throw 'Unsigned HAP inspection did not pass.'}
    $jsonRecord.artifacts+= $jsonArtifact
    Save-JsonNative
  }
  if($jsonRecord.artifacts[0].kernelSha256 -eq $jsonRecord.artifacts[1].kernelSha256){throw 'Harness and normal kernels must have distinct compile-time entry modes.'}
  $jsonRecord.exit=0
} catch {
  $jsonRecord.error=$_.Exception.ToString()
} finally {
  if($jsonPrepared -and $jsonReady -and $jsonCaptureReady){
    try {
      $jsonFinalCapture=@("$jsonRoot/.trellis/.runtime/prepare_json_ohos_inputs.py",'--host-manifest',$jsonPrepared.hostManifest,'--app-root',$jsonPrepared.appRoot,'--core-root',$jsonPrepared.coreRoot,'--output',"$jsonOut/source-after.json",'--before',"$jsonOut/source-before.json")+$jsonCaptureIdentityArgs
      $jsonRecord.capture=@{pid=$null;exit=$null;treeEmpty=$null;timedOut=$false;residualCleanup=$false;error=$null;started=$true}
      $jsonCapture=[QfliLuaAudit.BoundedProcess]::Run($jsonPython,$jsonFinalCapture,$jsonRoot,"$jsonOut/capture-after.log","$jsonOut/capture-after.stderr.log",7000,$null)
      $jsonRecord.capture=@{pid=$jsonCapture.RootProcessId;exit=$jsonCapture.RootExitCode;treeEmpty=$jsonCapture.TreeEmpty;timedOut=$jsonCapture.TimedOut;residualCleanup=$jsonCapture.ResidualTreeTerminated;error=$jsonCapture.Error}
      if(Test-Path -LiteralPath "$jsonOut/source-after.json"){
        $jsonAfter=Get-Content -LiteralPath "$jsonOut/source-after.json" -Raw | ConvertFrom-Json -AsHashtable
        foreach($jsonCategory in $jsonAfter.differences.Keys){
          foreach($jsonKind in @('added','deleted','changed')){
            foreach($jsonKey in @($jsonAfter.differences[$jsonCategory][$jsonKind])){$jsonRecord.sourceDrift+= "$jsonCategory/$jsonKind/$jsonKey"}
          }
        }
        foreach($jsonRepository in @($jsonAfter.repositoriesChanged)){$jsonRecord.sourceDrift+= "repository/$jsonRepository"}
      }
      if($jsonCapture.RootExitCode -ne 0 -or !$jsonCapture.TreeEmpty -or $jsonCapture.TimedOut -or $jsonCapture.Error){throw 'Final native source/identity comparison failed; inspect capture-after logs and source-after differences.'}
      if($jsonRecord.sourceDrift.Count -gt 0){throw 'Final native inputs, identities or repositories drifted.'}
    } catch {$jsonRecord.error="$($jsonRecord.error) Final native source check: $($_.Exception.Message)";$jsonRecord.exit=1}
  }
  if(@($jsonRecord.phases | Where-Object {$_.exit -ne 0}).Count -gt 0 -or $jsonRecord.error){$jsonRecord.exit=1}
  $jsonRecord.finishedUtc=[DateTime]::UtcNow.ToString('o')
  $jsonRecord.elapsedSeconds=[Math]::Round($jsonWatch.Elapsed.TotalSeconds,3)
  $jsonRecord.terminal=@($jsonRecord.phases | Where-Object {$_.started -and $_.treeEmpty -ne $true}).Count -eq 0
  if($jsonRecord.Contains('capture') -and $jsonRecord.capture.treeEmpty -ne $true){$jsonRecord.terminal=$false}
  $jsonPublicationAllowed=$false
  try {Save-JsonNative;$jsonPublicationAllowed=$true}
  catch {
    $jsonRecord.exit=1
    $jsonRecord.error="$($jsonRecord.error) Final result persistence failed; HOLD/manual reconciliation required: $($_.Exception.Message)"
    [Console]::Error.WriteLine(($jsonRecord | ConvertTo-Json -Depth 16 -Compress))
  }
  if($jsonReady -and $jsonPublicationAllowed){
    try {
      $jsonDisposition='RELEASE_PENDING_PUBLISHER; NO_SUCCESSOR_GRANT. Parent observer must confirm wrapper and all owned Jobs terminal before final relay.'
      $jsonMessage="JSON$GrantEvent isolated native gate pending wrapper exit=$($jsonRecord.exit); $jsonDisposition Artifacts=$($jsonRecord.artifacts.Count); drift=$($jsonRecord.sourceDrift.Count); evidence=$jsonOut/result.json. Unsigned x64 package proof only; no installed/device/ARM64/release-signing claim."
      $jsonTrellis=(Get-Command trellis -ErrorAction Stop).Source.Replace("'","''")
      [IO.File]::WriteAllText("$jsonOut/release.txt",$jsonMessage,[Text.UTF8Encoding]::new($false))
      $jsonPublish="& '$jsonTrellis' channel send qfli-core-release-sync --scope global --as json-offline-1022 --text-file '$jsonOut/release.txt'; exit `$LASTEXITCODE"
      $jsonEncoded=[Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($jsonPublish))
      $jsonRecord.publication=@{pid=$null;exit=$null;treeEmpty=$null;timedOut=$false;residualCleanup=$false;error=$null;started=$false}
      Save-JsonNative
      $jsonRecord.publication.started=$true
      $jsonPublisher=[QfliLuaAudit.BoundedProcess]::Run($jsonPowerShell,[string[]]@('-NoProfile','-NonInteractive','-EncodedCommand',$jsonEncoded),$jsonRoot,"$jsonOut/publication.log","$jsonOut/publication.stderr.log",5000,$null)
      $jsonRecord.publication=@{pid=$jsonPublisher.RootProcessId;exit=$jsonPublisher.RootExitCode;treeEmpty=$jsonPublisher.TreeEmpty;timedOut=$jsonPublisher.TimedOut;residualCleanup=$jsonPublisher.ResidualTreeTerminated;error=$jsonPublisher.Error;started=$true}
      if(!$jsonPublisher.TreeEmpty){$jsonRecord.terminal=$false}
      if($jsonPublisher.RootExitCode -ne 0 -or !$jsonPublisher.TreeEmpty -or $jsonPublisher.TimedOut -or $jsonPublisher.Error){throw 'Automatic release publisher unconfirmed.'}
    } catch {
      if(!$jsonRecord.Contains('publication')){$jsonRecord.publication=@{started=$false;error=$_.Exception.ToString()}}
      else {$jsonRecord.publication.error=$_.Exception.ToString()}
      if($jsonRecord.publication.started -and $jsonRecord.publication.treeEmpty -ne $true){$jsonRecord.terminal=$false}
      $jsonRecord.exit=1
      $jsonRecord.error="$($jsonRecord.error) Automatic release publication failed: $($_.Exception.Message) HOLD/manual reconciliation required."
      try {[IO.File]::WriteAllText("$jsonOut/release.txt",'PUBLICATION UNCONFIRMED; HOLD/manual reconciliation required.',[Text.UTF8Encoding]::new($false))}
      catch {[Console]::Error.WriteLine('Could not mark publication file unconfirmed; rely on final outer exit and result.')}
    } finally {
      $jsonRecord.finishedUtc=[DateTime]::UtcNow.ToString('o')
      $jsonRecord.elapsedSeconds=[Math]::Round($jsonWatch.Elapsed.TotalSeconds,3)
      $jsonRecord.budgetExceeded=$jsonWatch.Elapsed.TotalSeconds -gt $MaxSeconds
      if($jsonRecord.budgetExceeded){$jsonRecord.exit=1;$jsonRecord.error="$($jsonRecord.error) Actual total elapsed exceeded the granted budget; review final result before acceptance."}
      try {Save-JsonNative}
      catch {
        $jsonRecord.exit=1
        $jsonRecord.error="$($jsonRecord.error) Final publication result persistence failed: $($_.Exception.Message)"
        [Console]::Error.WriteLine(($jsonRecord | ConvertTo-Json -Depth 16 -Compress))
      }
    }
  }
  Write-Host "JSON OHOS result=$jsonOut/result.json"
}
exit $jsonRecord.exit
