from pathlib import Path
import subprocess, uuid, json, re, base64
root=next(parent for parent in Path(__file__).resolve().parents if (parent/"lib/json/json_verification_page.dart").is_file())
out=root/'build'/('native-window-controls-'+uuid.uuid4().hex[:8]);out.mkdir()
source=(root/'.trellis/.runtime/run_json_ohos_window.ps1').read_text(encoding='utf-8')
def quote(s): return "'"+str(s).replace("'","''")+"'"
results=[]
for name,orphan,child_exit,max_seconds,accept_fail in [('normal',False,0,240,False),('orphan',True,0,240,False),('failed-child',False,4,240,False),('insufficient-budget',False,0,90,False),('failed-acceptance',False,0,240,True)]:
 case=out/name;case.mkdir();child=case/'fake-child.ps1';transport=case/'fake-transport.ps1';stub=case/'observer-copy.ps1'
 result_path=root/'build/native-release-artifacts'/('synthetic-'+out.name+'-'+name)/'result.json'
 code=r'''param([int]$GrantEvent,[string]$PreparedManifest,[string]$NextOwner,[int]$MaxSeconds)
$ErrorActionPreference='Stop';$case=__CASE__
[IO.File]::WriteAllText("$case/validation-entered.txt",'synthetic')
__ORPHAN__
$resultPath=__RESULT__
[IO.Directory]::CreateDirectory((Split-Path $resultPath)) | Out-Null
$record=@{exit=__GATE__;terminal=$true;artifacts=@(@{synthetic=$true},@{synthetic=$true});sourceDrift=@();publication=@{treeEmpty=$true;exit=0;synthetic=$true}}
[IO.File]::WriteAllText($resultPath,($record|ConvertTo-Json -Depth 5))
Write-Host "JSON OHOS result=$resultPath"
exit __EXIT__
'''
 orphan_code=''
 if orphan:
  encoded=base64.b64encode('Start-Sleep -Seconds 30'.encode('utf-16-le')).decode()
  orphan_code=f'''$p=Start-Process -FilePath (Join-Path $PSHOME 'pwsh.exe') -ArgumentList @('-NoProfile','-NonInteractive','-EncodedCommand','{encoded}') -WindowStyle Hidden -PassThru
[IO.File]::WriteAllText("$case/descendant.json",(@{{pid=$p.Id;startTicks=$p.StartTime.ToUniversalTime().Ticks}}|ConvertTo-Json))'''
 child.write_text(code.replace('__CASE__',quote(case)).replace('__ORPHAN__',orphan_code).replace('__RESULT__',quote(result_path)).replace('__GATE__','0' if child_exit==0 else '1').replace('__EXIT__',str(child_exit)),encoding='utf-8')
 transport.write_text(r'''param([string]$Stage)
$ErrorActionPreference='Stop';$case=__CASE__
if($Stage -eq 'acceptance' -and __FAIL__){exit 9}
if($Stage -eq 'final-relay'){
 $gone=$true
 if(Test-Path "$case/descendant.json"){
  $d=Get-Content "$case/descendant.json" -Raw|ConvertFrom-Json
  $p=Get-Process -Id $d.pid -ErrorAction SilentlyContinue
  if($p -and $p.StartTime.ToUniversalTime().Ticks -eq $d.startTicks){$gone=$false}
 }
 [IO.File]::WriteAllText("$case/final-relay-check.json",(@{synthetic=$true;descendantGone=$gone}|ConvertTo-Json))
 if(!$gone){exit 8}
}
exit 0
'''.replace('__CASE__',quote(case)).replace('__FAIL__','$true' if accept_fail else '$false'),encoding='utf-8')
 body=f'''function Invoke-JsonWindowMessage([string]$Name,[string]$Message,[int]$WaitMilliseconds){{
 return Invoke-JsonWindowOwned $Name $jsonWindowPwsh ([string[]]@('-NoProfile','-NonInteractive','-File',{quote(transport)},'-Stage',$Name)) $WaitMilliseconds
}}
'''
 text=source.replace('$jsonWindowChildScript="$jsonWindowRoot/.trellis/.runtime/run_json_ohos_release.ps1"','$jsonWindowChildScript='+quote(child))
 text=re.sub(r'function Invoke-JsonWindowMessage\(.*?(?=function Test-JsonWindowRow)',lambda match:body,text,flags=re.S)
 assert 'channel send' not in text and '.runtime/run_json_ohos_release.ps1' not in text
 stub.write_text(text,encoding='utf-8')
 args=['D:/ProgramFiles/PowerShell/7/pwsh.exe','-NoProfile','-NonInteractive','-File',str(stub),'-GrantEvent','777','-PreparedManifest',str(root/'build/ohos-final-preparation-20261024.json'),'-NextOwner','synthetic-no-real-successor','-MaxSeconds',str(max_seconds)]
 run=subprocess.run(args,capture_output=True,text=True,timeout=45)
 (case/'stdout.log').write_text(run.stdout,encoding='utf-8');(case/'stderr.log').write_text(run.stderr,encoding='utf-8')
 lines=[line for line in run.stdout.splitlines() if line.startswith('JSON WINDOW result=')]
 assert len(lines)==1,(name,run.returncode,run.stdout,run.stderr)
 path=Path(lines[0].split('=',1)[1]);data=json.loads(path.read_text(encoding='utf-8'))
 expected=0 if name in ('normal','orphan') else 1
 assert run.returncode==expected,(name,run.returncode,data)
 assert data['terminal'] is True and data['handoffReady'] is True,(name,data)
 assert data['finalGatePassed'] is (expected==0),(name,data)
 assert all(row['treeEmpty'] is True for row in data['rows']),(name,data)
 if name in ('insufficient-budget','failed-acceptance'): assert not (case/'validation-entered.txt').exists(),name
 if orphan:
  row=next(row for row in data['rows'] if row['name']=='validation');assert row['residualCleanup'] is True
  assert json.loads((case/'final-relay-check.json').read_text())['descendantGone'] is True
 summary={'case':name,'outerExit':run.returncode,'terminal':data['terminal'],'handoffReady':data['handoffReady'],'finalGatePassed':data['finalGatePassed'],'elapsedSeconds':data['elapsedSeconds'],'result':str(path),'syntheticOnly':True,'sdkOrNetworkOrDeviceExecuted':False}
 results.append(summary);print(json.dumps(summary),flush=True)
(out/'controls.json').write_text(json.dumps({'sourceOnlySyntheticControls':True,'cases':results,'fixtureObserverChanges':['Child script replaced by a temporary synthetic process','Transport replaced by a local temporary process, with no channel message'],'runtimeAcceptance':False},indent=2)+'\n',encoding='utf-8')
print('Controls evidence:',out,flush=True)
