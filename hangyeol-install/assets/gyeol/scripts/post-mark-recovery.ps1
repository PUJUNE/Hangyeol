# gyeol PostToolUse hook - mark session as having a recovery event (PS port)
#
# Fires when a Bash command matches a file-restoration pattern (git show HEAD:,
# git checkout HEAD --, etc.). Touches a per-session recovery flag so the Stop
# hook adds an Incidents-section reminder to the daily-log demand.

$ErrorActionPreference = 'SilentlyContinue'

$stdin = ''
try { $stdin = [Console]::In.ReadToEnd() } catch { $stdin = '' }

$sid = ''
$cmd = ''
if ($stdin.Trim()) {
    try {
        $j = $stdin | ConvertFrom-Json
        if ($j.session_id) { $sid = [string]$j.session_id }
        if ($j.tool_input -and $j.tool_input.command) { $cmd = [string]$j.tool_input.command }
    } catch {}
}

if ($sid -and ($cmd -match 'git show HEAD\^?:|git checkout HEAD (--|~)')) {
    $flag = Join-Path $env:TEMP "gyeol_session_$sid.recovery"
    try { New-Item -ItemType File -Path $flag -Force | Out-Null } catch {}
}

[Console]::Out.Write('{}')
exit 0
