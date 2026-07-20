# 组会 PPT 工作流

用这个工作流慢慢制作组会汇报。默认一次只做一步；当前步骤没有形成清晰产物、没有完成检查，就不要推进到下一步。

## 总原则

- 每次只推进一个步骤，除非用户明确要求继续。
- 每一步结束时都要返回：产物路径、简短总结、已做检查、发现的问题、建议的下一步。
- 如果当前产物质量不够，先修当前步骤，不要急着进入下一步。
- Step 1-3 只做研究和内容，不做前端设计、模板设计、HTML、CSS、版式、配色或页面实现。
- 从 Step 4 开始，才允许讨论设计。
- 思考、审查和中间产物优先用 Markdown。
- 重要产物尽量按主题和日期保存，方便回溯。
- 修改已有 deck、HTML、Markdown、图片预览或 PPTX 前，必须先建立可恢复备份。
- 已有页面必须一页一页处理：一次只改一页、只渲染这一页、只验收这一页。
- 严禁一次性重生成全部 HTML、批量覆盖全部预览图，或用统一模板替换已有逐页设计。
- 严禁在没有备份和逐页验收的情况下，把 `slide-content.md` 全量回填到所有 HTML。

## 安全编辑协议

这部分优先级高于后续所有制作步骤。用于避免全量回填、批量生成或覆盖已有设计造成不可恢复损失。

### 备份规则

- 修改前先建立备份目录，例如 `backups/YYYYMMDD-HHMMSS/`。
- 备份至少包含即将修改的 HTML、Markdown、CSS、assets、preview PNG、PPTX/PDF。
- 若要修改多页，先只备份并修改当前页；不要为了“方便”批量备份后批量改写全部页面。
- 备份完成后，先列出备份路径，再开始编辑。
- 如果没有可用备份，不允许执行大范围替换、批量格式化、批量渲染或批量导出。

### 单页处理规则

- 每次只处理一页，例如 `slide-09.html`。
- 单页流程固定为：读取最新文件 -> 备份当前页 -> 修改当前页 -> 渲染当前页 -> 检查当前页 -> 更新 notes/todo -> 停止。
- 当前页通过检查前，不进入下一页。
- 子代理或 Fixer 一次只接收一个 slide 任务；等待其完成并确认文件变更后，才派发下一页。
- 不允许把 `slide-09`、`slide-10`、`slide-02` 这类多页任务同时塞给同一个 Fixer。

### 禁止事项

- 禁止把整套页面统一重生成成同一个模板。
- 禁止用 `slide-content.md` 一次性覆盖所有 HTML。
- 禁止在旧 HTML 仍有逐页设计时，直接删除并重建 `slides/`。
- 禁止一次性重渲染所有 PNG 作为“顺手检查”；除非用户明确要求全 deck export，且已有完整备份。
- 禁止在未读最新目标文件的情况下套用旧 patch。
- 禁止为了修正文案而改动无关版式、图表、CSS 或其它页面。

### 大范围修改例外

只有用户明确要求全 deck 级操作时，才允许跨页处理。即便如此，也必须：

- 先说明影响范围。
- 先建立完整备份。
- 先在 1 页样本上试运行。
- 样本通过后，再分批执行。
- 每批结束后做残留扫描和预览抽查。
- 保留变更清单，说明哪些页被改、哪些页只重渲染、哪些页未动。

## 语言策略

- 工作流说明、过程记录、审查意见默认用简体中文。
- 研究材料、引用文献、PPT 正文、图表标签、slide title 默认用英文。
- 演讲讲稿、speaker notes、口头解释策略默认用中文。
- `research-report.md` 和 `guided-article.md` 可以用英文写主体内容；如果需要给自己阅读，可以在关键处补中文解释。
- `content-review.md` 中，放到 PPT 上的文本用英文；演讲提示用中文。

## 产物地图

