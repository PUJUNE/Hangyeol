# gyeol SessionEnd hook - append-only evidence record (PowerShell port)
#
# Writes {"end":"<UTC ISO 8601>","cwd":"<path>"} to .session-log.jsonl whenever
# a session ends. Never blocks exit. The next SessionStart's staleness check
# reads this file to recover gaps where the Stop hook never fired.

$ErrorActionPreference = 'SilentlyContinue'

$GyeolHome = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path -LiteralPath $GyeolHome)) { exit 0 }

$log = Join-Path $GyeolHome '.session-log.jsonl'
$ts = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

$entry = [ordered]@{ end = $ts; cwd = [string]$PWD.Path }
$line = $entry | ConvertTo-Json -Compress

# Append as UTF-8 without BOM so every line stays parseable JSON.
try {
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::AppendAllText($log, $line + "`n", $utf8)
} catch {}
exit 0
