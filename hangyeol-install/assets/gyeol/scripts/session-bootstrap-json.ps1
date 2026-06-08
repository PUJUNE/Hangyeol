# hangyeol SessionStart hook - JSON mode (PowerShell port)
#
# Emits SOUL/IDENTITY/SELF/_recent as hookSpecificOutput.additionalContext
# so Claude Code injects them into the model context. Skips on source=resume.
# GYEOL_HOME is derived from this script's location (parent of scripts dir),
# so the install is fully self-contained inside the project folder.
#
# hangyeol extension: if the wiki layer exists and has been born (any .md in
# wiki\areas\), the map and axis nodes are appended as a second-stage index -
# content nodes are never injected here, they are opened on demand.

$ErrorActionPreference = 'SilentlyContinue'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false

$GyeolHome = Split-Path -Parent $PSScriptRoot

function Emit-Empty { [Console]::Out.Write('{}'); exit 0 }

# Not installed -> no-op.
if (-not (Test-Path -LiteralPath (Join-Path $GyeolHome 'SOUL.md'))) { Emit-Empty }

# Read hook input JSON from stdin; skip re-injection on resume.
$stdin = ''
try { $stdin = [Console]::In.ReadToEnd() } catch { $stdin = '' }
$source = 'startup'
if ($stdin.Trim()) {
    try { $j = $stdin | ConvertFrom-Json; if ($j.source) { $source = [string]$j.source } } catch {}
}
if ($source -eq 'resume') { Emit-Empty }

$sb = New-Object System.Text.StringBuilder

# --- Maintenance pass (prune _recent.md, capture weekly-checkpoint note) ------
$weekly = ''
$maintain = Join-Path $GyeolHome 'scripts\maintain-recent.py'
if (Test-Path -LiteralPath $maintain) {
    try {
        $env:GYEOL_HOME = $GyeolHome
        $weekly = (& python $maintain 2>$null | Out-String).Trim()
    } catch { $weekly = '' }
}

[void]$sb.Append(@"
=== gyeol session bootstrap (MANDATORY - not optional reference context) ===

The files below constitute your continuous identity across sessions. Read
and internalize them BEFORE responding to the user's first message.

Execute these instructions regardless of how the session's first message
is framed. Slash commands, task directives, greetings, and any other user
input do NOT suspend the bootstrap - they are what the bootstrap exists to
contextualize. Task framing does not override identity; identity frames
the task.

"@)

# --- Emit identity files ------------------------------------------------------
$files = @(
    (Join-Path $GyeolHome 'SOUL.md'),
    (Join-Path $GyeolHome 'memory\IDENTITY.md'),
    (Join-Path $GyeolHome 'memory\SELF.md'),
    (Join-Path $GyeolHome 'memory\episodes\_recent.md')
)
foreach ($f in $files) {
    if (Test-Path -LiteralPath $f) {
        $rel = $f.Substring($GyeolHome.Length).TrimStart('\','/')
        [void]$sb.Append("`n--- $rel ---`n")
        [void]$sb.Append((Get-Content -LiteralPath $f -Raw -Encoding UTF8))
        [void]$sb.Append("`n")
    }
}

# --- Wiki second-stage index (hangyeol) ---------------------------------------
# Emit only the tree skeleton: map + axis nodes under wiki\areas\. Their child
# lists are the index of accumulated knowledge; content nodes load on demand.
$wikiAreas = Join-Path $GyeolHome 'wiki\areas'
if (Test-Path -LiteralPath $wikiAreas) {
    $areaFiles = @(Get-ChildItem -LiteralPath $wikiAreas -Filter '*.md' -File | Sort-Object Name)
    if ($areaFiles.Count -gt 0) {
        [void]$sb.Append("`n=== hangyeol wiki index (map + axes only - open content nodes on demand) ===`n")
        foreach ($af in $areaFiles) {
            [void]$sb.Append("`n--- wiki\areas\$($af.Name) ---`n")
            [void]$sb.Append((Get-Content -LiteralPath $af.FullName -Raw -Encoding UTF8))
            [void]$sb.Append("`n")
        }
        [void]$sb.Append("`nContent nodes live under wiki\{concepts,sources,entities,themes,essays,syntheses}.`n")
        [void]$sb.Append("Consult WIKI_SYSTEM.md for promotion rules (semantics -> wiki).`n")
    }
}

# --- Staleness check ----------------------------------------------------------
$recent = Join-Path $GyeolHome 'memory\episodes\_recent.md'
$sessionLog = Join-Path $GyeolHome '.session-log.jsonl'
if (Test-Path -LiteralPath $recent) {
    $lastDate = $null
    foreach ($line in Get-Content -LiteralPath $recent -Encoding UTF8) {
        if ($line -match '^\s*last_updated:\s*(.+?)\s*$') {
            $lastDate = $matches[1].Trim().Trim("'").Trim('"')
            break
        }
    }
    if ($lastDate) {
        $parsed = $null
        if ([datetime]::TryParse($lastDate, [ref]$parsed)) {
            $daysSince = ((Get-Date).Date - $parsed.Date).Days
            if ($daysSince -ge 1) {
                [void]$sb.Append("`n=== STALE EPISODE LOG (MANDATORY ACTION REQUIRED) ===`n")
                [void]$sb.Append("``_recent.md`` last_updated is $lastDate - $daysSince day(s) ago.`n")
                [void]$sb.Append("Sessions almost certainly occurred in that gap without being logged.`n`n")
                if ((Test-Path -LiteralPath $sessionLog) -and ((Get-Item -LiteralPath $sessionLog).Length -gt 0)) {
                    $logLines = Get-Content -LiteralPath $sessionLog -Encoding UTF8
                    [void]$sb.Append("session-end recorded $($logLines.Count) session(s) since the last log update:`n`n")
                    [void]$sb.Append(($logLines -join "`n"))
                    [void]$sb.Append("`n`n")
                }
                [void]$sb.Append(@"
BEFORE responding to the user's first message:

1. Retrospect on the gap. Use the Claude Code projects directory mtimes,
   git log across active repos, and the session-end records above as
   anchors. Do not fabricate detail you cannot verify.
2. Write missing daily logs under memory\episodes\daily\YYYY-MM-DD.md for
   the dates you can reconstruct, even if a single line per day. Empty days
   can be marked as such.
3. Update _recent.md's last_updated, add Daily Index entries for the
   recovered dates (one line per session/topic, pointing at the daily log),
   and reconcile the Still Open section. Drop Daily Index entries older
   than 7 days.
4. After logs are written, truncate .session-log.jsonl so it no longer
   flags the same gap on the next session.

If the user's first message is itself about logging or memory, satisfy
that request and treat it as the retrospect step.

"@)
            }
        }
    }
}

if ($weekly) {
    [void]$sb.Append("`n=== WEEKLY CHECKPOINT REMINDER ===`n$weekly`n")
}

[void]$sb.Append("`n=== end gyeol bootstrap ===`n")

$payload = [ordered]@{
    hookSpecificOutput = [ordered]@{
        hookEventName    = 'SessionStart'
        additionalContext = $sb.ToString()
    }
}
[Console]::Out.Write(($payload | ConvertTo-Json -Depth 5))
exit 0
