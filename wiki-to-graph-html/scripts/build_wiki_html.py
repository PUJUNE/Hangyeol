"""
LLM 위키 → 단일 HTML 지식그래프 빌더.
지정한 wiki 폴더의 모든 .md를 스캔해 노드/엣지를 추출하고,
자체 force-directed 그래프 + 본문 뷰어 + 인터랙션 슬라이더를
한 장의 HTML 파일로 출력함. 산출물은 wiki 폴더가 없어도 단독 동작.

사용법:
  python build_wiki_html.py                       # ./wiki → ./wiki_graph.html
  python build_wiki_html.py <wiki_dir>            # <dir> → <dir>/../wiki_graph.html
  python build_wiki_html.py <wiki_dir> <out.html> # 출력 경로 직접 지정
  python build_wiki_html.py --title "제목"        # HTML <title>·placeholder 헤더
"""

from pathlib import Path
import argparse
import json
import re
import sys

EXCLUDE_DIRS = {"lint-reports"}
EXCLUDE_FILES = {"index.md", "log.md"}

TYPE_BY_DIR = {
    "concepts": "concept",
    "entities": "entity",
    "sources": "source",
    "themes": "theme",
    "syntheses": "synthesis",
    "essays": "essay",
    "areas": "synthesis",
    "worklog": "worklog",
}

# wiki 루트 직접 md는 frontmatter `type:` 필드를 보고 분류한다.
TYPE_FROM_FM_FALLBACK = {"concept", "entity", "source", "theme", "synthesis", "essay", "worklog"}

WIKILINK_RE = re.compile(r"\[\[([^\]]+?)\]\]")


def parse_frontmatter(text):
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm_raw = text[3:end].strip("\n")
    body = text[end + 4:].lstrip("\n")
    fm = {}
    current_key = None
    for line in fm_raw.splitlines():
        if not line.strip():
            continue
        if line.startswith("  - "):
            if current_key:
                fm.setdefault(current_key, []).append(line[4:].strip().strip('"'))
        elif ":" in line and not line.startswith(" "):
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()
            if val == "":
                current_key = key
                fm[key] = []
            else:
                current_key = None
                fm[key] = val.strip('"').strip("[]")
    return fm, body


def extract_slug(wikitext):
    s = wikitext.strip().strip('"').strip("'")
    m = re.match(r"^\[\[([^\]|]+)(\|[^\]]+)?\]\]$", s)
    if m:
        s = m.group(1)
    if "|" in s:
        s = s.split("|", 1)[0]
    return s.strip()


def collect(wiki_dir: Path):
    nodes = {}
    edges_set = set()

    for md in wiki_dir.rglob("*.md"):
        rel = md.relative_to(wiki_dir)
        if rel.parts[0] in EXCLUDE_DIRS:
            continue
        if md.name in EXCLUDE_FILES:
            continue
        slug = md.stem
        dir_name = rel.parts[0] if len(rel.parts) > 1 else ""
        text = md.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)
        # 폴더로 우선 분류, 폴더가 없거나 매핑 안 되면 frontmatter type을 사용
        if dir_name in TYPE_BY_DIR:
            ntype = TYPE_BY_DIR[dir_name]
        else:
            fm_type = (fm.get("type") or "").strip().strip('"').strip("'")
            ntype = fm_type if fm_type in TYPE_FROM_FM_FALLBACK else "other"
        title = fm.get("title", slug).strip('"')
        tags = fm.get("tags", "")
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]
        status = fm.get("status", "draft")
        nodes[slug] = {
            "id": slug,
            "title": title,
            "type": ntype,
            "tags": tags,
            "status": status,
            "body": body,
        }

        targets = set()
        for key in (
            "related_concepts", "related_entities", "related_sources", "related_themes",
            "related_syntheses", "related_essays", "related_worklog", "related_worklog_hub",
            "applies", "advances", "follows", "precedes",
        ):
            vals = fm.get(key, [])
            if isinstance(vals, list):
                for v in vals:
                    # frontmatter wikilink는 반드시 [[...]] 형식만 엣지로 인정.
                    # plain text 슬러그(raw 자료 메모)는 무시해 옵시디언과 동일하게 동작.
                    v_strip = v.strip().strip('"').strip("'")
                    m = re.match(r"^\[\[([^\]|]+)(\|[^\]]+)?\]\]$", v_strip)
                    if not m:
                        continue
                    t = m.group(1).split("|", 1)[0].strip()
                    if t:
                        targets.add(t)
        for m in WIKILINK_RE.finditer(body):
            t = extract_slug(m.group(1))
            if t:
                targets.add(t)

        for t in targets:
            if t == slug:
                continue
            a, b = sorted([slug, t])
            edges_set.add((a, b))

    final_nodes = list(nodes.values())
    final_edges = []
    valid_ids = set(nodes.keys())
    for a, b in edges_set:
        if a in valid_ids and b in valid_ids:
            final_edges.append({"source": a, "target": b})
        elif a in valid_ids or b in valid_ids:
            other = b if a in valid_ids else a
            ghost = a if a not in valid_ids else b
            if ghost not in nodes:
                nodes[ghost] = {
                    "id": ghost,
                    "title": ghost,
                    "type": "missing",
                    "tags": [],
                    "status": "missing",
                    "body": f"_(이 페이지는 아직 존재하지 않음. wikilink 대상으로만 등장)_\n\n원본 슬러그: `{ghost}`",
                }
                final_nodes.append(nodes[ghost])
            final_edges.append({"source": a, "target": b})

    return final_nodes, final_edges


