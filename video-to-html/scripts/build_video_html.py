#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build a fixed-tone interactive HTML report from structured video content JSON."""
from __future__ import annotations

import argparse
import base64
import json
import re
from datetime import datetime
from html import escape
from pathlib import Path
from string import Template


CSS = r"""
:root {
  --bg: #ececec;
  --panel: #f7f7f4;
  --ink: #0c0c0c;
  --muted: #54546c;
  --line: #b8b8b8;
  --navy: #0c3c84;
  --green: #0c5424;
  --purple: #3c246c;
  --charcoal: #243c54;
  --cool: #cce4e4;
  --lilac: #cccce4;
  --mint: #cce4cc;
  --accent: var(--navy);
  --accent-2: var(--green);
  --shadow: 0 1px 0 rgba(12, 12, 12, 0.08), 0 18px 32px rgba(36, 60, 84, 0.08);
  --radius: 4px;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: "Pretendard", "Noto Sans KR", "Malgun Gothic", "Apple SD Gothic Neo", system-ui, -apple-system, sans-serif;
  background:
    linear-gradient(90deg, rgba(12, 60, 132, 0.05) 0 1px, transparent 1px 100%),
    linear-gradient(0deg, rgba(12, 12, 12, 0.04) 0 1px, transparent 1px 100%),
    var(--bg);
  background-size: 42px 42px;
  color: var(--ink);
  line-height: 1.58;
  letter-spacing: 0;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.page { width: min(1180px, calc(100% - 32px)); margin: 0 auto; padding: 32px 0 56px; }
.hero { display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(280px, 0.65fr); gap: 20px; align-items: stretch; margin-bottom: 18px; }
.hero-main, .hero-side, .panel { background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius); box-shadow: var(--shadow); }
.hero-main {
  position: relative; overflow: hidden; padding: 34px; min-height: 320px; display: flex; flex-direction: column; justify-content: space-between;
  background: linear-gradient(120deg, rgba(12, 60, 132, 0.12), transparent 42%), linear-gradient(0deg, rgba(255,255,255,0.52), rgba(255,255,255,0.52)), var(--panel);
  border-top: 8px solid var(--navy);
}
.hero-main::after {
  content: ""; position: absolute; right: 24px; top: 24px; width: 34%; height: 74%; pointer-events: none; opacity: 0.44;
  background: linear-gradient(135deg, transparent 0 18%, var(--navy) 18% 22%, transparent 22% 38%, var(--green) 38% 42%, transparent 42% 58%, var(--purple) 58% 62%, transparent 62% 78%, var(--charcoal) 78% 82%, transparent 82% 100%);
  clip-path: polygon(18% 0, 100% 0, 82% 100%, 0 100%);
}
.eyebrow { margin: 0 0 10px; color: var(--green); font-size: 13px; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase; }
h1 { position: relative; z-index: 1; margin: 0; max-width: 760px; font-size: clamp(30px, 5vw, 64px); line-height: 1.08; letter-spacing: 0; color: #0c0c0c; word-break: keep-all; }
.lead { position: relative; z-index: 1; max-width: 820px; margin: 18px 0 0; color: #242424; font-size: 17px; word-break: keep-all; }
.meta-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin-top: 24px; }
.meta-item { border: 1px solid var(--line); border-radius: 6px; padding: 10px 12px; background: #eeeeee; min-height: 68px; }
.meta-item:nth-child(1) { border-top: 4px solid var(--navy); }
.meta-item:nth-child(2) { border-top: 4px solid var(--green); }
.meta-item:nth-child(3) { border-top: 4px solid var(--purple); }
.meta-item:nth-child(4) { border-top: 4px solid var(--charcoal); }
.meta-item span { display: block; color: var(--muted); font-size: 12px; }
.meta-item strong { display: block; margin-top: 4px; font-size: 14px; color: var(--ink); word-break: keep-all; }
.hero-side { padding: 18px; display: flex; flex-direction: column; gap: 14px; border-top: 8px solid var(--charcoal); }
.thumb-wrap { border-radius: 6px; overflow: hidden; background: #e4e4e4; border: 1px solid var(--line); min-height: 180px; display: grid; place-items: center; }
.thumb-wrap img { width: 100%; height: auto; display: block; aspect-ratio: 4 / 3; object-fit: contain; background: #0c0c0c; }
.source-box { border-left: 5px solid var(--accent); padding: 10px 12px; background: #e0f0f0; border-radius: 4px; font-size: 14px; color: #243c54; }
.controls { position: sticky; top: 0; z-index: 10; margin: 0 0 18px; padding: 12px; background: rgba(236,236,236,0.94); backdrop-filter: blur(10px); border-bottom: 1px solid var(--line); }
.control-inner { width: min(1180px, calc(100% - 32px)); margin: 0 auto; display: grid; grid-template-columns: minmax(240px, 1fr) auto; gap: 12px; align-items: center; }
.search { display: flex; align-items: center; gap: 10px; padding: 0 12px; min-height: 44px; border: 1px solid var(--line); border-radius: 6px; background: #f7f7f4; }
input[type="search"] { width: 100%; border: 0; outline: 0; background: transparent; font-size: 15px; color: var(--ink); }
.filters { display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }
button { font: inherit; color: var(--ink); border: 1px solid var(--line); background: var(--panel); border-radius: 4px; min-height: 38px; padding: 8px 12px; cursor: pointer; }
button:hover, button:focus-visible { border-color: var(--accent); outline: none; }
button.active { color: #fff; border-color: var(--accent); background: var(--accent); }
.layout { display: grid; grid-template-columns: 220px minmax(0, 1fr); gap: 18px; align-items: start; }
.nav { position: sticky; top: 84px; padding: 14px; background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius); box-shadow: var(--shadow); border-top: 6px solid var(--charcoal); }
.nav-title { margin: 0 0 10px; color: var(--muted); font-size: 12px; font-weight: 700; }
.nav a { display: block; padding: 8px 10px; border-radius: 6px; color: #243c54; font-size: 14px; }
.nav a:hover { background: var(--cool); text-decoration: none; }
section { scroll-margin-top: 92px; }
.panel { padding: 22px; margin-bottom: 18px; position: relative; }
.panel:nth-of-type(4n + 1) { border-top: 6px solid var(--navy); }
.panel:nth-of-type(4n + 2) { border-top: 6px solid var(--green); }
.panel:nth-of-type(4n + 3) { border-top: 6px solid var(--purple); }
.panel:nth-of-type(4n + 4) { border-top: 6px solid var(--charcoal); }
h2 { margin: 0 0 14px; font-size: 25px; line-height: 1.28; letter-spacing: 0; color: #0c0c0c; }
h3 { margin: 0 0 8px; font-size: 17px; line-height: 1.35; letter-spacing: 0; }
p { margin: 0 0 12px; }
.two-col { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.topic-grid, .fact-list { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
.topic-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.fact, .topic-card { border: 1px solid var(--line); border-radius: 6px; padding: 14px; background: #f7f7f4; min-height: 130px; }
.fact:nth-child(1) { border-left: 6px solid var(--navy); }
.fact:nth-child(2) { border-left: 6px solid var(--green); }
.fact:nth-child(3) { border-left: 6px solid var(--purple); }
.topic-card:nth-child(4n + 1) { border-top: 5px solid var(--navy); }
.topic-card:nth-child(4n + 2) { border-top: 5px solid var(--green); }
.topic-card:nth-child(4n + 3) { border-top: 5px solid var(--purple); }
.topic-card:nth-child(4n + 4) { border-top: 5px solid var(--charcoal); }
.tag { display: inline-flex; margin-bottom: 8px; padding: 3px 8px; border-radius: 4px; background: var(--cool); color: var(--charcoal); font-size: 12px; font-weight: 700; }
.timecode { display: inline-flex; align-items: center; width: fit-content; margin: 0 0 8px; padding: 3px 7px; border: 1px solid var(--line); border-radius: 4px; background: #eeeeee; color: var(--charcoal); font-size: 12px; font-weight: 700; line-height: 1.2; }
a.timecode { cursor: pointer; }
a.timecode:hover, a.timecode:focus-visible { border-color: var(--accent); color: var(--accent); text-decoration: none; outline: none; }
.tag + .timecode { margin-left: 6px; }
.timecode + .timecode { margin-left: 6px; }
.timecode-row { display: block; margin-bottom: 6px; }
.qa-item > .timecode { margin: 12px 0 0 16px; }
.note { margin-top: 12px; padding: 12px; border-radius: 6px; background: #e0f0f0; border: 1px solid #b0b0b0; color: #243c54; font-size: 14px; }
table { width: 100%; border-collapse: collapse; overflow: hidden; border: 1px solid var(--line); border-radius: 6px; background: #f7f7f4; }
th, td { border-bottom: 1px solid var(--line); padding: 12px; text-align: left; vertical-align: top; font-size: 14px; }
th { background: #e0f0f0; color: #243c54; font-weight: 700; }
tr:last-child td { border-bottom: 0; }
.flow { display: grid; grid-template-columns: 260px minmax(0, 1fr); gap: 16px; }
.flow-list { display: flex; flex-direction: column; gap: 8px; }
.flow-btn { text-align: left; min-height: 50px; border-left: 4px solid var(--line); }
.flow-btn.active { border-left-color: var(--green); background: var(--mint); color: var(--ink); }
.flow-detail, .tab-panel { min-height: 190px; border: 1px solid var(--line); border-radius: 6px; padding: 18px; background: #f7f7f4; }
.flow-detail .stage { color: var(--green); font-weight: 700; margin-bottom: 6px; }
.tab-list { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }
.qa-item { border: 1px solid var(--line); border-radius: 6px; overflow: hidden; background: #f7f7f4; margin-bottom: 10px; }
.qa-toggle { width: 100%; border: 0; border-radius: 0; text-align: left; display: flex; justify-content: space-between; align-items: center; padding: 14px 16px; background: #f7f7f4; font-weight: 700; }
.qa-body { display: none; padding: 0 16px 16px; color: #242424; }
.qa-item.open .qa-body { display: block; }
.diagram { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin-top: 12px; }
.diagram-step { min-height: 110px; border: 1px solid var(--line); border-radius: 6px; padding: 12px; background: var(--cool); }
.diagram-step:nth-child(1) { border-top: 6px solid var(--navy); }
.diagram-step:nth-child(2) { background: var(--mint); border-top: 6px solid var(--green); }
.diagram-step:nth-child(3) { background: var(--lilac); border-top: 6px solid var(--purple); }
.diagram-step:nth-child(4) { background: #e4e4e4; border-top: 6px solid var(--charcoal); }
.diagram-step b { display: block; margin-bottom: 6px; font-size: 13px; color: #0c0c0c; }
.diagram-step p { margin: 0; font-size: 13px; color: #242424; }
.footer { margin-top: 18px; color: var(--muted); font-size: 13px; text-align: center; }
mark { background: #fff2a8; padding: 0 2px; border-radius: 3px; }
@media (max-width: 920px) {
  .hero, .layout, .flow, .two-col { grid-template-columns: 1fr; }
  .nav { position: static; }
  .control-inner { grid-template-columns: 1fr; }
  .filters { justify-content: flex-start; }
  .meta-grid, .fact-list, .topic-grid, .diagram { grid-template-columns: 1fr; }
}
@media (max-width: 560px) {
  .page, .control-inner { width: min(100% - 20px, 1180px); }
  .hero-main, .panel { padding: 18px; }
  .meta-grid { grid-template-columns: 1fr 1fr; }
  table { display: block; overflow-x: auto; white-space: normal; }
}
"""


