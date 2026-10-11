<#
.SYNOPSIS
  Spireline PC spec check. READ-ONLY: changes nothing, installs nothing, writes no files.

.DESCRIPTION
  Prints CPU, RAM, GPU (name, VRAM, driver), Windows version and build, free space on
  every fixed drive, power/Windows Update settings, WSL status, Git/Claude tools, and the
  Slay the Spire 2 install (path, Steam buildid from appmanifest_2868840.acf, sts2.dll
  sha256, saves folder). Ends with a suggested .wslconfig sized to this machine and a
  list of warnings.

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File .\spec-check.ps1

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File .\spec-check.ps1 | Tee-Object -FilePath "$env:USERPROFILE\Desktop\spec-check.txt"

.NOTES
  -ExecutionPolicy Bypass applies to this one PowerShell process only; it does not change
  the machine's policy. Works in Windows PowerShell 5.1 and PowerShell 7.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Continue'
$ExpectedBuildId = '23811903'      # Slay the Spire 2 v0.107.1, the build Spireline is pinned to
$AppId = '2868840'                 # Steam app id (r33hab/sts2 HANDOFF.md: steam://rungameid/2868840)
$MinNvidiaDriverMajor = 580        # torch 2.12 in r33hab/sts2 uv.lock pulls CUDA 13.0 wheels; CUDA 13 needs an R580+ driver
$Warnings = New-Object System.Collections.Generic.List[string]

function Write-Section([string]$Title) { Write-Output ''; Write-Output ('== ' + $Title + ' ==') }
function Write-KV([string]$Key, $Value) { Write-Output ('{0,-32} {1}' -f $Key, $Value) }
function Add-Warn([string]$Text) { [void]$Warnings.Add($Text); Write-Output ('  WARN: ' + $Text) }
function Get-AcfValue([string]$Text, [string]$Key) {
    $m = [regex]::Match($Text, '"' + [regex]::Escape($Key) + '"\s+"([^"]*)"')
    if ($m.Success) { return $m.Groups[1].Value } else { return $null }
}

Write-Output ('Spireline spec check  ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz') + '  host ' + $env:COMPUTERNAME)

# ---------------------------------------------------------------- CPU
Write-Section 'CPU'
$cores = 0; $logical = 0
try {
    $procs = @(Get-CimInstance -ClassName Win32_Processor -ErrorAction Stop)
    $cores = [int](($procs | Measure-Object -Property NumberOfCores -Sum).Sum)
    $logical = [int](($procs | Measure-Object -Property NumberOfLogicalProcessors -Sum).Sum)
    Write-KV 'CPU' (($procs[0].Name -replace '\s+', ' ').Trim())
    Write-KV 'Sockets' $procs.Count
    Write-KV 'Physical cores' $cores
    Write-KV 'Logical processors' $logical
    Write-KV 'Max clock (MHz)' $procs[0].MaxClockSpeed
    Write-KV 'Virtualization in firmware' $procs[0].VirtualizationFirmwareEnabled
} catch { Add-Warn ('CPU query failed: ' + $_.Exception.Message) }

# ---------------------------------------------------------------- Memory
Write-Section 'Memory'
$ramGB = 0
try {
    $cs = Get-CimInstance -ClassName Win32_ComputerSystem -ErrorAction Stop
    $ramGB = [math]::Round($cs.TotalPhysicalMemory / 1GB, 1)
    Write-KV 'Usable RAM (GB)' $ramGB
    $dimms = @(Get-CimInstance -ClassName Win32_PhysicalMemory -ErrorAction SilentlyContinue)
    if ($dimms.Count -gt 0) {
        $installed = [math]::Round((($dimms | Measure-Object -Property Capacity -Sum).Sum) / 1GB, 0)
        $speeds = (@($dimms | ForEach-Object { $_.ConfiguredClockSpeed }) | Sort-Object -Unique) -join ', '
        Write-KV 'Installed RAM' ('{0} GB in {1} module(s), {2} MT/s' -f $installed, $dimms.Count, $speeds)
    }
    Write-KV 'Hypervisor running' $cs.HypervisorPresent
    if ($cs.HypervisorPresent) { Write-KV '' '(a running hypervisor means virtualization is on, even if the firmware line above says False)' }
} catch { Add-Warn ('Memory query failed: ' + $_.Exception.Message) }

