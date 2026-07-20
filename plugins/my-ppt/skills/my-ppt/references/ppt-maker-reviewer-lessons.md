# PPT Maker / Reviewer 经验沉淀

这份记录吸收自几个组会 PPT 制作线程，用来约束后续 workflow。它不记录具体项目内容，只保留可复用规则。

## 1. 最大事故模式

- 不要把 `slide-content.md` 当作唯一真相源一次性回填全部 HTML。
- 不要批量重生成所有页面，尤其是已有逐页设计和旧 preview 时。
- 如果全量回填出错，第一步不是继续修 HTML，而是停止、找备份、找旧 preview/PDF/PPTX。

## 2. 正确生产节奏

- 一次只做一页。
- 每页先明确它在叙事里的功能，再写内容。
- 每页都要经历：制作 -> 渲染 -> review -> fix -> 确认 -> 下一页。
- Reviewer 和 Fixer 都只拿当前页，不拿整套 deck。
- 等 reviewer 小修意见闭环后再推进下一页。

## 3. Reviewer 检查重点

- Action title 是否是结论型标题。
- 页面是否只服务一个核心信息。
- 正式页不能暴露本地路径、开发提示、待核查文本、讲稿提示或内部 TODO。
- 对公开项目、工具、产品的描述要保守：优先写 `project materials state/claim/describe`。
- 如果证据只能支持“偏好提升/功能声称/流程存在”，不要写成“事实正确/效果已验证”。
- 趋势判断、能力边界、引用准确性必须单独检查。

## 4. HTML 和内容分离

- Markdown 内容源使用 `<!-- anchor: xxx -->`。
- HTML 目标位置使用 `anchor="xxx"`。
- `anchor` 不参与 CSS 样式选择，只给程序匹配。
- 程序注入只能作为生成步骤，不能把 filled HTML 变成唯一编辑源。
- 已有 HTML 的逐页设计优先保留，不能用统一模板覆盖。

## 5. Speaker Notes

- 讲稿默认中文。
- notes 必须按 slide heading/编号严格配对。
- 生成后要检查 notes slide 数量、关键讲稿关键词和对应页。
- 不要只确认 notes XML 存在；还要确认正文讲稿真的写入。

## 6. 导出和兜底

- 常规输出要验证 PPTX、PDF、preview、notes。
- 如果 editable HTML 无法快速恢复，可以用已确认正确的 preview PNG 生成图片型 PPTX。
- 图片型 PPTX 只能作为交付兜底或临时汇报版本，必须另存新文件。
- 导出后抽查封面、第二页、关键结果页、最后一页，确认顺序、比例和裁切。
