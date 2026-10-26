#requires -Version 7.0
param([Parameter(Mandatory=$true)][ValidateRange(1,2147483647)][int]$GrantEvent,[ValidateRange(30,120)][int]$MaxSeconds=60)
$ErrorActionPreference='Stop'
$jsonControlsRoot='D:/MyNewProjects/qfli_json'
$jsonControlsHelper="$jsonControlsRoot/.trellis/.runtime/json-bounded-process.cs"
$jsonControlsPowerShell=Join-Path $PSHOME 'pwsh.exe'
$jsonControlsId=[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')+'-'+[Guid]::NewGuid().ToString('N').Substring(0,8)
$jsonControlsOut="$jsonControlsRoot/build/native-retention-controls/$jsonControlsId"
$jsonControlsClock=[Diagnostics.Stopwatch]::StartNew()
$jsonControlsRecord=[ordered]@{schemaVersion=1;grant=$GrantEvent;synthetic=$true;scope='isolated host Job-retention controls; no SDK/device/channel sends';startedUtc=[DateTime]::UtcNow.ToString('o');expectedMaximumSeconds=$MaxSeconds;ownerPid=$PID;cases=@();error=$null;exit=1;allReturnedOwnershipVerified=$false;allControlsPassed=$false;budgetExceeded=$false;finalGatePassed=$false}
[IO.Directory]::CreateDirectory($jsonControlsOut) | Out-Null
function Save-JsonControls {
  $jsonControlsRecord.elapsedSeconds=[Math]::Round($jsonControlsClock.Elapsed.TotalSeconds,3)
  [IO.File]::WriteAllText("$jsonControlsOut/result.json",($jsonControlsRecord|ConvertTo-Json -Depth 18),[Text.UTF8Encoding]::new($false))
}
function Write-JsonControlFile([string]$Path,[string]$Body){[IO.File]::WriteAllText($Path,$Body,[Text.UTF8Encoding]::new($false))}
function Quote-JsonControl([string]$Value){return "'"+$Value.Replace("'","''")+"'"}
function Get-JsonControlHash([string]$Path){return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()}
function Test-JsonReturnedOwnership($Run){return $Run.RootTerminal -eq $true -and $Run.JobActiveZero -eq $true -and $Run.TreeEmpty -eq $true -and $Run.HandlesClosed -eq $true -and (!$Run.RootProcessId -or $Run.RootCreationFileTime -gt 0)}
function Test-JsonProcessAccepted($Run){return (Test-JsonReturnedOwnership $Run) -and $Run.RootExitCode -eq 0 -and !$Run.TimedOut -and !$Run.HoldEntered -and !$Run.Error -and !$Run.CleanupError}
function Invoke-JsonRetentionCase([string]$Name,[string]$Code,[int]$Milliseconds,[bool]$Custodian=$false,[bool]$InvalidExecutable=$false,[bool]$ThrowOnStarted=$false){
  if($jsonControlsClock.Elapsed.TotalSeconds -ge $MaxSeconds){throw 'Controls start budget exhausted. No further case launched.'}
  $case="$jsonControlsOut/$Name";[IO.Directory]::CreateDirectory($case)|Out-Null
  $script="$case/child.ps1"
  Write-JsonControlFile $script ($Code.Replace('__CASE__',(Quote-JsonControl $case)).Replace('__HELPER__',(Quote-JsonControl $jsonControlsHelper)))
  $program=if($InvalidExecutable){"$case/absent.exe"}else{$jsonControlsPowerShell}
  $row=[ordered]@{name=$Name;synthetic=$true;custodian=$Custodian;started=$true;rootPid=$null;expectedWaitMilliseconds=$Milliseconds;scriptSha256=(Get-JsonControlHash $script);result=$null;returnedOwnershipVerified=$false;processAccepted=$false;controlPassed=$false;checks=@();elapsedMilliseconds=$null}
  $jsonControlsRecord.cases+=$row;Save-JsonControls
  $callback=[Action[int]]{param($ownedPid);$row.rootPid=$ownedPid;Save-JsonControls;if($ThrowOnStarted){throw 'Synthetic onStarted failure before resume.'}}
  $watch=[Diagnostics.Stopwatch]::StartNew()
  if($Custodian){$run=[QfliLuaAudit.BoundedProcess]::RunCustodian($program,[string[]]@('-NoProfile','-NonInteractive','-File',$script),$case,"$case/stdout.log","$case/stderr.log",$Milliseconds,$callback)}
  else{$run=[QfliLuaAudit.BoundedProcess]::Run($program,[string[]]@('-NoProfile','-NonInteractive','-File',$script),$case,"$case/stdout.log","$case/stderr.log",$Milliseconds,$callback)}
  $row.elapsedMilliseconds=$watch.ElapsedMilliseconds;$row.result=$run
  $row.returnedOwnershipVerified=Test-JsonReturnedOwnership $run;$row.processAccepted=Test-JsonProcessAccepted $run
  if(!$row.returnedOwnershipVerified){Save-JsonControls;throw "Returned ownership unverified for $Name. No next case or release permitted."}
  return @{row=$row;run=$run;directory=$case}
}
try {
  if($PSVersionTable.PSEdition -ne 'Core'){throw 'PowerShell Core required.'}
  $jsonControlsRecord.identities=[ordered]@{script=@{path=$PSCommandPath;sha256=(Get-JsonControlHash $PSCommandPath)};helper=@{path=$jsonControlsHelper;sha256=(Get-JsonControlHash $jsonControlsHelper)};powerShell=@{path=$jsonControlsPowerShell;sha256=(Get-JsonControlHash $jsonControlsPowerShell)}}
  Save-JsonControls
  # Compilation belongs only to a separately granted controls invocation.
  Add-Type -Path $jsonControlsHelper
  $case=Invoke-JsonRetentionCase 'normal' '$ErrorActionPreference=''Stop'';$case=__CASE__;[IO.File]::WriteAllText("$case/completed.txt",''normal'');exit 0' 5000
  $case.row.checks=@($case.row.processAccepted,(Test-Path -LiteralPath "$($case.directory)/completed.txt"));$case.row.controlPassed=$case.row.checks -notcontains $false;Save-JsonControls

  $case=Invoke-JsonRetentionCase 'payload-timeout' '$ErrorActionPreference=''Stop'';$case=__CASE__;[IO.File]::WriteAllText("$case/entered.txt",''payload'');Start-Sleep -Seconds 12;[IO.File]::WriteAllText("$case/unexpected-completion.txt",''late'')' 1800
  $case.row.checks=@(!$case.row.processAccepted,$case.run.TimedOut,($case.run.RootExitCode -ne 0),(Test-Path -LiteralPath "$($case.directory)/entered.txt"),!(Test-Path -LiteralPath "$($case.directory)/unexpected-completion.txt"));$case.row.controlPassed=$case.row.checks -notcontains $false;Save-JsonControls

  $case=Invoke-JsonRetentionCase 'custodian-timeout' '$ErrorActionPreference=''Stop'';$case=__CASE__;Start-Sleep -Milliseconds 1300;[IO.File]::WriteAllText("$case/completed.txt",''custodian survived deadline'');exit 0' 300 $true
  $hold=if($case.run.HoldEvidencePath -and (Test-Path -LiteralPath $case.run.HoldEvidencePath)){Get-Content -LiteralPath $case.run.HoldEvidencePath -Raw|ConvertFrom-Json}else{$null}
  $case.row.holdEntry=$hold
  $case.row.checks=@(!$case.row.processAccepted,$case.run.TimedOut,$case.run.HoldEntered,($case.run.RootExitCode -eq 0),[bool]$case.run.Error,(Test-Path -LiteralPath "$($case.directory)/completed.txt"),($hold.status -eq 'HOLD'),($hold.rootCreationFileTime -eq $case.run.RootCreationFileTime));$case.row.controlPassed=$case.row.checks -notcontains $false;Save-JsonControls

  $nested=@'
$ErrorActionPreference='Stop';$case=__CASE__;$helper=__HELPER__
Add-Type -Path $helper
$payload=Join-Path $case 'inner.ps1'
[IO.File]::WriteAllText($payload,('$case='+"'"+$case.Replace("'","''")+"'"+';[IO.File]::WriteAllText("$case/inner-started.txt",''inner'');Start-Sleep -Milliseconds 1200;[IO.File]::WriteAllText("$case/inner-completed.txt",''inner terminal path'');exit 0'))
$inner=[QfliLuaAudit.BoundedProcess]::Run((Join-Path $PSHOME 'pwsh.exe'),[string[]]@('-NoProfile','-NonInteractive','-File',$payload),$case,"$case/inner.stdout.log","$case/inner.stderr.log",6000,$null)
[IO.File]::WriteAllText("$case/inner-result.json",($inner|ConvertTo-Json -Depth 8))
if(!$inner.RootTerminal -or !$inner.JobActiveZero -or !$inner.TreeEmpty -or !$inner.HandlesClosed -or $inner.RootExitCode -ne 0 -or $inner.TimedOut -or $inner.HoldEntered -or $inner.Error -or $inner.CleanupError){exit 7}
[IO.File]::WriteAllText("$case/holder-completed.txt",'holder observed inner terminal0');exit 0
'@
  $case=Invoke-JsonRetentionCase 'nested-holder' $nested 300 $true
  $inner=if(Test-Path -LiteralPath "$($case.directory)/inner-result.json"){Get-Content -LiteralPath "$($case.directory)/inner-result.json" -Raw|ConvertFrom-Json}else{$null}
  $case.row.innerResult=$inner
  $case.row.checks=@(!$case.row.processAccepted,$case.run.TimedOut,$case.run.HoldEntered,($case.run.RootExitCode -eq 0),(Test-Path -LiteralPath "$($case.directory)/holder-completed.txt"),(Test-Path -LiteralPath "$($case.directory)/inner-completed.txt"),[bool]$inner,(Test-JsonReturnedOwnership $inner),(Test-JsonProcessAccepted $inner),($inner.RootProcessId -ne $case.run.RootProcessId));$case.row.controlPassed=$case.row.checks -notcontains $false;Save-JsonControls

  $case=Invoke-JsonRetentionCase 'invalid-executable' 'exit 0' 5000 $false $true
  $case.row.checks=@(!$case.row.processAccepted,($case.run.RootProcessId -eq 0),[bool]$case.run.Error);$case.row.controlPassed=$case.row.checks -notcontains $false;Save-JsonControls

  $case=Invoke-JsonRetentionCase 'on-started-failure' '$case=__CASE__;[IO.File]::WriteAllText("$case/unexpected-resume.txt",''bad'');exit 0' 5000 $false $false $true
  $case.row.checks=@(!$case.row.processAccepted,($case.run.RootProcessId -gt 0),[bool]$case.run.Error,!(Test-Path -LiteralPath "$($case.directory)/unexpected-resume.txt"));$case.row.controlPassed=$case.row.checks -notcontains $false;Save-JsonControls

  $case=Invoke-JsonRetentionCase 'publisher-nonzero' '$case=__CASE__;[IO.File]::WriteAllText("$case/synthetic-publisher.txt",''no channel or network call'');exit 9' 5000
  $case.row.checks=@(!$case.row.processAccepted,($case.run.RootExitCode -eq 9),!($case.run.TimedOut),(Test-Path -LiteralPath "$($case.directory)/synthetic-publisher.txt"));$case.row.controlPassed=$case.row.checks -notcontains $false;Save-JsonControls

  $jsonControlsRecord.allReturnedOwnershipVerified=@($jsonControlsRecord.cases|Where-Object {!$_.returnedOwnershipVerified}).Count -eq 0
  $jsonControlsRecord.allControlsPassed=$jsonControlsRecord.cases.Count -eq 7 -and @($jsonControlsRecord.cases|Where-Object {!$_.controlPassed}).Count -eq 0
  if($jsonControlsRecord.allReturnedOwnershipVerified -and $jsonControlsRecord.allControlsPassed){$jsonControlsRecord.exit=0}
} catch {$jsonControlsRecord.exit=1;$jsonControlsRecord.error=$_.Exception.ToString()}
finally {
  $jsonControlsRecord.budgetExceeded=$jsonControlsClock.Elapsed.TotalSeconds -gt $MaxSeconds
  if($jsonControlsRecord.budgetExceeded){$jsonControlsRecord.exit=1}
  $jsonControlsRecord.identityDrift=@()
  if($jsonControlsRecord.Contains('identities')){
    foreach($name in @('script','helper','powerShell')){
      try {if((Get-JsonControlHash $jsonControlsRecord.identities[$name].path) -ne $jsonControlsRecord.identities[$name].sha256){$jsonControlsRecord.identityDrift+=$name}}
      catch {$jsonControlsRecord.identityDrift+=$name}
    }
  }
  if($jsonControlsRecord.identityDrift.Count -gt 0){$jsonControlsRecord.exit=1}
  $jsonControlsRecord.finishedUtc=[DateTime]::UtcNow.ToString('o')
  $jsonControlsRecord.finalGatePassed=$jsonControlsRecord.exit -eq 0 -and !$jsonControlsRecord.budgetExceeded -and $jsonControlsRecord.allControlsPassed -and $jsonControlsRecord.allReturnedOwnershipVerified
  Save-JsonControls
  Write-Host "JSON RETENTION CONTROLS result=$jsonControlsOut/result.json"
}
exit $jsonControlsRecord.exit