# ---------------------------------------------------------------- GPU
Write-Section 'GPU'
foreach ($vc in @(Get-CimInstance -ClassName Win32_VideoController -ErrorAction SilentlyContinue)) {
    Write-KV 'Adapter' $vc.Name
    Write-KV '  Windows driver version' $vc.DriverVersion
    if ($vc.DriverDate) { Write-KV '  Driver date' ($vc.DriverDate.ToString('yyyy-MM-dd')) }
}
# Win32_VideoController.AdapterRAM is 32-bit and caps at 4 GB, so read VRAM from the display class key.
$classKey = 'HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}'
foreach ($k in @(Get-ChildItem -Path $classKey -ErrorAction SilentlyContinue | Where-Object { $_.PSChildName -match '^\d{4}$' })) {
    $p = Get-ItemProperty -Path $k.PSPath -ErrorAction SilentlyContinue
    if ($p -and $p.PSObject.Properties['HardwareInformation.qwMemorySize']) {
        try {
            $bytes = [double]$p.'HardwareInformation.qwMemorySize'
            Write-KV ('  VRAM (' + $p.DriverDesc + ')') ('{0:N1} GB' -f ($bytes / 1GB))
        } catch { }
    }
}
$smi = $null
foreach ($cand in @((Join-Path $env:SystemRoot 'System32\nvidia-smi.exe'), (Join-Path $env:ProgramFiles 'NVIDIA Corporation\NVSMI\nvidia-smi.exe'))) {
    if (Test-Path -LiteralPath $cand) { $smi = $cand; break }
}
if (-not $smi) { $c = Get-Command nvidia-smi.exe -ErrorAction SilentlyContinue; if ($c) { $smi = $c.Source } }
if ($smi) {
    $q = @(& $smi '--query-gpu=name,memory.total,driver_version' '--format=csv,noheader' 2>&1)
    foreach ($line in $q) { Write-KV 'nvidia-smi (name, VRAM, driver)' $line }
    $hdr = (& $smi 2>&1 | Out-String)
    if ($hdr -match 'CUDA Version:\s*([\d.]+)') { Write-KV 'Highest CUDA the driver supports' $Matches[1] }
    if ("$($q[0])" -match ',\s*(\d+)\.(\d+)\s*$') {
        $major = [int]$Matches[1]
        if ($major -lt $MinNvidiaDriverMajor) {
            Add-Warn ('NVIDIA driver {0}.{1} is older than R{2}; update it on Windows (CHECKLIST A5)' -f $Matches[1], $Matches[2], $MinNvidiaDriverMajor)
        }
    }
} else {
    Add-Warn 'nvidia-smi.exe not found: install or update the NVIDIA driver (CHECKLIST A5)'
}

# ---------------------------------------------------------------- Windows
Write-Section 'Windows'
try {
    $os = Get-CimInstance -ClassName Win32_OperatingSystem -ErrorAction Stop
    $cv = Get-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion' -ErrorAction SilentlyContinue
    Write-KV 'Edition' ('{0} ({1})' -f $os.Caption, $cv.EditionID)
    Write-KV 'Version' ('{0}, build {1}.{2}, {3}' -f $cv.DisplayVersion, $os.BuildNumber, $cv.UBR, $os.OSArchitecture)
    Write-KV 'Last boot' $os.LastBootUpTime
    $build = [int]$os.BuildNumber
    if ($build -lt 22000) {
        Add-Warn 'Windows 10: some .wslconfig keys (vmIdleTimeout, networkingMode=mirrored) need Windows 11'
    } elseif ($build -lt 22621) {
        Add-Warn 'Windows 11 older than 22H2: networkingMode=mirrored is not available'
    }
    if ($cv.EditionID -match 'Core') { Write-KV '' 'Home edition: Group Policy update controls are not available; use Active hours and Pause updates' }
} catch { Add-Warn ('Windows query failed: ' + $_.Exception.Message) }

