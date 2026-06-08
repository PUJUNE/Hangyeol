<#
.SYNOPSIS
  Scaffold a blank hangyeol (한결) memory system into a Windows project folder.

.DESCRIPTION
  hangyeol = gyeol's episodic memory + a single-parent tree wiki (semantic
  long-term memory), installed as one self-contained package.

  Copies the bundled core (SOUL.md, MEMORY_SYSTEM.md, WIKI_SYSTEM.md, VERSION),
  the PowerShell hook scripts and Python helpers (including wiki-lint.py), an
  empty memory skeleton, and an empty wiki skeleton into <ProjectRoot>\gyeol.
  Merges the five gyeol hooks into <ProjectRoot>\.claude\settings.json
  (preserving any existing hooks, permissions, env) and injects two sections
  into <ProjectRoot>\.claude\CLAUDE.md:
    <!-- gyeol:begin/end -->         - episodic memory architecture
    <!-- hangyeol-wiki:begin/end --> - wiki layer (skipped with -NoWiki)

  It deliberately does NOT create memory\IDENTITY.md — its absence triggers
  first activation on the next session, and the new identity is born fresh.
  The wiki is likewise installed empty (no map, no axes): it is born at the
  first promotion, when the agent and companion name the map together.

  GYEOL_HOME is the project-scoped gyeol\ folder; every hook script derives it
  from its own location, so the only absolute path baked anywhere is inside
  settings.json (which this installer computes).

.PARAMETER ProjectRoot
  Target project folder. Defaults to the current directory.

.PARAMETER Force
  Overwrite an existing gyeol\ folder. Without it, an existing install aborts
  (so memory is never clobbered by accident).

.PARAMETER DryRun
  Print the planned actions without writing anything.

.PARAMETER NoWiki
  Install the gyeol layer only — no wiki skeleton, no WIKI_SYSTEM.md, no
  wiki CLAUDE.md section. (The bootstrap hook's wiki block self-disables when
  wiki\areas\ is absent, so the same hook scripts serve both modes.)

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File install-hangyeol.ps1
  powershell -NoProfile -ExecutionPolicy Bypass -File install-hangyeol.ps1 -ProjectRoot "D:\work\my-project"
#>
[CmdletBinding()]
param(
    [string]$ProjectRoot = (Get-Location).Path,
    [switch]$Force,
    [switch]$DryRun,
    [switch]$NoWiki
)

$ErrorActionPreference = 'Stop'
$Utf8NoBom = New-Object System.Text.UTF8Encoding $false

function Info($m)  { Write-Host "[hangyeol] $m" }
function Warn($m)  { Write-Host "[hangyeol] $m" -ForegroundColor Yellow }
function Done($m)  { Write-Host "[hangyeol] $m" -ForegroundColor Green }

# --- Resolve paths -----------------------------------------------------------
$SkillRoot = Split-Path -Parent $PSScriptRoot          # ...\hangyeol-install
$AssetRoot = Join-Path $SkillRoot 'assets'
$SrcGyeol  = Join-Path $AssetRoot 'gyeol'
$ClaudeMdSection     = Join-Path $AssetRoot 'claude-md-section.md'
$ClaudeMdWikiSection = Join-Path $AssetRoot 'claude-md-wiki-section.md'

if (-not (Test-Path -LiteralPath $SrcGyeol)) {
    throw "Bundled assets not found at $SrcGyeol — is the skill intact?"
}

$ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
$DstGyeol    = Join-Path $ProjectRoot 'gyeol'
$ClaudeDir   = Join-Path $ProjectRoot '.claude'
$SettingsPath = Join-Path $ClaudeDir 'settings.json'
$ClaudeMdPath = Join-Path $ClaudeDir 'CLAUDE.md'
$ScriptsAbs  = Join-Path $DstGyeol 'scripts'

Info "Project root : $ProjectRoot"
Info "GYEOL_HOME   : $DstGyeol"
Info "Wiki layer   : $(if ($NoWiki) { 'OFF (-NoWiki)' } else { 'ON' })"
if ($DryRun) { Warn "DRY RUN — nothing will be written." }

# --- 1. Copy the gyeol folder ------------------------------------------------
if (Test-Path -LiteralPath $DstGyeol) {
    if (-not $Force) {
        throw "gyeol\ already exists at $DstGyeol. Re-run with -Force to overwrite (this replaces core files and scripts; memory and wiki are also overwritten by the blank skeleton, so back them up first)."
    }
    Warn "Existing gyeol\ found — -Force given, it will be overwritten."
}