def build_html(nodes, edges, out_path: Path, title: str):
    payload = json.dumps({"nodes": nodes, "edges": edges}, ensure_ascii=False)
    html = HTML_TEMPLATE.replace("__DATA__", payload).replace("__TITLE__", title)
    out_path.write_text(html, encoding="utf-8")
    print(f"wrote {out_path} ({out_path.stat().st_size:,} bytes)")
    print(f"  nodes: {len(nodes)}")
    print(f"  edges: {len(edges)}")


HTML_TEMPLATE = r"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>__TITLE__</title>
<style>
:root {
  --bg: #1e1e26;
  --bg-2: #262630;
  --bg-3: #2f2f3a;
  --fg: #e6e6ea;
  --muted: #9a9aa8;
  --border: #3a3a48;
  --accent: #7ab7ff;
  --c-concept: #6aa9ff;
  --c-entity: #6bd49a;
  --c-source: #f0a86b;
  --c-theme: #c98ef0;
  --c-synthesis: #e8d36a;
  --c-essay: #b0b0c0;
  --c-worklog: #ff8aa8;
  --c-missing: #6a6a78;
}
* { box-sizing: border-box; }
html, body { margin: 0; height: 100%; background: var(--bg); color: var(--fg);
  font-family: -apple-system, "Segoe UI", "Apple SD Gothic Neo", "Malgun Gothic", sans-serif; }
