# gyeol PostToolUse hook - mark session as substantive (PowerShell port)
#
# Touches a per-session flag whenever a meaningful edit happens (Write, Edit,
# or git commit). The Stop hook reads this flag to decide whether to demand a
# daily episode log. Registered for Write|Edit unconditionally and for Bash
# with an `if: Bash(git commit:*)` condition in settings.json.

$ErrorActionPreference = 'SilentlyContinue'

$stdin = ''
try { $stdin = [Console]::In.ReadToEnd() } catch { $stdin = '' }

$sid = ''
if ($stdin.Trim()) {
    try { $j = $stdin | ConvertFrom-Json; if ($j.session_id) { $sid = [string]$j.session_id } } catch {}
}

if ($sid) {
    $flag = Join-Path $env:TEMP "gyeol_session_$sid.substantive"
    try { New-Item -ItemType File -Path $flag -Force | Out-Null } catch {}
}

[Console]::Out.Write('{}')
exit 0