- `topic-brainstorm.md`：选题候选、选择理由、风险。
- `research-report.md`：详细、专业的研究报告。
- `guided-article.md`：可直接阅读的导读式文章，用来支撑 PPT 内容。
- `design-frontend.md`：视觉视角、版式方向、模板设计规则。
- `design-content.md`：内容设计、叙事角度、用词、术语、slide title 风格。
- `template-spec.md`：生成模板前的模板需求说明。
- `content-template-map.md`：内容和模板位置的匹配关系。
- `content-review.md`：只用于快速内容审查的纯 Markdown slide 文本。
- `deck-source/`：生成最终 deck 的源文件。
- `final/`：最终 PPTX、PDF、渲染检查图。

## Step 1 - 选题 / Brainstorming

目标：选出一个值得做组会汇报的题目。

输入：
- 最近论文、项目进展、未解决问题、导师/课题组关注点。
- 汇报时长和听众背景。

输出：
- `topic-brainstorm.md`

检查：
- 题目有清晰的科学问题。
- 题目能放进给定汇报时长。
- 题目有足够可靠的英文资料。
- 题目不只是自己感兴趣，也对组里有价值。
- 预期 takeaway 可以用一句英文说清楚。

停止条件：
- 选出 1 个推荐题目，并保留 2-3 个备选题目。

## Step 2 - 收集信息并写研究报告

目标：收集资料，写一份详细、专业、可追溯的 Markdown 研究报告。

输入：
- 已选题目。
- 英文论文、笔记、数据、已有 slide、导师意见。

输出：
- `research-report.md`

建议结构：
- Executive summary
- Research question
- Background
- Key concepts
- Methods
- Main findings
- Conflicts or uncertainty
- Important figures/tables to recreate or cite
- Glossary
- References
- Open questions

检查：
- 关键论断能追溯到来源，推断要明确标注。
- 重要公式、定义、假设都写清楚。
- 报告不依赖 PPT 也能读懂。
- 不讨论前端、模板、版式或视觉设计。
- 资料和术语优先保持英文。

停止条件：
- 研究报告已经足够支撑一次组会汇报。

## Step 3 - 转换为导读式文章

目标：把研究报告转换成一篇可以直接阅读的导读式文章，用来支撑 PPT 内容。

输入：
- `research-report.md`

输出：
- `guided-article.md`

检查：
- 文章有顺畅的学习路径。
- 每个概念先解释为什么重要，再进入细节。
- 不提前写成 slide outline。
- 保留必要技术深度，但去掉报告式堆料。
- 不讨论前端、模板、版式或视觉设计。
- 主体内容可用英文，必要的自我解释可用中文补充。

停止条件：
- 课题组成员不看 PPT，只读这篇文章，也能理解主题主线。

## Step 4 - 生成设计文档

目标：把设计拆成视觉设计和内容设计两个文件。

输入：
- `guided-article.md`
- 听众和组会场景
- 过去的组会 PPT 示例

输出：
- `design-frontend.md`
- `design-content.md`

`design-frontend.md` 写：
- 视觉视角
- 版式系统
- 图表和示意图风格
- 字体、颜色、间距、层级
- 模板约束

`design-content.md` 写：
- 叙事角度
- 术语选择
- 语气
- slide title 风格
- 数学、代码、细节暴露程度
- 中文演讲讲解策略

检查：
- 视觉设计不改写科学内容。
- 内容设计不依赖具体前端实现。
- 两份文档可以独立审查。
- PPT 正文语言策略明确：slide 上英文，讲解用中文。

停止条件：
- 两份设计文档足够具体，可以指导后续生产。

## Step 5 - 生成合适的模板

目标：生成适合本次组会汇报的模板。

输入：
- `design-frontend.md`
- 过去的 PPT 示例
- 品牌或课题组约束

输出：
- `template-spec.md`
- 模板源文件或可复用 deck skeleton

检查：
- 模板支持 title、section、concept、method、result、comparison、summary、backup slides。
- 模板有足够弹性，但不要产生太多一次性 layout。
- 模板可以先独立渲染和检查，再放内容。

停止条件：
- 模板能承载预期内容，不需要边做边临时改版式。

## Step 6 - 内容和模板匹配

