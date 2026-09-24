#!/usr/bin/env node

/**
 * Code-Manor CLI
 * Unified helper for initializing and managing Code-Manor workspaces.
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

function getHomeDir() {
  return os.homedir();
}

function getProjectsJsonPath() {
  const home = getHomeDir();
  return path.join(home, '.gemini', 'antigravity', 'projects.json');
}

function toWslPath(windowsPath) {
  const normalized = windowsPath.replace(/\\/g, '/');
  const match = normalized.match(/^([a-zA-Z]):\/(.*)$/);
  if (match) {
    const drive = match[1].toLowerCase();
    const rest = match[2];
    return `/mnt/${drive}/${rest}`;
  }
  return normalized;
}

function toWindowsPath(linuxPath) {
  const normalized = linuxPath.replace(/\\/g, '/');
  const match = normalized.match(/^\/mnt\/([a-zA-Z])\/(.*)$/);
  if (match) {
    const drive = match[1].toLowerCase();
    const rest = match[2];
    return `${drive}:/${rest}`;
  }
  return normalized;
}

function resolvePaths(targetDir) {
  const absPath = path.resolve(targetDir);
  const isWindows = process.platform === 'win32';

  let windowsPath = '';
  let wslPath = '';

  if (isWindows) {
    windowsPath = absPath.replace(/\\/g, '/');
    wslPath = toWslPath(windowsPath);
  } else {
    // Linux, macOS, or WSL
    wslPath = absPath;
    windowsPath = toWindowsPath(absPath);
  }

  return { absPath, windowsPath, wslPath };
}

function detectProjectName(targetDir) {
  const pkgPath = path.join(targetDir, 'package.json');
  if (fs.existsSync(pkgPath)) {
    try {
      const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));
      if (pkg.name) return pkg.name;
    } catch (e) {}
  }
  return path.basename(path.resolve(targetDir));
}

function detectStack(targetDir) {
  if (fs.existsSync(path.join(targetDir, 'package.json'))) {
    const hasTs = fs.existsSync(path.join(targetDir, 'tsconfig.json'));
    return hasTs ? 'typescript' : 'javascript';
  }
  if (fs.existsSync(path.join(targetDir, 'pyproject.toml')) || fs.existsSync(path.join(targetDir, 'requirements.txt'))) {
    return 'python';
  }
  if (fs.existsSync(path.join(targetDir, 'Cargo.toml'))) {
    return 'rust';
  }
  if (fs.existsSync(path.join(targetDir, 'go.mod'))) {
    return 'go';
  }
  return 'general';
}

function ensureFile(filePath, defaultContent) {
  if (!fs.existsSync(filePath)) {
    fs.mkdirSync(path.dirname(filePath), { recursive: true });
    fs.writeFileSync(filePath, defaultContent, 'utf8');
    return true;
  }
  return false;
}

function initCommand(args) {
  let targetDir = '.';
  let policy = 'staged';
  let customName = null;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--policy' && args[i + 1]) {
      policy = args[++i];
    } else if (args[i] === '--name' && args[i + 1]) {
      customName = args[++i];
    } else if (!args[i].startsWith('-')) {
      targetDir = args[i];
    }
  }

  const { absPath, windowsPath, wslPath } = resolvePaths(targetDir);
  if (!fs.existsSync(absPath)) {
    console.error(`❌ Error: Target directory does not exist: ${absPath}`);
    process.exit(1);
  }

  const projectName = customName || detectProjectName(absPath);
  const projectId = projectName.toLowerCase().replace(/[^a-z0-9_-]/g, '-');
  const stack = detectStack(absPath);

  console.log(`🏰 Code-Manor: Initializing project in '${absPath}'...`);

  // 1. Ensure .memory/ directory & core files
  const memoryDir = path.join(absPath, '.memory');
  const archCreated = ensureFile(
    path.join(memoryDir, 'ARCHITECTURE.md'),
    `# 🏰 ${projectName} Architecture\n\nCanonical architectural baseline and module boundaries.\n`
  );
  const decCreated = ensureFile(
    path.join(memoryDir, 'DECISIONS.md'),
    `# 🏛️ ${projectName} Architectural Decisions\n\nRecord of enduring, non-trivial architectural decisions (In-place edit).\n`
  );
  const lesCreated = ensureFile(
    path.join(memoryDir, 'LESSONS.md'),
    `# 🧠 ${projectName} Lessons Learned\n\nEdge cases, debugging findings, and domain rules.\n`
  );

  // 2. Ensure .frontier.toml and .tasks.toml
  const frontierCreated = ensureFile(
    path.join(absPath, '.frontier.toml'),
    `# frontier-axi configuration\n[frontier]\nversion = "1.0"\n`
  );
  const tasksCreated = ensureFile(
    path.join(absPath, '.tasks.toml'),
    `# tasks-axi configuration\n[tasks]\nversion = "1.0"\n`
  );

  // 3. Ensure Makefile for `make check`
  const makefilePath = path.join(absPath, 'Makefile');
  let makefileCreated = false;
  if (!fs.existsSync(makefilePath)) {
    let makefileTemplate = `.PHONY: check test test:unit test:integration\n\n# Hermetic local gate (zero external DB/network required)\ncheck: test:unit\n\ntest:unit:\n\techo "Configure hermetic unit test command in Makefile"\n\ntest:integration:\n\techo "Configure integration test command in Makefile"\n\ntest:\n\techo "Configure test command in Makefile"\n`;
    if (stack === 'typescript' || stack === 'javascript') {
      makefileTemplate = `.PHONY: check lint typecheck test test:unit test:integration\n\n# Tier 1 Mandatory Hermetic Local Gate (Zero external DB/Docker/network)\ncheck: lint typecheck test:unit\n\nlint:\n\tnpm run lint\n\ntypecheck:\n\tnpx tsc --noEmit\n\ntest:unit:\n\tnpm run test:unit 2>/dev/null || npm test -- --testPathIgnorePatterns="integration" 2>/dev/null || npm test\n\ntest:integration:\n\tnpm run test:integration 2>/dev/null || npm test\n\ntest:\n\tnpm test\n`;
    } else if (stack === 'python') {
      makefileTemplate = `.PHONY: check lint typecheck test test:unit test:integration\n\n# Tier 1 Mandatory Hermetic Local Gate (Zero external DB/Docker/network)\ncheck: lint typecheck test:unit\n\nlint:\n\truff check .\n\ntypecheck:\n\tpyright\n\ntest:unit:\n\tpytest -q -m "not integration" 2>/dev/null || pytest -q\n\ntest:integration:\n\tpytest -q -m "integration"\n\ntest:\n\tpytest\n`;
    }
    fs.writeFileSync(makefilePath, makefileTemplate, 'utf8');
    makefileCreated = true;
  }

  // 4. Update projects.json
  const projectsJsonPath = getProjectsJsonPath();
  let projects = [];
  if (fs.existsSync(projectsJsonPath)) {
    try {
      projects = JSON.parse(fs.readFileSync(projectsJsonPath, 'utf8'));
    } catch (e) {
      console.warn(`⚠️ Warning: Could not parse existing projects.json, initializing fresh list.`);
      projects = [];
    }
  } else {
    fs.mkdirSync(path.dirname(projectsJsonPath), { recursive: true });
  }

  // Check if project exists by id or path
  const existingIndex = projects.findIndex(
    p => p.id === projectId || p.windows_path === windowsPath || p.wsl_path === wslPath
  );

  const projectEntry = {
    id: projectId,
    name: projectName,
    windows_path: windowsPath,
    wsl_path: wslPath,
    tracker: "tasks-axi",
    memory_dir: ".memory",
    status: "active",
    last_active: new Date().toISOString(),
    policy: policy
  };

  if (existingIndex >= 0) {
    projects[existingIndex] = { ...projects[existingIndex], ...projectEntry };
    console.log(`🔄 Updated existing registry entry in projects.json`);
  } else {
    projects.push(projectEntry);
    console.log(`✨ Registered new project in projects.json`);
  }

  fs.writeFileSync(projectsJsonPath, JSON.stringify(projects, null, 4), 'utf8');

  console.log(`\n✅ Project successfully wired into Code-Manor Estate!`);
  console.log(`--------------------------------------------------`);
  console.log(`📌 Project ID:     ${projectId} (${projectName})`);
  console.log(`📁 Windows Path:   ${windowsPath}`);
  console.log(`🐧 WSL/Linux Path: ${wslPath}`);
  console.log(`🛡️ Policy:         ${policy}`);
  console.log(`📋 Tracker:        tasks-axi`);
  console.log(`🧠 Memory:         .memory/ (DECISIONS.md, ARCHITECTURE.md, LESSONS.md)`);
  if (makefileCreated) console.log(`🛠️ Makefile:       Provisioned canonical 'make check' baseline`);
  console.log(`--------------------------------------------------`);
  console.log(`🚀 Next: Run '/butler' inside this workspace or '/steward' to orchestrate across projects.\n`);
}

function listCommand() {
  const projectsJsonPath = getProjectsJsonPath();
  if (!fs.existsSync(projectsJsonPath)) {
    console.log(`No projects.json registry found at: ${projectsJsonPath}`);
    return;
  }
  const projects = JSON.parse(fs.readFileSync(projectsJsonPath, 'utf8'));
  console.log(`\n🏰 Code-Manor Fleet Registry (${projects.length} projects):\n`);
  projects.forEach((p, idx) => {
    console.log(` ${idx + 1}. [${p.id}] ${p.name}`);
    console.log(`    Path:   ${p.windows_path || p.wsl_path}`);
    console.log(`    Policy: ${p.policy || 'staged'} | Status: ${p.status || 'active'}`);
  });
  console.log('');
}

function printHelp() {
  console.log(`
🏰 Code-Manor CLI

Usage:
  code-manor init [directory] [options]   Initialize and register a project into projects.json
  code-manor list                         List all registered projects in the fleet
  code-manor help                         Show this help message

Options for init:
  --policy <yolo|staged|strict>           Verification policy (default: staged)
  --name <custom-name>                    Custom project name (default: package.json or folder name)

Examples:
  code-manor init .
  code-manor init ./backend --policy strict
  code-manor list
`);
}

const command = process.argv[2];
const args = process.argv.slice(3);

switch (command) {
  case 'init':
    initCommand(args);
    break;
  case 'list':
  case 'ls':
    listCommand();
    break;
  case 'help':
  case '--help':
  case '-h':
  case undefined:
    printHelp();
    break;
  default:
    console.error(`Unknown command: ${command}`);
    printHelp();
    process.exit(1);
}
