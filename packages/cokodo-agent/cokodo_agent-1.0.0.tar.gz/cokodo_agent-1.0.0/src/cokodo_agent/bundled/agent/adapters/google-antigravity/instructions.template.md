# Google Antigravity Agent Adapter

> Zero-adaptation compatibility with Antigravity Agent.

---

## Compatibility

This protocol is **natively compatible** with Google Antigravity Agent:

| Feature | This Protocol | Antigravity |
|---------|---------------|-------------|
| Skills location | `$AGENT_DIR/skills/<name>/SKILL.md` | `skills/<name>/SKILL.md` ✅ |
| Frontmatter | YAML with name + description | YAML ✅ |
| Rules | `$AGENT_DIR/core/` | Rules directory ✅ |

---

## Direct Usage

Skills can be used directly without adaptation:

```
@$AGENT_DIR/skills/guardian/SKILL.md
```

---

## Optional: Create Rules References

Run adapter script to create rule reference files:

```bash
python $AGENT_DIR/adapters/google-antigravity/adapt_for_antigravity.py
```

This creates `$AGENT_DIR/rules/` with references to core files.

---

## Rule References

```
@$AGENT_DIR/core/core-rules.md
@$AGENT_DIR/core/instructions.md
@$AGENT_DIR/core/conventions.md
```

---

*Adapt $AGENT_DIR to your actual directory name*