# ---------------------------------------------------------------- Power and updates
Write-Section 'Power and Windows Update (read-only)'
Write-KV 'Active power scheme' (((powercfg /getactivescheme 2>&1) | Out-String).Trim())
function Get-PowerAcSeconds([string]$Sub, [string]$Setting) {
    $out = ((powercfg /query SCHEME_CURRENT $Sub $Setting 2>&1) | Out-String)
    if ($out -match 'Current AC Power Setting Index:\s*0x([0-9a-fA-F]+)') { return [Convert]::ToInt64($Matches[1], 16) }
    return $null
}
$sleepAc = Get-PowerAcSeconds 'SUB_SLEEP' 'STANDBYIDLE'
$hibAc = Get-PowerAcSeconds 'SUB_SLEEP' 'HIBERNATEIDLE'
foreach ($pair in @(@('Sleep after (AC)', $sleepAc), @('Hibernate after (AC)', $hibAc))) {
    $v = $pair[1]
    if ($null -eq $v) { $txt = 'not reported (hibernation off, or non-English Windows: check Control Panel > Power Options)' }
    elseif ($v -eq 0) { $txt = 'never' }
    else { $txt = ('{0} min' -f [math]::Round($v / 60)) }
    Write-KV $pair[0] $txt
}
if (($null -ne $sleepAc -and $sleepAc -ne 0) -or ($null -ne $hibAc -and $hibAc -ne 0)) {
    Add-Warn 'The PC sleeps or hibernates on AC power: run the powercfg commands in CHECKLIST A3'
}
$ux = Get-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings' -ErrorAction SilentlyContinue
if ($ux -and $null -ne $ux.ActiveHoursStart) {
    Write-KV 'Windows Update active hours' ('{0}:00 to {1}:00' -f $ux.ActiveHoursStart, $ux.ActiveHoursEnd)
    if ($null -ne $ux.SmartActiveHoursState) { Write-KV 'Automatic active hours state' $ux.SmartActiveHoursState }
} else {
    Write-KV 'Windows Update active hours' 'not set (CHECKLIST A4)'
}

# ---------------------------------------------------------------- Disks
Write-Section 'Disks (fixed drives)'
$fixed = @(Get-CimInstance -ClassName Win32_LogicalDisk -Filter 'DriveType=3' -ErrorAction SilentlyContinue)
foreach ($d in $fixed) {
    $size = [math]::Round($d.Size / 1GB, 0)
    $free = [math]::Round($d.FreeSpace / 1GB, 0)
    $pct = 0
    if ($d.Size) { $pct = [math]::Round(100 * $d.FreeSpace / $d.Size, 0) }
    Write-KV ('Drive ' + $d.DeviceID) ('{0} GB free of {1} GB ({2}%), {3}, label "{4}"' -f $free, $size, $pct, $d.FileSystem, $d.VolumeName)
    if ($d.DeviceID -eq $env:SystemDrive -and $free -lt 80) {
        Add-Warn ('{0} has {1} GB free; WSL (Ubuntu + .NET + ~7 GB of torch/CUDA wheels + caches) wants 80 GB or more' -f $d.DeviceID, $free)
    }
}
try {
    foreach ($pd in @(Get-PhysicalDisk -ErrorAction Stop)) {
        Write-KV ('Physical disk ' + $pd.DeviceId) ('{0}, {1}, {2:N0} GB' -f $pd.FriendlyName, $pd.MediaType, ($pd.Size / 1GB))
    }
} catch { Write-KV 'Physical disks' '(Get-PhysicalDisk not available in this session)' }

