# Cursor Rules Template

> Copy this content to `.cursorrules` in your project root.

---

## Protocol Reference

**Main protocol entry**: `$AGENT_DIR/start-here.md`

### Key Files
1. Read `$AGENT_DIR/start-here.md` at session start
2. Follow `$AGENT_DIR/core/core-rules.md` non-negotiable principles
3. Reference `$AGENT_DIR/project/context.md` for project background

---

## Core Rules

### Coding Standards
- **Encoding**: Always `encoding='utf-8'`
- **Files**: `$AGENT_DIR/` uses kebab-case
- **Paths**: Use forward slashes `/`

### Three Prohibitions
1. No external CDN links
2. No UI hard jumps (use 250-300ms transitions)
3. No unauthorized API exposure

---

## Skills Reference

| Skill | Path |
|-------|------|
| Code quality | `$AGENT_DIR/skills/guardian/` |
| AI integration | `$AGENT_DIR/skills/ai-integration/` |
| Protocol maintenance | `$AGENT_DIR/skills/agent-governance/` |

---

*Adapt $AGENT_DIR to your actual directory name*