HTML_TEMPLATE = Template("""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${title} | 인터랙티브 리포트</title>
  <style>${css}</style>
</head>
<body>
  <div class="controls" aria-label="리포트 탐색 도구">
    <div class="control-inner">
      <label class="search" for="searchInput">
        <span aria-hidden="true">⌕</span>
        <input id="searchInput" type="search" placeholder="검색어 입력">
      </label>
      <div class="filters" id="filters" aria-label="주제 필터"></div>
    </div>
  </div>
  <main class="page">
    <div class="hero">
      <header class="hero-main">
        <div>
          <p class="eyebrow">Video Interactive Report</p>
          <h1>${title}</h1>
          <p class="lead">${summary}</p>
        </div>
        <div class="meta-grid">${meta_items}</div>
      </header>
      <aside class="hero-side" aria-label="영상 출처">
        <div class="thumb-wrap">${thumbnail_html}</div>
        <div class="source-box"><strong>출처</strong><br>${source_html}</div>
        <div class="source-box">${source_note}</div>
      </aside>
    </div>
    <div class="layout">
      <nav class="nav" aria-label="섹션 이동">
        <p class="nav-title">섹션</p>
        ${nav_links}
      </nav>
      <div>
        ${sections_html}
        <section id="topics" class="panel">
          <h2>주제 카드</h2>
          <div id="resultCount" class="note" aria-live="polite"></div>
          <div id="topicGrid" class="topic-grid"></div>
        </section>
        <section id="flow" class="panel">
          <h2>논지 흐름</h2>
          <div class="flow">
            <div class="flow-list" id="flowList" role="tablist" aria-label="논지 단계"></div>
            <article class="flow-detail" id="flowDetail" tabindex="0"></article>
          </div>
        </section>
        <section id="compare" class="panel">
          <h2>비교</h2>
          <div class="tab-list" id="tabs" role="tablist" aria-label="비교 탭"></div>
          <div class="tab-panel" id="tabPanel" role="tabpanel"></div>
        </section>
        ${table_html}
        <section id="qa" class="panel">
          <h2>Q&amp;A</h2>
          <div id="qaList"></div>
        </section>
        <section id="takeaway" class="panel">
          <h2>정리</h2>
          ${takeaways}
        </section>
      </div>
    </div>
    <p class="footer">${footer}</p>
  </main>
  <script>
    const reportData = ${data_json};
    ${javascript}
  </script>
</body>
</html>
""")