目标：把导读文章里的内容映射到模板结构。

输入：
- `guided-article.md`
- `design-content.md`
- 模板源文件或 `template-spec.md`

输出：
- `content-template-map.md`

检查：
- 每张 slide 只有一个角色。
- 每个内容块都有目标模板位置。
- 重要概念有足够空间。
- 信息过密的地方先拆分，不要留到制作时再补救。

停止条件：
- 后续实现可以按映射表执行，不需要每次重读整篇文章。

## Step 7 - 生成纯内容审查 Markdown

目标：把匹配后的内容转换成一个适合快速内容审查的纯 Markdown 文件。

输入：
- `content-template-map.md`

输出：
- `content-review.md`

规则：
- 不做设计 styling。
- 不写复杂 layout 指令，只保留简单 slot 标签。
- 每张 slide 包含：slide number、英文 action title、英文正文、figure/table placeholder、中文 speaker note draft。

检查：
- 文本可以快速审查。
- slide title 是 takeaway，不是普通标签。
- 正文足够短，可以直接放上 slide。
- 缺失图片、证据或数据的位置标清楚。

停止条件：
- 内容先被批准，再进入设计实现。

## Step 8 - 设计和内容锚定

目标：把已批准的 Markdown 内容放入模板，同时保持内容和设计分离。

输入：
- `content-review.md`
- 模板源文件

输出：
- `deck-source/` 中的 anchored deck source

规则：
- 内容源仍然是 Markdown。
- 设计源只负责 layout 和 style。
- 对已有 deck 做内容锚定时，一次只锚定一页；先备份该页 HTML 和 preview。
- `content-review.md` 可以作为内容源，但不得一次性回填到全部 HTML。
- Markdown 内容块用 HTML comment 标注 anchor，格式为 `<!-- anchor: s001.title -->` 和 `<!-- /anchor -->`。
- HTML 或模板端只用 `anchor="s001.title"` 匹配位置，不根据文字内容、class 名或顺序猜测。
- 使用稳定 anchor 表示 slide slot，方便以后用脚本自动放置内容。
- 不要把内容手工埋进 HTML 或设计代码里；能用 anchor 表达就用 anchor。
- 推荐 anchor 命名：`s001.title`、`s001.body`、`s001.figure`、`s001.caption`、`s001.notes.zh`。

示例：

```md
<!-- anchor: s001.title -->
Hydronium prefers the air-water interface
<!-- /anchor -->

<!-- anchor: s001.notes.zh -->
这里用中文解释经典连续介质图像和分子模拟结果的差异。
<!-- /anchor -->
```

```html
<h1 anchor="s001.title"></h1>
<aside anchor="s001.notes.zh"></aside>
```

检查：
- 每个 Markdown 内容块都映射到稳定 anchor。
- 未使用 anchor 要报告。
- 放置过程中没有悄悄改内容。
- 当前页的设计结构没有被统一模板替换。

停止条件：
- deck source 可以由内容和模板重新生成。

## Step 9 - 调整设计

目标：只在设计层面调整已经放入内容的 deck。

输入：
- anchored deck source
- 渲染预览图

输出：
- 更新后的 deck source
- review renders

检查：
- 没有文字重叠。
- 图和表可读。
- slide 层级清晰。
- 版式支持中文演讲节奏。
- 除非用户明确要求，否则不改已批准内容。
- 只检查和交付当前页 preview；不要批量覆盖其它页预览。

停止条件：
- 渲染结果已经适合正式汇报。

## Step 10 - 输出 PPT

目标：导出最终汇报文件。

输入：
- final deck source

输出：
- `.pptx`
- `.pdf`
- rendered slide images 或 contact sheets
- 最终版 `content-review.md`

检查：
- 导出前已有完整备份。
- PPTX 能打开。
- PDF 页数和 PPTX slide 数一致。
- 渲染预览不是空白。
- 最终文件使用稳定的小写文件名。
- final 目录包含 source、PPTX、PDF、review material。

停止条件：
- deck 可以用于正式组会汇报，或发给人做最后审查。
