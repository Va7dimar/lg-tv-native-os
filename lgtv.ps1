param([string]$TvIp="192.168.0.2")
$ErrorActionPreference="Stop"
$dir="$env:LOCALAPPDATA\LGTVRemote"; $keyFile="$dir\client-key-remote.txt"
[Net.ServicePointManager]::ServerCertificateValidationCallback={$true}
function Open-Ws($uri){ $w=New-Object Net.WebSockets.ClientWebSocket; try{ $w.Options.RemoteCertificateValidationCallback={$true} }catch{}; $w.ConnectAsync([Uri]$uri,[Threading.CancellationToken]::None).Wait(8000)|Out-Null; if($w.State -ne 'Open'){throw "no connect $uri"}; $w }
function Send($w,$o){ $b=[Text.Encoding]::UTF8.GetBytes(($o|ConvertTo-Json -Depth 10 -Compress)); $w.SendAsync([ArraySegment[byte]]$b,'Text',$true,[Threading.CancellationToken]::None).Wait()|Out-Null }
$script:buf=New-Object byte[] 65536; $script:ms2=New-Object IO.MemoryStream; $script:pend=$null
function Recv($w,$ms){ while($true){ if(-not $script:pend){$script:pend=$w.ReceiveAsync([ArraySegment[byte]]$script:buf,[Threading.CancellationToken]::None)}; try{ if(-not $script:pend.Wait($ms)){return $null} }catch{ "SOCKET_CLOSED state=$($w.State) status=$($w.CloseStatus) $($w.CloseStatusDescription)" | Write-Host; throw }; $r=$script:pend.Result; $script:pend=$null; $script:ms2.Write($script:buf,0,$r.Count); if($r.EndOfMessage){ $txt=[Text.Encoding]::UTF8.GetString($script:ms2.ToArray()); $script:ms2.SetLength(0); return ($txt|ConvertFrom-Json) } } }
$w=$null; foreach($u in "wss://${TvIp}:3001/","ws://${TvIp}:3000/"){ try{$w=Open-Ws $u; "connected $u"; break}catch{"fail $u $($_.Exception.Message)"} }
$perms=@("READ_INSTALLED_APPS","READ_RUNNING_APPS","READ_TV_CURRENT_TIME","READ_POWER_STATE","READ_NETWORK_STATE","READ_INPUT_DEVICE_LIST","READ_CURRENT_CHANNEL","CONTROL_INPUT_JOYSTICK","CONTROL_MOUSE_AND_KEYBOARD","READ_SETTINGS","WRITE_SETTINGS")
$payload=@{forcePairing=$false;pairingType="PROMPT";manifest=@{manifestVersion=1;appVersion="1.0";permissions=$perms;signed=@{appId="com.lgtvnativeos.remote.settings";vendorId="com.lgtvnativeos";created="20261108";localizedAppNames=@{""="LG TV Native OS Remote Settings"}}}}
if(Test-Path $keyFile){$payload["client-key"]=([IO.File]::ReadAllText($keyFile)).Trim(); "USING_SAVED_KEY"} elseif($env:LGPAIR -ne "1"){ "NO_SAVED_KEY (set LGPAIR=1 to pair once)"; exit 2 } else { "PAIRING_NEW" }
Send $w @{type="register";id="reg0";payload=$payload}
$t0=Get-Date; $deadline=(Get-Date).AddSeconds(90); $ok=$false
while((Get-Date) -lt $deadline){ $m=Recv $w 5000; if(-not $m){continue}
 if($m.type -eq 'response' -and $m.payload.pairingType){ "TV_PAIRING_RESPONSE t=$([int]((Get-Date)-$t0).TotalSeconds)s" }
 elseif($m.type -eq 'registered'){ $k=$m.payload.'client-key'; if($k){ [IO.File]::WriteAllText($keyFile,[string]$k); if(-not (Test-Path $keyFile)){ "KEY_WRITE_FAILED" } }; "REGISTERED after $([int]((Get-Date)-$t0).TotalSeconds)s keyFile=$(Test-Path $keyFile)"; $ok=$true; break }
 elseif($m.type -eq 'error'){ "ERROR $($m.error)"; break } }
if(-not $ok){ "NOT_REGISTERED"; exit 1 }
function Q($uri,$pl){ $script:n++; $id="q$($script:n)"; $o=@{type="request";id=$id;uri=$uri}; if($pl){$o.payload=$pl}; Send $w $o; for($k=0;$k -lt 4;$k++){$r=Recv $w 5000; if($r -and $r.id -eq $id){return $r}}; $null }
$r=Q "ssap://com.webos.applicationManager/getForegroundAppInfo"; "FG: $($r.type) $($r.payload|ConvertTo-Json -Compress)"
$r=Q "ssap://com.webos.service.networkinput/getPointerInputSocket"; $p=Open-Ws $r.payload.socketPath
if($env:LGKEYS) { foreach($k in $env:LGKEYS -split ","){ $b=[Text.Encoding]::UTF8.GetBytes("type:button`nname:$k`n`n"); $ok=$p.SendAsync([ArraySegment[byte]]$b,'Text',$true,[Threading.CancellationToken]::None).Wait(3000); "SENT $k ok=$ok"; Start-Sleep -Milliseconds 900 } }
Start-Sleep 2; $r=Q "ssap://com.webos.applicationManager/getForegroundAppInfo"; "FG_AFTER: $($r.payload.appId)"


if($env:LGREAD -eq "1"){ $v=@{}; foreach($k in "backlight","contrast","brightness","color"){ $v[$k]=(Q "ssap://settings/getSystemSettings" @{category="picture";keys=@($k)}).payload.settings.$k }; "SLIDERS_AFTER: $($v|ConvertTo-Json -Compress)" }