JAVASCRIPT = r"""
let activeCategory = "all";
let activeFlow = 0;
let activeTab = reportData.tabs[0] ? reportData.tabs[0].id : "";
const filterRoot = document.getElementById("filters");
const topicGrid = document.getElementById("topicGrid");
const resultCount = document.getElementById("resultCount");
const searchInput = document.getElementById("searchInput");
const flowList = document.getElementById("flowList");
const flowDetail = document.getElementById("flowDetail");
const tabRoot = document.getElementById("tabs");
const tabPanel = document.getElementById("tabPanel");
const qaList = document.getElementById("qaList");

function escapeRegExp(value) { return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }
function timecodeValues(item) {
  if (!item) return [];
  let values = item.timecodes || item.timecode || item.timestamp;
  if (!values && item.start_sec !== undefined && item.start_sec !== null) {
    values = secondsToTimecode(item.start_sec);
  }
  if (!values) return [];
  return Array.isArray(values) ? values.filter(Boolean).map(String) : [String(values)];
}
function secondsToTimecode(value) {
  const total = Math.max(0, Math.floor(Number(value)));
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const seconds = total % 60;
  const mm = String(minutes).padStart(2, "0");
  const ss = String(seconds).padStart(2, "0");
  return hours ? String(hours) + ":" + mm + ":" + ss : mm + ":" + ss;
}
function youtubeLink(seconds) {
  return reportData.videoId ? "https://www.youtube.com/watch?v=" + reportData.videoId + "&t=" + seconds + "s" : "";
}
function timecodeToSeconds(value) {
  const parts = String(value).trim().split(":");
  if (!parts.length || !parts.every(function(part) { return /^\d+$/.test(part); })) return null;
  const numbers = parts.map(Number);
  if (numbers.length === 2) return numbers[0] * 60 + numbers[1];
  if (numbers.length === 3) return numbers[0] * 3600 + numbers[1] * 60 + numbers[2];
  return null;
}
function timecodeBadge(label, className) {
  const seconds = timecodeToSeconds(label);
  if (reportData.videoId && seconds !== null) {
    return '<a class="' + className + '" href="' + youtubeLink(seconds) + '" target="_blank" rel="noreferrer">영상 ' + label + '</a>';
  }
  return '<span class="' + className + '">영상 ' + label + '</span>';
}
function timecodeHtml(item, inline) {
  const values = timecodeValues(item);
  if (!values.length) return "";
  const className = inline ? "timecode" : "timecode timecode-row";
  return values.map(function(value) { return timecodeBadge(value, className); }).join("");
}
function highlight(text, query) {
  if (!query) return text;
  const pattern = new RegExp("(" + escapeRegExp(query) + ")", "gi");
  return String(text).replace(pattern, "<mark>$1</mark>");
}
function renderFilters() {
  const categories = [{ id: "all", label: "전체" }].concat(reportData.categories || []);
  filterRoot.innerHTML = categories.map(function(item) {
    return '<button type="button" class="' + (item.id === activeCategory ? "active" : "") + '" data-filter="' + item.id + '">' + item.label + '</button>';
  }).join("");
  filterRoot.querySelectorAll("button").forEach(function(button) {
    button.addEventListener("click", function() {
      activeCategory = button.dataset.filter;
      renderFilters();
      renderTopics();
    });
  });
}
function renderTopics() {
  const query = searchInput.value.trim();
  const lowerQuery = query.toLowerCase();
  const filtered = (reportData.topics || []).filter(function(item) {
    const categoryMatch = activeCategory === "all" || item.category === activeCategory;
    const haystack = [item.title, item.body, item.detail, timecodeValues(item).join(" ")].join(" ").toLowerCase();
    return categoryMatch && (!lowerQuery || haystack.includes(lowerQuery));
  });
  resultCount.textContent = filtered.length + "개 주제가 표시됨.";
  if (!filtered.length) {
    topicGrid.innerHTML = '<div class="note">검색 조건에 맞는 주제가 없음.</div>';
    return;
  }
  topicGrid.innerHTML = filtered.map(function(item) {
    const cat = (reportData.categories || []).find(function(c) { return c.id === item.category; });
    const label = cat ? cat.label : item.category;
    return '<article class="topic-card"><span class="tag">' + label + '</span>' + timecodeHtml(item, true) + '<h3>' + highlight(item.title, query) + '</h3><p>' + highlight(item.body, query) + '</p><p>' + highlight(item.detail || "", query) + '</p></article>';
  }).join("");
}
function renderFlow() {
  const flows = reportData.flows || [];
  flowList.innerHTML = flows.map(function(item, index) {
    const times = timecodeValues(item);
    const timeText = times.length ? '<br>영상 ' + times.join(" / ") : '';
    return '<button type="button" role="tab" aria-selected="' + (index === activeFlow) + '" class="flow-btn ' + (index === activeFlow ? "active" : "") + '" data-flow="' + index + '">' + item.stage + '<br>' + item.title + timeText + '</button>';
  }).join("");
  flowList.querySelectorAll("button").forEach(function(button) {
    button.addEventListener("click", function() {
      activeFlow = Number(button.dataset.flow);
      renderFlow();
    });
  });
  const item = flows[activeFlow];
  flowDetail.innerHTML = item ? timecodeHtml(item, false) + '<div class="stage">' + item.stage + '</div><h3>' + item.title + '</h3><p>' + item.text + '</p><p><strong>전개상 역할</strong> ' + (item.point || "") + '</p>' : "";
}
function renderTabs() {
  const tabs = reportData.tabs || [];
  tabRoot.innerHTML = tabs.map(function(item) {
    return '<button type="button" role="tab" aria-selected="' + (item.id === activeTab) + '" class="' + (item.id === activeTab ? "active" : "") + '" data-tab="' + item.id + '">' + item.label + '</button>';
  }).join("");
  tabRoot.querySelectorAll("button").forEach(function(button) {
    button.addEventListener("click", function() {
      activeTab = button.dataset.tab;
      renderTabs();
    });
  });
  const item = tabs.find(function(tab) { return tab.id === activeTab; });
  tabPanel.innerHTML = item ? timecodeHtml(item, false) + '<h3>' + item.title + '</h3><p>' + item.body + '</p><ul>' + (item.list || []).map(function(entry) {
    if (typeof entry === "object") return '<li>' + timecodeHtml(entry, true) + ' ' + (entry.text || entry.body || "") + '</li>';
    return '<li>' + entry + '</li>';
  }).join("") + '</ul>' : "";
}
function renderQa() {
  qaList.innerHTML = (reportData.questions || []).map(function(item, index) {
    return '<article class="qa-item ' + (index === 0 ? "open" : "") + '">' + timecodeHtml(item, false) + '<button class="qa-toggle" type="button" aria-expanded="' + (index === 0) + '" data-qa="' + index + '"><span>' + item.q + '</span><span aria-hidden="true">' + (index === 0 ? "−" : "+") + '</span></button><div class="qa-body">' + item.a + '</div></article>';
  }).join("");
  qaList.querySelectorAll(".qa-toggle").forEach(function(button) {
    button.addEventListener("click", function() {
      const item = button.closest(".qa-item");
      const isOpen = item.classList.toggle("open");
      button.setAttribute("aria-expanded", String(isOpen));
      button.lastElementChild.textContent = isOpen ? "−" : "+";
    });
  });
}
searchInput.addEventListener("input", renderTopics);
renderFilters();
renderTopics();
renderFlow();
renderTabs();
renderQa();
"""


