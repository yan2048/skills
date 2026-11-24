---
name: skill-lint
description: 校验 WorkBuddy skill 目录结构与 SKILL.md frontmatter 是否合规，输出可定位到行号的错误与警告。当需要检查新写的 skill、批量体检仓库内所有 skill、或在 CI 中拦截不合规 skill 时使用。关键词：skill 校验、SKILL.md 检查、frontmatter 校验、skill lint。
---

# skill-lint — SKILL.md 规范校验器

_把「skill 写得好不好」里可机械判定的部分固化成检查项，剩下的人才需要肉眼判断。_

## 何时使用

- 新写了一个 skill，提交前想确认结构没漏项（frontmatter、名称一致性、必要章节）
- 仓库里 skill 变多后，想一次性体检所有 skill 是否都合规
- 想在 CI 里加一道门，阻止不合规的 skill 合入 main
- 排查「为什么我的 skill 明明放进去了却不被触发」——通常是 description 缺触发关键词

不适用：判断 skill 内容质量（流程是否合理、指令是否可执行）。这部分本工具只做结构校验，仍需人工 review。

## 工作流程

1. **定位目标**：确认要校验的范围。整个仓库用 `skills/`，单个 skill 用 `skills/<name>/` 或直接给 `SKILL.md` 路径。
2. **运行校验**：

   ```bash
   python3 skills/skill-lint/scripts/lint_skills.py skills/
   ```

   首次使用或排查某一条规则时，可加 `--json` 便于逐条对照：

   ```bash
   python3 skills/skill-lint/scripts/lint_skills.py skills/<name> --json
   ```

3. **读输出**：`ERROR` 必须修（结构已破损，AI 可能无法加载）；`WARN` 判断是否需要修（例如模板类 skill 可以不按「何时使用/工作流程/约束」三段式写）。
4. **修完复跑**，直到错误为 0。CI 想连警告一起卡住时加 `--strict`。
5. **接 CI**：仓库已内置 `.github/workflows/skill-lint.yml`，push 与 PR 时自动跑一遍。

## 规则表

| 代码 | 级别 | 检查内容 |
|------|------|----------|
| E001 | error | 目录下缺少 `SKILL.md`，或文件不可读 |
| E002 | error | 缺少 YAML frontmatter，或 `---` 未闭合 |
| E003 | error | `name` 缺失或为空 |
| E004 | error | `name` 含非法字符（只允许小写字母、数字、中划线） |
| E005 | error | `name` 与所在目录名不一致 |
| E006 | error | `description` 缺失或为空 |
| W001 | warn | `description` 少于 20 字符，触发场景写得不够 |
| W002 | warn | `description` 超过 200 字符，可能稀释路由精度 |
| W003 | warn | `description` 未见触发标记（「关键词」「当……时」等） |
| W004 | warn | 正文缺少一级标题 |
| W005 | warn | 缺少推荐章节「何时使用 / 工作流程 / 约束」 |
| W006 | warn | 章节标题下没有内容 |

规则取舍理由与反例见 `references/rules.md`。

## 命令行参数

| 参数 | 说明 |
|------|------|
| `paths...` | skills 根目录或单个 `SKILL.md`，默认 `skills` |
| `--strict` | warning 也视为失败（CI 严格模式） |
| `--json` | 输出机器可读 JSON，含 `summary` 与逐条 issue |
| `--quiet` | 只打印失败项与汇总 |

退出码：`0` 通过 / `1` 有 error（`--strict` 下含 warning）/ `2` 参数或路径错误。

## 约束

- 只读：本脚本不修改任何 SKILL.md，修复动作由人（或 AI）确认后再做。
- 零依赖：只用 Python 标准库，不引入 PyYAML；frontmatter 只解析顶层 `key: value`（含 `>` / `|` 折叠写法），嵌套结构不在校验范围内。
- 只校验一级子目录：`skills/<name>/SKILL.md` 视为一个 skill，`scripts/`、`references/` 等二级目录不会被当成独立 skill。
- 不做内容质量评判：流程是否可执行、示例是否真实，属于 review 职责，不要指望脚本给出结论。
