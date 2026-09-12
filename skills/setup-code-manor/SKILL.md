---
name: setup-code-manor
description: Setup and health-check wizard for Code-Manor. Auto-discovers workspaces from Antigravity 2.0, populates projects.json, and verifies WSL, tasks-axi, and no-mistakes toolchains.
---

# 🛠️ Setup Code-Manor — Wizard & Environment Health Check

Run this skill to configure and verify the **Code-Manor** orchestration environment on your machine. It ensures all dependencies across Windows, WSL, `tasks-axi`, and `projects.json` are properly wired.

---

## 📋 What This Skill Performs

1. **Workspace Auto-Discovery (`projects.json` Sync):**
   - Inspects Antigravity 2.0 desktop workspace records located at `AppData\Roaming\Antigravity\User\workspaceStorage`.
   - Extracts all known project folders.
   - Normalizes Windows paths (`C:/...`) to WSL paths (`/mnt/c/...`).
   - Populates or updates `C:\Users\oguz_\.gemini\antigravity\projects.json` so **`/steward`** can instantly locate any project with zero token overhead.

2. **WSL2 Toolchain Verification:**
   - Verifies WSL Ubuntu-24.04 availability.
   - Checks `tasks-axi` executable in WSL (`wsl -d Ubuntu-24.04 -u oguz which tasks-axi`).
   - Checks `no-mistakes` gate in WSL (`wsl -d Ubuntu-24.04 -u oguz /home/oguz/.no-mistakes/bin/no-mistakes --version`).
   - Checks `git` and `gh` authentication status in WSL.

3. **Memory & SSOT Baseline:**
   - Checks whether target projects have `.memory/` directories and `.tasks.toml` configs.
   - Offers to initialize `.memory/` (`ARCHITECTURE.md`, `PATTERNS.md`, `LESSONS.md`) if missing.

---

## 🚀 Execution Steps

When invoked, the agent should run the following diagnostic script:

```powershell
# 1. Discover workspaces from Antigravity Roaming
$wsStorage = "$env:APPDATA\Antigravity\User\workspaceStorage"
$projects = @()

if (Test-Path $wsStorage) {
    $wsFiles = Get-ChildItem -Path $wsStorage -Filter "workspace.json" -Recurse -Depth 2
    foreach ($f in $wsFiles) {
        try {
            $json = Get-Content $f.FullName -Raw | ConvertFrom-Json
            if ($json.folder) {
                $rawPath = [System.Uri]::UnescapeDataString($json.folder.Replace("file:///", ""))
                $normPath = $rawPath.Replace("\", "/")
                if (Test-Path $normPath) {
                    $projectName = Split-Path $normPath -Leaf
                    $drive = $normPath.Substring(0, 1).ToLower()
                    $wslPath = "/mnt/$drive" + $normPath.Substring(2)
                    
                    $hasTasksAxi = Test-Path "$normPath/.tasks.toml"
                    $hasMemory = Test-Path "$normPath/.memory"
                    
                    $projects += [PSCustomObject]@{
                        id = $projectName.ToLower().Replace(" ", "-")
                        name = $projectName
                        windows_path = $normPath
                        wsl_path = $wslPath
                        tracker = if ($hasTasksAxi) { "tasks-axi" } else { "none" }
                        memory_dir = if ($hasMemory) { ".memory" } else { "none" }
                        status = "active"
                    }
                }
            }
        } catch {}
    }
}

# 2. Write projects.json
$projectsFile = "$env:USERPROFILE\.gemini\antigravity\projects.json"
$projects | ConvertTo-Json -Depth 4 | Set-Content -Path $projectsFile -Encoding utf8
Write-Host "Discovered and registered $($projects.Count) projects into projects.json"

# 3. Verify WSL tools
wsl -d Ubuntu-24.04 -u oguz bash -c "which tasks-axi || echo 'tasks-axi not in PATH'"
wsl -d Ubuntu-24.04 -u oguz bash -c "/home/oguz/.no-mistakes/bin/no-mistakes --version 2>/dev/null || echo 'no-mistakes not found'"
```

Finally, present a clean summary table to the user with the discovered projects and verification status.