def html_paragraphs(items: list[str]) -> str:
    return "\n".join(html_paragraph(item) for item in items)


def get_text(item: object, key: str = "text") -> str:
    if isinstance(item, dict):
        return str(item.get(key) or item.get("body") or "")
    return str(item)


def timecode_values(item: object) -> list[str]:
    if not isinstance(item, dict):
        return []
    values = item.get("timecodes") or item.get("timecode") or item.get("timestamp")
    if values is None and item.get("start_sec") is not None:
        values = seconds_to_timecode(item["start_sec"])
    if values is None:
        return []
    if isinstance(values, (list, tuple)):
        return [str(value) for value in values if value not in (None, "")]
    return [str(values)]


def seconds_to_timecode(value: object) -> str:
    total = max(0, int(float(value)))
    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


_VIDEO_ID: str | None = None

YOUTUBE_ID_RE = re.compile(r"(?:v=|youtu\.be/|/embed/|/shorts/|/live/)([A-Za-z0-9_-]{11})")


def extract_video_id(url: object) -> str | None:
    if not url:
        return None
    match = YOUTUBE_ID_RE.search(str(url))
    return match.group(1) if match else None


def timecode_to_seconds(value: object) -> int | None:
    parts = str(value).strip().split(":")
    if not parts or not all(part.isdigit() for part in parts):
        return None
    numbers = [int(part) for part in parts]
    if len(numbers) == 2:
        return numbers[0] * 60 + numbers[1]
    if len(numbers) == 3:
        return numbers[0] * 3600 + numbers[1] * 60 + numbers[2]
    return None


