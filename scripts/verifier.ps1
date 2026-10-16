# Vérifie que tout est là (Windows), sans rien changer. Code de sortie 0 = prêt.
$m = 0
function A($c) { [bool](Get-Command $c -ErrorAction SilentlyContinue) }
foreach ($c in "ffmpeg","yt-dlp") { if (A $c) { Write-Host "  OK  $c" } else { Write-Host "  manque $c"; $m = 1 } }
$Py = if (A py) { "py" } elseif (A python) { "python" } else { $null }
if ($Py) { & $Py -c "import faster_whisper" 2>$null; if ($LASTEXITCODE -eq 0) { Write-Host "  OK  transcription" } else { Write-Host "  manque transcription"; $m = 1 } } else { Write-Host "  manque python"; $m = 1 }
exit $m