.app { display: grid; grid-template-columns: minmax(320px, 1fr) 8px minmax(320px, 480px); height: 100vh; }
.graph-pane { position: relative; overflow: hidden; background: var(--bg); min-width: 0; }
.splitter { background: var(--border); border-left: 1px solid var(--bg-2); border-right: 1px solid var(--bg-2); cursor: col-resize; touch-action: none; transition: background 0.15s ease; }
.splitter:hover, .splitter.active { background: var(--accent); }
body.resizing { cursor: col-resize; user-select: none; }
.doc-pane { background: var(--bg-2); overflow-y: auto; padding: 24px 28px; min-width: 0; }
svg { width: 100%; height: 100%; display: block; cursor: grab; }
svg.dragging { cursor: grabbing; }
.node-label { font-size: 11px; fill: var(--fg); pointer-events: none; user-select: none; }
.node circle { stroke: rgba(255,255,255,0.15); stroke-width: 1.5; cursor: pointer; }
.node.active circle { stroke: #fff; stroke-width: 2.5; }
.node.faded { opacity: 0.15; }
.link { stroke: #4a4a58; stroke-opacity: 0.6; }
.link.highlight { stroke: var(--accent); stroke-opacity: 1; stroke-width: 1.6; }
.link.faded { opacity: 0.08; }

.toolbar { position: absolute; top: 12px; left: 12px; display: flex; flex-direction: column; gap: 8px;
  background: rgba(38,38,48,0.92); padding: 10px 12px; border-radius: 8px; border: 1px solid var(--border); z-index: 10; }
.toolbar-row { display: flex; gap: 8px; align-items: center; }
.toolbar input[type="text"] { background: var(--bg-3); color: var(--fg); border: 1px solid var(--border);
  border-radius: 6px; padding: 6px 10px; font-size: 13px; width: 200px; outline: none; }
.toolbar input[type="text"]:focus { border-color: var(--accent); }
.slider-row { display: grid; grid-template-columns: 70px 1fr 44px; gap: 8px; align-items: center; font-size: 12px; color: var(--muted); }
.slider-row input[type="range"] { width: 100%; accent-color: var(--accent); }
.slider-row .val { text-align: right; color: var(--fg); font-variant-numeric: tabular-nums; font-size: 11px; }
.legend { position: absolute; bottom: 12px; left: 12px; background: rgba(38,38,48,0.92);
  padding: 10px 12px; border-radius: 8px; border: 1px solid var(--border); font-size: 12px; z-index: 10; }
.legend label { display: flex; align-items: center; gap: 6px; cursor: pointer; padding: 2px 0; }
.legend .dot { width: 10px; height: 10px; border-radius: 50%; }
.legend input { margin: 0; }
.hud { position: absolute; top: 12px; right: 12px; background: rgba(38,38,48,0.92);
  padding: 6px 10px; border-radius: 6px; font-size: 11px; color: var(--muted); border: 1px solid var(--border); z-index: 10; }

.doc-pane h1 { font-size: 22px; margin: 0 0 6px; }
.doc-pane .meta { color: var(--muted); font-size: 12px; margin-bottom: 18px; }
.doc-pane .meta .pill { display: inline-block; padding: 2px 8px; border-radius: 999px; background: var(--bg-3);
  margin-right: 6px; font-size: 11px; color: var(--fg); }
.doc-pane h2 { font-size: 16px; margin: 22px 0 8px; padding-bottom: 4px; border-bottom: 1px solid var(--border); }
.doc-pane h3 { font-size: 14px; margin: 18px 0 6px; color: var(--fg); }
.doc-pane p { line-height: 1.7; margin: 8px 0; }
.doc-pane ul, .doc-pane ol { line-height: 1.7; padding-left: 22px; }
.doc-pane li { margin: 3px 0; }
.doc-pane code { background: var(--bg-3); padding: 1px 6px; border-radius: 4px; font-size: 12.5px; }
.doc-pane a.wikilink { color: var(--accent); text-decoration: none; border-bottom: 1px dashed var(--accent); cursor: pointer; }
.doc-pane a.wikilink:hover { background: rgba(122,183,255,0.12); }
.doc-pane a.wikilink.missing { color: var(--c-missing); border-bottom-style: dotted; }
.doc-pane a.ext { color: var(--accent); }
.doc-pane strong { color: #fff; }
.doc-pane em { color: #d4d4dc; }
.doc-pane hr { border: none; border-top: 1px solid var(--border); margin: 18px 0; }
.doc-pane blockquote { border-left: 3px solid var(--border); margin: 10px 0; padding: 4px 12px; color: var(--muted); }

.placeholder { color: var(--muted); font-size: 13px; padding-top: 80px; text-align: center; }
.placeholder h2 { border: none; font-size: 18px; color: var(--fg); }

.backlinks { margin-top: 28px; padding-top: 14px; border-top: 1px solid var(--border); }
.backlinks h3 { color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; margin: 0 0 8px; }
.backlinks ul { list-style: none; padding: 0; }
.backlinks li { padding: 2px 0; font-size: 13px; }
</style>
</head>
<body>
<div class="app">
  <div class="graph-pane">
    <div class="toolbar">
      <div class="toolbar-row">
        <input type="text" id="search" placeholder="검색 (제목·태그)" autocomplete="off">
        <button id="reset" style="background:var(--bg-3);color:var(--fg);border:1px solid var(--border);border-radius:6px;padding:6px 10px;cursor:pointer;font-size:12px">초기화</button>
      </div>
      <div class="slider-row">
        <span>노드 크기</span>
        <input type="range" id="s-node" min="2" max="14" step="1" value="5">
        <span class="val" id="v-node">5</span>
      </div>
      <div class="slider-row">
        <span>장력(반발)</span>
        <input type="range" id="s-rep" min="200" max="6000" step="100" value="1800">
        <span class="val" id="v-rep">1800</span>
      </div>
      <div class="slider-row">
        <span>엣지 거리</span>
        <input type="range" id="s-link" min="20" max="280" step="5" value="90">
        <span class="val" id="v-link">90</span>
      </div>
    </div>
    <div class="hud" id="hud">노드 0 / 엣지 0</div>
    <div class="legend" id="legend"></div>
    <svg id="graph"></svg>
  </div>
  <div class="splitter" id="splitter" role="separator" aria-orientation="vertical" aria-label="좌우 패널 너비 조절" tabindex="0"></div>
  <div class="doc-pane" id="doc">
    <div class="placeholder">
      <h2>__TITLE__</h2>
      <p>왼쪽 그래프의 노드를 클릭하면<br>여기에 문서가 표시됩니다.</p>
    </div>
  </div>
</div>

<script>
const DATA = __DATA__;

const TYPE_COLORS = {
  concept: getComputedStyle(document.documentElement).getPropertyValue('--c-concept').trim(),
  entity: getComputedStyle(document.documentElement).getPropertyValue('--c-entity').trim(),
  source: getComputedStyle(document.documentElement).getPropertyValue('--c-source').trim(),
  theme: getComputedStyle(document.documentElement).getPropertyValue('--c-theme').trim(),
  synthesis: getComputedStyle(document.documentElement).getPropertyValue('--c-synthesis').trim(),
  essay: getComputedStyle(document.documentElement).getPropertyValue('--c-essay').trim(),
  worklog: getComputedStyle(document.documentElement).getPropertyValue('--c-worklog').trim(),
  missing: getComputedStyle(document.documentElement).getPropertyValue('--c-missing').trim(),
  other: '#888'
};

const TYPE_LABELS = {
  concept: '개념', entity: '인물', source: '소스', theme: '테마',
  synthesis: '종합', essay: '에세이', worklog: '활동', missing: '미생성', other: '기타'
};

// ------- index -------
const nodeById = {};
DATA.nodes.forEach(n => { nodeById[n.id] = n; });
const adjacency = {};
DATA.nodes.forEach(n => { adjacency[n.id] = new Set(); });
DATA.edges.forEach(e => {
  if (adjacency[e.source]) adjacency[e.source].add(e.target);
  if (adjacency[e.target]) adjacency[e.target].add(e.source);
});
const degree = {};
DATA.nodes.forEach(n => { degree[n.id] = adjacency[n.id].size; });

// type filter state
const activeTypes = new Set(Object.keys(TYPE_LABELS));

// ------- legend -------
const legendEl = document.getElementById('legend');
Object.entries(TYPE_LABELS).forEach(([key, label]) => {
  const id = 'tp-' + key;
  const wrap = document.createElement('label');
  wrap.innerHTML = `<input type="checkbox" id="${id}" checked>
    <span class="dot" style="background:${TYPE_COLORS[key]}"></span> ${label}`;
  legendEl.appendChild(wrap);
  wrap.querySelector('input').addEventListener('change', (e) => {
    if (e.target.checked) activeTypes.add(key); else activeTypes.delete(key);
    applyFilters();
  });
});

// ------- svg setup -------
const svg = document.getElementById('graph');
const SVG_NS = 'http://www.w3.org/2000/svg';
function el(name, attrs={}) {
  const e = document.createElementNS(SVG_NS, name);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  return e;
}

let width = svg.clientWidth;
let height = svg.clientHeight;

// transform group
const gZoom = el('g'); svg.appendChild(gZoom);
const gLinks = el('g'); gZoom.appendChild(gLinks);
const gNodes = el('g'); gZoom.appendChild(gNodes);

// init positions: random circle
DATA.nodes.forEach((n, i) => {
  const angle = (i / DATA.nodes.length) * Math.PI * 2;
  const r = Math.min(width, height) * 0.3;
  n.x = width / 2 + Math.cos(angle) * r;
  n.y = height / 2 + Math.sin(angle) * r;
  n.vx = 0; n.vy = 0;
});

// build link elements
const linkEls = DATA.edges.map(e => {
  const line = el('line', { class: 'link' });
  e._el = line;
  e._source = nodeById[e.source];
  e._target = nodeById[e.target];
  gLinks.appendChild(line);
  return line;
});

// build node elements
let baseR = 5;
function radiusOf(n) { return baseR + Math.min(degree[n.id], 10) * (baseR / 5); }
function applyNodeRadii() {
  DATA.nodes.forEach(n => {
    const r = radiusOf(n);
    n._r = r;
    if (n._circle) n._circle.setAttribute('r', r);
    if (n._label) n._label.setAttribute('dy', -(r + 4));
  });
}

DATA.nodes.forEach(n => {
  const g = el('g', { class: 'node' });
  const r = radiusOf(n);
  n._r = r;
  const c = el('circle', { r: r, fill: TYPE_COLORS[n.type] || '#888' });
  const t = el('text', { class: 'node-label', dy: -(r + 4), 'text-anchor': 'middle' });
  t.textContent = n.title;
  g.appendChild(c);
  g.appendChild(t);
  n._g = g;
  n._circle = c;
  n._label = t;
  gNodes.appendChild(g);

  // drag + click
  let dragStart = null;
  g.addEventListener('mousedown', (ev) => {
    ev.stopPropagation();
    dragStart = { x: ev.clientX, y: ev.clientY, moved: false, nx: n.x, ny: n.y };
    n._fixed = true;
    const onMove = (mv) => {
      const dx = (mv.clientX - dragStart.x) / zoom.k;
      const dy = (mv.clientY - dragStart.y) / zoom.k;
      if (Math.abs(dx) + Math.abs(dy) > 2) dragStart.moved = true;
      n.x = dragStart.nx + dx;
      n.y = dragStart.ny + dy;
      n.vx = 0; n.vy = 0;
      tick(false);
    };
    const onUp = () => {
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
      n._fixed = false;
      if (!dragStart.moved) selectNode(n.id);
    };
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
  });
});

// zoom / pan
const zoom = { k: 1, x: 0, y: 0 };
function applyZoom() {
  gZoom.setAttribute('transform', `translate(${zoom.x},${zoom.y}) scale(${zoom.k})`);
}
svg.addEventListener('wheel', (ev) => {
  ev.preventDefault();
  const rect = svg.getBoundingClientRect();
  const mx = ev.clientX - rect.left;
  const my = ev.clientY - rect.top;
  const delta = -ev.deltaY * 0.0015;
  const newK = Math.min(4, Math.max(0.2, zoom.k * (1 + delta)));
  // zoom around cursor
  zoom.x = mx - (mx - zoom.x) * (newK / zoom.k);
  zoom.y = my - (my - zoom.y) * (newK / zoom.k);
  zoom.k = newK;
  applyZoom();
}, { passive: false });

let panStart = null;
svg.addEventListener('mousedown', (ev) => {
  panStart = { x: ev.clientX - zoom.x, y: ev.clientY - zoom.y };
  svg.classList.add('dragging');
});
document.addEventListener('mousemove', (ev) => {
  if (!panStart) return;
  zoom.x = ev.clientX - panStart.x;
  zoom.y = ev.clientY - panStart.y;
  applyZoom();
});
document.addEventListener('mouseup', () => {
  panStart = null;
  svg.classList.remove('dragging');
});

// ------- force simulation -------
const params = {
  repulsion: 1800,
  linkDist: 90,
  linkStrength: 0.06,
  centerStrength: 0.012,
  damping: 0.82,
};

function step() {
  // repulsion (O(n^2), n<60 → 괜찮음)
  const N = DATA.nodes.length;
  for (let i = 0; i < N; i++) {
    const a = DATA.nodes[i];
    if (a._hidden) continue;
    for (let j = i + 1; j < N; j++) {
      const b = DATA.nodes[j];
      if (b._hidden) continue;
      let dx = a.x - b.x, dy = a.y - b.y;
      let d2 = dx*dx + dy*dy;
      if (d2 < 1) { d2 = 1; dx = Math.random() - 0.5; dy = Math.random() - 0.5; }
      const f = params.repulsion / d2;
      const d = Math.sqrt(d2);
      const fx = (dx / d) * f, fy = (dy / d) * f;
      a.vx += fx; a.vy += fy;
      b.vx -= fx; b.vy -= fy;
    }
  }
  // links
  DATA.edges.forEach(e => {
    const a = e._source, b = e._target;
    if (a._hidden || b._hidden) return;
    const dx = b.x - a.x, dy = b.y - a.y;
    const d = Math.sqrt(dx*dx + dy*dy) || 1;
    const diff = (d - params.linkDist) * params.linkStrength;
    const fx = (dx / d) * diff, fy = (dy / d) * diff;
    a.vx += fx; a.vy += fy;
    b.vx -= fx; b.vy -= fy;
  });
  // centering
  const cx = width / 2, cy = height / 2;
  DATA.nodes.forEach(n => {
    if (n._hidden) return;
    n.vx += (cx - n.x) * params.centerStrength;
    n.vy += (cy - n.y) * params.centerStrength;
  });
  // integrate
  DATA.nodes.forEach(n => {
    if (n._fixed || n._hidden) { n.vx = 0; n.vy = 0; return; }
    n.vx *= params.damping;
    n.vy *= params.damping;
    n.x += n.vx * 0.05;
    n.y += n.vy * 0.05;
  });
}

function tick(simulate=true) {
  if (simulate) step();
  DATA.nodes.forEach(n => {
    if (n._g) n._g.setAttribute('transform', `translate(${n.x},${n.y})`);
  });
  DATA.edges.forEach(e => {
    e._el.setAttribute('x1', e._source.x);
    e._el.setAttribute('y1', e._source.y);
    e._el.setAttribute('x2', e._target.x);
    e._el.setAttribute('y2', e._target.y);
  });
}

let running = true;
let settleTimer = null;
function animate() {
  if (running) tick(true);
  requestAnimationFrame(animate);
}
animate();

function reheat(durationMs = 4000) {
  params.damping = 0.82;
  running = true;
  if (settleTimer) clearTimeout(settleTimer);
  settleTimer = setTimeout(() => {
    params.damping = 0.92;
    setTimeout(() => { running = false; tick(false); }, 1500);
  }, durationMs);
}

const appEl = document.querySelector('.app');
const graphPaneEl = document.querySelector('.graph-pane');
const splitterEl = document.getElementById('splitter');

function updateGraphViewport() {
  width = svg.clientWidth;
  height = svg.clientHeight;
  tick(false);
}

function setPaneSplit(graphWidth) {
  const rect = appEl.getBoundingClientRect();
  const splitterWidth = splitterEl.offsetWidth || 8;
  const minGraph = 320;
  const minDoc = 320;
  const maxGraph = Math.max(minGraph, rect.width - splitterWidth - minDoc);
  const nextGraph = Math.min(Math.max(graphWidth, minGraph), maxGraph);
  const nextDoc = Math.max(rect.width - splitterWidth - nextGraph, minDoc);
  appEl.style.gridTemplateColumns = `${nextGraph}px ${splitterWidth}px ${nextDoc}px`;
  updateGraphViewport();
}

splitterEl.addEventListener('pointerdown', (ev) => {
  ev.preventDefault();
  const startX = ev.clientX;
  const startGraphWidth = graphPaneEl.getBoundingClientRect().width;
  splitterEl.classList.add('active');
  document.body.classList.add('resizing');

  const onMove = (moveEv) => {
    setPaneSplit(startGraphWidth + moveEv.clientX - startX);
  };
  const onUp = () => {
    splitterEl.classList.remove('active');
    document.body.classList.remove('resizing');
    document.removeEventListener('pointermove', onMove);
    document.removeEventListener('pointerup', onUp);
    reheat(1200);
  };

  document.addEventListener('pointermove', onMove);
  document.addEventListener('pointerup', onUp, { once: true });
});

splitterEl.addEventListener('keydown', (ev) => {
  if (ev.key !== 'ArrowLeft' && ev.key !== 'ArrowRight') return;
  ev.preventDefault();
  const delta = ev.key === 'ArrowLeft' ? -40 : 40;
  setPaneSplit(graphPaneEl.getBoundingClientRect().width + delta);
  reheat(1200);
});

window.addEventListener('resize', () => {
  setPaneSplit(graphPaneEl.getBoundingClientRect().width);
});

// ------- selection / filter -------
let activeId = null;
function selectNode(id) {
  activeId = id;
  const neighbors = new Set([id, ...adjacency[id]]);
  DATA.nodes.forEach(n => {
    n._g.classList.toggle('active', n.id === id);
    n._g.classList.toggle('faded', !neighbors.has(n.id));
  });
  DATA.edges.forEach(e => {
    const touch = e.source === id || e.target === id;
    e._el.classList.toggle('highlight', touch);
    e._el.classList.toggle('faded', !touch);
  });
  renderDoc(id);
}

function clearSelection() {
  activeId = null;
  DATA.nodes.forEach(n => { n._g.classList.remove('active','faded'); });
  DATA.edges.forEach(e => { e._el.classList.remove('highlight','faded'); });
}

function applyFilters() {
  const q = document.getElementById('search').value.trim().toLowerCase();
  DATA.nodes.forEach(n => {
    const typeOk = activeTypes.has(n.type);
    const qOk = !q || n.title.toLowerCase().includes(q) || (n.tags || []).some(t => t.toLowerCase().includes(q));
    const visible = typeOk && qOk;
    n._hidden = !visible;
    n._g.style.display = visible ? '' : 'none';
  });
  DATA.edges.forEach(e => {
    const visible = !e._source._hidden && !e._target._hidden;
    e._el.style.display = visible ? '' : 'none';
  });
  updateHud();
}

function updateHud() {
  const nv = DATA.nodes.filter(n => !n._hidden).length;
  const ev = DATA.edges.filter(e => !e._source._hidden && !e._target._hidden).length;
  document.getElementById('hud').textContent = `노드 ${nv} / 엣지 ${ev}`;
}
updateHud();

document.getElementById('search').addEventListener('input', applyFilters);
document.getElementById('reset').addEventListener('click', () => {
  document.getElementById('search').value = '';
  activeTypes.clear();
  Object.keys(TYPE_LABELS).forEach(k => activeTypes.add(k));
  document.querySelectorAll('.legend input').forEach(i => i.checked = true);
  applyFilters();
  clearSelection();
  document.getElementById('doc').innerHTML = '<div class="placeholder"><h2>__TITLE__</h2><p>왼쪽 그래프의 노드를 클릭하면<br>여기에 문서가 표시됩니다.</p></div>';
});

// ------- minimal markdown renderer -------
function escapeHtml(s) {
  return s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

function renderInline(s) {
  s = escapeHtml(s);
  // code
  s = s.replace(/`([^`]+)`/g, '<code>$1</code>');
  // bold
  s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  // italic
  s = s.replace(/(^|[^*])\*([^*\n]+)\*/g, '$1<em>$2</em>');
  // wikilink
  s = s.replace(/\[\[([^\]|]+)(\|([^\]]+))?\]\]/g, (m, slug, _p, alias) => {
    const id = slug.trim();
    const known = !!nodeById[id];
    const label = (alias || (nodeById[id] ? nodeById[id].title : id));
    return `<a class="wikilink${known && nodeById[id].type==='missing' ? ' missing' : (known ? '' : ' missing')}" data-slug="${escapeHtml(id)}">${escapeHtml(label)}</a>`;
  });
  // external link
  s = s.replace(/\[([^\]]+)\]\((https?:[^)]+)\)/g, '<a class="ext" href="$2" target="_blank" rel="noopener">$1</a>');
  return s;
}

function renderMarkdown(md) {
  const lines = md.split('\n');
  let html = '';
  let i = 0;
  let inList = false; let listTag = '';
  const closeList = () => { if (inList) { html += `</${listTag}>`; inList = false; } };

  while (i < lines.length) {
    const line = lines[i];
    if (/^\s*$/.test(line)) { closeList(); i++; continue; }
    let m;
    if ((m = line.match(/^(#{1,4})\s+(.+)$/))) {
      closeList();
      const lvl = m[1].length;
      html += `<h${lvl}>${renderInline(m[2])}</h${lvl}>`;
      i++; continue;
    }
    if ((m = line.match(/^\s*[-*]\s+(.+)$/))) {
      if (!inList || listTag !== 'ul') { closeList(); html += '<ul>'; inList = true; listTag = 'ul'; }
      html += `<li>${renderInline(m[1])}</li>`;
      i++; continue;
    }
    if ((m = line.match(/^\s*\d+\.\s+(.+)$/))) {
      if (!inList || listTag !== 'ol') { closeList(); html += '<ol>'; inList = true; listTag = 'ol'; }
      html += `<li>${renderInline(m[1])}</li>`;
      i++; continue;
    }
    if (line.startsWith('> ')) {
      closeList();
      html += `<blockquote>${renderInline(line.slice(2))}</blockquote>`;
      i++; continue;
    }
    if (line.trim() === '---') {
      closeList();
      html += '<hr>';
      i++; continue;
    }
    // paragraph: collect until blank
    closeList();
    let para = line;
    while (i + 1 < lines.length && lines[i+1].trim() !== '' && !/^(#{1,4}\s|[-*]\s|\d+\.\s|>\s|---)/.test(lines[i+1])) {
      i++;
      para += ' ' + lines[i];
    }
    html += `<p>${renderInline(para)}</p>`;
    i++;
  }
  closeList();
  return html;
}

// ------- doc panel -------
function renderDoc(id) {
  const n = nodeById[id];
  if (!n) return;
  const doc = document.getElementById('doc');
  const typeColor = TYPE_COLORS[n.type];
  const typeLabel = TYPE_LABELS[n.type] || n.type;
  const tagsHtml = (n.tags || []).map(t => `<span class="pill">#${escapeHtml(t)}</span>`).join('');

  // backlinks
  const backlinks = [];
  Object.keys(adjacency[id] || {}).length;
  adjacency[id].forEach(other => backlinks.push(other));
  const backHtml = backlinks.length === 0 ? '<em style="color:var(--muted)">없음</em>' :
    '<ul>' + backlinks.map(b => {
      const target = nodeById[b];
      return `<li><a class="wikilink${target.type==='missing'?' missing':''}" data-slug="${escapeHtml(b)}">${escapeHtml(target.title)}</a> <span style="color:var(--muted);font-size:11px">(${TYPE_LABELS[target.type]||target.type})</span></li>`;
    }).join('') + '</ul>';

  doc.innerHTML = `
    <h1>${escapeHtml(n.title)}</h1>
    <div class="meta">
      <span class="pill" style="background:${typeColor};color:#1e1e26;font-weight:600">${typeLabel}</span>
      ${tagsHtml}
      ${n.status ? `<span class="pill">status: ${escapeHtml(n.status)}</span>` : ''}
    </div>
    <div class="body">${renderMarkdown(n.body || '')}</div>
    <div class="backlinks">
      <h3>연결된 페이지</h3>
      ${backHtml}
    </div>
  `;
  doc.scrollTop = 0;

  doc.querySelectorAll('a.wikilink').forEach(a => {
    a.addEventListener('click', (ev) => {
      ev.preventDefault();
      const slug = a.getAttribute('data-slug');
      if (nodeById[slug]) selectNode(slug);
    });
  });
}

// ------- sliders -------
function bindSlider(id, valId, onChange) {
  const s = document.getElementById(id);
  const v = document.getElementById(valId);
  v.textContent = s.value;
  s.addEventListener('input', () => {
    v.textContent = s.value;
    onChange(parseFloat(s.value));
  });
}
bindSlider('s-node', 'v-node', (val) => {
  baseR = val;
  applyNodeRadii();
});
bindSlider('s-rep', 'v-rep', (val) => {
  params.repulsion = val;
  reheat();
});
bindSlider('s-link', 'v-link', (val) => {
  params.linkDist = val;
  reheat();
});

// initial: pick highest-degree node
const initial = [...DATA.nodes].sort((a,b) => degree[b.id] - degree[a.id])[0];
if (initial) setTimeout(() => selectNode(initial.id), 600);

// initial settle
reheat(7000);
</script>
</body>
</html>
"""


def main():
    p = argparse.ArgumentParser(description="LLM 위키 → 단일 HTML 지식그래프 빌더")
    p.add_argument("wiki_dir", nargs="?", default="wiki",
                   help="스캔할 위키 폴더 (기본 ./wiki)")
    p.add_argument("out", nargs="?", default=None,
                   help="출력 HTML 경로 (기본 <wiki_dir>의 부모/wiki_graph.html)")
    p.add_argument("--title", default="LLM Wiki Graph",
                   help="HTML 문서 제목 및 placeholder 헤더")
    args = p.parse_args()

    wiki_dir = Path(args.wiki_dir).resolve()
    if not wiki_dir.is_dir():
        print(f"error: wiki dir not found {wiki_dir}", file=sys.stderr)
        sys.exit(1)
    out_path = Path(args.out).resolve() if args.out else (wiki_dir.parent / "wiki_graph.html")
    nodes, edges = collect(wiki_dir)
    build_html(nodes, edges, out_path, args.title)


if __name__ == "__main__":
    main()