# ---------------------------------------------------------------- WSL
Write-Section 'WSL'
$env:WSL_UTF8 = '1'   # this process only: makes wsl.exe print UTF-8 instead of UTF-16
$wslExe = Join-Path $env:SystemRoot 'System32\wsl.exe'
if (Test-Path -LiteralPath $wslExe) {
    foreach ($wslArgs in @(@('--version'), @('--status'), @('--list', '--verbose'))) {
        Write-Output ('-- wsl ' + ($wslArgs -join ' '))
        $o = (& $wslExe @wslArgs 2>&1 | Out-String)
        Write-Output $o.TrimEnd()
    }
} else {
    Write-Output 'wsl.exe not found: WSL is not installed (CHECKLIST B2).'
}
$wslconfig = Join-Path $env:USERPROFILE '.wslconfig'
if (Test-Path -LiteralPath $wslconfig) {
    Write-Output ('-- existing ' + $wslconfig)
    Get-Content -LiteralPath $wslconfig | ForEach-Object { Write-Output ('   ' + $_) }
} else {
    Write-KV '.wslconfig' 'none yet (CHECKLIST B1)'
}

# ---------------------------------------------------------------- Tools
Write-Section 'Tools'
$git = Get-Command git.exe -ErrorAction SilentlyContinue
if ($git) { Write-KV 'Git for Windows' (((& $git.Source --version 2>&1) | Out-String).Trim()) } else { Write-KV 'Git for Windows' 'not installed (CHECKLIST A7)' }
$winget = Get-Command winget.exe -ErrorAction SilentlyContinue
Write-KV 'winget' $(if ($winget) { 'present' } else { 'not found' })
$claudeNative = Get-Command claude.exe -ErrorAction SilentlyContinue
Write-KV 'Claude Code (native Windows)' $(if ($claudeNative) { $claudeNative.Source + '  (not needed: Spireline runs Claude Code inside WSL)' } else { 'not installed (fine: Claude Code goes inside WSL)' })
$desktop = $null
foreach ($cand in @((Join-Path $env:LOCALAPPDATA 'AnthropicClaude'), (Join-Path $env:LOCALAPPDATA 'Programs\Claude'))) {
    if (Test-Path -LiteralPath $cand) { $desktop = $cand; break }
}
if (-not $desktop) {
    try {
        $appx = Get-AppxPackage -Name '*Claude*' -ErrorAction Stop | Select-Object -First 1
        if ($appx) { $desktop = $appx.PackageFullName }
    } catch { }
}
Write-KV 'Claude Desktop app' $(if ($desktop) { $desktop } else { 'not detected (CHECKLIST A8; also check the Start menu)' })

