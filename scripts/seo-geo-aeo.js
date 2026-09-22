'use strict';

/**
 * Hexo generator + HTML filter for SEO / AEO / GEO.
 *
 * Lives in this theme as scripts/seo-geo-aeo.js (Hexo loads theme scripts
 * on `hexo generate`). Can also be copied to the site's scripts/.
 *
 * Config (site _config.yml):
 *
 *   url: https://hanayo.cn
 *   language: zh-CN
 *   author: Alan Jager
 *   description: KVM / virtio / Linux 内核排查笔记
 *
 *   seo_geo_aeo:
 *     sameAs:
 *       - https://github.com/AlanJager
 *     llms_limit: 20
 */

function siteUrl() {
  const raw = (hexo.config.url || 'https://hanayo.cn').replace(/\/$/, '');
  return raw.replace(/^http:\/\//i, 'https://');
}

function lang() {
  return hexo.config.language || 'zh-CN';
}

function cfg() {
  return hexo.config.seo_geo_aeo || {};
}

function abs(path) {
  if (!path) return siteUrl() + '/';
  if (/^https?:\/\//i.test(path)) {
    return path.replace(/^http:\/\/hanayo\.cn/i, 'https://hanayo.cn');
  }
  return siteUrl() + '/' + String(path).replace(/^\//, '').replace(/index\.html$/, '');
}

function iso(value) {
  if (!value) return '';
  try {
    return new Date(value).toISOString();
  } catch (err) {
    return '';
  }
}

function xmlEscape(value) {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function textEscape(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

hexo.extend.generator.register('seo-robots', function () {
  const url = siteUrl();
  const body = [
    'User-agent: *',
    'Allow: /',
    '',
    'User-agent: OAI-SearchBot',
    'Allow: /',
    '',
    'User-agent: ChatGPT-User',
    'Allow: /',
    '',
    'User-agent: Claude-SearchBot',
    'Allow: /',
    '',
    'User-agent: PerplexityBot',
    'Allow: /',
    '',
    'User-agent: Googlebot',
    'Allow: /',
    '',
    '# Training crawlers are allowed so original write-ups can be cited.',
    '# Set seo_geo_aeo.block_training: true to emit Disallow for GPTBot / Google-Extended.',
    '',
    'Sitemap: ' + url + '/sitemap.xml',
    '',
  ];
  if (cfg().block_training) {
    body.splice(-3, 0, 'User-agent: GPTBot', 'Disallow: /', '', 'User-agent: Google-Extended', 'Disallow: /', '');
  }
  return {path: 'robots.txt', data: body.join('\n')};
});

hexo.extend.generator.register('seo-sitemap', function (locals) {
  const url = siteUrl();
  const entries = [{loc: url + '/', lastmod: iso(new Date()), changefreq: 'weekly', priority: '1.0'}];

  (locals.posts || {data: []}).sort('-updated').forEach(function (post) {
    if (post.draft) return;
    entries.push({
      loc: abs(post.path),
      lastmod: iso(post.updated || post.date),
      changefreq: 'monthly',
      priority: '0.8',
    });
  });

  (locals.pages || {data: []}).forEach(function (page) {
    if (!page.path) return;
    const path = String(page.path).replace(/index\.html$/, '');
    if (path.indexOf('page/') === 0) return;
    entries.push({
      loc: abs(page.path),
      lastmod: iso(page.updated || page.date),
      changefreq: 'monthly',
      priority: path.indexOf('tools/') === 0 ? '0.7' : '0.5',
    });
  });

  const seen = {};
  const xml = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
  ];
  entries.forEach(function (item) {
    const loc = item.loc.replace(/\/+$/, '/') === url + '/' ? url + '/' : item.loc.replace(/\/index\.html$/, '/');
    if (seen[loc]) return;
    seen[loc] = true;
    xml.push('  <url>');
    xml.push('    <loc>' + xmlEscape(loc) + '</loc>');
    if (item.lastmod) xml.push('    <lastmod>' + xmlEscape(item.lastmod.slice(0, 10)) + '</lastmod>');
    xml.push('    <changefreq>' + item.changefreq + '</changefreq>');
    xml.push('    <priority>' + item.priority + '</priority>');
    xml.push('  </url>');
  });
  xml.push('</urlset>', '');
  return {path: 'sitemap.xml', data: xml.join('\n')};
});

hexo.extend.generator.register('seo-llms', function (locals) {
  const url = siteUrl();
  const limit = Number(cfg().llms_limit || 20);
  const query = locals.posts;
  const posts = query && typeof query.sort === 'function'
    ? query.sort('-updated').limit(limit).toArray()
    : [];
  const lines = [
    '# ' + (hexo.config.title || '花の様に'),
    '',
    '> ' + (hexo.config.description || 'Alan Jager 的 KVM / virtio / Linux 内核排查笔记。'),
    '',
    '- 站点: ' + url + '/',
    '- 作者: ' + (hexo.config.author || 'Alan Jager'),
    '- GitHub: https://github.com/AlanJager',
    '',
    '## 工具',
    '',
    '- [resume-hub](' + url + '/tools/resume-hub/): Codex 限额后从本机 session 切到 Grok / Claude。',
    '',
    '## 近期文章',
    '',
  ];
  posts.forEach(function (post) {
    if (post.draft) return;
    const desc = textEscape(post.description || post.excerpt || '');
    const suffix = desc ? ' — ' + desc.slice(0, 160) : '';
    lines.push('- [' + textEscape(post.title) + '](' + abs(post.path) + ')' + suffix);
  });
  lines.push('', '本文由 Hexo 生成（scripts/seo-geo-aeo.js）。', '');
  return {path: 'llms.txt', data: lines.join('\n')};
});

hexo.extend.filter.register('after_render:html', function (str) {
  if (!str || str.indexOf('</head>') === -1) return str;

  if (!/\<html[^>]*\blang=/i.test(str)) {
    str = str.replace(/<html\b/i, '<html lang="' + lang() + '"');
  }

  str = str.replace(/http:\/\/hanayo\.cn/g, 'https://hanayo.cn');

  if (str.indexOf('application/ld+json') !== -1) return str;

  const ogTitle = (str.match(/property="og:title"\s+content="([^"]*)"/i) || [])[1];
  const ogUrl = (str.match(/property="og:url"\s+content="([^"]*)"/i) || [])[1];
  const ogType = (str.match(/property="og:type"\s+content="([^"]*)"/i) || [])[1];
  const ogDesc = (str.match(/property="og:description"\s+content="([^"]*)"/i) ||
    str.match(/name="description"\s+content="([^"]*)"/i) || [])[1];
  const published = (str.match(/property="article:published_time"\s+content="([^"]*)"/i) || [])[1];
  const modified = (str.match(/property="article:modified_time"\s+content="([^"]*)"/i) || [])[1];

  const sameAs = cfg().sameAs || ['https://github.com/AlanJager'];
  const person = {
    '@type': 'Person',
    name: hexo.config.author || 'Alan Jager',
    url: siteUrl() + '/',
    sameAs: sameAs,
  };
  const graph = [
    {
      '@type': 'WebSite',
      name: hexo.config.title || '花の様に',
      url: siteUrl() + '/',
      inLanguage: lang(),
      publisher: person,
    },
  ];
  if (ogType === 'article' && ogTitle && ogUrl) {
    graph.push({
      '@type': 'BlogPosting',
      headline: ogTitle,
      description: ogDesc || undefined,
      url: ogUrl.replace(/^http:\/\//, 'https://'),
      datePublished: published || undefined,
      dateModified: modified || published || undefined,
      inLanguage: lang(),
      author: person,
      mainEntityOfPage: ogUrl.replace(/^http:\/\//, 'https://'),
    });
  }

  const payload = {
    '@context': 'https://schema.org',
    '@graph': graph,
  };
  const tag = '<script type="application/ld+json">' + JSON.stringify(payload) + '</script>';
  return str.replace('</head>', tag + '\n</head>');
});