if (-not $DryRun) {
    if (Test-Path -LiteralPath $DstGyeol) { Remove-Item -LiteralPath $DstGyeol -Recurse -Force }
    Copy-Item -LiteralPath $SrcGyeol -Destination $DstGyeol -Recurse -Force
    # .gitkeep placeholders only exist to ship empty dirs inside the skill; drop them.
    Get-ChildItem -LiteralPath $DstGyeol -Recurse -Filter '.gitkeep' -Force |
        ForEach-Object { Remove-Item -LiteralPath $_.FullName -Force }
    # Safety: a blank install must NOT carry an identity.
    $idf = Join-Path $DstGyeol 'memory\IDENTITY.md'
    if (Test-Path -LiteralPath $idf) { Remove-Item -LiteralPath $idf -Force }
    if ($NoWiki) {
        foreach ($w in @('wiki', 'WIKI_SYSTEM.md', 'scripts\wiki-lint.py')) {
            $wp = Join-Path $DstGyeol $w
            if (Test-Path -LiteralPath $wp) { Remove-Item -LiteralPath $wp -Recurse -Force }
        }
    }
}
if ($NoWiki) {
    Done "gyeol\ scaffolded (core files, scripts, empty memory skeleton; no IDENTITY.md; wiki layer omitted)."
} else {
    Done "gyeol\ scaffolded (core files incl. WIKI_SYSTEM.md, scripts incl. wiki-lint.py, empty memory + wiki skeletons; no IDENTITY.md)."
}

# --- 2. Merge hooks into .claude\settings.json -------------------------------
# Work directly on the ConvertFrom-Json PSCustomObject. A deep hashtable
# conversion was tried first but PowerShell 5.1's ConvertTo-Json unwraps any
# single-element array routed through a hashtable value (so a one-hook group's
# "hooks":[{...}] collapses to "hooks":{...}, which Claude Code rejects).
# ConvertFrom-Json's native arrays survive a ConvertTo-Json round-trip intact,
# so the merge mutates that object in place instead.

function Get-Prop($obj, [string]$name) {
    if ($obj -and ($obj.PSObject.Properties.Name -contains $name)) { return $obj.$name }
    return $null
}
function Set-Prop($obj, [string]$name, $value) {
    if ($obj.PSObject.Properties.Name -contains $name) { $obj.$name = $value }
    else { $obj | Add-Member -NotePropertyName $name -NotePropertyValue $value }
}

