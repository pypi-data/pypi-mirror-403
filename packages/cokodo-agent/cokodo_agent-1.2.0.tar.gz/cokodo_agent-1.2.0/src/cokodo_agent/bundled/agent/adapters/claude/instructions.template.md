# Claude Instructions Template

> For Claude Code integration.

---

## Overview

Claude Code uses `.claude/skills/` directory (different from `$AGENT_DIR/skills/`).

### Compatibility

| Feature | This Protocol | Claude Code |
|---------|---------------|-------------|
| Directory | `$AGENT_DIR/skills/` | `.claude/skills/` |
| Entry file | `SKILL.md` | `SKILL.md` ✅ |
| Frontmatter | YAML supported | YAML supported ✅ |

---

## Setup Options

### Option 1: Symlink (Recommended)

```bash
ln -s $AGENT_DIR/skills .claude/skills
```

### Option 2: Run Adapter Script

```bash
python $AGENT_DIR/adapters/claude/adapt_for_claude.py
```

This copies skills to `.claude/skills/` directory.

---

## Skill Format

Skills already include Claude-compatible YAML frontmatter:

```yaml
---
name: skill-name
description: |
  Skill description.
---

# Skill Content
...
```

---

*Adapt $AGENT_DIR to your actual directory name*
