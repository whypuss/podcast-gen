// server.js — 同時 serve Vue 靜態文件 + 代理 API 請求到後端
// 用法: node server.js
const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');

const PORT = 5174;
const DIST_DIR = path.join(__dirname, 'dist');
const API_TARGET = 'http://127.0.0.1:8765'; // 後端地址

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js':   'application/javascript',
  '.css':  'text/css',
  '.json': 'application/json',
  '.png':  'image/png',
  '.jpg':  'image/jpeg',
  '.svg':  'image/svg+xml',
  '.ico':  'image/x-icon',
  '.woff2':'font/woff2',
  '.woff': 'font/woff',
  '.mp3':  'audio/mpeg',
  '.wav':  'audio/wav',
};

const server = http.createServer((req, res) => {
  const parsedUrl = url.parse(req.url, true);
  const pathname = parsedUrl.pathname;

  // ── API 代理 ────────────────────────────────────────────────────────────────
  if (pathname.startsWith('/generate') || pathname.startsWith('/models') ||
      pathname.startsWith('/health') || pathname.startsWith('/download') ||
      pathname.startsWith('/api/')) {
    const target = API_TARGET + pathname;
    const proxyReq = http.request(target, {
      method: req.method,
      headers: { ...req.headers, host: 'localhost' },
    }, (proxyRes) => {
      res.writeHead(proxyRes.statusCode, {
        ...proxyRes.headers,
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
      });
      proxyRes.pipe(res);
    });
    proxyReq.on('error', (e) => {
      res.writeHead(502);
      res.end('Backend unavailable');
    });
    req.pipe(proxyReq);
    return;
  }

  // ── CORS 預檢 ────────────────────────────────────────────────────────────────
  if (req.method === 'OPTIONS') {
    res.writeHead(204, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Access-Control-Max-Age': '86400',
    });
    res.end();
    return;
  }

  // ── 靜態文件 ────────────────────────────────────────────────────────────────
  let filePath = path.join(DIST_DIR, pathname === '/' ? 'index.html' : pathname);

  // 安全檢查：不允許遍歷目錄
  if (!filePath.startsWith(DIST_DIR)) {
    res.writeHead(403);
    res.end('Forbidden');
    return;
  }

  const ext = path.extname(filePath).toLowerCase();
  const contentType = MIME_TYPES[ext] || 'application/octet-stream';

  fs.readFile(filePath, (err, data) => {
    if (err) {
      if (err.code === 'ENOENT') {
        // SPA fallback → index.html
        fs.readFile(path.join(DIST_DIR, 'index.html'), (err2, html) => {
          if (err2) {
            res.writeHead(404);
            res.end('Not Found');
          } else {
            res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
            res.end(html);
          }
        });
      } else {
        res.writeHead(500);
        res.end('Server Error');
      }
      return;
    }
    res.writeHead(200, { 'Content-Type': contentType });
    res.end(data);
  });
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`Server running on http://0.0.0.0:${PORT}`);
  console.log(`API proxy → ${API_TARGET}`);
});
