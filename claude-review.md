Permission to write `claude-review.md` was denied, so the full review is below. I didn't run anything and there's no PowerShell here, so the proposed code is untested. Labels: **[lib]** = library behaviour I'm confident of, **[evidence]** = from your runs or the code, **[hyp]** = untested guess, **[unsure]** = I don't reliably know how webOS 6 behaves here.

## 1. Framing, and ENTER vs click

- **[lib]** Your framing is correct. `type:button\nname:X\n\n`, sent as a text frame on the `getPointerInputSocket` path, is what lgtv2, aiowebostv, bscpylgtv and PyWebOSTV all use. `lgtv.ps1:23` matches it, and the navigation that worked confirms it **[evidence]**.
- **[lib]** `ENTER` is the right name for OK; PyWebOSTV's `ok()` sends it. `type:click` is a different kind of event: it clicks wherever the pointer is, even if the pointer is hidden. **Keep ENTER** for moving through menus.
- **Bug:** line 23 splits `LGKEYS` on commas without trimming. `"ENTER, LEFT"` sends the name `" LEFT"` with a leading space, which the TV probably ignores. Trim the names and only allow known ones.

## 2. Why the menu closed

| Candidate | Status |
|---|---|
| Sockets closing abruptly when the process ends | **[evidence] against**: every earlier run did this and the menu stayed open between runs |
| A new registration on each run | **[evidence] against**, same reason |
| The `getForegroundAppInfo` calls (lines 21, 24) | **[evidence] against**: every run made them |
| The `LGREAD=1` readback | **[hyp]**, weak: it only reads, but it isn't ruled out if this was the first run with `LGREAD=1` while the menu was open |
| ENTER on a slider row hides the full menu and shows a small slider bar that later times out | **[hyp] [unsure]** about this model |
| ENTER didn't start editing, so LEFT moved focus back or out | **[hyp]**: this explains both the menu closing and backlight staying at 100. It's likelier if the row is greyed out because of Energy Saving **[unsure]** |
| The menu had already closed before the run (idle timeout) | **[hyp]** |
| The 0.9 s spacing | Unlikely |

**You may already have the answer:** the `FG:` and `FG_AFTER:` lines from that run.
- If `FG:` shows the settings app and `FG_AFTER:` doesn't, the keys closed the menu.
- If `FG:` was already something else, the menu was closed before the run started.

I expect the settings app to show up as something like `com.palm.app.settings` **[unsure]**, so check that once with the menu open.

## 3. Is the backlight readback reliable?

- **[lib]** `getSystemSettings` returns values for the current input and picture mode. Panel Brightness is `backlight`; I'm fairly sure of that mapping for webOS 4–6.
- **[unsure]** I don't know whether the stored value updates on every step or only when the slider closes. Because the picture changes live, I'd expect it to update immediately.
- Your readback ran about 3 s after LEFT, so a lag is unlikely. My best guess is that **LEFT never reached the slider [hyp]**.
- I'm fairly sure `getSystemSettings` also accepts `subscribe:true`; bscpylgtv uses it. Subscribing in a persistent session would settle the lag question.

## 4. Minimal fix: replace lines 22–27

This keeps one registration and one pointer socket for the whole session, takes commands from stdin, and closes both sockets properly:

```powershell
$r=Q "ssap://com.webos.service.networkinput/getPointerInputSocket"
if(-not $r -or -not $r.payload.socketPath){ "NO_POINTER_SOCKET $($r|ConvertTo-Json -Compress)"; exit 3 }
$p=Open-Ws $r.payload.socketPath
$allowed='ENTER','LEFT','RIGHT','UP','DOWN','BACK','EXIT','MENU','HOME'
function Key($n){ $b=[Text.Encoding]::UTF8.GetBytes("type:button`nname:$n`n`n"); $p.SendAsync([ArraySegment[byte]]$b,'Text',$true,[Threading.CancellationToken]::None).Wait(3000) }
function Close-Ws($s){ if(-not $s){return}; if($s.State -eq 'Open'){ try{ $s.CloseOutputAsync('NormalClosure','bye',[Threading.CancellationToken]::None).Wait(2000)|Out-Null }catch{} }; $s.Dispose() }
function Ts{ Get-Date -Format 'HH:mm:ss.fff' }
try {
  "READY: key NAME | fg | read | wait MS | quit"
  while(($line=[Console]::In.ReadLine()) -ne $null){
    $c=$line.Trim() -split '\s+',2
    switch($c[0]){
      'key'  { $n="$($c[1])".Trim().ToUpper(); if($allowed -notcontains $n){ "REJECT '$n'"; break }; "$(Ts) SENT $n ok=$(Key $n)" }
      'fg'   { $r=Q "ssap://com.webos.applicationManager/getForegroundAppInfo"; "$(Ts) FG $($r.payload.appId)" }
      'read' { $r=Q "ssap://settings/getSystemSettings" @{category="picture";keys=@("backlight","contrast","brightness","color","energySaving")}; "$(Ts) READ $($r.payload.settings|ConvertTo-Json -Compress)" }
      'wait' { Start-Sleep -Milliseconds ([int]$c[1]) }
      'quit' { return }
      default { "UNKNOWN '$line'" }
    }
  }
} finally { Close-Ws $p; Close-Ws $w }
```

- It uses `CloseOutputAsync` rather than `CloseAsync`, because `Recv` can leave a receive still waiting and `CloseAsync` would conflict with it.
- If `energySaving` makes the read fail on this firmware, remove it from the key list.

## Safe minimal verification

These steps only send remote buttons and never write settings over SSAP. Take a photo after each step.

**A. Check the script itself, with no keys.** Open the menu by hand and focus Panel Brightness.
1. Run the old script with no `LGKEYS` and no `LGREAD`. Take a photo.
2. Run it again with only `LGREAD=1`. Take a photo.

If the menu is still open after both, the connection, the re-registration, the abrupt exit and the readback are all ruled out.

**B. One persistent session**, with focus on Panel Brightness:
```
fg            # note which app is in front
read          # expect backlight 100
key ENTER
wait 1500     # photo: full menu, small slider bar, or nothing?
fg
key LEFT
wait 1500     # photo
read          # 99 = the slider moved; 100 = LEFT went to navigation
fg
key RIGHT     # puts any change back (to 100)
wait 1500
read
quit
```

How to read the results:
- **`fg` changes after ENTER:** pressing ENTER on that row leaves or hides the menu.
- **The app stays the same, a small bar appears, and the value goes to 99:** the slider works, and the menu "closing" was the bar timing out.
- **The app changes after LEFT and the value stays 100:** LEFT moved focus instead of adjusting the slider. Check whether Energy Saving has locked the row.
