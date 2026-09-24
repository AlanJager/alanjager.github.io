const fs = require('fs');
const path = require('path');

const visuals = new Set([
  'hero', 'overview', 'encode_formula', 'lab', 'output_formula',
  'layer_map', 'layer_notes', 'method_grid', 'runtime_flow',
  'runtime_formula', 'memory_grid', 'capacity_formula', 'memory_calc'
]);
const visualDirectory = path.join(__dirname, '..', 'visuals', 'quantization');

hexo.extend.tag.register('quant_visual', function (args) {
  const name = args[0];
  if (!visuals.has(name)) throw new Error(`Unknown quantization visual: ${name}`);
  const html = fs.readFileSync(path.join(visualDirectory, `${name}.html`), 'utf8');
  if (name === 'hero') {
    return '<link rel="stylesheet" href="/css/quantization-article.css">\n' + html;
  }
  if (name === 'lab') {
    return html + '<script defer src="/js/quantization-demo.js"></script>\n';
  }
  return html;
});
