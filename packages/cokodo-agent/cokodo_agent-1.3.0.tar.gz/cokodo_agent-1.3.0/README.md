# Cokodo Agent

A CLI tool to generate standardized AI collaboration protocol (`.agent`) for your projects.

Similar to `create-react-app`, this tool helps you quickly set up an `.agent` directory with best practices for AI-assisted development.

---

## Installation

```bash
# Install globally
pip install cokodo-agent

# Or use pipx (recommended)
pipx install cokodo-agent
```

---

## Quick Start

```bash
# Navigate to your project
cd my-project

# Run the generator (any of these commands work)
co init           # Short alias
cokodo init       # Full name
cokodo-agent init # Package name

# Or specify a path
co init ./new-project
```

---

## Usage

### Interactive Mode (Default)

```bash
$ co init

  Cokodo Agent v1.2.0
  ====================

  Fetching protocol...
    OK Protocol v3.0.0

? Project name: my-awesome-app
? Brief description: A task management web application

? Primary tech stack:
  > Python
    Rust
    Qt/C++
    Mixed
    Other

? AI tools to configure (at least one required):
  [x] Cokodo (Protocol Only)    # Default - only .agent/
  [ ] Cursor
  [ ] GitHub Copilot
  [ ] Claude Projects
  [ ] Google Antigravity

  Generating .agent/
  OK Created .agent/

  Success! Created .agent in /path/to/my-awesome-app

  Next steps:
    1. Review .agent/project/context.md
    2. Start coding with AI assistance!
```

### Quick Mode

```bash
# Use defaults, skip prompts (Cokodo mode - protocol only)
co init --yes

# Specify options directly
co init --name "my-app" --stack python -y
```

### Commands

| Command | Description |
|---------|-------------|
| `co init [path]` | Create .agent in target directory |
| `co lint [path]` | Check protocol compliance |
| `co diff [path]` | Compare local .agent with latest protocol |
| `co sync [path]` | Sync local .agent with latest protocol |
| `co context [path]` | Get context files based on stack and task |
| `co journal [path]` | Record a session entry to session-journal.md |
| `co update-checksums` | Update checksums in manifest.json (maintainer only) |
| `co version` | Show version information |

### Options for `co init`

| Option | Description |
|--------|-------------|
| `--yes, -y` | Skip prompts, use defaults |
| `--name` | Project name |
| `--stack` | Tech stack (python/rust/qt/mixed/other) |
| `--force` | Overwrite existing .agent directory |
| `--offline` | Use built-in protocol (no network) |

### Options for `co lint`

| Option | Description |
|--------|-------------|
| `--rule, -r` | Check specific rule only |
| `--format, -f` | Output format (text/json/github) |

### Options for `co context`

| Option | Description |
|--------|-------------|
| `--stack, -s` | Tech stack (python/rust/qt/mixed) |
| `--task, -t` | Task type (coding/testing/review/documentation/bug_fix) |
| `--output, -o` | Output format (list/paths/content) |

### Options for `co journal`

| Option | Description |
|--------|-------------|
| `--title, -t` | Session title (e.g., "Feature X implementation") |
| `--completed, -c` | Completed items (comma-separated) |
| `--debt, -d` | Technical debt items (comma-separated) |
| `--decisions` | Key decisions made (comma-separated) |
| `--interactive, -i` | Interactive mode with prompts |

---

## Protocol Sources

The tool fetches the latest protocol from multiple sources with fallback:

| Priority | Source | Description |
|----------|--------|-------------|
| 1 | GitHub Release | Latest version from repository |
| 2 | Remote Server | Backup server [reserved] |
| 3 | Built-in | Bundled version in package |

```
Priority 1: GitHub Release
    |
    | [unavailable]
    v
Priority 2: Remote Server [reserved, not implemented]
    |
    | [unavailable]
    v
Priority 3: Built-in (offline fallback)
```

---

## Generated Structure

### Cokodo Mode (Default)

Only generates `.agent/` directory:

```
my-project/
+-- .agent/                     # Protocol directory
    +-- start-here.md           # * Entry point
    +-- quick-reference.md      # Cheat sheet
    +-- core/                   # Governance rules
    +-- project/                # Project-specific (customized)
    +-- skills/                 # Skill modules
    +-- adapters/               # Tool adapter templates
    +-- scripts/                # Helper scripts
```

### With AI Tool Adapters

Additional files based on selected tools:

| Tool | Generated File |
|------|----------------|
| Cursor | `.cursorrules` |
| GitHub Copilot | `.github/copilot-instructions.md` |
| Claude Projects | `.claude/instructions.md` |
| Google Antigravity | `.agent/rules/` directory |

---

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `COKODO_OFFLINE` | Force offline mode (`1` or `true`) |
| `COKODO_CACHE_DIR` | Custom cache directory |

### Cache Location

Downloaded protocols are cached at:
- Linux/macOS: `~/.cache/cokodo/`
- Windows: `%LOCALAPPDATA%\cokodo\cache\`

---

## Development

```bash
# Clone repository
git clone https://github.com/dinwind/agent_protocol.git
cd agent_protocol/cokodo-agent

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Documentation

- [Complete Usage Guide](../docs/usage-guide.md) - Detailed usage instructions
- [使用指南 (中文)](../docs/usage-guide_cn.md) - Chinese documentation
- [Agent Protocol Documentation](https://github.com/dinwind/agent_protocol)
- [Report Issues](https://github.com/dinwind/agent_protocol/issues)
