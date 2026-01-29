# Documentation Navigation Index

> **Purpose**: Quickly locate AI protocol layer documents
>
> **Note**: `$AGENT_DIR` refers to protocol root directory (e.g., `.agent`, `.agent_cn`). See `manifest.json` for actual name.

---

## 🚀 Quick Entry

### Required Reading (In Order)
1. [start-here.md](start-here.md) - ⭐ AI startup instructions (first-time required)
2. [quick-reference.md](quick-reference.md) - 📋 Cheat sheet (one-page reference)
3. [core/instructions.md](core/instructions.md) - Collaboration rules entry
4. [project/context.md](project/context.md) - Project business context
5. [project/tech-stack.md](project/tech-stack.md) - Tech stack description

---

## 📋 Core Specification Documents

### Governance Engine (core/)
| Document | Purpose | When to Read |
|----------|---------|--------------|
| [core-rules.md](core/core-rules.md) | Core philosophy, ILI isolation, Three Prohibitions | First contact |
| [instructions.md](core/instructions.md) | AI collaboration guidelines, capability boundaries | First contact |
| [conventions.md](core/conventions.md) | Naming conventions, Git conventions | Before commit |
| [security.md](core/security.md) | Security development standards ⭐ | Security-related |

### Workflows (core/workflows/)
| Document | Purpose | When to Read |
|----------|---------|--------------|
| [bug-prevention.md](core/workflows/bug-prevention.md) | Bug prevention knowledge base ⭐ | Before coding |
| [design-principles.md](core/workflows/design-principles.md) | SSOT, DI, simplicity-first | During design |
| [testing.md](core/workflows/testing.md) | Testing protocol, data isolation | Writing tests |
| [pre-task-checklist.md](core/workflows/pre-task-checklist.md) | Pre-task checklist | Before starting |
| [documentation.md](core/workflows/documentation.md) | Documentation standards | Writing docs |
| [quality-assurance.md](core/workflows/quality-assurance.md) | QA process | Before delivery |
| [review-process.md](core/workflows/review-process.md) | Code review process | Before PR |

### Tech Stack Specs (core/stack-specs/)
| Document | Purpose | Applicable Projects |
|----------|---------|---------------------|
| [python.md](core/stack-specs/python.md) | Python development standards | Python projects |
| [rust.md](core/stack-specs/rust.md) | Rust development standards | Rust projects |
| [qt.md](core/stack-specs/qt.md) | Qt/C++/QML development standards | Qt projects |
| [git.md](core/stack-specs/git.md) | Git workflow standards | All projects |

---

## 📋 Project Instance (project/)

| Document | Purpose | Update Frequency |
|----------|---------|------------------|
| [context.md](project/context.md) | Project business context | On requirement changes |
| [tech-stack.md](project/tech-stack.md) | Tech stack and environment | On tech decisions |
| [known-issues.md](project/known-issues.md) | Known issues and solutions | When issues found |
| [adr/](project/adr/) | Business architecture decision records | On major decisions |

---

## 🛠️ Skill Modules (skills/)

Reusable automation capability encapsulation:

| Document | Purpose |
|----------|---------|
| [skill-interface.md](skills/skill-interface.md) | Skill interface spec (read before developing new skills) |

| Skill | Function | Use Case |
|-------|----------|----------|
| [guardian](skills/guardian/SKILL.md) | Code/doc quality gate | Pre-commit check |
| [ai-integration](skills/ai-integration/) | LLM/AI service integration ⭐ | AI feature dev |
| [agent-governance](skills/agent-governance/SKILL.md) | Protocol health check | Protocol maintenance |

### AI Integration Skill Details (skills/ai-integration/)
| Document | Content |
|----------|---------|
| [llm-client.md](skills/ai-integration/llm-client.md) | LLM client design patterns |
| [prompt-engineering.md](skills/ai-integration/prompt-engineering.md) | Prompt engineering best practices |
| [domain-adaptation.md](skills/ai-integration/domain-adaptation.md) | Domain adaptation methodology |

---

## 📜 Protocol Evolution (meta/)

| Document | Purpose |
|----------|---------|
| [protocol-adr.md](meta/protocol-adr.md) | Protocol architecture decision records |

---

## 🔌 AI Tool Adapters (adapters/)

| Adapter | Purpose |
|---------|---------|
| [github-copilot/](adapters/github-copilot/) | GitHub Copilot instruction template |
| [cursor/](adapters/cursor/) | Cursor config template |
| [claude/](adapters/claude/) | Claude instruction template |
| [google-antigravity/](adapters/google-antigravity/) | Google Antigravity Agent adapter ⭐ |
| [ci/](adapters/ci/) | CI/CD integration templates |

---

## 🔧 Helper Scripts (scripts/)

| Script | Function | Command |
|--------|----------|---------|
| init_agent.py | Protocol initialization | `python scripts/init_agent.py` |
| lint-protocol.py | Protocol compliance check | `python scripts/lint-protocol.py` |
| token-counter.py | Token statistics | `python scripts/token-counter.py` |

---

## 📁 Directory Tree Structure

```
$AGENT_DIR/
├── start-here.md           # ⭐ Entry file
├── quick-reference.md      # 📋 Cheat sheet
├── index.md                # Navigation (you are here)
├── manifest.json           # 📦 Loading strategy & metadata
│
├── core/                   # 🔧 Governance engine (generic)
│   ├── core-rules.md
│   ├── instructions.md
│   ├── conventions.md
│   ├── security.md
│   ├── workflows/
│   └── stack-specs/
│
├── project/                # 📋 Project instance (specific)
│   ├── context.md
│   ├── tech-stack.md
│   ├── known-issues.md
│   └── adr/
│
├── skills/                 # 🛠️ Skill modules
│   ├── skill-interface.md
│   ├── guardian/
│   ├── ai-integration/
│   └── agent-governance/
│
├── meta/                   # 📜 Protocol evolution
│   └── protocol-adr.md
│
├── adapters/               # 🔌 AI tool adapters
│   ├── github-copilot/
│   ├── cursor/
│   ├── claude/
│   └── ci/
│
└── scripts/                # 🔧 Helper tools
    ├── init_agent.py
    ├── lint-protocol.py
    └── token-counter.py
```

---

## 💡 Usage Tips

### AI Assistant Workflow
1. **Each session start**: Read `start-here.md`
2. **Before coding**: Reference `core/instructions.md` + relevant `stack-specs/`
3. **Before commit**: Check `core/conventions.md`
4. **On issues**: Consult `core/workflows/bug-prevention.md`

### Documentation Maintenance
- Found new pitfall → Record in `bug-prevention.md`
- Major decision → Create ADR document
- Protocol change → Update `meta/protocol-adr.md`

---

*Last updated: 2026-01-23*
*Protocol version: 2.1.0*
