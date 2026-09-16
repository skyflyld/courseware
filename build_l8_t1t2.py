#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_l8_t1t2.py — Lektion 8 · Text 1 & Text 2 + Schaubild beschreiben 课件生成器
输入: l8t1t2-data.json + l8t1t2-texts.json
输出: lektion8-t1t2-schaubild.html (单文件, 自包含 CSS/JS, 零外部请求)
复用 build_l8_berufe.py 的 CSS / JS 资产（设计令牌 + 对比度修复 + 投影挡位）
数据纪律: 德文一律取 JSON 原值，不改写、不补造；数字与 JSON 一致。
"""
import json
import os
import random
import subprocess

import build_l8_berufe as base

DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(DIR, 'l8t1t2-data.json')
TEXTS_FILE = os.path.join(DIR, 'l8t1t2-texts.json')
OUT = os.path.join(DIR, 'lektion8-t1t2-schaubild.html')

h = base.h
esc_attr = base.esc_attr
tools_buttons = base.tools_buttons

CSS_EXTRA = '''
  /* ===== Schaubild / Text 1 & 2 专用件 ===== */
  .chart-card { background: #fff; border: 1px solid #e3e6eb; border-radius: 14px; padding: 16px; margin: 12px 0; }
  .chart-title { font-size: var(--fs-word); font-weight: 700; margin: 0 0 4px; }
  .chart-sub, .chart-quelle { font-size: var(--fs-cap); color: #5f6672; margin: 0 0 8px; }
  .chart-group { margin-top: 16px; }
  .chart-group h4 { font-size: var(--fs-sm); font-weight: 700; margin: 0 0 8px; color: #1a3d6d; }
  .chart-row { display: flex; align-items: center; gap: 8px; margin: 6px 0; }
  .chart-lbl { flex: 0 0 38%; font-size: var(--fs-cap); line-height: 1.35; overflow-wrap: break-word; }
  .chart-track { flex: 1; background: #eef1f5; border-radius: 8px; min-height: 26px; }
  .chart-bar { display: flex; align-items: center; justify-content: flex-end; height: 26px;
    border-radius: 8px; color: #fff; font-size: var(--fs-cap); font-weight: 700; padding-right: 8px;
    cursor: pointer; min-width: 68px; }
  .chart-bar.m { background: #1a73e8; }
  .chart-bar.f { background: #6a1b9a; }
  .chart-bar.sel { outline: 3px solid #146c2e; outline-offset: 2px; }
  .chart-detail { margin-top: 12px; min-height: 44px; background: #f7f8fa; border-left: 4px solid #1a73e8;
    border-radius: 8px; padding: 8px 12px; font-size: var(--fs-sm); }
  .rm-tabs { display: flex; flex-wrap: wrap; gap: 4px; margin: 8px 0 12px; }
  .rm-item { background: #fff; border: 1px solid #e3e6eb; border-radius: 8px; padding: 8px 12px; margin: 6px 0; }
  .rm-de { font-size: var(--fs-body); font-weight: 600; }
  .rm-cn { color: #3c4450; }
  .rm-tip { font-size: var(--fs-cap); color: #146c2e; }
  .qz-item { background: #fff; border: 1px solid #e3e6eb; border-radius: 8px; padding: 8px 12px; margin: 8px 0; }
  .qz-q { font-size: var(--fs-body); font-weight: 600; margin: 0 0 6px; }
  .qz-opts { display: flex; flex-wrap: wrap; gap: 8px; }
  .qz-opt { border: 1px solid #c9ced6; border-radius: 8px; padding: 6px 12px; font-size: var(--fs-sm);
    cursor: pointer; background: #fff; min-height: 34px; display: inline-flex; align-items: center; }
  .qz-opt.sel { border-color: #1a73e8; background: #e8f0fe; font-weight: 700; }
  .qz-opt.ok { border-color: #146c2e; background: #e6f4ea; }
  .qz-opt.bad { border-color: #b3261e; background: #fdecea; }
  .qz-item .src { display: inline-block; margin-top: 6px; }
  .tb { width: 100%; border-collapse: collapse; font-size: var(--fs-sm); margin: 8px 0; }
  .tb th, .tb td { border: 1px solid #e3e6eb; padding: 6px 8px; text-align: left; vertical-align: top; }
  .tb th { background: #f2f4f7; font-weight: 700; }
  .stp { border-left: 3px solid #1a73e8; padding-left: 12px; margin: 10px 0; }
  .stp-n { display: inline-block; background: #1a73e8; color: #fff; border-radius: 50%; width: 22px; height: 22px;
    line-height: 22px; text-align: center; font-size: var(--fs-cap); font-weight: 700; margin-right: 6px; }
  .stp-fn { font-weight: 700; font-size: var(--fs-sm); }
  .dt-text { background: #fff; border: 1px solid #e3e6eb; border-radius: 8px; padding: 12px; font-size: var(--fs-body); }
  .dt-seg { cursor: pointer; border-bottom: 2px dotted #9aa3ad; }
  .dt-seg.marked { background: #fdecea; border-bottom-color: #b3261e; font-weight: 700; }
  .dt-seg.hit { background: #e6f4ea; border-bottom-color: #146c2e; }
  .l2-chip { display: inline-flex; align-items: center; gap: 8px; border: 1px solid #c9ced6; border-radius: 8px;
    padding: 8px 12px; margin: 6px; background: #fff; font-size: var(--fs-sm); cursor: pointer; min-height: 34px; }
  .l2-chip.ranked { border-color: #1a73e8; background: #e8f0fe; }
  .l2-num { display: inline-block; width: 22px; height: 22px; line-height: 22px; text-align: center;
    border-radius: 50%; background: #1a73e8; color: #fff; font-size: var(--fs-cap); font-weight: 700; }
  .zone { border: 1px solid #d7dbe2; border-radius: 8px; padding: 12px; margin: 10px 0; background: #fbfcfd; }
  .zone-h { font-size: var(--fs-body); font-weight: 700; margin: 0 0 6px; }
  @media (max-width: 620px) {
    .chart-lbl { flex: 0 0 46%; }
    .chart-bar { min-width: 56px; }
  }
  .vc-mini { background: #fff; border: 1px solid #e3e6eb; border-radius: 8px; padding: 8px 10px;
    font-size: var(--fs-sm); }
  .anat { background: #fff; border: 1px solid #e3e6eb; border-radius: 12px; padding: 12px; margin: 12px 0; }
  .anat svg { width: 100%; height: auto; display: block; }
  .anat-lbl { font: 700 13px system-ui, sans-serif; fill: #17427f; }
  .anat-cap { font: 12px system-ui, sans-serif; fill: #5f6672; }
'''

JS_EXTRA = '''
/* ===== 图表高亮 ===== */
function chHi(el){
  document.querySelectorAll('#chart .chart-bar').forEach(function(b){ b.classList.remove('sel'); });
  el.classList.add('sel');
  const d = document.getElementById('chartDetail');
  if (d) d.innerHTML = el.dataset.detail || '';
}
/* ===== 通用选择题 ===== */
function qzPick(el){
  const item = el.closest('.qz-item');
  item.querySelectorAll('.qz-opt').forEach(function(o){ o.classList.remove('sel', 'ok', 'bad'); });
  el.classList.add('sel');
}
function qzCheck(boxId){
  const box = document.getElementById(boxId);
  if (!box) return;
  let ok = 0, tot = 0;
  box.querySelectorAll('.qz-item').forEach(function(it){
    tot++;
    const opts = Array.prototype.slice.call(it.querySelectorAll('.qz-opt'));
    const sel = opts.findIndex(function(o){ return o.classList.contains('sel'); });
    const ans = parseInt(it.dataset.a, 10);
    opts.forEach(function(o, k){ o.classList.remove('ok', 'bad'); if (k === ans) o.classList.add('ok'); });
    if (sel === ans) ok++; else if (sel >= 0) opts[sel].classList.add('bad');
  });
  const res = document.getElementById(boxId + '-res');
  if (res){ res.textContent = '正确 ' + ok + ' / ' + tot; res.className = 'kw-result'; }
}
function qzClear(boxId){
  const box = document.getElementById(boxId);
  if (!box) return;
  box.querySelectorAll('.qz-opt').forEach(function(o){ o.classList.remove('sel', 'ok', 'bad'); });
  const res = document.getElementById(boxId + '-res');
  if (res) res.textContent = '';
}
/* ===== 通用词库填空（T1/T2 课文） ===== */
let clzSel = null;
function clzClick(el){
  if (el.classList.contains('filled')){
    el.textContent = el.dataset.ph;
    el.classList.remove('filled', 'ok', 'bad', 'sel');
    clzSel = null;
    return;
  }
  const box = el.closest('.clz-box');
  box.querySelectorAll('.cloze-blank').forEach(function(b){ b.classList.remove('sel'); });
  clzSel = el;
  el.classList.add('sel');
}
function clzFill(id, chip){
  const box = document.getElementById(id);
  if (!clzSel){
    const r = document.getElementById(id + '-res');
    if (r) r.textContent = '请先点句子里的空位，再点词库里的词';
    return;
  }
  clzSel.textContent = chip.textContent;
  clzSel.classList.add('filled');
  clzSel.classList.remove('sel', 'ok', 'bad');
  clzSel = null;
}
function clzCheck(id){
  const box = document.getElementById(id);
  let ok = 0, tot = 0, empty = 0;
  box.querySelectorAll('.cloze-blank').forEach(function(b){
    tot++;
    if (!b.classList.contains('filled')){ empty++; b.classList.remove('ok', 'bad'); return; }
    const alts = (b.dataset.alt || '').split('|').filter(Boolean).map(norm);
    const good = norm(b.textContent) === norm(b.dataset.ans) || alts.indexOf(norm(b.textContent)) >= 0;
    b.classList.remove('ok', 'bad');
    b.classList.add(good ? 'ok' : 'bad');
    if (good) ok++;
  });
  const r = document.getElementById(id + '-res');
  if (r) r.textContent = '正确 ' + ok + ' / ' + tot + ' 空' + (empty ? '（还有 ' + empty + ' 空未填）' : '');
}
function clzReveal(id){
  const box = document.getElementById(id);
  box.querySelectorAll('.cloze-blank').forEach(function(b){
    b.textContent = b.dataset.ans;
    b.classList.add('filled', 'ok');
    b.classList.remove('bad', 'sel');
  });
  const r = document.getElementById(id + '-res');
  if (r) r.textContent = '已显示参考答案（教师用）';
  clzSel = null;
}
function clzClear(id){
  const box = document.getElementById(id);
  box.querySelectorAll('.cloze-blank').forEach(function(b){
    b.textContent = b.dataset.ph;
    b.classList.remove('filled', 'ok', 'bad', 'sel');
  });
  const r = document.getElementById(id + '-res');
  if (r) r.textContent = '';
  clzSel = null;
}
/* ===== 找错侦探 ===== */
function dtMark(el){
  el.classList.toggle('marked');
  el.classList.remove('hit');
}
function dtCheck(id){
  const box = document.getElementById(id);
  let hit = 0, miss = 0, wrong = 0, tot = 0;
  box.querySelectorAll('.dt-seg[data-err="1"]').forEach(function(s){ tot++; });
  box.querySelectorAll('.dt-seg').forEach(function(s){
    const isErr = s.dataset.err === '1';
    const marked = s.classList.contains('marked');
    if (isErr && marked){ s.classList.add('hit'); hit++; }
    if (isErr && !marked) miss++;
    if (!isErr && marked) wrong++;
  });
  const r = document.getElementById(id + '-res');
  if (r) r.textContent = '找到 ' + hit + ' / ' + tot + ' 处' + (miss ? '，漏掉 ' + miss + ' 处' : '') + (wrong ? '，误标 ' + wrong + ' 处' : '');
}
function dtReveal(id){
  const box = document.getElementById(id);
  box.querySelectorAll('.dt-seg[data-err="1"]').forEach(function(s){ s.classList.add('hit', 'marked'); });
  const r = document.getElementById(id + '-res');
  if (r) r.textContent = '已标出全部错误（教师用）';
}
function dtClear(id){
  const box = document.getElementById(id);
  box.querySelectorAll('.dt-seg').forEach(function(s){ s.classList.remove('marked', 'hit'); });
  const r = document.getElementById(id + '-res');
  if (r) r.textContent = '';
}
/* ===== 排序（阶梯第 2 关） ===== */
function l2Seq(el, key){
  const box = document.getElementById(key);
  const cur = parseInt(el.dataset.seq || '0', 10);
  const used = Array.prototype.slice.call(box.querySelectorAll('.l2-chip'))
    .map(function(c){ return parseInt(c.dataset.seq || '0', 10); });
  if (cur > 0){ el.dataset.seq = '0'; el.querySelector('.l2-num').textContent = ''; el.classList.remove('ranked'); }
  else {
    const nxt = Math.max.apply(null, used.concat([0])) + 1;
    el.dataset.seq = String(nxt);
    el.querySelector('.l2-num').textContent = String(nxt);
    el.classList.add('ranked');
  }
  const res = document.getElementById(key + '-res');
  if (res) res.textContent = '';
}
function l2Check(key){
  const box = document.getElementById(key);
  let ok = 0, tot = 0;
  box.querySelectorAll('.l2-chip').forEach(function(c, i){
    tot++;
    const want = i + 1;
    const got = parseInt(c.dataset.seq || '0', 10);
    const right = got === want;
    c.classList.remove('ok', 'bad');
    c.classList.add(right ? 'ok' : 'bad');
    if (right && got === parseInt(c.dataset.rank, 10)) ok++;
  });
  const res = document.getElementById(key + '-res');
  if (res) res.textContent = '顺序正确 ' + ok + ' / ' + tot;
}
function l2Reset(key){
  const box = document.getElementById(key);
  box.querySelectorAll('.l2-chip').forEach(function(c){
    c.dataset.seq = '0'; c.classList.remove('ranked', 'ok', 'bad');
    c.querySelector('.l2-num').textContent = '';
  });
  const res = document.getElementById(key + '-res');
  if (res) res.textContent = '';
}
'''


# ---------------------------------------------------------------- 1 home
def sec_home(d):
    m = d['meta']
    objs = ''.join('<li>%s</li>' % h(o) for o in m['objectives'])
    flow = ''.join('<tr><td class="fl-t">%s</td></tr>' % h(f) for f in m['flow'])
    cards = [
        ('chart', '📊 Schaubild', '真实图表：Top-5 职业培训，男女各五'),
        ('redemittel', '🧭 句型库', '四类 Redemittel：排名 / 比例 / 比较 / 结论'),
        ('satzbau', '🔧 变形金刚', '同一组数据，四种说法（语序拼装）'),
        ('ladder', '🪜 四层阶梯', '读数字 → 排序 → 比较 → 评论'),
        ('vocab', '🃏 词汇卡', '26 张图表描述词卡（点卡翻面）'),
        ('t1', '📖 Text 1', '统计文：挖空 + 段落功能 + 句型标注'),
        ('t2a', '👤 Text 2a', 'Erika：人物文结构与转折点'),
        ('t2b', '👤 Text 2b', 'Simon：人物文与强项自述'),
        ('traum', '📈 调查改写', '把 Traumberufe 调查改写成图表语言'),
        ('detect', '🕵️ 找错侦探', '三段描述，找出数字错 / 比较错 / 句型错'),
        ('essay', '🎯 作文卡', '专四图表作文四段式骨架 + 填空'),
    ]
    grid = ''.join('<div class="text-card home-card" onclick="switchSection(\'%s\')"><h3>%s</h3><p>%s</p></div>'
                   % (sid, h(t), h(p)) for sid, t, p in cards)
    return f'''    <section id="home" class="active">
      <div class="hero">
        <h1>Schaubilder beschreiben</h1>
        <p class="sub">{h(m['subtitle'])}</p>
        <p class="meta">{h(m['source'])}</p>
      </div>
      <div class="highlight-box">🎬 课堂用法：先看图说数（不写句子），再上句型库，最后拼句子。顶部导航切节，右下 A± 投影放大。习题右上角标来源：教材原句 / 图表数据 / 句型示例。</div>
      <div class="home-grid">{grid}</div>
      <div class="obj-box"><strong>学习目标 Lernziele：</strong><ul>{objs}</ul></div>
      <div class="text-card" style="margin-top:12px">
        <h3>⏱️ 课堂流程（45 分钟建议）</h3>
        <table class="flow-table">{flow}</table>
      </div>
      <div class="text-card" style="margin-top:12px">
        <h3>⚠️ 素材边界（先说清楚）</h3>
        <p class="zh-hint">Text 1 / Text 2 的挖空文本与词库、教材答案句、图表数字，全部按素材逐字转录；Text 2 的两段人物文原题未给词库，此处词库为课堂便利所加，答案按上下文推定；Traumberufe 调查只给绝对数，<b>故意不算百分比</b>（分母不明）。教材课文全文页未提供，若拿到原文页可一键替换数据层。</p>
      </div>
    </section>
'''


# ---------------------------------------------------------------- 2 chart
def sec_chart(d):
    c = d['chart']
    maxv = max(b['value'] for g in c['groups'] for b in g['bars'])
    blocks = []
    for g in c['groups']:
        rows = []
        for i, b in enumerate(g['bars']):
            w = round(b['value'] / maxv * 100, 1)
            detail = ('<b>%s</b><br>Platz %d · %s Ausbildungsanfänger · 占本榜榜首 %s%% '
                      '<span class="src">Quelle: Bundesinstitut für Berufsbildung</span>'
                      % (h(b['name']), i + 1, format(b['value'], ',d').replace(',', '.'),
                         round(b['value'] / g['bars'][0]['value'] * 100, 1)))
            rows.append(
                f'<div class="chart-row"><div class="chart-lbl" lang="de">{h(b["name"])}</div>'
                f'<div class="chart-track"><div class="chart-bar {g["key"]}" style="width:{w}%" '
                f'data-detail="{esc_attr(detail)}" onclick="chHi(this)">{format(b["value"], ",d").replace(",", ".")}</div></div></div>')
        blocks.append(f'<div class="chart-group"><h4>{h(g["label"])}</h4>{"".join(rows)}</div>')
    facts = ''.join('<div class="rm-item"><div class="rm-de" lang="de">%s</div><div class="rm-cn">%s</div></div>'
                    % (h(f['de']), h(f['cn'])) for f in c['facts'])
    qz = ''.join(
        '<div class="qz-item" data-a="%d"><p class="qz-q">%d. %s</p><div class="qz-opts">%s</div>'
        '<span class="src">%s</span></div>'
        % (q['a'], i + 1, h(q['q']),
           ''.join('<span class="qz-opt" onclick="qzPick(this)" lang="de">%s</span>' % h(o) for o in q['opts']),
           h(q['src']))
        for i, q in enumerate(c['quiz']))
    btns = tools_buttons(['<button class="btn" onclick="qzCheck(\'qz-chart\')">✓ 检查</button>',
                          '<button class="btn ghost" onclick="qzClear(\'qz-chart\')">↺ 清空</button>',
                          '<span id="qz-chart-res" class="kw-result"></span>'])
    return f'''    <section id="chart">
      <h2 class="section-title"><span class="num">1</span> 📊 Schaubild lesen · 先读懂图</h2>
      <p class="zh-hint">先别写句子。让学生只看图说三件事：榜首是谁、两榜的交集是谁、哪一栏的榜首更高。点条形看该条数据明细。</p>
      <div class="chart-card">
        <p class="chart-title" lang="de">{h(c['title'])}</p>
        <p class="chart-sub" lang="de">{h(c['sub'])}</p>
        <p class="chart-sub"><b>{h(c.get('legend', ''))}</b>　<b>单位</b>：{h(c['unit'])}</p>
        {''.join(blocks)}
        <div class="chart-detail" id="chartDetail">点任一条形，这里显示该职位的名次与人数。</div>
        <p class="chart-quelle" lang="de">{h(c['quelle'])}</p>
      </div>
      <div class="anat">
        <p class="zh-hint"><b>图的解剖图</b>：写作文前先在图里指位置说清楚名称（德语专四阅卷喜欢看你点出 Achse / Quelle）。</p>
        <svg viewBox="0 0 640 300" role="img" aria-label="Balkendiagramm: Aufbau">
          <line x1="70" y1="40" x2="70" y2="240" stroke="#17427f" stroke-width="2"/>
          <line x1="70" y1="240" x2="600" y2="240" stroke="#17427f" stroke-width="2"/>
          <rect x="110" y="120" width="54" height="120" fill="#1a73e8"/>
          <rect x="190" y="170" width="54" height="70" fill="#1a73e8"/>
          <rect x="270" y="200" width="54" height="40" fill="#1a73e8"/>
          <rect x="350" y="150" width="54" height="90" fill="#6a1b9a"/>
          <rect x="430" y="190" width="54" height="50" fill="#6a1b9a"/>
          <rect x="510" y="215" width="54" height="25" fill="#6a1b9a"/>
          <text class="anat-lbl" x="80" y="30">Titel / Überschrift</text>
          <text class="anat-lbl" x="12" y="150">y-Achse</text>
          <text class="anat-cap" x="12" y="168">Anzahl / Prozent</text>
          <text class="anat-lbl" x="330" y="268">x-Achse</text>
          <text class="anat-cap" x="405" y="268">Berufe / Kategorien</text>
          <text class="anat-lbl" x="110" y="112">Balken</text>
          <text class="anat-lbl" x="350" y="142">zweite Gruppe</text>
          <text class="anat-cap" x="70" y="292">Quelle: Bundesinstitut für Berufsbildung</text>
          <line x1="70" y1="245" x2="70" y2="255" stroke="#5f6672"/>
          <line x1="600" y1="245" x2="600" y2="255" stroke="#5f6672"/>
        </svg>
      </div>
      <div class="text-card">
        <h3>🔎 读图结论（可直接当课堂口述素材）</h3>
        {facts}
      </div>
      <div class="text-card">
        <h3>✅ 快问快答（8 题）</h3>
        <div class="qz-box" id="qz-chart">{qz}</div>
        {btns}
      </div>
    </section>
'''


# ---------------------------------------------------------------- 3 redemittel
def sec_redemittel(d):
    tabs, panels = [], []
    for i, g in enumerate(d['redemittel']):
        cls = 'person-btn active' if i == 0 else 'person-btn'
        tabs.append('<button class="%s" onclick="switchVocabTab(\'rm-%s\',this)">%s</button>' % (cls, g['key'], h(g['cat'])))
        items = ''.join(
            '<div class="rm-item"><div class="rm-de" lang="de">%s</div><div class="rm-cn">%s</div>%s</div>'
            % (h(it['de']), h(it['cn']),
               ('<div class="rm-tip">💡 %s</div>' % h(it['tip'])) if it.get('tip') else '')
            for it in g['items'])
        cls2 = 'person-content active' if i == 0 else 'person-content'
        panels.append('<div class="%s" id="rm-%s"><p class="zh-hint note">%s</p>%s</div>' % (cls2, g['key'], h(g['note']), items))
    return f'''    <section id="redemittel">
      <h2 class="section-title"><span class="num">2</span> 🧭 Redemittel · 图表描述句型库</h2>
      <p class="zh-hint">四类句型按作文里的出场顺序排：先排名，再比例，然后比较，最后结论。课堂做法：每类挑 2 条，当场套到图上说一遍。</p>
      <div class="person-tabs rm-tabs">{''.join(tabs)}</div>
      {''.join(panels)}
    </section>
'''


# ---------------------------------------------------------------- 4 satzbau
def sec_satzbau(d):
    s = d['satzbau']
    cards = []
    for i, it in enumerate(s['items']):
        order = it['chunks']
        chips = list(enumerate(order))
        random.Random(700 + i).shuffle(chips)
        chips_html = ''.join('<span class="sb-chunk" data-i="%d" onclick="sbPick(this,%d)" lang="de">%s</span>'
                             % (k, i, h(txt)) for k, txt in chips)
        cards.append(f'''      <div class="sb-card">
        <div class="sb-zh"><b>{i + 1})</b> <span class="um-pat">{h(it['cat'])}</span> {h(it['zh'])}</div>
        <div class="sb-pool" id="sb-pool-{i}">{chips_html}</div>
        <div class="sb-line" id="sb-line-{i}"></div>
        <div class="sb-actions">
          <button class="btn" onclick="sbCheck({i})">✓ 检查语序</button>
          <button class="btn ghost" onclick="sbUndo({i})">↶ 撤回</button>
          <button class="btn ghost" onclick="sbReset({i})">↺ 重排</button>
          <button class="btn ghost" onclick="sbShow({i})">👁 参考语序</button>
          <span class="fill-result" id="sb-res-{i}"></span>
        </div>
        <div class="um-src">📖 {h(it['src'])}</div>
      </div>''')
    return f'''    <section id="satzbau">
      <h2 class="section-title"><span class="num">3</span> 🔧 Satzbau · 同一组数据的四种说法</h2>
      <p class="zh-hint">{h(s['note'])}</p>
      {''.join(cards)}
    </section>
'''


# ---------------------------------------------------------------- 5 ladder
def sec_ladder(d):
    lv = d['ladder']['levels']
    # L1 配对（复用连线引擎）
    l1 = lv[0]
    idx = list(range(len(l1['pairs'])))
    random.Random(310).shuffle(idx)
    left = ''.join('<div class="c-item de" data-pair="%d" data-gid="0" lang="de" onclick="cClick(this)">%s</div>'
                   % (i, h(p['a'])) for i, p in enumerate(l1['pairs']))
    right = ''.join('<div class="c-item cn" data-pair="%d" data-gid="0" onclick="cClick(this)">%s</div>'
                    % (j, h(l1['pairs'][j]['b'])) for j in idx)
    # L2 排序
    l2 = lv[1]
    l2chips = ''.join(
        '<span class="l2-chip" data-rank="%d" data-seq="0" onclick="l2Seq(this,\'l2-box\')">'
        '<span class="l2-num"></span><span lang="de">%s</span></span>' % (it['rank'], h(it['name']))
        for it in l2['items'])
    l3 = lv[2]
    l4 = lv[3]
    l2btns = tools_buttons(['<button class="btn" onclick="l2Check(\'l2-box\')">✓ 检查顺序</button>',
                            '<button class="btn ghost" onclick="l2Reset(\'l2-box\')">↺ 重来</button>',
                            '<span id="l2-box-res" class="kw-result"></span>'])

    def quiz_block(items, key, title):
        qz = ''.join(
            '<div class="qz-item" data-a="%d"><p class="qz-q">%d. %s</p><div class="qz-opts">%s</div><span class="src">%s</span></div>'
            % (q['a'], i + 1, h(q['q']),
               ''.join('<span class="qz-opt" onclick="qzPick(this)" lang="de">%s</span>' % h(o) for o in q['opts']),
               h(q.get('src', '')))
            for i, q in enumerate(items))
        btns = tools_buttons(['<button class="btn" onclick="qzCheck(\'%s\')">✓ 检查</button>' % key,
                              '<button class="btn ghost" onclick="qzClear(\'%s\')">↺ 清空</button>' % key,
                              '<span id="%s-res" class="kw-result"></span>' % key])
        return f'''      <div class="zone">
        <p class="zone-h">{h(title)}</p>
        <div class="qz-box" id="{key}">{qz}</div>
        {btns}
      </div>'''

    return f'''    <section id="ladder">
      <h2 class="section-title"><span class="num">4</span> 🪜 Vier Stufen · 四层阶梯</h2>
      <p class="zh-hint">{h(d['ladder']['note'])}</p>
      <div class="zone">
        <p class="zone-h">Stufe 1 · {h(l1['title'])}</p>
        <p class="zh-hint">{h(l1['task'])}</p>
        <div class="connect-game">
          <div class="connect-field"><div class="connect-col">{left}</div><div class="connect-col">{right}</div></div>
          <div class="connect-score">匹配：<span id="cg-cnt-0">0</span> / {len(l1['pairs'])}</div>
        </div>
      </div>
      <div class="zone">
        <p class="zone-h">Stufe 2 · {h(l2['title'])}</p>
        <p class="zh-hint">{h(l2['task'])}</p>
        <div id="l2-box">{l2chips}</div>
        {l2btns}
      </div>
{quiz_block(l3['items'], 'qz-l3', 'Stufe 3 · ' + l3['title'] + '｜' + l3['task'])}
{quiz_block(l4['items'], 'qz-l4', 'Stufe 4 · ' + l4['title'] + '｜' + l4['task'])}
    </section>
'''


# ---------------------------------------------------------------- 5b vocab
def sec_vocab(d):
    v = d['vocab']
    cards = ''.join('<div class="vc-card" onclick="flipCard(this)"><div class="vc-inner">'
                    '<div class="vc-front" lang="de">%s</div>'
                    '<div class="vc-back">%s</div></div></div>' % (h(t['de']), h(t['cn']))
                    for t in v['items'])
    return f'''    <section id="vocab">
      <h2 class="section-title"><span class="num">5</span> 🃏 {h(v['title'])}</h2>
      <p class="zh-hint">{h(v['instruction'])}</p>
      <div class="vocab-grid">{cards}</div>
      <p class="zh-hint note">来源：{h(v['src'])}</p>
    </section>
'''


# ---------------------------------------------------------------- 6 T1
def sec_t1(d):
    t = d['t1']
    bank = ''.join('<span class="bank-chip" onclick="clzFill(\'clz-t1\', this)">%s</span>' % h(w) for w in t['bank'])
    paras = []
    n = 0
    for blk in t['cloze']:
        txt = blk['p']
        for a in blk['ans']:
            n += 1
            txt = txt.replace('[[%d]]' % n,
                              '<span class="cloze-blank" data-ph="(%d)" data-ans="%s" onclick="clzClick(this)">(%d)</span>'
                              % (n, esc_attr(a), n), 1)
        paras.append(f'<p class="cloze-p" lang="de">{txt}</p>')
    btns = tools_buttons(['<button class="btn" onclick="clzCheck(\'clz-t1\')">✓ 检查</button>',
                          '<button class="btn ghost" onclick="clzReveal(\'clz-t1\')">👁 显示答案</button>',
                          '<button class="btn ghost" onclick="clzClear(\'clz-t1\')">↺ 清空</button>',
                          '<span id="clz-t1-res" class="kw-result"></span>'])
    struct = ''.join(
        '<div class="stp"><span class="stp-n">%s</span><span class="stp-fn">%s</span>'
        '<div class="es-d" lang="de">%s</div><div class="rm-cn">%s</div></div>'
        % (h(s['n']), h(s['fn']), h(s['de']), h(s['cn'])) for s in t['structure'])
    pats = ''.join(
        '<div class="rm-item"><div class="rm-de" lang="de">%s</div><div class="rm-tip">%s · %s</div></div>'
        % (h(p['de']), h(p['cat']), h(p['src'])) for p in t['patterns'])
    links = ''.join('<tr><td lang="de">%s</td><td>%s</td></tr>' % (h(c['sent']), h(c['map'])) for c in t['chartLinks'])
    return f'''    <section id="t1">
      <h2 class="section-title"><span class="num">6</span> 📖 {h(t['title'])} <span class="src src-lg">{h(t['kind'])}</span></h2>
      <p class="zh-hint">{h(t['lead'])}</p>
      <div class="clz-box" id="clz-t1">
        <div class="bank-box"><strong>Wortbank：</strong>{bank}</div>
        {''.join(paras)}
        {btns}
      </div>
      <p class="zh-hint note">📌 {h(t['provenance'])}</p>
      <div class="text-card">
        <h3>🧱 段落功能（作文可以直接照这个骨架）</h3>
        {struct}
      </div>
      <div class="text-card">
        <h3>🔍 文中的图表描述句型（教材原句照抄）</h3>
        {pats}
      </div>
      <div class="text-card">
        <h3>🔗 句子 ↔ 图表：这句话说的是图上哪一块</h3>
        <table class="tb"><tr><th>教材句子</th><th>对应图表位置</th></tr>{links}</table>
      </div>
    </section>
'''


# ---------------------------------------------------------------- 8/9 T2
def sec_t2(d, key, num):
    t = d[key]
    if t['bank']:
        bank_head = '<strong>Wortbank：</strong>' if key == 't1' else '<strong>Wortbank（课堂便利，非原题）：</strong>'
        bank_html = '<div class="bank-box">%s%s</div>' % (
            bank_head, ''.join('<span class="bank-chip" onclick="clzFill(\'clz-%s\', this)">%s</span>'
                               % (key, h(w)) for w in t['bank']))
    else:
        bank_html = ('<p class="zh-hint note">原题为听力填空，<b>教材没有词库</b>：先听/读一遍再说答案，'
                     '答案与依据见本页下方说明。</p>')
    paras = []
    n = 0
    for blk in t['cloze']:
        txt = blk['p']
        for a in blk['ans']:
            n += 1
            txt = txt.replace('[[%d]]' % n,
                              '<span class="cloze-blank" data-ph="(%d)" data-ans="%s" onclick="clzClick(this)">(%d)</span>'
                              % (n, esc_attr(a), n), 1)
        paras.append(f'<p class="cloze-p" lang="de">{txt}</p>')
    btns = tools_buttons(['<button class="btn" onclick="clzCheck(\'clz-%s\')">✓ 检查</button>' % key,
                          '<button class="btn ghost" onclick="clzReveal(\'clz-%s\')">👁 显示答案</button>' % key,
                          '<button class="btn ghost" onclick="clzClear(\'clz-%s\')">↺ 清空</button>' % key,
                          '<span id="clz-%s-res" class="kw-result"></span>' % key])
    struct = ''.join(
        '<div class="stp"><span class="stp-n">%s</span><span class="stp-fn">%s</span><div class="rm-cn">%s</div></div>'
        % (h(s['n']), h(s['fn']), h(s['cn'])) for s in t['structure'])
    tb = t['table']
    head = ''.join('<th>%s</th>' % h(c) for c in tb['head'])
    rows = ''.join('<tr>%s</tr>' % ''.join('<td lang="de">%s</td>' % h(c) for c in r) for r in tb['rows'])
    return f'''    <section id="{key}">
      <h2 class="section-title"><span class="num">{num}</span> 👤 {h(t['title'])} <span class="src src-lg">{h(t['kind'])} · {h(t['sub'])}</span></h2>
      <p class="zh-hint">{h(t['lead'])}</p>
      <div class="clz-box" id="clz-{key}">
        {bank_html}
        {''.join(paras)}
        {btns}
      </div>
      <p class="zh-hint note">📌 {h(t['provenance'])}</p>
      <p class="highlight-box" lang="de">💬 {h(t['quote'])}</p>
      <div class="text-card">
        <h3>🧱 人物文结构（与统计文对照着讲）</h3>
        {struct}
      </div>
      <div class="text-card">
        <h3>📋 教材 Textarbeit 表（原文照抄）</h3>
        <table class="tb"><tr>{head}</tr>{rows}</table>
        <p class="zh-hint note">来源：{h(tb['src'])}</p>
      </div>
    </section>
'''


# ---------------------------------------------------------------- 9 traum
def sec_traum(d):
    t = d['traum']
    head = ''.join('<th>%s</th>' % h(c) for c in t['table'][0])
    rows = ''.join('<tr>%s</tr>' % ''.join('<td>%s</td>' % h(c) for c in r) for r in t['table'][1:])
    tasks = ''.join(
        f'''      <div class="fill-item">
        <div class="fill-zh">{i + 1}. {h(x['zh'])}</div>
        <div class="fill-input-line">
          <input class="fill-input" data-ans="{esc_attr(x['ans'])}" placeholder="Deine Formulierung …" lang="de"
                 onkeydown="if(event.key==='Enter')fillCheck(this,'.fill-item')">
          <button class="fill-check" onclick="fillCheck(this,'.fill-item')">✓</button>
          <span class="fill-result"></span>
        </div>
        <div class="um-tip">💡 {h(x['hint'])}</div>
        <div class="um-src" lang="de">参考：{h(x['ans'])}</div>
      </div>''' for i, x in enumerate(t['tasks']))
    return f'''    <section id="traum">
      <h2 class="section-title"><span class="num">9</span> 📈 {h(t['title'])}</h2>
      <p class="zh-hint">{h(t['lead'])}</p>
      <div class="text-card">
        <h3>📄 调查原文（教材照抄）</h3>
        <p class="de-full" lang="de">{h(t['srcText'])}</p>
        <p class="zh-hint note">来源：{h(t['src'])}</p>
      </div>
      <div class="text-card">
        <h3>🔄 把「几次」变成「表格」</h3>
        <table class="tb"><tr>{head}</tr>{rows}</table>
        <p class="zh-hint note">{h(t['tableNote'])}</p>
      </div>
      <div class="text-card">
        <h3>✍️ 用图表句型复述（写完点 ✓）</h3>
        {tasks}
      </div>
    </section>
'''


# ---------------------------------------------------------------- 10 detect
def sec_detect(d):
    dt = d['detect']
    blocks = []
    for it in dt['items']:
        text = it['text']
        frags = []
        for e in it['errors']:
            frags.append(e['frag'])
        segs = []
        rest = text
        # 逐错误片段切分：命中片段标 data-err=1，其余标 data-err=0
        pieces = []
        pos = 0
        marks = []
        for e in it['errors']:
            k = text.find(e['frag'], pos)
            if k < 0:
                continue
            marks.append((k, k + len(e['frag']), e))
        marks.sort()
        for k, k2, e in marks:
            if k > pos:
                pieces.append((text[pos:k], None))
            pieces.append((text[k:k2], e))
            pos = k2
        if pos < len(text):
            pieces.append((text[pos:], None))
        for txt, e in pieces:
            if e is None:
                segs.append('<span class="dt-seg" data-err="0" onclick="dtMark(this)">%s</span>' % h(txt))
            else:
                segs.append('<span class="dt-seg" data-err="1" onclick="dtMark(this)">%s</span>' % h(txt))
        why = ''.join('<li><b>[%s]</b> %s</li>' % (h(e['type']), h(e['why'])) for e in it['errors'])
        did = it['id']
        btns = tools_buttons(['<button class="btn" onclick="dtCheck(\'dt-%s\')">✓ 检查</button>' % did,
                              '<button class="btn ghost" onclick="dtReveal(\'dt-%s\')">👁 标出全部</button>' % did,
                              '<button class="btn ghost" onclick="dtClear(\'dt-%s\')">↺ 清空</button>' % did,
                              '<span id="dt-%s-res" class="kw-result"></span>' % did])
        blocks.append(f'''      <div class="text-card">
        <h3>{h(it['title'])}</h3>
        <div class="dt-text" id="dt-{did}" lang="de">{''.join(segs)}</div>
        {btns}
        <div class="kw-tools"><button class="btn ghost" onclick="toggleBox('dtWhy-{did}')">💡 错误类型与解析</button></div>
        <div id="dtWhy-{did}" style="display:none"><ul class="lk-zh">{why}<li><b>[改法]</b> <span lang="de">{h(it['fix'])}</span></li></ul></div>
      </div>''')
    return f'''    <section id="detect">
      <h2 class="section-title"><span class="num">10</span> 🕵️ Fehlerjagd · 找错侦探</h2>
      <p class="zh-hint">{h(dt['note'])}</p>
      {''.join(blocks)}
    </section>
'''


# ---------------------------------------------------------------- 11 essay
def sec_essay(d):
    e = d['essay']
    parts = ''.join(
        '<div class="stp"><span class="stp-fn">%s</span><div class="rm-cn">%s</div>'
        '<ul class="lk-zh">%s</ul>'
        '<div class="rm-de" lang="de">例：%s</div></div>'
        % (h(p['part']), h(p['fn']),
           ''.join('<li lang="de">%s</li>' % h(r) for r in p['rm']), h(p['example']))
        for p in e['parts'])
    fill = ''.join(
        f'''      <div class="fill-item">
        <div class="fill-zh">{i + 1}. {h(x['zh'])}</div>
        <div class="fill-input-line">
          <input class="fill-input" data-ans="{esc_attr(x['ans'])}" placeholder="Dein Satz …" lang="de"
                 onkeydown="if(event.key==='Enter')fillCheck(this,'.fill-item')">
          <button class="fill-check" onclick="fillCheck(this,'.fill-item')">✓</button>
          <span class="fill-result"></span>
        </div>
        <div class="um-tip">💡 {h(x['hint'])}</div>
      </div>''' for i, x in enumerate(e['fill']))
    return f'''    <section id="essay">
      <h2 class="section-title"><span class="num">11</span> 🎯 Prüfungskarte · 专四图表作文卡</h2>
      <p class="zh-hint">{h(e['note'])}</p>
      <div class="text-card">
        <h3>🧱 四段式骨架</h3>
        {parts}
      </div>
      <div class="text-card">
        <h3>✍️ 八个句子（写完点 ✓，按参考答案判）</h3>
        {fill}
      </div>
      <div class="text-card">
        <h3>⏱️ 计时播报员（课堂活动）</h3>
        <p class="zh-hint">30 秒内用 ≥4 个不同类别的 Redemittel 描述本图（至少一个 Rangordnung + 一个 Prozentanteile/Vergleich + 一个 Fazit）。同桌计数。</p>
        <div class="kw-tools"><button class="btn" onclick="startTimer('tm-bc', 30)">▶ 30 秒计时</button>
          <button class="btn ghost" onclick="resetTimer('tm-bc', 30)">↺ 重置</button>
          <span class="kw-result" id="tm-bc">30</span></div>
      </div>
    </section>
'''


# ---------------------------------------------------------------- assemble
def main():
    d = {}
    with open(DATA_FILE, encoding='utf-8') as f:
        d.update(json.load(f))
    with open(TEXTS_FILE, encoding='utf-8') as f:
        d.update(json.load(f))

    secs = [('home', '首页'), ('chart', '📊 图表'), ('redemittel', '🧭 句型库'), ('satzbau', '🔧 变形'),
            ('ladder', '🪜 阶梯'), ('vocab', '🃏 词汇卡'), ('t1', '📖 T1'), ('t2a', '👤 Erika'),
            ('t2b', '👤 Simon'), ('traum', '📈 调查改写'), ('detect', '🕵️ 找错'), ('essay', '🎯 作文卡')]

    css = open(os.path.join(DIR, 'template_css.css'), encoding='utf-8').read()
    css = css.replace('</style>', base.EXTRA_CSS + CSS_EXTRA + '</style>')

    nav = ('<nav><div class="top-nav"><div class="logo" style="cursor:pointer" onclick="switchSection(\'home\')">'
           '<span class="logo-icon">📊</span><span>L8 · Schaubild</span></div>'
           '<div class="nav-links" id="navLinks">')
    for sid, lbl in secs:
        nav += '<button onclick="switchSection(\'%s\')">%s</button>' % (sid, lbl)
    nav += ('</div><button class="hamburger" onclick="toggleNav()">☰</button></div>'
            '<div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div></nav>')

    body = (sec_home(d) + sec_chart(d) + sec_redemittel(d) + sec_satzbau(d) + sec_ladder(d) +
            sec_vocab(d) + sec_t1(d) + sec_t2(d, 't2a', 7) + sec_t2(d, 't2b', 8) +
            sec_traum(d) + sec_detect(d) + sec_essay(d))

    sb = [[c for c in it['chunks']] for it in d['satzbau']['items']]
    data_js = json.dumps({'sb': sb}, ensure_ascii=False)
    core_js = base.CORE_JS.replace('__SECTIONS__', json.dumps([s[0] for s in secs]))

    html = ('<!DOCTYPE html>\n<html lang="zh-CN" data-cw-profile="interaction">\n<head>\n'
            '<meta charset="UTF-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1.0">\n'
            '<title>Lektion 8 · Schaubilder beschreiben · Text 1 &amp; Text 2</title>\n'
            + css + '\n</head>\n<body>\n' + nav +
            '<div class="main"><div class="container">\n' + body + '\n</div></div>\n'
            '<div class="vocab-overlay" id="vocabOverlay" onclick="hideVocab()"></div>\n'
            '<div class="vocab-panel" id="vocabPanel">\n'
            '  <div class="vocab-panel-header"><span id="vpWord" class="vp-word"></span>\n'
            '    <button onclick="hideVocab()" class="vp-close">&times;</button></div>\n'
            '  <div id="vpZh" class="vp-zh"></div>\n'
            '  <div id="vpEx" class="vp-ex"></div>\n'
            '</div>\n'
            '<div class="proj-ctl" id="projCtl">\n'
            '  <button class="proj-mini" onclick="projToggle(event)" title="投影放大">A±</button>\n'
            '  <div class="proj-body" id="projBody">\n'
            '    <button onclick="projStep(-1)" title="缩小">A−</button>\n'
            '    <span class="proj-label" id="projLabel">标准</span>\n'
            '    <button onclick="projStep(1)" title="放大（投影用）">A+</button>\n'
            '    <button onclick="projReset()" title="回到标准">↺</button>\n'
            '  </div>\n'
            '</div>\n'
            '<script>\nconst DOC = ' + data_js + ';\n' + core_js + '\n' + base.EXTRA_JS + '\n' + JS_EXTRA + '\n</script>\n'
            '</body>\n</html>\n')

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(html)
    print('Generated: %s (%d bytes)' % (OUT, len(html)))

    js = html[html.find('<script>') + 8: html.rfind('</script>')]
    r = subprocess.run(['node', '-e',
                        'try{require("vm").compileFunction(JSON.parse(process.argv[1]));console.log("JS OK")}'
                        'catch(e){console.log("JS ERROR: "+e.message.substring(0,200))}',
                        json.dumps(js)], capture_output=True, text=True, timeout=20)
    print(r.stdout.strip() or r.stderr[:300])

    print('sections open=%d close=%d' % (html.count('<section'), html.count('</section>')))
    for sid, _ in secs:
        assert 'id="%s"' % sid in html, 'missing section ' + sid
    print('all %d section ids present' % len(secs))
    print('nav items = %d' % len(secs))
    print('chart bars = %d | quiz = %d | redemittel = %d | satzbau = %d | detect = %d | essay fill = %d'
          % (html.count('class="chart-bar'), html.count('class="qz-item'),
             sum(len(g['items']) for g in d['redemittel']), html.count('sb-card'),
             html.count('dt-text'), html.count('fill-input')))
    print('cloze blanks = %d | bank chips = %d | css %d bytes' % (html.count('cloze-blank'), html.count('bank-chip'), len(css)))


if __name__ == '__main__':
    main()