# ---------------------------------------------------------------- Steam and Slay the Spire 2
Write-Section 'Steam and Slay the Spire 2'
$roots = New-Object System.Collections.Generic.List[string]
$libs = New-Object System.Collections.Generic.List[string]
function Add-UniquePath($List, [string]$PathText, [string]$MustContain) {
    if (-not $PathText) { return }
    $q = ($PathText -replace '/', '\').TrimEnd('\')
    foreach ($e in $List) { if ($e -ieq $q) { return } }   # Windows paths are case-insensitive
    if ($MustContain) { if (-not (Test-Path -LiteralPath (Join-Path $q $MustContain))) { return } }
    elseif (-not (Test-Path -LiteralPath $q)) { return }
    [void]$List.Add($q)
}
try { Add-UniquePath $roots (Get-ItemProperty -Path 'HKCU:\Software\Valve\Steam' -ErrorAction Stop).SteamPath '' } catch { }
try { Add-UniquePath $roots (Get-ItemProperty -Path 'HKLM:\SOFTWARE\WOW6432Node\Valve\Steam' -ErrorAction Stop).InstallPath '' } catch { }
Add-UniquePath $roots (Join-Path ${env:ProgramFiles(x86)} 'Steam') ''
Add-UniquePath $roots (Join-Path $env:ProgramFiles 'Steam') ''
foreach ($r in $roots) {
    Add-UniquePath $libs $r 'steamapps'
    $vdf = Join-Path $r 'steamapps\libraryfolders.vdf'
    if (Test-Path -LiteralPath $vdf) {
        foreach ($m in [regex]::Matches((Get-Content -Raw -LiteralPath $vdf), '"path"\s+"([^"]+)"')) {
            Add-UniquePath $libs ($m.Groups[1].Value -replace '\\\\', '\') 'steamapps'
        }
    }
}
foreach ($d in $fixed) {
    foreach ($sub in @('SteamLibrary', 'Steam', 'Games\Steam', 'Games\SteamLibrary', 'Program Files (x86)\Steam')) {
        Add-UniquePath $libs (Join-Path ($d.DeviceID + '\') $sub) 'steamapps'
    }
}
Write-KV 'Steam install(s)' $(if ($roots.Count) { $roots -join '; ' } else { 'not found' })
Write-KV 'Steam libraries found' $(if ($libs.Count) { $libs -join '; ' } else { 'none' })

$autoMeaning = @{ '0' = 'Always keep this game updated'; '1' = 'Only update this game when I launch it'; '2' = 'High priority' }
$found = $false
foreach ($lib in $libs) {
    $acf = Join-Path $lib ('steamapps\appmanifest_' + $AppId + '.acf')
    if (-not (Test-Path -LiteralPath $acf)) { continue }
    $found = $true
    $text = Get-Content -Raw -LiteralPath $acf
    $buildid = Get-AcfValue $text 'buildid'
    $installdir = Get-AcfValue $text 'installdir'
    $auto = Get-AcfValue $text 'AutoUpdateBehavior'
    $target = Get-AcfValue $text 'TargetBuildID'
    $state = Get-AcfValue $text 'StateFlags'
    $last = Get-AcfValue $text 'LastUpdated'
    Write-KV 'appmanifest' $acf
    Write-KV 'Name' (Get-AcfValue $text 'name')
    Write-KV 'buildid' $buildid
    if ($buildid -eq $ExpectedBuildId) {
        Write-KV 'Build check' ('MATCH: ' + $ExpectedBuildId + ' (v0.107.1)')
    } else {
        Add-Warn ('buildid ' + $buildid + ' is not ' + $ExpectedBuildId + ' (v0.107.1). Do not launch the game; see CHECKLIST troubleshooting.')
    }
    if ($target -and $target -ne '0' -and $target -ne $buildid) { Add-Warn ('Steam has an update queued to build ' + $target + ': launching from Steam will install it') }
    $autoText = $auto
    if ($auto -and $autoMeaning.ContainsKey($auto)) { $autoText = $auto + ' = ' + $autoMeaning[$auto] + ' (Steam convention; confirm in the game Properties)' }
    Write-KV 'AutoUpdateBehavior' $autoText
    if ($auto -ne '1') { Add-Warn 'Set Properties > Updates to "Only update this game when I launch it" (CHECKLIST A6)' }
    Write-KV 'StateFlags' ($state + '  (4 = fully installed; other bits mean an update or validation is pending)')
    if ($last -match '^\d+$') { Write-KV 'LastUpdated' ([DateTimeOffset]::FromUnixTimeSeconds([int64]$last).LocalDateTime) }
    $gameDir = Join-Path $lib ('steamapps\common\' + $installdir)
    Write-KV 'Game folder' $gameDir
    if (Test-Path -LiteralPath $gameDir) {
        $dll = Get-ChildItem -LiteralPath $gameDir -Recurse -Depth 3 -Filter 'sts2.dll' -File -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -match 'data_sts2_' } | Select-Object -First 1
        if ($dll) {
            Write-KV 'sts2.dll' $dll.FullName
            Write-KV 'sts2.dll sha256' ((Get-FileHash -LiteralPath $dll.FullName -Algorithm SHA256).Hash.ToLower())
        } else {
            Write-KV 'sts2.dll' 'not found under data_sts2_*'
        }
        $bytes = (Get-ChildItem -LiteralPath $gameDir -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
        Write-KV 'Game folder size' ('{0:N2} GB (needed free space for the archive copy in A6)' -f ($bytes / 1GB))
        $mods = Join-Path $gameDir 'mods'
        Write-KV 'mods folder' $(if (Test-Path -LiteralPath $mods) { 'present: ' + $mods } else { 'absent (unmodded install)' })
    }
}
if (-not $found) { Add-Warn ('No appmanifest_' + $AppId + '.acf in any Steam library found: Slay the Spire 2 is not installed, or is in a library this script did not find') }

Write-Section 'Slay the Spire 2 saves and logs'
$saveDir = Join-Path $env:APPDATA 'SlayTheSpire2'
if (Test-Path -LiteralPath $saveDir) {
    $files = @(Get-ChildItem -LiteralPath $saveDir -Recurse -File -ErrorAction SilentlyContinue)
    $sum = ($files | Measure-Object -Property Length -Sum).Sum
    Write-KV 'Save folder' ('{0}  ({1} files, {2:N1} MB)' -f $saveDir, $files.Count, ($sum / 1MB))
    Write-KV '.run history files' (@($files | Where-Object { $_.Extension -eq '.run' })).Count
    $log = Join-Path $saveDir 'logs\godot.log'
    if (Test-Path -LiteralPath $log) {
        $m = Select-String -LiteralPath $log -Pattern 'release=(v[\d.]+)' | Select-Object -First 1
        if ($m) { Write-KV 'Game log release' $m.Matches[0].Groups[1].Value }
    }
} else {
    Write-KV 'Save folder' ($saveDir + ' not found (game never run on this PC?)')
}

# ---------------------------------------------------------------- Suggested .wslconfig
Write-Section 'Suggested %UserProfile%\.wslconfig (NOT written; copy it yourself in CHECKLIST B1)'
if ($ramGB -gt 0 -and $logical -gt 0) {
    $ram = [int][math]::Round($ramGB)
    $reserve = [int][math]::Max(6, [math]::Min(12, [math]::Round($ram * 0.25)))
    $wslMem = [int][math]::Max(4, $ram - $reserve)
    $wslProc = [int][math]::Max(2, $logical - 2)
    $wslSwap = [int][math]::Min(16, [math]::Max(4, [math]::Floor($wslMem / 4)))
    Write-Output '[wsl2]'
    Write-Output ('# {0} GB RAM in this PC; {1} GB left for Windows, Steam and the Desktop app' -f $ram, ($ram - $wslMem))
    Write-Output ('memory={0}GB' -f $wslMem)
    Write-Output ('# {0} logical processors in this PC; 2 left for Windows' -f $logical)
    Write-Output ('processors={0}' -f $wslProc)
    Write-Output ('swap={0}GB' -f $wslSwap)
    Write-Output ''
    Write-Output '[general]'
    Write-Output 'instanceIdleTimeout=-1'
    Write-Output ''
    Write-Output '[experimental]'
    Write-Output 'autoMemoryReclaim=gradual'
    Write-Output 'sparseVhd=true'
} else {
    Write-Output '(RAM or CPU count unknown; use the template in CHECKLIST B1 and fill the numbers in by hand)'
}

# ---------------------------------------------------------------- Summary
Write-Section 'Summary'
if ($Warnings.Count -eq 0) {
    Write-Output 'No warnings.'
} else {
    Write-Output ('{0} warning(s):' -f $Warnings.Count)
    foreach ($w in $Warnings) { Write-Output ('  - ' + $w) }
}
Write-Output ''
Write-Output 'Nothing was changed on this PC.'
