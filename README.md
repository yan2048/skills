# WorkBuddy Skills

个人开源的 WorkBuddy Skill 合集，每周持续更新（新增 skill 或修复问题）。

## 简介

这里存放为 WorkBuddy（AI 助手）编写的 Skill：每个 skill 是一个独立目录，包含一份 `SKILL.md`，为 AI 提供特定任务的领域知识、工作流程与工具用法约定。

## 目录结构

```
skills/
└── example-skill/        # 每个 skill 一个目录
    └── SKILL.md          # skill 定义（含 YAML frontmatter）
```

## 使用方式

将某个 skill 目录放入 WorkBuddy 的 skills 目录（用户级：`~/.workbuddy/skills/`，项目级：`{workspace}/.workbuddy/skills/`），WorkBuddy 会根据 SKILL.md 的描述自动在匹配任务时加载。

## Skill 清单

| Skill | 说明 | 状态 |
|-------|------|------|
| [example-skill](skills/example-skill/) | skill 编写模板与结构示例 | ✅ 可用 |

## 编写规范

- 每个 skill 一个目录，入口为 `SKILL.md`
- `SKILL.md` 顶部使用 YAML frontmatter 声明 `name` 和 `description`
- description 应写清触发场景与关键词，便于 AI 正确路由
- 复杂流程可拆分为子文档（`references/`）或脚本（`scripts/`）
- 内容以「可执行的工作流 + 具体命令 + 边界约束」为主，避免空泛描述

## Roadmap

详见 [ROADMAP.md](ROADMAP.md)。

## License

[MIT](LICENSE)
