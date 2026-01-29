# CI/CD Integration Templates

> Templates for integrating protocol checks into CI pipelines.

---

## Available Templates

| Template | Purpose |
|----------|---------|
| `github-actions.template.yml` | GitHub Actions workflow |
| `pre-commit-config.template.yaml` | Pre-commit hooks |

---

## GitHub Actions Setup

```bash
cp $AGENT_DIR/adapters/ci/github-actions.template.yml .github/workflows/ci.yml
```

---

## Pre-commit Setup

```bash
cp $AGENT_DIR/adapters/ci/pre-commit-config.template.yaml .pre-commit-config.yaml
pip install pre-commit
pre-commit install
```

---

*Adapt $AGENT_DIR to your actual directory name*