def timecode_badge(label: str, class_name: str) -> str:
    seconds = timecode_to_seconds(label)
    if _VIDEO_ID and seconds is not None:
        href = f"https://www.youtube.com/watch?v={_VIDEO_ID}&t={seconds}s"
        return f'<a class="{class_name}" href="{escape(href)}" target="_blank" rel="noreferrer">영상 {escape(label)}</a>'
    return f'<span class="{class_name}">영상 {escape(label)}</span>'


def timecode_html(item: object, *, inline: bool = False) -> str:
    values = timecode_values(item)
    if not values:
        return ""
    class_name = "timecode" if inline else "timecode timecode-row"
    return "".join(timecode_badge(value, class_name) for value in values)


def html_paragraph(item: object) -> str:
    text = get_text(item)
    return f"<p>{timecode_html(item)}{escape(text)}</p>"


def table_from_rows(title: str, headers: list[str], rows: list[list[str] | dict]) -> str:
    head = "".join(f"<th>{escape(str(h))}</th>" for h in headers)
    rendered_rows = []
    for row in rows:
        if isinstance(row, dict):
            cells = row.get("cells") or row.get("row") or []
            row_time = timecode_html(row)
            rendered_rows.append(
                "<tr>" + "".join(
                    f"<td>{row_time if index == 0 else ''}{escape(str(cell))}</td>"
                    for index, cell in enumerate(cells)
                ) + "</tr>"
            )
        else:
            rendered_rows.append("<tr>" + "".join(f"<td>{escape(str(cell))}</td>" for cell in row) + "</tr>")
    body = "\n".join(rendered_rows)
    return f'<section class="panel"><h2>{escape(title)}</h2><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></section>'


