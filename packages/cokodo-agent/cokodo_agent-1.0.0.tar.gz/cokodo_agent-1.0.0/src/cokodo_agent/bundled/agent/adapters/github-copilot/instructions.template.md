# GitHub Copilot Instructions Template

> Copy to `.github/copilot-instructions.md` in your project.

---

## Protocol Reference

**Main protocol entry**: `$AGENT_DIR/start-here.md`

### Priority Files

| File | Priority | Description |
|------|----------|-------------|
| `$AGENT_DIR/core/core-rules.md` | ⭐⭐⭐ | Non-negotiable core rules |
| `$AGENT_DIR/core/instructions.md` | ⭐⭐⭐ | AI collaboration guidelines |
| `$AGENT_DIR/project/context.md` | ⭐⭐ | Project business context |
| `$AGENT_DIR/project/tech-stack.md` | ⭐⭐ | Tech stack description |

---

## Coding Guidelines

Before generating or modifying code, reference rules in `$AGENT_DIR/start-here.md`.

### Key Rules
- **Encoding**: `$AGENT_DIR/` files use kebab-case
- Always specify `encoding='utf-8'` for file operations
- Use `autotest_` prefix for test data

---

## Skills

| Skill | Purpose |
|-------|---------|
| `$AGENT_DIR/skills/guardian/SKILL.md` | Code quality check |
| `$AGENT_DIR/skills/ai-integration/` | AI integration dev |
| `$AGENT_DIR/skills/agent-governance/SKILL.md` | Protocol maintenance |

---

*Adapt $AGENT_DIR to your actual directory name*
