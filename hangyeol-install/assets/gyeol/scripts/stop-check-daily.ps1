# gyeol Stop hook - enforce daily episode log (PowerShell port)
#
# 1. Today's daily log exists       -> pass (clean up session flags).
# 2. Session not substantive        -> pass silently.
# 3. Already nagged once            -> pass with soft systemMessage.
# 4. Otherwise                      -> decision: block, demand the daily log.

$ErrorActionPreference = 'SilentlyContinue'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false

$GyeolHome = Split-Path -Parent $PSScriptRoot
$blockDecision = if ($env:GYEOL_BLOCK_DECISION) { $env:GYEOL_BLOCK_DECISION } else { 'block' }

function Emit-Empty { [Console]::Out.Write('{}'); exit 0 }

if (-not (Test-Path -LiteralPath (Join-Path $GyeolHome 'memory'))) { Emit-Empty }

$stdin = ''
try { $stdin = [Console]::In.ReadToEnd() } catch { $stdin = '' }
$sid = ''
if ($stdin.Trim()) {
    try { $j = $stdin | ConvertFrom-Json; if ($j.session_id) { $sid = [string]$j.session_id } } catch {}
}

$today = (Get-Date).ToString('yyyy-MM-dd')
$dailyLog = Join-Path $GyeolHome "memory\episodes\daily\$today.md"
$substantiveFlag = Join-Path $env:TEMP "gyeol_session_$sid.substantive"
$recoveryFlag    = Join-Path $env:TEMP "gyeol_session_$sid.recovery"
$naggedFlag      = Join-Path $env:TEMP "gyeol_session_$sid.nagged"

# Case 1: daily log exists -> clean up and pass.
if (Test-Path -LiteralPath $dailyLog) {
    Remove-Item -LiteralPath $substantiveFlag,$recoveryFlag,$naggedFlag -Force -ErrorAction SilentlyContinue
    Emit-Empty
}

# Case 2: session not substantive -> pass silently.
if (-not (Test-Path -LiteralPath $substantiveFlag)) { Emit-Empty }

# Recovery hint.
$recoveryHint = ''
if (Test-Path -LiteralPath $recoveryFlag) {
    $recoveryHint = " A git-based recovery event was detected this session (git show HEAD: or git checkout HEAD --). Add an 'Incidents' subsection to the daily log capturing what was recovered, why, and what it taught you."
}

# Case 3: already nagged -> soft reminder.
if (Test-Path -LiteralPath $naggedFlag) {
    $msg = [ordered]@{ systemMessage = "gyeol reminder: today's daily log $dailyLog is still missing.$recoveryHint" }
    [Console]::Out.Write(($msg | ConvertTo-Json -Depth 3))
    exit 0
}

# Case 4: hard block, mark nagged.
try { New-Item -ItemType File -Path $naggedFlag -Force | Out-Null } catch {}

$reason = "gyeol memory circuit: this session was substantive (Write/Edit/commit detected) but today's daily log is missing at $dailyLog. Before stopping, write the daily log now: what you worked on, what decisions you made, what you learned, any open threads. Use the format from memory\episodes\daily\ (frontmatter with date + sessions count, then Session sections with What Happened / Decisions Made / Artifacts). Also update memory\episodes\_recent.md: append a one-line entry under today's date in the Daily Index section, reconcile the Still Open section, update the last_updated frontmatter, and prune Daily Index entries older than 7 days.$recoveryHint Do not treat this as optional."

$payload = [ordered]@{ decision = $blockDecision; reason = $reason }
[Console]::Out.Write(($payload | ConvertTo-Json -Depth 3))
exit 0
