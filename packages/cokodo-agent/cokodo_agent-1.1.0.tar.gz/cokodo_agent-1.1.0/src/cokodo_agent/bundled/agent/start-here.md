# AI Collaboration Entry Point

> **First message for new AI sessions**: Please read this file to establish project context, then strictly follow protocol rules.

> **Directory naming convention**: This protocol directory can be named `.agent`, `.agent_cn`, etc. Documentation uses `$AGENT_DIR` as placeholder for the protocol root directory. See `directory_name` in `manifest.json` for actual name.

---

## 📍 Protocol Architecture Overview

This protocol uses an **Engine-Instance Separation** architecture, decoupling generic governance rules from project-specific information:

- **`core/`**: Governance engine (generic rules, no project-specific info allowed).
- **`project/`**: Instance data (project context, tech stack, known issues).
- **`skills/`**: Modular capabilities (on-demand tools and specifications).
- **`adapters/`**: AI tool adapters (Cursor, Claude, Copilot, etc.).

See [index.md](index.md) or [quick-reference.md](quick-reference.md) for detailed directory structure.

---

## 📚 Context Building Path (Required Reading)

⚠️ **Mandatory**: AI must load documents in the following order during first session to establish baseline understanding.

### 1. Core Protocol (Required for every session)

- [quick-reference.md](quick-reference.md): **One-page cheat sheet** (coding, Git, common commands).
- [core/core-rules.md](core/core-rules.md): **Core principles** (isolation, security, delivery quality).
- [project/context.md](project/context.md): **Project context** (business logic, feature status).

### 2. Technical Specifications (Read before starting tasks)

- [core/instructions.md](core/instructions.md): AI collaboration guidelines and behavior boundaries.
- [project/tech-stack.md](project/tech-stack.md): Tech stack, dependencies, and environment config.
- [core/stack-specs/](core/stack-specs/): Select language-specific development standards (Python/Rust/Qt/Git).

### 3. On-Demand Loading (For specific scenarios)

- [project/known-issues.md](project/known-issues.md): Consult when debugging or encountering new bugs.
- [core/workflows/](core/workflows/): Standard processes for coding, testing, documentation, or review.
- [skills/](skills/): Consult when needing automated checks or specific feature integration.

---

## 🛠️ Quick Start Commands

```powershell
# Set protocol directory variable (modify according to actual directory name)
$AGENT_DIR = ".agent"

# 1. Check protocol compliance
python $AGENT_DIR/scripts/lint-protocol.py

# 2. Count Token usage
python $AGENT_DIR/scripts/token-counter.py

# 3. Run code quality checks
python $AGENT_DIR/skills/guardian/scripts/check_all.py
```

---

*Last updated: 2026-01-23*
*Protocol version: 2.1.0*
