# Project Commands

> agent_protocol 常用命令

---

## Protocol Check

```bash
# 协议合规检查
python .agent/scripts/lint-protocol.py

# Token 统计
python .agent/scripts/token-counter.py
```

---

## Sync Protocol

```bash
# 同步协议到其他项目（手动）
# 复制 core/, adapters/, meta/, scripts/ 到目标项目

# 使用 history-sync 工具
python .me/scripts/sync-history.py
python .me/scripts/sync-history.py --apply
```

---

*This file is project-specific. Update when commands change.*
