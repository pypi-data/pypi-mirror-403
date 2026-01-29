# Code Review Process

> Guidelines for conducting and receiving code reviews.

---

## 1. Before Requesting Review

### Submitter Checklist

- [ ] Code compiles/runs without errors
- [ ] All tests pass
- [ ] Linting passes
- [ ] Self-reviewed the diff
- [ ] PR description is complete
- [ ] Commits are logically organized

---

## 2. PR Description Template

```markdown
## Summary
Brief description of changes

## Changes
- Change 1
- Change 2

## Testing
How was this tested?

## Screenshots (if UI changes)
Before/after screenshots

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

---

## 3. Reviewer Guidelines

### What to Look For

| Category | Items |
|----------|-------|
| **Correctness** | Logic errors, edge cases, error handling |
| **Design** | SOLID principles, appropriate abstractions |
| **Security** | Input validation, authentication, data exposure |
| **Performance** | Obvious bottlenecks, resource usage |
| **Maintainability** | Readability, documentation, complexity |
| **Testing** | Coverage, test quality, edge cases |

### Comment Guidelines

```markdown
# Good comments
"Consider using a constant here for maintainability"
"This could cause N+1 queries - consider eager loading"
"Nit: typo in variable name"

# Avoid
"This is wrong" (explain why)
"I don't like this" (suggest alternative)
```

---

## 4. Comment Prefixes

| Prefix | Meaning |
|--------|---------|
| `blocking:` | Must fix before merge |
| `suggestion:` | Optional improvement |
| `question:` | Need clarification |
| `nit:` | Minor style issue |
| `praise:` | Good work! |

---

## 5. Handling Feedback

### As Submitter
- Respond to all comments
- Explain reasoning if disagreeing
- Mark resolved conversations
- Request re-review after changes

### As Reviewer
- Be constructive and specific
- Explain the "why"
- Offer alternatives
- Approve when satisfied

---

## 6. Merge Criteria

- [ ] At least 1 approval
- [ ] All blocking comments resolved
- [ ] CI passes
- [ ] No merge conflicts
- [ ] Branch is up to date

---

*This file is a generic engine rule, must not contain any project-specific information*
*Protocol version: 2.1.0*
