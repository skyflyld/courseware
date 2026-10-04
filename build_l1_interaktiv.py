#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_l1_interaktiv.py — Lektion 1《Rund um das Glück》互动课件生成器
输入: l1-data.json + l1-vocab.json + l1-text-zh.json + l1-vocab-zh.json
输出: lektion1-rund-um-das-glueck.html（单文件，自包含 CSS/JS，零外部请求）

基底: 复用 build_l8_berufe.py（设计令牌 / 投影挡位 / 词卡 / 连线 / 面板）
      + build_l8_t1t2.py（读词查义面板样式、选择题件 qz-*、表格 tb、透明卡片）
      模板结构对齐 build_l9_bewerbung.py（Sky 2026-10-04 指令：按 L9 模版做 L1）。
原子原则: 一个脚本 → 一个产物；不在产物上做增量修补。
数据纪律: 德文/中文一律取 JSON 原值，不改写、不补造。
与 L9 的两处结构差异（L1 课文形态不同）：
  ① T1 是双声部（Oma / Emilie 就六个话题各说一段）→ 左右对照卡，不是整段课文
  ② T2 是采访（Lukas 问 / 刘教授答）→ 分轮对话卡；练习 9 的五个空在阅读页已按上下文填入
"""
import json
import os
import re
import subprocess

import build_l8_berufe as base
import build_l8_t1t2 as t12

DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(DIR, 'l1-data.json')
VOCAB_FILE = os.path.join(DIR, 'l1-vocab.json')
TEXT_ZH_FILE = os.path.join(DIR, 'l1-text-zh.json')
VOCAB_ZH_FILE = os.path.join(DIR, 'l1-vocab-zh.json')
OUT = os.path.join(DIR, 'lektion1-rund-um-das-glueck.html')
TEXT_ZH = {}          # {"t1": {德文句: 中文}, "t2": {...}}
VOCAB_ZH = {}         # {教材例句: 中文}
MISSING_TR = []       # 缺译文的句子（构建时清零才算过）
SB_DOC = []           # 语序工坊参考答案（按语序拼装的词块）

h = base.h
esc_attr = base.esc_attr
tools_buttons = base.tools_buttons
_js = t12._js_str


def h(s):
    """正文转义 + 分隔符「·」禁用行首（换行质量层做法 4：用不换行空格粘住前文）。"""
    return base.h(str(s)).replace(' ·', '\u00a0·')


def slot_html(s):
    """句型骨架里的 [槽] 渲染成可换槽高亮。"""
    return re.sub(r'\[([^\[\]]+)\]', r'<span class="slot">\1</span>', h(s))


def _same_de(a, b):
    n = lambda s: re.sub(r'\s+', ' ', str(s or '')).strip().rstrip('.').strip().lower()
    return bool(a) and bool(b) and n(a) == n(b)


# ---------------------------------------------------------------- 点词查义
# %%
_WORD_RE_CACHE = {}


def _word_re(form):
    r = _WORD_RE_CACHE.get(form)
    if r is None:
        r = re.compile(r'(?<![A-Za-zÄÖÜäöüß])' + re.escape(form) + r'(?![A-Za-zÄÖÜäöüß])')
        _WORD_RE_CACHE[form] = r
    return r


def _gloss_span(e, surface):
    def zh_of(ex):
        z = VOCAB_ZH.get(ex, '')
        return z

    return ('<span class="gl" title="点一下看释义、例句与译文" '
            'onclick="event.stopPropagation();showVocab(%s)">%s</span>'
            % (','.join(_js(x) for x in (e.get('w', ''), e.get('zh', ''),
                                         e.get('ex', ''), zh_of(e.get('ex', '')),
                                         e.get('def', ''))), h(surface)))


def gloss_render(text, glist):
    """按词条的 forms 在句子里自动标可点词。

    判据：德文词边界（前后都不是字母）；同一位置多个命中取最长的那个；
    命中区间不重叠（先定先占）。不做词形还原——forms 是手工列的，列了才标。
    """
    spans = []
    for e in glist:
        for f in e.get('forms') or []:
            for m in _word_re(f).finditer(text):
                spans.append((m.start(), m.end(), e))
    spans.sort(key=lambda t: (t[0], -(t[1] - t[0])))
    out, last = [], 0
    for s, e_, ent in spans:
        if s < last:
            continue
        out.append(h(text[last:s]))
        out.append(_gloss_span(ent, text[s:e_]))
        last = e_
    out.append(h(text[last:]))
    return ''.join(out)


def tr_render(sents, glist, key):
    """逐句点译：每句包一层可点 span，点一下就地显示该句中文。

    数据层（l1_sents.split_sents）与渲染层用的是同一批句子（JSON 里已是切好的列表），
    故这里做精确匹配；查不到就原样渲染并记入 MISSING_TR，构建时报警。
    """
    zhmap = TEXT_ZH.get(key, {})
    out = []
    for sent in sents:
        body = gloss_render(sent, glist)
        zh = zhmap.get(sent)
        if zh:
            out.append('<span class="tr-s" title="点一下看这句的中文" onclick="trToggle(this)">'
                       '%s<span class="tr-zh" lang="zh-CN">%s</span></span> ' % (body, h(zh)))
        else:
            MISSING_TR.append('%s · %s' % (key, sent))
            out.append('%s ' % body)
    return ''.join(out).strip()


# ---------------------------------------------------------------- 词场表
def wf_rows(rows):
    """词场表行：词条（可点）/ 中文 / 常用搭配 / 教材例句 + 译文。"""
    out = []
    for r in rows:
        ex_de = r.get('ex', '')
        ex_zh = r.get('exZh', '') or VOCAB_ZH.get(ex_de, '')
        ex = '%s' % h(ex_de) if ex_de else '<span class="wf-none">（教材原页无此句）</span>'
        same = _same_de(ex_de, r.get('coll', ''))
        if same:
            tail = ('<td class="wf-both" data-l="常用搭配 ＝ 教材例句" lang="de" colspan="2">%s</td>'
                    % ex)
        else:
            tail = ('<td class="wf-coll" data-l="搭配" lang="de">%s</td>'
                    '<td class="wf-ex" data-l="例句" lang="de">%s</td>' % (h(r['coll']), ex))
        out.append('<tr><td class="wf-w" data-l="词条" lang="de" role="button" tabindex="0"'
                   ' title="点一下看例句与中文译文" onclick="wfShow(this)"'
                   ' data-w="%s" data-cn="%s" data-ex="%s" data-zh="%s" data-coll="%s"'
                   ' data-same="%s" data-note="%s">%s<span class="wf-more">例句</span></td>'
                   '<td class="wf-cn" data-l="中文">%s</td>%s</tr>'
                   % (esc_attr(r['w']), esc_attr(r['cn']), esc_attr(ex_de), esc_attr(ex_zh),
                      esc_attr(r['coll']), '1' if same else '0', '',
                      base.word_html(r['w']), h(r['cn']), tail))
    return ''.join(out)


def wf_table(rows):
    return ('<div class="vocab-table-wrap" style="overflow-x:auto"><table class="tb wf-table">'
            '<tr><th>词条</th><th>中文</th><th>常用搭配</th><th>教材例句</th></tr>%s</table></div>'
            % wf_rows(rows))


# ---------------------------------------------------------------- 句型条（L1 形态）
def sm_items(items):
    """句型条：骨架（槽位高亮）+ 什么时候用 + 三句例句 + 换槽练习 + 常见错法。"""
    out = []
    for it in items:
        ex = ''.join(
            '<div class="sm-ex-row"><div class="sm-ex-de" lang="de">%s</div>'
            '<div class="sm-ex-zh">%s <span class="src">%s</span></div></div>'
            % (h(e['de']), h(e['zh']), h(e['src'])) for e in it['ex'])
        slots = ''.join('<div class="sm-slot-row"><span lang="de">%s</span>'
                        '<span class="sm-slot-hint">%s</span></div>'
                        % (h(s['de']), h(s['zh'])) for s in it['slots'])
        wrong = ''.join('<div class="sm-wrong-row"><span class="sm-bad" lang="de">✗ %s</span>'
                        '<span class="sm-good" lang="de">✓ %s</span></div>'
                        % (h(w['bad']), h(w['good'])) for w in it['wrong'])
        out.append('''      <div class="sm-item">
        <div class="sm-fn">%s <span class="src">教材 %s</span></div>
        <div class="sm-de" lang="de">%s</div>
        <div class="sm-tip">💡 %s</div>
        <div class="sm-ex">%s</div>
        <div class="sm-sub">🔁 换槽说一遍</div>%s
        <div class="sm-sub">⚠️ 常见错法</div>%s
      </div>''' % (h(it['fn']), h(it.get('src') or it['ex'][0]['src']),
                   slot_html(it['pattern']), h(it['use']), ex, slots, wrong))
    return ''.join(out)


def sb_cards(items):
    """语序工坊：词块点选拼句（复用 L8 的 sb-* 组件与 JS）。"""
    out = []
    for i, it in enumerate(items):
        SB_DOC.append(it['chunks'])
        chips = ''.join('<span class="sb-chunk" data-i="%d" onclick="sbPick(this,%d)" lang="de">%s</span>'
                        % (k, i, h(c)) for k, c in enumerate(it['chunks']))
        out.append('''      <div class="sb-card">
        <div class="sb-zh"><span class="sm-cat">%s</span> <span class="src">%s</span><br>%s</div>
        <div class="sb-pool" id="sb-pool-%d">%s</div>
        <div class="sb-line" id="sb-line-%d"></div>
        <div class="sb-actions">
          <button class="btn" onclick="sbCheck(%d)">✓ 检查语序</button>
          <button class="btn ghost" onclick="sbUndo(%d)">↶ 撤回</button>
          <button class="btn ghost" onclick="sbReset(%d)">↺ 重排</button>
          <button class="btn ghost" onclick="sbShow(%d)">👁 参考语序</button>
          <span class="fill-result" id="sb-res-%d"></span>
        </div>
      </div>''' % (h(it['cat']), h(it['src']), h(it['zh']), i, chips, i, i, i, i, i, i))
    return ''.join(out)


# ---------------------------------------------------------------- 1 home
def sec_home(d, v9):
    m = d['meta']
    objs = ''.join('<li>%s</li>' % h(x) for x in m['objectives'])
    rows = []
    for item in m['flow']:
        a, b = item.split('：', 1) if '：' in item else (item, '')
        rows.append('<tr><td class="fl-t">%s</td><td>%s</td></tr>' % (h(a), h(b)))
    wf = v9['wortfelder']
    n_wf = sum(len(g['rows']) for g in wf['groups'])
    n_vocab = sum(len(g['words']) for g in d['vocab']['groups'])
    n_pairs = sum(len(g['pairs']) for g in d['connectGrids'])
    n_sm = sum(len(g['items']) for g in v9['satzmuster']['groups'])
    n_gm = len(d['grammar']['units'])
    cards = [
        ('t1', '📖 Text 1 · 两代人的童年',
         'Oma 与 Emilie 就六个话题各说一段 · %d 个重点词可点' % len(d['t1']['glossar'])),
        ('t2', '👤 Text 2 · 关于幸福的采访',
         '刘教授的五步回答 · %d 个重点词可点' % len(d['t2']['glossar'])),
        ('vocab', '📚 词汇精讲',
         '%d 词条分 %d 个词场 · 带搭配与教材例句 · 词表 %d 词' % (n_wf, len(wf['groups']), n_vocab)),
        ('satzmuster', '🧩 句型库',
         '课文长出来的 %d 条句型 + %d 句语序工坊' % (n_sm, len(v9['satzmuster']['werkstatt']['items']))),
        ('grammar', '🔤 语法六讲', '每讲：想干什么 → 一句话规则 → 三步 → 三十秒自测'),
        ('connect', '🔗 连线配对', '%d 组 · %d 对（含介词搭配）' % (len(d['connectGrids']), n_pairs)),
        ('luecken', '✍️ 介词填空', '%d 空 · 填完点 ✓ 核对' % len(d['luecken']['items'])),
        ('anwenden', '✍️ 学以致用', '练习 9 完形 + 改写 8 + 中译德 10 + 采访六问'),
        ('quiz', '✅ 快问快答', '%d 题 · 课文理解' % len(d['quiz']['items'])),
        ('translation', '🎯 翻译卡', '%d 张 · 先自己译再翻面' % len(d['translation']['cards'])),
    ]
    g = ''.join('<div class="text-card home-card" onclick="switchSection(\'%s\')"><h3>%s</h3><p>%s</p></div>'
                % (i, t, s) for i, t, s in cards)
    return '''    <section id="home" class="active">
      <div class="hero">
        <h1>%s</h1>
        <p class="sub">%s</p>
        <p class="meta">%s</p>
      </div>
      <div class="highlight-box">🎬 怎么用：点顶部导航切节；课文里带虚线的德语词点一下出释义与例句，<b>点句子</b>看中文译文；词场里<b>点词条</b>出教材例句与译文；词卡点一下翻面；练习写完点「检查」。投影时点右下角 A± 放大。</div>
      <div class="home-grid">%s</div>
      <div class="obj-box"><strong>学习目标 Lernziele：</strong><ul>%s</ul></div>
      <div class="text-card" style="margin-top:12px">
        <h3>🧭 学习路线（建议 45 分钟走完）</h3>
        <table class="flow-table">%s</table>
      </div>
    </section>
''' % (h(m['title']), h(m['subtitle']), h(m['source']), g, objs, ''.join(rows))


# ---------------------------------------------------------------- 2 课文 T1（双声部）
def sec_t1(d):
    t = d['t1']
    gl = t.get('glossar', [])
    intro = ''.join('<p class="cloze-p tr-p" lang="de">%s</p>' % tr_render(turn['sents'], gl, 't1')
                    for turn in t['intro'])
    blocks = []
    for b in t['blocks']:
        blocks.append('''      <div class="duo">
        <div class="duo-h"><span class="duo-n">%s</span> <span class="duo-t">%s</span>
          <span class="src">%s</span></div>
        <div class="duo-grid">
          <div class="duo-col oma"><span class="duo-who">Oma · 战后一代</span>
            <p class="duo-de" lang="de">%s</p></div>
          <div class="duo-col emi"><span class="duo-who">Emilie · Z 世代</span>
            <p class="duo-de" lang="de">%s</p></div>
        </div>
      </div>''' % (h(b['no']), h(b['topic']), h(b['page']),
                   tr_render(b['oma'], gl, 't1'), tr_render(b['emilie'], gl, 't1')))
    struct = ''.join(
        '<div class="stp"><span class="stp-n">%s</span><span class="stp-fn" lang="de">%s</span>'
        '<div class="rm-cn">%s</div></div>' % (h(s['n']), h(s['de']), h(s['cn']))
        for s in t['structure'])
    quotes = ''.join(
        '<div class="qt"><div class="qt-h">%s <span class="src">%s</span></div>'
        '<div class="qt-de" lang="de">»%s«</div><div class="qt-zh">%s</div>'
        '<div class="qt-tip">💡 %s</div></div>'
        % (h(q['n']), h(q['src']), h(q['de']), h(q['zh']), h(q['tip'])) for q in t['quotes'])
    return '''    <section id="t1">
      <h2 class="section-title"><span class="num">1</span> 📖 %s <span class="src src-lg">%s · %s · %s</span></h2>
      <p class="zh-hint">%s</p>
      <p class="zh-hint">✏️ 带虚线的德文词点一下，弹出中文释义、这词在课文里的原句与译文；<b>点句子</b>看整句参考译文（先自己读，卡住了再点）。</p>
      <div class="text-card read-card">%s</div>
      <div class="duo-wrap">%s</div>
      <div class="text-card"><h3>🌍 Landeskunde · Generation\u00a0Z</h3>
        <p class="cloze-p tr-p" lang="de">%s</p></div>
      <p class="zh-hint note">📌 %s</p>
      <div class="text-card">
        <h3>🧱 六个话题（教材 ①–⑥ 的切法）</h3>
        %s
      </div>
      <div class="text-card">
        <h3>💬 课文里值得记住的原句</h3>
        %s
      </div>
    </section>
''' % (h(t['title']), h(t['kind']), h(t['sub']), h(t['page_note']), h(t['lead']), intro,
       ''.join(blocks), tr_render(t['landeskunde'], gl, 't1'), h(t['provenance']), struct, quotes)


# ---------------------------------------------------------------- 3 课文 T2（采访）
def sec_t2(d):
    t = d['t2']
    gl = t.get('glossar', [])
    parts = []
    for turn in t['dialogue']:
        de = tr_render(turn['sents'], gl, 't2')
        who = turn['who']
        side = 'r' if who.startswith('Lukas') else 'l'
        label = 'Lukas（提问）' if who.startswith('Lukas') else 'Frau Prof. Liu（回答）'
        parts.append('<div class="dlg-turn %s"><span class="dlg-who">%s</span>'
                     '<p class="dlg-de" lang="de">%s</p></div>' % (side, h(label), de))
    struct = ''.join(
        '<div class="stp"><span class="stp-n">%s</span><span class="stp-fn" lang="de">%s</span>'
        '<div class="rm-cn">%s</div></div>' % (h(s['n']), h(s['de']), h(s['cn']))
        for s in t['structure'])
    quotes = ''.join(
        '<div class="qt"><div class="qt-h">%s <span class="src">%s</span></div>'
        '<div class="qt-de" lang="de">»%s«</div><div class="qt-zh">%s</div>'
        '<div class="qt-tip">💡 %s</div></div>'
        % (h(q['n']), h(q['src']), h(q['de']), h(q['zh']), h(q['tip'])) for q in t['quotes'])
    return '''    <section id="t2">
      <h2 class="section-title"><span class="num">2</span> 👤 %s <span class="src src-lg">%s · %s · %s</span></h2>
      <p class="zh-hint">%s</p>
      <p class="zh-hint">✏️ <b>点句子</b>看这句的参考译文；带虚线的词仍可点开看释义、原句与译文。</p>
      <div class="text-card read-card dlg-card">
        <p class="cloze-p dlg-lead" lang="de">%s</p>
        %s
      </div>
      <p class="zh-hint note">📌 %s</p>
      <p class="highlight-box">🧩 教材练习 9 的五个空（本页已按上下文填入，练习仍可在「学以致用」里做一遍）：<span lang="de">Was die Menschen in einem Land glücklich macht</span> / <span lang="de">Was sie früher glücklich machte</span> / <span lang="de">Wer genug zu essen und ein sicheres Zuhause hatte</span> / <span lang="de">Was das Glücksgefühl auslöst</span> / <span lang="de">Wer in solch einem Land lebt</span></p>
      <div class="text-card">
        <h3>🧭 采访的五步推进（对应对话里的位置）</h3>
        %s
      </div>
      <div class="text-card">
        <h3>💬 采访里值得背下来的原话</h3>
        %s
      </div>
    </section>
''' % (h(t['title']), h(t['kind']), h(t['sub']), h(t['page_note']), h(t['lead']),
       tr_render(t['lead_sents'], gl, 't2'), ''.join(parts), h(t['provenance']),
       struct, quotes)


# ------------------------------------------------- 4 词汇精讲（词场表 + 构词 + 词卡）
def sec_vocab(d, v9):
    v = d['vocab']
    wf = v9['wortfelder']
    groups = v['groups']

    tabs, panels = [], []
    for i, g in enumerate(wf['groups']):
        a = ' active' if i == 0 else ''
        tabs.append('<button class="person-btn%s" onclick="switchVocabTab(\'vc2-%s\',this)">%s'
                    '<span class="wf-cnt">%d</span></button>'
                    % (a, g['id'], h(g['label']), len(g['rows'])))
        panels.append('<div class="person-content%s" id="vc2-%s">'
                      '<p class="zh-hint">%s</p>'
                      '<p class="zh-hint note">📖 出处：<span class="src">%s</span></p>%s</div>'
                      % (a, g['id'], h(g['lead']), h(g['src']), wf_table(g['rows'])))

    wb = v9['wortbildung']
    wb_head = ''.join('<th>%s</th>' % h(c) for c in wb['header'])
    wb_rows = ''.join('<tr>%s</tr>' % ''.join('<td lang="de">%s</td>' % h(c) for c in r)
                      for r in wb['rows'])
    wb_card = ('<div class="text-card"><h3>%s</h3><p class="zh-hint">%s</p>'
               '<div class="vocab-table-wrap" style="overflow-x:auto">'
               '<table class="tb"><tr>%s</tr>%s</table></div>'
               '<p class="zh-hint note">%s</p></div>'
               % (h(wb['title']), h(wb['lead']), wb_head, wb_rows, h(wb.get('note', ''))))

    cgroups = []
    for grp in groups:
        cards = ''.join(base.vocab_card(wd, grp.get('src', '')) for wd in grp['words'])
        cgroups.append('<h4 class="card-h">%s <span class="wf-cnt">%d</span>'
                       ' <span class="src">%s</span></h4><div class="vocab-grid">%s</div>'
                       % (h(grp['label']), len(grp['words']), h(grp.get('src', '')), cards))

    full = ''.join('<tr class="wf-grp"><td colspan="4">%s <span class="src">%s</span></td></tr>%s'
                   % (h(g['label']), h(g['src']), wf_rows(g['rows'])) for g in wf['groups'])
    n_wf = sum(len(g['rows']) for g in wf['groups'])
    return '''    <section id="vocab">
      <h2 class="section-title"><span class="num">3</span> 📚 %s <span class="src src-lg">%s</span></h2>
      <p class="zh-hint">%s</p>
      <p class="zh-hint note">👉 每个词条点一下：出这个词的<b>教材例句 + 中文译文 + 常用搭配</b>；搭配句与教材例句为同一句时只印一次。</p>
      <p class="zh-hint note">教材标注：<b>( )</b> 词尾 / 复数形式，<b>¨</b> 变音，<b>+A / +D</b> 支配格；标注降权显示，主词为黑体。</p>
      <div class="person-tabs">%s</div>%s
      %s
      <h3 class="sub-h">🃏 快速过词 · 教材词表 %d 词</h3>
      <p class="zh-hint">上面按词场讲，这里按教材词表过一遍（Vokabeln 1-6 / 1-9）。点卡翻面看中文；右下 ▶ 看词条与出处。</p>
      %s
      %s
      <div id="l1Table" style="display:none"><div class="vocab-table-wrap" style="overflow-x:auto"><table class="tb wf-table">%s</table></div></div>
      <p class="zh-hint note">来源：%s</p>
    </section>
''' % (h(wf['title']), h(wf['src']), h(wf['instruction']), ''.join(tabs), ''.join(panels),
       wb_card, sum(len(g['words']) for g in groups), ''.join(cgroups),
       tools_buttons(['<button class="btn ghost" onclick="toggleBox(\'l1Table\')">📋 展开全表（%d 词条 · 含搭配）</button>' % n_wf]),
       full, h(v['src']))


# ------------------------------------------------- 5 句型库
def sec_satzmuster(v9):
    sm = v9['satzmuster']
    tabs, panels = [], []
    for i, g in enumerate(sm['groups']):
        a = ' active' if i == 0 else ''
        tabs.append('<button class="person-btn%s" onclick="switchVocabTab(\'sm-%s\',this)">%s'
                    '<span class="wf-cnt">%d</span></button>'
                    % (a, g['id'], h(g['label']), len(g['items'])))
        panels.append('<div class="person-content%s" id="sm-%s">'
                      '<p class="zh-hint">%s</p>'
                      '<p class="zh-hint note">📖 出处：<span class="src">%s</span></p>%s</div>'
                      % (a, g['id'], h(g['note']), h(g['src']), sm_items(g['items'])))
    wk = sm['werkstatt']
    return '''    <section id="satzmuster">
      <h2 class="section-title"><span class="num">4</span> 🧩 %s <span class="src src-lg">教材 Lektion 1 · Text 1 / Text 2</span></h2>
      <p class="zh-hint">%s</p>
      <div class="person-tabs">%s</div>%s
      <h3 class="sub-h">%s</h3>
      <p class="zh-hint">%s</p>
      %s
    </section>
''' % (h(sm['title']), h(sm['instruction']), ''.join(tabs), ''.join(panels),
       h(wk['title']), h(wk['note']), sb_cards(wk['items']))


# ------------------------------------------------- 6 语法六讲
def sec_grammar(d):
    units = []
    for u in d['grammar']['units']:
        steps = ''.join('<li>%s</li>' % h(s) for s in u['steps'])
        ex = ''.join('<div class="gm-ex-row"><div class="rm-de" lang="de">%s</div>'
                     '<div class="rm-cn">%s <span class="src">%s</span></div></div>'
                     % (h(e['de']), h(e['zh']), h(e['src'])) for e in u['ex'])
        wrong = ''.join('<div class="sm-wrong-row"><span class="sm-bad" lang="de">✗ %s</span>'
                        '<span class="sm-good" lang="de">✓ %s</span></div>'
                        % (h(w['bad']), h(w['good'])) for w in u['wrong'])
        quiz = ''.join('<div class="gm-q"><p class="gm-qq" lang="de">%s</p>'
                       '<button class="btn ghost gm-btn" onclick="gmShow(this)">看答案</button>'
                       '<div class="gm-a"><span lang="de">%s</span></div></div>'
                       % (h(q['q']), h(q['a'])) for q in u['quiz'])
        units.append('''      <div class="gm-item">
        <div class="gm-head"><span class="gm-no">%s</span> <span class="gm-title">%s</span></div>
        <div class="gm-want">🎯 %s</div>
        <div class="gm-rule">%s</div>
        <ol class="gm-steps">%s</ol>
        <div class="sm-sub">📖 例句</div>%s
        <div class="sm-sub">⚠️ 常见错法</div>%s
        <div class="sm-sub">⏱️ 三十秒自测</div>%s
      </div>''' % (h(u['no']), h(u['title']), h(u['want']), h(u['rule']), steps, ex, wrong, quiz))
    return '''    <section id="grammar">
      <h2 class="section-title"><span class="num">5</span> 🔤 语法六讲 · Grammatik</h2>
      <p class="zh-hint">每讲四件事：说话人想干什么（%d 句话的规则）→ 三步 → 例句 → 三十秒自测。不堆术语，够用就行。</p>
      %s
    </section>
''' % (len(d['grammar']['units']), ''.join(units))


# ---------------------------------------------------------------- 7 连线
def sec_connect(d):
    out = []
    for gi, cg in enumerate(d['connectGrids']):
        idx = list(range(len(cg['pairs'])))
        # 固定种子，保证每次生成一致（可复现）
        order = idx[::2] + idx[1::2]
        left = ''.join('<div class="c-item de" data-pair="%d" data-gid="%d" lang="de" onclick="cClick(this)">%s</div>'
                       % (i, gi, h(p[0])) for i, p in enumerate(cg['pairs']))
        right = ''.join('<div class="c-item cn" data-pair="%d" data-gid="%d" onclick="cClick(this)">%s</div>'
                        % (j, gi, h(cg['pairs'][j][1])) for j in order)
        out.append('''      <div class="connect-game">
        <h3>%s <span class="src src-lg">%s</span></h3>
        <p class="zh-hint">点左列德语，再点右列中文，配对成功变绿；点错会红闪一下，可以重试。</p>
        <div class="connect-field">
          <div class="connect-col">%s</div><div class="connect-col">%s</div>
        </div>
        <div class="connect-score">匹配：<span id="cg-cnt-%d">0</span> / %d</div>
      </div>''' % (h(cg['title']), h(cg.get('src', '')), left, right, gi, len(cg['pairs'])))
    return '''    <section id="connect">
      <h2 class="section-title"><span class="num">6</span> 🔗 连线配对 · Vernetzen</h2>
      <p class="zh-hint">%d 组各连一遍（最后一组是本课介词搭配）：点左列德语，再点右列中文。整组连完，照着左列把德文读一遍。</p>
%s
    </section>
''' % (len(d['connectGrids']), '\n'.join(out))


# ---------------------------------------------------------------- 8 介词填空
def sec_luecken(d):
    lk = d['luecken']
    items = []
    for it in lk['items']:
        items.append('''      <div class="fill-item lk-item">
        <p class="lk-de" lang="de">%s</p>
        <div class="fill-input-line">
          <input class="fill-input" data-ans="%s" placeholder="介词 / 连词 …" lang="de"
                 onkeydown="if(event.key==='Enter')lkCheck(this)">
          <button class="fill-check" onclick="lkCheck(this)">✓</button>
          <span class="fill-result"></span>
        </div>
        <div class="um-tip">💡 %s</div>
      </div>''' % (h(it['de']), esc_attr(it['ans']), h(it['zh'])))
    return '''    <section id="luecken">
      <h2 class="section-title"><span class="num">7</span> ✍️ %s <span class="src src-lg">%s</span></h2>
      <p class="zh-hint">%s</p>
      <p class="zh-hint note">大小写不敏感；答案不唯一时，格与意义正确即算对。</p>
%s
      %s
    </section>
''' % (h(lk['title']), h(lk['src']), h(lk['instruction']), '\n'.join(items),
       tools_buttons(['<button class="btn" onclick="lkCheckAll()">✓ 全部检查</button>',
                      '<button class="btn ghost" onclick="lkRevealAll()">👁 显示答案</button>',
                      '<button class="btn ghost" onclick="lkClearAll()">↺ 清空</button>',
                      '<span id="lkResult" class="kw-result"></span>']))


# ---------------------------------------------------------------- 9 学以致用
def sec_anwenden(v9):
    rc = v9['rede_cloze']
    bank = ''.join('<span class="bank-chip" onclick="clzFill(\'clz-rede\', this)">%s</span>' % h(w)
                   for w in rc['bank'])
    n = 0
    paras = []
    for blk in rc['blocks']:
        txt = h(blk['p'])
        for a in blk['ans']:
            n += 1
            txt = txt.replace('[[%d]]' % n,
                              '<span class="cloze-blank" data-ph="(%d)" data-ans="%s" '
                              'onclick="clzClick(this)">(%d)</span>' % (n, esc_attr(a), n), 1)
        cls = 'cloze-p dlg-line' if n and blk['ans'] else 'cloze-p'
        paras.append('<p class="%s" lang="de">%s</p>' % (cls, txt))

    def sw_block(items):
        out = []
        for i, x in enumerate(items):
            pat = ('<div class="sm-de sw-pat" lang="de">%s</div>' % slot_html(x['pat'])) \
                if x.get('pat') else ''
            de = ('<div class="sw-de" lang="de">%s</div>' % h(x['de'])) if x.get('de') else ''
            ref = x.get('ref') or ''
            ref_html = ('<div class="ref-box" style="display:none"><span class="ref-lbl">参考写法</span>\n'
                        '          <span lang="de">%s</span></div>' % h(ref)) if ref else ''
            out.append('''      <div class="fill-item sw-item">
        <div class="fill-zh">%d. <b>%s</b></div>
        %s%s
        <div class="fill-input-line">
          <textarea class="um-ta" rows="2" placeholder="%s" lang="de"></textarea>
        </div>
        <div class="kw-tools">
          <button class="btn ghost" onclick="refShow(this)">💬 参考写法</button>
          <span class="um-tip">%s</span>
        </div>
        %s
      </div>''' % (i + 1, h(x.get('zh') or x.get('k') or ''), de, pat,
                   esc_attr(x.get('ph', '')), h(x.get('ph', '')), ref_html))
        return ''.join(out)

    sw = v9['schreibwerkstatt']
    return '''    <section id="anwenden">
      <h2 class="section-title"><span class="num">8</span> ✍️ %s</h2>
      <p class="zh-hint">%s</p>
      <p class="zh-hint note">📖 出处：<span class="src">%s</span></p>
      <div class="clz-box" id="clz-rede">
        <div class="bank-box"><strong>Wortbank（教材练习 9 给的五个句子片段）：</strong>%s</div>
        %s
        %s
      </div>
      <h3 class="sub-h">🔄 改写 · 按括号里的要求重写</h3>
      %s
      <h3 class="sub-h">🀄 中译德 · 用上这一课的句型</h3>
      %s
      <h3 class="sub-h">%s</h3>
      <p class="zh-hint">%s</p>
      %s
    </section>
''' % (h(sw['title']), h(sw['instruction']), h(rc['src']), bank, '\n'.join(paras),
       base.tools_buttons(['<button class="btn" onclick="clzCheck(\'clz-rede\')">✓ 检查</button>',
                           '<button class="btn ghost" onclick="clzReveal(\'clz-rede\')">👁 显示答案</button>',
                           '<button class="btn ghost" onclick="clzClear(\'clz-rede\')">↺ 清空</button>',
                           '<span id="clz-rede-res" class="kw-result"></span>']),
       sw_block(sw['rewrite']), sw_block(sw['translate']),
       h(sw['interview']['title']), h(sw['interview']['instruction']),
       sw_block(sw['interview']['items']))


# ---------------------------------------------------------------- 10 快问快答
def sec_quiz(d):
    q = d['quiz']
    items = ''.join(
        '<div class="qz-item" data-a="%d"><p class="qz-q">%d. %s</p><div class="qz-opts">%s</div></div>'
        % (it['a'], i + 1, h(it['q']),
           ''.join('<span class="qz-opt" onclick="qzPick(this)" lang="de">%s %s</span>'
                   % (chr(65 + k), h(o)) for k, o in enumerate(it['opts'])))
        for i, it in enumerate(q['items']))
    return '''    <section id="quiz">
      <h2 class="section-title"><span class="num">9</span> ✅ %s <span class="src src-lg">%s</span></h2>
      <p class="zh-hint">%s</p>
      <div class="qz-box" id="qz-l1">%s</div>
      %s
    </section>
''' % (h(q['title']), h(q['src']), h(q['instruction']), items,
       tools_buttons(['<button class="btn" onclick="qzCheck(\'qz-l1\')">✓ 检查</button>',
                      '<button class="btn ghost" onclick="qzClear(\'qz-l1\')">↺ 清空</button>',
                      '<span id="qz-l1-res" class="kw-result"></span>']))


# ---------------------------------------------------------------- 11 翻译卡
def sec_translation(d):
    t = d['translation']
    cards = []
    for i, c in enumerate(t['cards'], 1):
        cards.append('''        <div class="tc-card" onclick="flipTrans(this)">
          <div class="tc-inner">
            <div class="tc-front"><span class="tc-num">%d</span>
              <div class="tc-de" lang="de">%s</div>
              <div class="tc-tip">📖 %s</div></div>
            <div class="tc-back"><span class="tc-num">%d</span>
              <div class="rm-cn">%s</div><div class="tc-tip">💡 %s</div></div>
          </div>
        </div>''' % (i, h(c['de']), h(c['src']), i, h(c['zh']), h(c['tip'])))
    return '''    <section id="translation">
      <h2 class="section-title"><span class="num">10</span> 🎯 %s</h2>
      <p class="zh-hint">%s</p>
      <p class="zh-hint note">%s</p>
      <div class="translation-grid">%s</div>
    </section>
''' % (h(t['title']), h(t['instruction']), h(t['note']), '\n'.join(cards))


# ---------------------------------------------------------------- CSS
CSS_L1 = '''
  /* ===== 语法强调 / 原句卡 / 对话排版 ===== */
  /* 标题两行时均分，避免「Z」这类单字母孤行 */
  h1, h2, h3, h4 { text-wrap: balance; }
  .gh { color: #123a72; font-weight: 700; }
  .qt { border-left: 3px solid #1a73e8; padding-left: 12px; margin: 10px 0; }
  .qt-h { font-weight: 700; font-size: var(--fs-sm); color: #123a72; margin-bottom: 4px; }
  .qt-de { font-size: var(--fs-body); line-height: 1.75; }
  .qt-zh { color: #3c4450; font-size: var(--fs-sm); margin-top: 4px; }
  .qt-tip { color: #5f6672; font-size: var(--fs-sm); line-height: 1.7; margin-top: 4px; }
  /* ===== 双声部（Oma / Emilie 左右对照）===== */
  .duo-wrap { margin-top: var(--sp-3); }
  .duo { background: #fff; border: 1px solid #e3e6eb; border-radius: 10px;
         padding: var(--sp-3); margin-bottom: var(--sp-3); }
  .duo-h { font-weight: 700; color: #123a72; font-size: var(--fs-sm); margin-bottom: var(--sp-2); }
  .duo-n { display: inline-block; background: #17427f; color: #fff; border-radius: 6px;
           padding: 0 8px; margin-right: 4px; font-size: var(--fs-cap); }
  .duo-t { margin-right: 6px; }
  .duo-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
              gap: var(--sp-3); }
  .duo-col { background: #fbfcfe; border: 1px solid #e3e6eb; border-radius: 10px;
             padding: var(--sp-2) var(--sp-3); }
  .duo-col.oma { border-left: 3px solid #8a6d1f; }
  .duo-col.emi { border-left: 3px solid #146c2e; }
  .duo-who { display: inline-block; font-size: var(--fs-cap); font-weight: 700; color: #123a72;
             background: #e8f0fe; border-radius: 6px; padding: 2px 8px; margin-bottom: 4px; }
  .duo-col.oma .duo-who { background: #fdf7e6; color: #8a6d1f; }
  .duo-col.emi .duo-who { background: #e6f4ea; color: #146c2e; }
  .duo-de { margin: 0; font-size: var(--fs-body); line-height: 1.85; }
  /* ===== 对话（Lukas / Frau Prof. Liu）===== */
  .dlg-card .dlg-lead { margin-bottom: 14px; }
  .dlg-turn { margin: 0 0 10px; max-width: 94%; }
  .dlg-turn.l { margin-right: auto; }
  .dlg-turn.r { margin-left: auto; }
  .dlg-who { display: inline-block; font-size: var(--fs-cap); font-weight: 700; color: #123a72;
             background: #e8f0fe; border-radius: 6px; padding: 2px 8px; margin-bottom: 4px; }
  .dlg-turn.r .dlg-who { background: #e6f4ea; color: #146c2e; }
  .dlg-de { margin: 0; font-size: var(--fs-body); line-height: 1.75;
            background: #fff; border: 1px solid #e3e6eb; border-radius: 10px; padding: 8px 12px; }
  .dlg-turn.r .dlg-de { background: #fbfcfe; }
  /* ===== 介词填空 ===== */
  .lk-item .lk-de { font-size: var(--fs-word); line-height: 1.9; margin: 0 0 8px; }
  .lk-item { border-left: 3px solid #1a73e8; }
  /* ===== 翻译卡 ===== */
  .tc-front .rm-cn { font-size: var(--fs-body); line-height: 1.6; }
  .translation-grid { align-items: stretch; }
  .tc-card { min-width: 0; }
  .tc-front, .tc-back { overflow-wrap: anywhere; }
  .vc-card .vc-detail, .vc-detail { width: 36px; height: 36px; font-size: 15px; opacity: .9; }
  .vc-front, .vc-back { padding-bottom: 40px; }
  /* 词卡正面：长复合词按德语音节断行（基底是 overflow-wrap:anywhere → 会断出单字母孤行）*/
  .vc-front .vc-w, .vc-back .vc-w, .vc-front, .vc-back {
    overflow-wrap: break-word; hyphens: auto; -webkit-hyphens: auto;
  }

  /* ===== 词场表 / 句型库 / 学以致用 ===== */
  .card-h { margin: 16px 0 8px; font-size: var(--fs-sm); color: #17427f; }
  .wf-cnt { display: inline-block; font-size: var(--fs-cap); background: #e8f0fe; color: #17427f;
            border-radius: 8px; padding: 0 8px; margin-left: 4px; vertical-align: 1px; }
  .wf-table { width: 100%; table-layout: fixed; font-size: var(--fs-sm); }
  .wf-table th { background: #eef3fa; color: #17427f; font-size: var(--fs-cap); text-align: left; }
  .wf-table th:nth-child(1), .wf-table td:nth-child(1) { width: 21%; }
  .wf-table th:nth-child(2), .wf-table td:nth-child(2) { width: 26%; }
  .wf-table th:nth-child(3), .wf-table td:nth-child(3) { width: 25%; }
  .wf-w { font-weight: 700; color: #123a72; }
  .wf-table .wf-w, .wf-table .wf-coll, .wf-table .wf-ex { overflow-wrap: break-word; }
  .wf-table .vc-w { overflow-wrap: break-word; hyphens: auto; -webkit-hyphens: auto; }
  .wf-w .vc-note { color: #5f6672; font-weight: 400; font-size: var(--fs-cap); white-space: nowrap; }
  .wf-cn { color: #1d1d1f; }
  .wf-coll { color: #3c4450; }
  .wf-ex { color: #3c4450; }
  .wf-none { color: #5f6672; }
  .wf-grp td { background: #17427f; color: #fff; font-weight: 700; border-radius: 0; }
  .sub-h { margin: 16px 0 8px; font-size: var(--fs-body); color: #123a72; }
  .sm-item { background: #fff; border: 1px solid #e3e6eb; border-left: 3px solid #17427f;
             border-radius: 10px; padding: 12px 16px; margin-bottom: 12px; }
  .sm-fn { font-weight: 700; color: #17427f; font-size: var(--fs-sm); margin-bottom: 8px; }
  .sm-de { font-size: var(--fs-word); line-height: 1.85; margin: 0 0 8px; color: #111; }
  .sm-de .slot { background: #fff3cf; border-bottom: 2px solid #d9a300; padding: 0 2px;
                 border-radius: 3px; }
  .sm-zh { color: #3c4450; font-size: var(--fs-sm); }
  .sm-tip { color: #5f6672; font-size: var(--fs-sm); line-height: 1.7; margin-top: 4px; }
  .sm-cat { font-weight: 700; color: #17427f; }
  .sm-sub { font-weight: 700; color: #17427f; font-size: var(--fs-sm);
            margin: 12px 0 6px; }
  .sm-ex-row { border-left: 2px solid #d9a300; padding-left: 10px; margin-bottom: 8px; }
  .sm-ex-de { font-size: var(--fs-body); line-height: 1.75; color: #1d1d1f; }
  .sm-ex-zh { font-size: var(--fs-sm); color: #3c4450; margin-top: 2px; }
  .sm-slot-row { font-size: var(--fs-body); line-height: 1.8; color: #1d1d1f;
                 background: #f8fafc; border-radius: 8px; padding: 6px 10px; margin-bottom: 6px; }
  .sm-slot-hint { display: block; font-size: var(--fs-sm); color: #5f6672; }
  .sm-wrong-row { margin-bottom: 6px; font-size: var(--fs-body); line-height: 1.7; }
  .sm-bad { display: block; color: #a4262c; }
  .sm-good { display: block; color: #146c2e; }
  .sw-item { border-left: 3px solid #2e7d32; }
  .sw-de { font-size: var(--fs-body); line-height: 1.8; color: #1d1d1f; margin-bottom: 6px; }
  .sw-pat { font-size: var(--fs-body); line-height: 1.8; background: #f8fafc;
            border-radius: 8px; padding: 8px 12px; margin: 8px 0; }
  #anwenden .fill-zh { font-size: var(--fs-body); }
  #anwenden .um-ta { width: 100%; font-family: inherit; font-size: var(--fs-body); padding: 8px 12px;
                     border: 1px solid #cfd6e0; border-radius: 8px; }
  .cloze-p.dlg-line { padding-left: 8px; border-left: 2px solid #e3e6eb; }

  /* ===== 语法六讲 ===== */
  .gm-item { background: #fff; border: 1px solid #e3e6eb; border-left: 3px solid #17427f;
             border-radius: 10px; padding: 12px 16px; margin-bottom: 12px; }
  .gm-head { font-size: var(--fs-word); font-weight: 700; color: #123a72; margin-bottom: 6px; }
  .gm-no { display: inline-block; background: #17427f; color: #fff; border-radius: 6px;
           padding: 0 8px; font-size: var(--fs-sm); margin-right: 4px; }
  .gm-want { font-size: var(--fs-sm); color: #17427f; background: #eef3fa; border-radius: 8px;
             padding: 6px 10px; margin-bottom: 8px; }
  .gm-rule { font-size: var(--fs-body); line-height: 1.75; color: #1d1d1f;
             border-left: 3px solid #d9a300; padding-left: 10px; margin-bottom: 8px; }
  .gm-steps { margin: 0 0 8px; padding-left: 22px; }
  .gm-steps li { font-size: var(--fs-sm); color: #3c4450; line-height: 1.8; }
  .gm-ex-row { border-left: 2px solid #d9a300; padding-left: 10px; margin-bottom: 8px; }
  .gm-q { border-top: 1px dashed #dfe4ea; padding-top: 8px; margin-top: 8px; }
  .gm-qq { font-size: var(--fs-body); line-height: 1.7; margin: 0 0 6px; }
  .gm-btn { margin-bottom: 6px; }
  .gm-a { display: none; font-size: var(--fs-body); line-height: 1.7; color: #146c2e;
          background: #e6f4ea; border-radius: 8px; padding: 6px 10px; }
  .gm-q.open .gm-a { display: block; }

  /* ===== 逐句点译 ===== */
  .tr-s { cursor: pointer; border-radius: 4px; }
  .tr-s:hover { background: #f2f7ff; }
  .tr-zh { display: none; background: #fff8e6; color: #7a5b12; border-left: 2px solid #d9a300;
           border-radius: 4px; padding: 0 8px; margin: 0 4px; font-size: .92em; }
  .tr-s.open { background: #f2f7ff; }
  .tr-s.open .tr-zh { display: inline; }
  .tr-p { line-height: 2; }

  /* ===== 词条点开面板 ===== */
  .wf-w { cursor: pointer; }
  .wf-w:hover { background: #f2f7ff; }
  .wf-more { display: inline-block; margin-left: 4px; font-size: var(--fs-cap); font-weight: 400;
             color: #17427f; background: #e8f0fe; border-radius: 6px; padding: 0 8px;
             vertical-align: 1px; white-space: nowrap; }
  .vp-sec { font-size: var(--fs-cap); font-weight: 700; color: #17427f; margin: 12px 0 4px; }
  .vp-de { font-size: var(--fs-body); line-height: 1.7; color: #1d1d1f; }
  .vp-tr { font-size: var(--fs-body); line-height: 1.7; color: #7a5b12; background: #fff8e6;
           border-radius: 6px; padding: 4px 8px; margin-top: 4px; }
  .vp-none { font-size: var(--fs-sm); color: #5f6672; }
  #vpEx .vp-tr { border-left: 2px solid #d9a300; margin-top: 4px; padding: 4px 8px; }
  .vp-lb { font-weight: 700; color: #8a6d1f; margin-right: 6px; }
  #vpEx .vp-def { margin-top: 8px; font-size: var(--fs-sm); line-height: 1.7; color: #5f6672; }
  #vpEx .vp-def .vp-lb { color: #5f6672; }
  .wf-both { color: #3c4450; }
  .vp-note { margin-top: 8px; font-size: var(--fs-sm); line-height: 1.7; color: #8a6d1f;
             background: #fdf7e6; border-radius: 6px; padding: 4px 8px; }
  /* 手机：四列词场表改成逐词块；点开的译文另起一行 */
  @media (max-width: 640px) {
    .wf-table, .wf-table tr, .wf-table td { display: block; width: auto !important; }
    .wf-table th { display: none; }
    .wf-table tr { border-bottom: 1px solid #e6eaf0; padding: 8px 0; }
    .wf-table td { border: 0; padding: 0 0 4px; }
    .wf-table td[data-l]::before { content: attr(data-l) '：'; color: #5f6672;
                                   font-size: var(--fs-cap); margin-right: 4px; }
    .wf-table tr.wf-grp { padding: 0; border: 0; }
    .wf-table tr.wf-grp td { background: #17427f; color: #fff; padding: 8px;
                             border-radius: 6px; }
    .wf-more { display: none; }
    .tr-zh { margin: 0; }
    #t1 .tr-s.open .tr-zh, #t2 .tr-s.open .tr-zh { display: block; margin: 4px 0 0; }
  }
'''

JS_L1 = '''
/* ===== 逐句点译 ===== */
function trToggle(el){ el.classList.toggle('open'); }
/* ===== 语法自测：点开看答案 ===== */
function gmShow(btn){
  const q = btn.closest('.gm-q');
  if (!q) return;
  q.classList.toggle('open');
  btn.textContent = q.classList.contains('open') ? '收起答案' : '看答案';
}
/* ===== 课文点词面板（覆盖基底 showVocab）：例句 + 例句译文 + 常用搭配 ===== */
function showVocab(w, cn, ex, tr, def){
  document.getElementById('vpWord').textContent = w || '';
  document.getElementById('vpZh').textContent = cn || '';
  const box = document.getElementById('vpEx');
  if (tr || def){
    const parts = [];
    if (ex) parts.push('<div class="vp-de" lang="de">' + wfEsc(ex) + '</div>');
    if (tr) parts.push('<div class="vp-tr"><span class="vp-lb">参考译文</span>'
      + wfEsc(tr) + '</div>');
    if (def) parts.push('<div class="vp-def"><span class="vp-lb">常用搭配</span>'
      + wfEsc(def) + '</div>');
    box.innerHTML = parts.join('');
  } else {
    box.textContent = ex || '';
  }
  document.getElementById('vocabPanel').classList.add('show');
  document.getElementById('vocabOverlay').classList.add('show');
}
/* ===== 词条面板：教材例句 + 中文译文 + 常用搭配 ===== */
function wfEsc(s){ return String(s == null ? '' : s).replace(/[&<>]/g, function(c){
  return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c]; }); }
function wfShow(cell){
  const d = cell.dataset;
  document.getElementById('vpWord').textContent = d.w || '';
  document.getElementById('vpZh').textContent = d.cn || '';
  const same = d.same === '1';
  const parts = [];
  if (d.ex){
    parts.push('<div class="vp-sec">' + (same ? '教材例句 · 常用搭配' : '教材例句')
      + ' <span class="src">教材原句</span></div>'
      + '<div class="vp-de" lang="de">' + wfEsc(d.ex) + '</div>');
    if (d.zh) parts.push('<div class="vp-tr">' + wfEsc(d.zh) + '</div>');
  } else {
    parts.push('<div class="vp-sec">教材例句</div>'
      + '<div class="vp-none">教材此页无例句，看下面的常用搭配。</div>');
  }
  if (!same && d.coll) parts.push('<div class="vp-sec">常用搭配</div>'
    + '<div class="vp-de" lang="de">' + wfEsc(d.coll) + '</div>');
  document.getElementById('vpEx').innerHTML = parts.join('');
  document.getElementById('vocabPanel').classList.add('show');
  document.getElementById('vocabOverlay').classList.add('show');
}
/* ===== 介词填空（逐题核对）===== */
function lkCheck(el){
  const line = el.closest('.fill-input-line');
  const inp = line.querySelector('input');
  const res = line.querySelector('.fill-result');
  const val = inp.value.trim();
  const ok = !!val && norm(val) === norm(inp.dataset.ans);
  inp.classList.remove('ok', 'bad'); inp.classList.add(ok ? 'ok' : 'bad');
  if (res){ res.textContent = ok ? '✓ richtig' : (val ? '✗ 再想想' : '');
            res.className = 'fill-result ' + (ok ? 'correct' : 'wrong'); }
  return ok;
}
function lkCheckAll(){
  let ok = 0, tot = 0;
  document.querySelectorAll('#luecken .lk-item').forEach(function(item){
    tot++;
    if (lkCheck(item.querySelector('.fill-check'))) ok++;
  });
  document.getElementById('lkResult').textContent = '正确 ' + ok + ' / ' + tot + ' 题';
}
function lkRevealAll(){
  document.querySelectorAll('#luecken .lk-item').forEach(function(item){
    const inp = item.querySelector('input');
    const res = item.querySelector('.fill-result');
    inp.value = inp.dataset.ans; inp.classList.remove('bad'); inp.classList.add('ok');
    if (res){ res.textContent = ''; res.className = 'fill-result'; }
  });
  document.getElementById('lkResult').textContent = '已显示参考答案';
}
function lkClearAll(){
  document.querySelectorAll('#luecken .lk-item').forEach(function(item){
    const inp = item.querySelector('input');
    const res = item.querySelector('.fill-result');
    inp.value = ''; inp.classList.remove('ok', 'bad');
    if (res){ res.textContent = ''; res.className = 'fill-result'; }
  });
  document.getElementById('lkResult').textContent = '';
}
'''


# ---------------------------------------------------------------- assemble
def main():
    with open(DATA_FILE, encoding='utf-8') as f:
        d = json.load(f)
    with open(VOCAB_FILE, encoding='utf-8') as f:
        v9 = json.load(f)
    with open(TEXT_ZH_FILE, encoding='utf-8') as f:
        TEXT_ZH.update(json.load(f))
    with open(VOCAB_ZH_FILE, encoding='utf-8') as f:
        VOCAB_ZH.update(json.load(f).get('ex', {}))

    # 搭配连线并入连线节（数据结构与 connectGrids 同形）
    d['connectGrids'].append({'title': v9['kollokationen']['title'],
                              'src': v9['kollokationen']['src'],
                              'pairs': v9['kollokationen']['pairs']})

    secs = [('home', '首页'), ('t1', '📖 T1 童年'), ('t2', '👤 T2 采访'), ('vocab', '📚 词汇精讲'),
            ('satzmuster', '🧩 句型库'), ('grammar', '🔤 语法六讲'), ('connect', '🔗 连线'),
            ('luecken', '✍️ 填空'), ('anwenden', '✍️ 学以致用'), ('quiz', '✅ 快问快答'),
            ('translation', '🎯 翻译卡')]

    css = open(os.path.join(DIR, 'template_css.css'), encoding='utf-8').read()
    css = css.replace('</style>', base.EXTRA_CSS + t12.CSS_EXTRA + CSS_L1 + '</style>')

    nav = ('<nav><div class="top-nav"><div class="logo" style="cursor:pointer" onclick="switchSection(\'home\')">'
           '<span class="logo-icon">🎓</span><span>Lektion 1 · Rund um das Glück</span></div>'
           '<div class="nav-links" id="navLinks">')
    for sid, lbl in secs:
        nav += '<button onclick="switchSection(\'%s\')">%s</button>' % (sid, lbl)
    nav += ('</div><button class="hamburger" onclick="toggleNav()">☰</button></div>'
            '<div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div></nav>')

    body = (sec_home(d, v9) + sec_t1(d) + sec_t2(d) + sec_vocab(d, v9) + sec_satzmuster(v9) +
            sec_grammar(d) + sec_connect(d) + sec_luecken(d) + sec_anwenden(v9) +
            sec_quiz(d) + sec_translation(d))

    core_js = base.CORE_JS.replace('__SECTIONS__', json.dumps([s[0] for s in secs]))
    data_js = json.dumps({'sb': SB_DOC}, ensure_ascii=False)

    html = ('<!DOCTYPE html>\n<html lang="zh-CN" data-cw-profile="interaction">\n<head>\n'
            '<meta charset="UTF-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1.0">\n'
            '<title>Lektion 1 · Rund um das Glück · 互动课件</title>\n'
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
            '<script>\nconst DOC = ' + data_js + ';\n' + core_js + '\n' + base.EXTRA_JS + '\n'
            + t12.JS_EXTRA + '\n' + JS_L1 + '\n</script>\n</body>\n</html>\n')

    # 学生向措辞归一化：共用基底里带有教师向旧措辞，本页定点替换
    for _a, _b in [('已显示参考答案（教师用）', '已显示参考答案'),
                   ('（课堂现场用，宽屏才显示）', '（宽屏才显示）'),
                   ('（投影时不用弹窗）', '')]:
        html = html.replace(_a, _b)

    # 换行质量：「 · 」分隔符两侧都粘住（既不让「·」起行，也不把标签断成两截）
    html = html.replace(' · ', '\u00a0·\u00a0')
    html = html.replace('\u00a0· ', '\u00a0·\u00a0')

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(html)
    print('Generated: %s (%d bytes)' % (OUT, len(html)))

    # --- JS 语法自检 ---
    js = html[html.find('<script>') + 8: html.rfind('</script>')]
    r = subprocess.run(['node', '-e',
                        'try{require("vm").compileFunction(JSON.parse(process.argv[1]));console.log("JS OK")}'
                        'catch(e){console.log("JS ERROR: "+e.message.substring(0,200))}',
                        json.dumps(js)], capture_output=True, text=True, timeout=30)
    print(r.stdout.strip() or r.stderr[:300])

    # --- 结构自检 ---
    print('sections open=%d close=%d' % (html.count('<section'), html.count('</section>')))
    for sid, _ in secs:
        assert 'id="%s"' % sid in html, 'missing section ' + sid
    print('all %d section ids present | nav items = %d' % (len(secs), len(secs)))
    assert '%%' not in html, '标记未替换干净'

    # --- 逐句点译覆盖率：缺一条都不算过 ---
    t1s = list(d['t1']['landeskunde'])
    for turn in d['t1']['intro']:
        t1s += turn['sents']
    for b in d['t1']['blocks']:
        t1s += b['oma'] + b['emilie']
    t2s = list(d['t2']['lead_sents'])
    for turn in d['t2']['dialogue']:
        t2s += turn['sents']
    n_tr = html.count('class="tr-s"')
    exp_tr = len(t1s) + len(t2s)
    if MISSING_TR:
        print('❌ 有 %d 句无译文：' % len(MISSING_TR))
        for s in MISSING_TR[:10]:
            print('   ', s)
    print('逐句点译: %d 个可点句（应 %d / 缺译文 %d）| T1 %d 句 · T2 %d 句'
          % (n_tr, exp_tr, len(MISSING_TR), len(t1s), len(t2s)))
    assert not MISSING_TR, '有句子缺译文'
    assert n_tr == exp_tr, '可点句数 %d ≠ 课文句数 %d' % (n_tr, exp_tr)

    # --- 虚线词例句译文覆盖率 ---
    gl_all = [(k, e) for k in ('t1', 't2') for e in d[k]['glossar']]
    miss_gl = [(k, e['w'], e.get('ex', '')) for k, e in gl_all
               if e.get('ex') and not VOCAB_ZH.get(e['ex'])]
    n_gl = sum(1 for _, e in gl_all if e.get('ex'))
    print('点词例句译文: %d/%d 条（缺 %d）' % (n_gl - len(miss_gl), n_gl, len(miss_gl)))
    for k, w, ex in miss_gl[:8]:
        print('   ✗ %s %s | %s' % (k, w, ex[:70]))
    assert not miss_gl, '有点词例句缺中文译文'

    # --- 词场表同行去重 ---
    dup_rows = [(g['label'], r['w']) for g in v9['wortfelder']['groups'] for r in g['rows']
                if _same_de(r.get('ex', ''), r.get('coll', ''))]
    n_both = html.count('class="wf-both"')
    print('搭配＝例句（合并为一格）: %d 个词条 → 渲染 %d 格' % (len(dup_rows), n_both))
    assert n_both == len(dup_rows), '合并格数 %d ≠ 重复词条数 %d' % (n_both, len(dup_rows))
    bad_tr = 0
    for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.S):
        cells = re.findall(r'<td[^>]*class="wf-(?:coll|ex|both)"[^>]*>(.*?)</td>', tr, re.S)
        txt = [re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', c)).strip().rstrip('.').lower()
               for c in cells]
        if len(txt) > 1 and len(set(txt)) != len(txt):
            bad_tr += 1
    print('同行重复终检: 仍重复的行 = %d（应 0）' % bad_tr)
    assert bad_tr == 0, '词场表仍有同一行内重复的德文'

    # --- 数据量核对 ---
    print('vc-card = %d (词表 %d) | gl = %d (glossar %d) | c-item = %d (pairs %d)'
          % (html.count('class="vc-card"'), sum(len(g['words']) for g in d['vocab']['groups']),
             html.count('class="gl"'), len(d['t1']['glossar']) + len(d['t2']['glossar']),
             html.count('class="c-item'), sum(len(g['pairs']) for g in d['connectGrids']) * 2))
    print('lk-item = %d | qz-item = %d | tc-card = %d | stp = %d | qt = %d | duo = %d | gm-item = %d | sm-item = %d | sb-card = %d'
          % (html.count('class="fill-item lk-item"'), html.count('class="qz-item"'),
             html.count('class="tc-card"'), html.count('class="stp"'), html.count('class="qt"'),
             html.count('class="duo"'), html.count('class="gm-item"'),
             html.count('class="sm-item"'), html.count('class="sb-card"')))
    assert html.count('class="tc-card"') == len(d['translation']['cards'])
    assert html.count('class="duo"') == len(d['t1']['blocks'])
    assert html.count('class="gm-item"') == len(d['grammar']['units'])
    assert html.count('class="fill-item lk-item"') == len(d['luecken']['items'])
    assert html.count('class="sm-item"') == sum(len(g['items']) for g in v9['satzmuster']['groups'])
    assert html.count('class="sb-card"') == len(v9['satzmuster']['werkstatt']['items'])


if __name__ == '__main__':
    main()
