---
name: example-skill
description: skill 编写模板与结构示例。当需要新建一个 WorkBuddy skill、或想了解 SKILL.md 的标准结构与编写规范时使用。关键词：新建skill、skill模板、SKILL.md、skill规范。
---

# Example Skill — WorkBuddy Skill 编写模板

_本文件同时是一个可运行的模板：复制本目录改名，替换内容即可成为新 skill。_

## 1. Frontmatter 规范

```yaml
---
name: skill-name            # 小写中划线命名，与目录名一致
description: 一句话说明用途与触发时机，写清"何时该用"，并附触发关键词。
---
```

要点：

- `description` 是 AI 路由的唯一依据，必须包含触发场景 + 关键词（中英文均可）
- 只在 frontmatter 出现的字段才算元数据，正文从一级标题开始

## 2. 正文推荐结构

```markdown
# Skill 名称

_一句话定位。_

## 何时使用
- 场景 A
- 场景 B

## 工作流程
1. 步骤 1（写清楚输入输出）
2. 步骤 2（给出具体命令/代码）
3. 步骤 3（说明边界与失败处理）

## 约束
- 禁止……
- 必须……
```

## 3. 进阶结构（按需添加）

- `references/` — 拆分长文档（如领域知识、字段字典），正文里注明"需要时读取"
- `scripts/` — 可执行脚本，正文写明调用方式与参数
- `assets/` — 模板、字体、静态资源

## 4. 质量自查

- [ ] 换成新 name 后，目录名、frontmatter、标题三处一致
- [ ] description 覆盖了用户可能的说法（含同义触发词）
- [ ] 流程步骤可直接执行，没有"凭感觉"的模糊指令
- [ ] 有明确的约束/禁区，避免 AI 过度发挥