def embed_image(path: Path) -> str:
    suffix = path.suffix.lower()
    mime = "image/png" if suffix == ".png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def safe_filename(name: str, limit: int = 120) -> str:
    name = re.sub(r'[\\/:*?"<>|]', "_", name)
    name = re.sub(r"\s+", " ", name).strip().rstrip(".")
    return (name or "video_report")[:limit]


def default_output_path(content_json: Path, data: dict, out: Path | None) -> Path:
    title = safe_filename(str(data.get("title") or content_json.stem))
    default_name = f"{datetime.now().strftime('%y%m%d')}_{title}.html"

    if out is None:
        return content_json.parent / default_name

    if out.exists() and out.is_dir():
        return out / default_name

    if out.suffix.lower() != ".html":
        out.mkdir(parents=True, exist_ok=True)
        return out / default_name

    return out


def build_html(data: dict, thumbnail_file: Path | None = None) -> str:
    title = str(data.get("title") or "영상 인터랙티브 리포트")
    metadata = data.get("metadata") or {}
    meta_order = data.get("meta_order") or ["channel", "upload_date", "duration", "subtitle"]
    meta_labels = {
        "channel": "채널",
        "upload_date": "업로드",
        "duration": "길이",
        "subtitle": "자막",
        "source": "출처",
    }
    meta_items = []
    for key in meta_order[:4]:
        value = metadata.get(key, "")
        meta_items.append(f'<div class="meta-item"><span>{escape(meta_labels.get(key, key))}</span><strong>{escape(str(value))}</strong></div>')

    thumb = ""
    if thumbnail_file:
        thumb = embed_image(thumbnail_file)
    elif data.get("thumbnail_data_uri"):
        thumb = str(data["thumbnail_data_uri"])
    elif data.get("thumbnail_url"):
        thumb = str(data["thumbnail_url"])
    thumbnail_html = f'<img src="{escape(thumb)}" alt="{escape(title)} 썸네일">' if thumb else "<span>Video Report</span>"

    source_url = metadata.get("url") or data.get("url") or ""
    source_html = f'<a href="{escape(source_url)}" target="_blank" rel="noreferrer">{escape(source_url)}</a>' if source_url else "원본 자료 기반"

    global _VIDEO_ID
    _VIDEO_ID = extract_video_id(source_url)

    nav_links = []
    sections_html = []
    for index, section in enumerate(data.get("sections", []), start=1):
        sid = section.get("id") or f"section-{index}"
        heading = section.get("title") or f"섹션 {index}"
        nav_links.append(f'<a href="#{escape(sid)}">{escape(heading)}</a>')
        blocks = []
        if timecode_html(section):
            blocks.append(timecode_html(section))
        if section.get("paragraphs"):
            blocks.append(html_paragraphs(section["paragraphs"]))
        if section.get("diagram"):
            steps = "".join(f'<div class="diagram-step">{timecode_html(step)}<b>{escape(step.get("title", ""))}</b><p>{escape(step.get("body", ""))}</p></div>' for step in section["diagram"])
            blocks.append(f'<div class="diagram">{steps}</div>')
        if section.get("facts"):
            facts = "".join(f'<article class="fact">{timecode_html(item)}<b>{escape(item.get("title", ""))}</b><p>{escape(item.get("body", ""))}</p></article>' for item in section["facts"])
            blocks.append(f'<div class="fact-list">{facts}</div>')
        sections_html.append(f'<section id="{escape(sid)}" class="panel"><h2>{escape(heading)}</h2>{"".join(blocks)}</section>')

    nav_links.extend([
        '<a href="#topics">주제 카드</a>',
        '<a href="#flow">논지 흐름</a>',
        '<a href="#compare">비교</a>',
        '<a href="#qa">Q&amp;A</a>',
        '<a href="#takeaway">정리</a>',
    ])

    table_html = ""
    if data.get("table"):
        table = data["table"]
        table_html = table_from_rows(table.get("title", "표"), table.get("headers", []), table.get("rows", []))

    return HTML_TEMPLATE.substitute(
        title=escape(title),
        summary=escape(str(data.get("summary") or "")),
        css=CSS,
        meta_items="".join(meta_items),
        thumbnail_html=thumbnail_html,
        source_html=source_html,
        source_note=escape(str(data.get("source_note") or "자막과 메타데이터를 바탕으로 작성한 리포트임.")),
        nav_links="\n".join(nav_links),
        sections_html="\n".join(sections_html),
        table_html=table_html,
        takeaways=html_paragraphs(data.get("takeaways", [])),
        footer=escape(str(data.get("footer") or "정적 HTML 리포트임.")),
        data_json=json.dumps(
            {
                "videoId": _VIDEO_ID,
                "categories": data.get("categories", []),
                "topics": data.get("topics", []),
                "flows": data.get("flows", []),
                "tabs": data.get("tabs", []),
                "questions": data.get("questions", []),
            },
            ensure_ascii=False,
        ),
        javascript=JAVASCRIPT,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("content_json", type=Path)
    parser.add_argument("--out", type=Path, default=None, help="Output .html path or output directory. Defaults to YYMMDD_title.html next to content_json.")
    parser.add_argument("--thumbnail-file", type=Path, default=None)
    args = parser.parse_args()

    data = json.loads(args.content_json.read_text(encoding="utf-8"))
    html = build_html(data, args.thumbnail_file)
    output_path = default_output_path(args.content_json, data, args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"OK: {output_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