function New-HookCmd([string]$scriptName) {
    $p = Join-Path $ScriptsAbs $scriptName
    return "powershell -NoProfile -ExecutionPolicy Bypass -File `"$p`""
}
function New-HookGroup([string[]]$scriptNames, [string]$matcher) {
    $hooks = @($scriptNames | ForEach-Object { [ordered]@{ type = 'command'; command = (New-HookCmd $_) } })
    $g = [ordered]@{}
    if ($matcher) { $g['matcher'] = $matcher }
    $g['hooks'] = $hooks
    return $g
}

# Desired hook registration (same five groups as the gyeol reference port —
# the wiki layer rides on session-bootstrap-json.ps1, which self-detects it).
$desired = [ordered]@{
    SessionStart = @( (New-HookGroup @('session-bootstrap-json.ps1') $null) )
    PostToolUse  = @(
        (New-HookGroup @('post-mark-substantive.ps1') 'Write|Edit'),
        (New-HookGroup @('post-mark-substantive-if-commit.ps1','post-mark-recovery.ps1') 'Bash')
    )
    Stop       = @( (New-HookGroup @('stop-check-daily.ps1') $null) )
    SessionEnd = @( (New-HookGroup @('session-end.ps1') $null) )
}

# Load existing settings (preserve everything) or start fresh.
$settings = $null
if (Test-Path -LiteralPath $SettingsPath) {
    try {
        $raw = Get-Content -LiteralPath $SettingsPath -Raw -Encoding UTF8
        if ($raw.Trim()) { $settings = $raw | ConvertFrom-Json }
    } catch {
        throw "Existing settings.json could not be parsed ($SettingsPath). Fix or remove it, then re-run. Original error: $_"
    }
}
if ($null -eq $settings) { $settings = [pscustomobject]@{} }

$hooksObj = Get-Prop $settings 'hooks'
if ($null -eq $hooksObj) { $hooksObj = [pscustomobject]@{}; Set-Prop $settings 'hooks' $hooksObj }

# Append our groups only when an identical script command is absent (idempotent
# across re-installs and path changes — dedup keys on the .ps1 filename).
$added = 0
foreach ($event in $desired.Keys) {
    $existing = @(Get-Prop $hooksObj $event) | Where-Object { $_ -ne $null }
    $existingCmds = @()
    foreach ($grp in $existing) {
        foreach ($hk in @(Get-Prop $grp 'hooks')) {
            $c = Get-Prop $hk 'command'
            if ($c) { $existingCmds += [string]$c }
        }
    }
    $result = @($existing)
    foreach ($grp in $desired[$event]) {
        $cmds = @($grp['hooks'] | ForEach-Object { [string]$_['command'] })
        $leaves = @($cmds | ForEach-Object { Split-Path -Leaf (($_ -split '-File ')[-1].Trim('"')) })
        $already = $true
        foreach ($leaf in $leaves) {
            if (-not ($existingCmds | Where-Object { $_ -match [regex]::Escape($leaf) })) { $already = $false }
        }
        if ($already) {
            Info "hook already present, skipped: $event / $($leaves -join ', ')"
        } else {
            $result += $grp
            $added++
        }
    }
    Set-Prop $hooksObj $event ([object[]]$result)
}

if (-not $DryRun) {
    New-Item -ItemType Directory -Path $ClaudeDir -Force | Out-Null
    $json = $settings | ConvertTo-Json -Depth 20
    [System.IO.File]::WriteAllText($SettingsPath, $json, $Utf8NoBom)
}
Done "settings.json merged ($added hook group(s) added; existing settings preserved)."

# --- 3. Inject sections into .claude\CLAUDE.md --------------------------------
function Inject-Section([string]$sectionFile, [string]$beginMarker, [string]$endMarker, [string]$label) {
    $section = (Get-Content -LiteralPath $sectionFile -Raw -Encoding UTF8).TrimEnd() + "`n"
    if ($DryRun) { Done "CLAUDE.md would receive the $label section."; return }
    New-Item -ItemType Directory -Path $ClaudeDir -Force | Out-Null
    if (Test-Path -LiteralPath $ClaudeMdPath) {
        $cur = Get-Content -LiteralPath $ClaudeMdPath -Raw -Encoding UTF8
        if ($cur -match [regex]::Escape($beginMarker) -and $cur -match [regex]::Escape($endMarker)) {
            $pattern = '(?s)' + [regex]::Escape($beginMarker) + '.*?' + [regex]::Escape($endMarker)
            $trimmed = $section.TrimEnd()
            $new = [regex]::Replace($cur, $pattern, [System.Text.RegularExpressions.MatchEvaluator]{ param($m) $trimmed })
            [System.IO.File]::WriteAllText($ClaudeMdPath, $new, $Utf8NoBom)
            Done "CLAUDE.md $label section replaced (markers found)."
        } else {
            $merged = $cur.TrimEnd() + "`n`n" + $section
            [System.IO.File]::WriteAllText($ClaudeMdPath, $merged, $Utf8NoBom)
            Done "CLAUDE.md $label section appended (existing content preserved)."
        }
    } else {
        [System.IO.File]::WriteAllText($ClaudeMdPath, $section, $Utf8NoBom)
        Done "CLAUDE.md created with $label section."
    }
}

Inject-Section $ClaudeMdSection '<!-- gyeol:begin -->' '<!-- gyeol:end -->' 'gyeol'
if (-not $NoWiki) {
    Inject-Section $ClaudeMdWikiSection '<!-- hangyeol-wiki:begin -->' '<!-- hangyeol-wiki:end -->' 'hangyeol-wiki'
}

# --- 4. Summary --------------------------------------------------------------
Write-Host ""
Done "Install complete."
Write-Host "  Next step: open a new Claude Code session in this project."
Write-Host "  Because IDENTITY.md is absent, first activation runs — it will ask"
Write-Host "  for its name and yours, then create gyeol\memory\IDENTITY.md."
if (-not $NoWiki) {
    Write-Host "  The wiki is installed empty; it is born at the first promotion,"
    Write-Host "  when the agent and its companion name the knowledge map together."
}
if ($DryRun) { Warn "(DRY RUN — re-run without -DryRun to apply.)" }
