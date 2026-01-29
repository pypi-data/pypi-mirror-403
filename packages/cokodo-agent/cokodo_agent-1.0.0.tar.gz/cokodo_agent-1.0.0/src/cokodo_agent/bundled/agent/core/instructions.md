# AI Collaboration Guidelines

This file defines AI assistant collaboration guidelines and behavior standards during project development.

---

## 1. Session Initialization

AI assistant must establish context at each new session start:
1. **Required**: `start-here.md`, `project/context.md`, `project/tech-stack.md`.
2. **Check**: `project/known-issues.md` for historical pain points.
3. **Confirm**: Current task goals, constraints, and risks.

---

## 2. Coding Collaboration Standards

- **Style specs**: Strictly follow corresponding language specs under `core/stack-specs/`.
- **Core requirement**: Explicitly specify UTF-8 encoding, never omit. See [core/examples.md](examples.md) for details.
- **Consistency**: Maintain consistency with existing codebase architecture and naming style.

---

## 3. Task Execution Flow

### 3.1 Task Lifecycle
1. **Before task**: Understand requirements, check `bug-prevention.md`, make incremental plan.
2. **During execution**: **Develop → Verify → Continue**. Each step must close loop, avoid modifying too many files at once.
3. **After task**: Run compliance check scripts, ensure no newly introduced warnings or errors.

### 3.2 Incremental Verification
> Always maintain minimal changeset, ensure system stability through frequent test verification.

---

## 4. Communication and Confirmation

- **Problem clarification**: Must proactively ask when requirements are vague, boundaries unclear, or potential conflicts exist.
- **Solution tradeoffs**: When proposing solutions, briefly explain reasoning and potential risks/tradeoffs.
- **Progress reporting**: Complex tasks should sync progress in stages, marking current blockers.

---

## 5. Behavior Boundaries and Risk Control

### 5.1 Autonomy Principles
- **L3 (Execute directly)**: Code generation, refactoring, formatting, adding comments.
- **L2 (Notify after execution)**: Create non-sensitive files, update non-core configs.
- **L1 (Ask before execution)**: **Delete files**, modify core project dependencies, production environment operations.
- **L0 (Forbidden)**: Access/store sensitive credentials, unauthorized financial transactions, modify security policies.

See [core/workflows/ai-boundaries.md](workflows/ai-boundaries.md) for detailed capability lists and boundary definitions.

---

## 6. Error Handling and Prevention

1. **Found bug**: Record symptoms → Locate root cause → Fix → Update `bug-prevention.md`.
2. **When uncertain**: Prefer conservative approach, clearly mark assumptions.

---

*This file is a generic engine rule, must not contain any project-specific information*
*Protocol version: 2.1.0*
