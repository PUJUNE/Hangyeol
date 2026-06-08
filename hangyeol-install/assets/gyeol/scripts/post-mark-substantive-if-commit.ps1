# gyeol PostToolUse hook - mark substantive only on git commit (PS port)
#
# Variant of post-mark-substantive.ps1 that inspects the shell command and only
# marks the session substantive when it contains "git commit". Used on the Bash
# matcher so ordinary shell calls do not trip the substantive flag (which would
# over-trigger the Stop hook's daily-log demand).

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

if ($sid -and ($cmd -match 'git\s+commit')) {
    $flag = Join-Path $env:TEMP "gyeol_session_$sid.substantive"
    try { New-Item -ItemType File -Path $flag -Force | Out-Null } catch {}
}

[Console]::Out.Write('{}')
exit 0
