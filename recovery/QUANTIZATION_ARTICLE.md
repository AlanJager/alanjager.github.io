# 量化文章的编辑与发布

- 正文：`source/_posts/model-quantization-principles.md`。标题、文字、引用和章节锚点都在这里编辑。
- 图解与实验标记：在 Markdown 中写 `{% quant_visual 名称 %}`。可用名称及实现见 `scripts/quantization-tags.js`，对应 HTML 位于 `visuals/quantization/`。
- 样式与交互：`source/css/quantization-article.css`、`source/js/quantization-demo.js`。它们只作用于 `.quant-article` 内的页面。
- 主题包装：`themes/landscape/layout/_partial/article.ejs` 只为本文添加 `.quant-article` 容器，保留博客原有页头、侧栏和文章页脚。

运行 `npm ci && npm run build` 后，生成页位于 `public/2026/09/24/model-quantization-principles/index.html`。发布到已有 `github_pages` 分支时，更新这个页面以及 `css/quantization-article.css`、`js/quantization-demo.js`；其他历史文章不需要重新生成。

改造前的主题版 EJS 保存在 `recovery/quantization-themed.ejs`，更早的独立页面保存在 `recovery/quantization-standalone.ejs`。
