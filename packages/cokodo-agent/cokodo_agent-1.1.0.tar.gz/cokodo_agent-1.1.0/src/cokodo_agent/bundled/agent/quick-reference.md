# Protocol Quick Reference

> One-page quick reference, suitable for printing or keeping in a tab.
> 
> **Note**: `$AGENT_DIR` refers to protocol root directory (e.g., `.agent`, `.agent_cn`). See `manifest.json` for actual name.

---

## 🚨 Iron Rules

| ✅ Must Do | ❌ Forbidden |
|-----------|-------------|
| UTF-8 encoding (`encoding='utf-8'`) | Bare `except:` catch |
| Forward slash paths (`src/main.py`) | Hardcoded absolute paths |
| `autotest_` test prefix | UI hard jumps (no animation) |
| Dynamic RunID | External CDN links |
| Explicit error handling | Unauthorized API exposure |

---

## 📛 Naming Quick Reference

| Context | Convention | Example |
|---------|------------|---------|
| `$AGENT_DIR/` files | kebab-case | `bug-prevention.md` |
| Python class | PascalCase | `UserManager` |
| Python function/variable | snake_case | `get_user_by_id` |
| Python constant | UPPER_SNAKE | `MAX_RETRIES` |
| Rust type | PascalCase | `SyncTask` |
| Rust function/variable | snake_case | `process_file` |
| C++ class | PascalCase | `FileManager` |
| C++ method | camelCase | `getUserById` |
| C++ member variable | m_ + camelCase | `m_userName` |
| Git branch | prefix/kebab | `feature/user-auth` |

---

## 📁 Protocol Structure

```
$AGENT_DIR/
├── start-here.md      ⭐ Entry (required)
├── quick-reference.md 📋 This file
├── core/              🔧 Generic rules
│   ├── core-rules.md  ⚠️ Non-negotiable
│   ├── instructions.md
│   └── stack-specs/   Per tech stack
├── project/           📋 Project-specific
│   ├── context.md
│   └── tech-stack.md
└── skills/            🛠️ On-demand
```

---

## 🔧 Common Commands

```bash
# Protocol check
python $AGENT_DIR/scripts/lint-protocol.py

# Token count
python $AGENT_DIR/scripts/token-counter.py

# Initialize new project
python $AGENT_DIR/scripts/init_agent.py --project-name "Name" --stack python
```

---

## 📝 Commit Format

```
<type>(<scope>): <subject>

Types: feat|fix|docs|style|refactor|perf|test|chore
```

**Examples**:
- `feat(auth): add JWT refresh`
- `fix(api): handle null response`
- `docs(readme): update setup guide`

---

## 🧪 Test Data

```python
# Python
run_id = uuid.uuid4().hex[:8]
test_name = f"autotest_user_{run_id}"

# Pre-cleanup
db.query(User).filter(User.name.startswith('autotest_')).delete()
```

```rust
// Rust
let run_id = format!("{:08x}", rand::random::<u32>());
let test_name = format!("autotest_user_{}", run_id);
```

---

## 📊 Code Quality Thresholds

| Metric | Threshold |
|--------|-----------|
| Cyclomatic complexity | ≤ 10 |
| Function lines | ≤ 50 |
| File lines | ≤ 500 |
| Parameter count | ≤ 5 |
| Nesting depth | ≤ 4 |
| Test coverage | ≥ 60% |
| Critical path coverage | ≥ 80% |

---

## 🔗 Quick Links

| Scenario | Document |
|----------|----------|
| Before starting task | `workflows/pre-task-checklist.md` |
| While coding | `stack-specs/{python,rust,qt}.md` |
| Writing tests | `workflows/testing.md` |
| Encountering bug | `workflows/bug-prevention.md` |
| Before commit | `conventions.md` |
| AI integration | `skills/ai-integration/` |
| Code review | `workflows/review-process.md` |

---

## ⚡ Emergency Check

30-second pre-commit check:

- [ ] `encoding='utf-8'` specified
- [ ] No hardcoded paths/secrets
- [ ] Tests passing
- [ ] No lint errors

---

*Protocol version: 2.1.0*
