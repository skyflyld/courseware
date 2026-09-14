#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_l8_berufe.py — Lektion 8《Was will ich werden? Was kann ich werden?》课堂互动课件生成器
输入: l8-data.json
输出: lektion8-berufe-interaktiv.html  (单文件, 自包含 CSS/JS, 零外部请求)
原子原则: 一个脚本 → 一个产物, 不在产物上做增量修补。
数据纪律: 所有德文/中文一律取 l8-data.json 原值, 不改写、不补造；数字与 JSON 一致。
"""
import json
import os
import random
import re
import subprocess
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(DIR, 'l8-data.json')
OUT = os.path.join(DIR, 'lektion8-berufe-interaktiv.html')


# ---------------------------------------------------------------- helpers
def h(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def esc_attr(s):
    return h(s).replace('"', '&quot;')


TOK_RE = re.compile(
    r'\([^()]*\)|\[[^\[\]]*\]|\+\s*(?:A|D|G|Akk|Dat|Gen)(?:\s*(?:\+|/)\s*(?:A|D|G|Akk|Dat|Gen))*'
    r'|\+\s*mit\s+\w+|nur\s+Sg|meist\s+Sg|\s+-\S*', re.I)


def word_html(w):
    """词条渲染：主词加粗；教材标注降权（小一号 + 灰）。
    标注形态： ( ) 复数/变格词尾 · [ ] 读音 · +A/+D/+mit Dat 支配格 · nur Sg 仅单数
    从词条尾部反复剥离标注 token，剩余的即主词。"""
    w = str(w)
    rest, toks = w, []
    while True:
        m = re.search(r'\s*(' + TOK_RE.pattern + r')\s*$', rest, re.I)
        if not m:
            break
        toks.insert(0, m.group(1).strip())
        rest = rest[:m.start()].strip()
    if not toks or not rest:
        return '<span class="vc-w">%s</span>' % h(w)
    notes = ''
    for tok in toks:
        if tok.startswith('['):
            cls = 'vc-note vc-phon'
        elif tok.startswith('-'):
            # 复数词尾（-en / -e/-s / 单个 -）单独包一层禁断，
            # 否则浏览器会在连字符后折断成「die Anforderung -」+「en」
            cls = 'vc-note vc-pl'
        else:
            cls = 'vc-note'
        notes += '<span class="%s">%s</span>' % (cls, h(tok))
    return '<span class="vc-w">%s</span>%s' % (h(rest), notes)


def vocab_card(wd, src):
    ex = '📖 出处：' + src
    return ('<div class="vc-card" onclick="flipCard(this)"><div class="vc-inner">'
            '<div class="vc-front" lang="de">%s</div>'
            '<div class="vc-back">%s</div></div>'
            '<button class="vc-detail" title="词条与出处" '
            'onclick="event.stopPropagation();showVocab(\'%s\',\'%s\',\'%s\')">▶</button></div>'
            % (word_html(wd['w']), h(wd['cn']), esc_attr(wd['w']), esc_attr(wd['cn']), esc_attr(ex)))


def tools_buttons(buttons):
    return '<div class="kw-tools">%s</div>' % ''.join(buttons)


# ---------------------------------------------------------------- 1 home
def sec_home(d):
    m = d['meta']
    objs = ''.join('<li>%s</li>' % h(x) for x in m['objectives'])
    rows = []
    for item in m['flow']:
        if '：' in item:
            a, b = item.split('：', 1)
        else:
            a, b = item, ''
        rows.append('<tr><td class="fl-t">%s</td><td>%s</td></tr>' % (h(a), h(b)))
    n_e1 = sum(len(g['words']) for g in d['vocabGroups'])
    n_e2 = sum(len(g['words']) for g in d['vocabGroupsE2']['groups'])
    n_conn = sum(len(g['pairs']) for g in d['connectGrids'])
    cards = [
        ('vocab', '📇 E1 词汇卡片', '%d 词 · 四组翻转卡（正面德语，翻面中文）' % n_e1),
        ('vocab2', '📗 E2 词汇卡片', '%d 词 · Entdecken 2 · 四组翻转卡' % n_e2),
        ('blitz', '⚡ Blitzrunde 抢答', '%d 张中德卡 · 带计时器' % len(d['blitz'])),
        ('connect', '🔗 连线配对', '%d 组 · %d 对（任务 / 利弊 / 名词↔形容词）' % (len(d['connectGrids']), n_conn)),
        ('mindmap', '🗺️ Wortfeld Beruf 词场', '%d 类 · %d 词块归类' % (len(d['mindmap']['cats']), len(d['mindmap']['words']))),
        ('luecken', '✍️ Ü2 动词填空', '%d 空 · 词库选词 + 检查' % len(d['luecken']['gaps'])),
        ('eigenschaften', '🧩 Eigenschaften 属性', '%d 组名词↔形容词 + %d 条描述配对' % (len(d['eigenschaften']['table']), len(d['eigenschaften']['match']))),
        ('softskills', '🎯 Ü2 Soft Skills', '%d 空 · 三选一' % len(d['softskills']['gaps'])),
        ('umformen', '🔤 Ü9 改写', '%d 句 · zwar … aber 等句型' % len(d['umformen']['items'])),
        ('redemittel', '💬 Redemittel 表达库', '%d 栏优缺点 + %d 栏统计描述' % (len(d['redemittel']['vorteile']['cols']), len(d['redemittel']['statistik']['cols']))),
        ('berufe', '🃏 Beruferaten 猜职业', '%d 张任务卡 + 示例对话' % len(d['berufe']['tasks'])),
        ('uebersetzen', '🎯 Ü11 中译德', '%d 句 · 中文原文 + 参考译文' % len(d['uebersetzen']['sentences'])),
        ('spiele', '🏆 课堂游戏 & 计分板', '%d 个活动 + A/B 计分 + 计时' % len(d['klassenspiele'])),
    ]
    g = ''.join('<div class="text-card home-card" onclick="switchSection(\'%s\')"><h3>%s</h3><p>%s</p></div>'
                % (i, t, s) for i, t, s in cards)
    return '''    <section id="home" class="active">
      <div class="hero">
        <h1>%s</h1>
        <p class="sub">%s</p>
        <p class="meta">%s</p>
      </div>
      <div class="highlight-box">🎬 课堂用法：点顶部导航切节，题目右上角标教材出处，点卡片翻面，点「检查」核对答案，投影时点右下 A± 放大。</div>
      <div class="home-grid">%s</div>
      <div class="obj-box"><strong>学习目标 Lernziele：</strong><ul>%s</ul></div>
      <div class="text-card" style="margin-top:12px">
        <h3>⏱️ 课堂流程（建议）</h3>
        <table class="flow-table">%s</table>
      </div>
    </section>
''' % (h(m['title']), h(m['subtitle']), h(m['source']), g, objs, ''.join(rows))


# ---------------------------------------------------------------- 2 vocab (E1)
def sec_vocab(d):
    groups = d['vocabGroups']
    tabs, panels = [], []
    for i, grp in enumerate(groups):
        a = ' active' if i == 0 else ''
        tabs.append('<button class="person-btn%s" onclick="switchVocabTab(\'vc-%s\',this)">%s</button>'
                    % (a, grp['id'], h(grp['label'])))
        cards = ''.join(vocab_card(wd, grp.get('src', '')) for wd in grp['words'])
        panels.append('<div class="person-content%s" id="vc-%s">'
                      '<p class="zh-hint note">📖 出处：<span class="src">%s</span></p>'
                      '<div class="vocab-grid">%s</div></div>'
                      % (a, grp['id'], h(grp.get('src', '')), cards))
    rows = ''.join('<tr><td class="vt-de" lang="de">%s</td><td class="vt-cn">%s</td></tr>'
                   % (word_html(wd['w']), h(wd['cn']))
                   for grp in groups for wd in grp['words'])
    n = sum(len(g['words']) for g in groups)
    return '''    <section id="vocab">
      <h2 class="section-title"><span class="num">1</span> 📇 词汇卡片 E1 · Wortschatzkarten</h2>
      <p class="zh-hint">点卡片翻面看中文，点右下 ▶ 看词条与出处。读名词请带冠词，说动词请带支配格。</p>
      <p class="zh-hint note">教材标注：<b>( )</b> 词尾 / 复数形式，<b>¨</b> 变音（Ä/Ö/Ü），<b>...</b> 省略词干，<b>nur Sg</b> 仅单数，<b>+A / +D / +mit Dat</b> 支配格，<b>[ ]</b> 读音。标注部分已降权显示，主词为黑体。</p>
      <div class="person-tabs">%s</div>%s
      %s
      <div id="e1Table" style="display:none"><div class="vocab-table-wrap"><table class="vocab-table">%s</table></div></div>
    </section>
''' % (''.join(tabs), ''.join(panels),
       tools_buttons(['<button class="btn ghost" onclick="toggleBox(\'e1Table\')">📋 展开全表（%d 词）</button>' % n]),
       rows)


# ---------------------------------------------------------------- 3 vocab (E2)
def sec_vocab2(d):
    v = d['vocabGroupsE2']
    tabs, panels = [], []
    for i, grp in enumerate(v['groups']):
        a = ' active' if i == 0 else ''
        tabs.append('<button class="person-btn%s" onclick="switchVocabTab(\'vc2-%s\',this)">%s</button>'
                    % (a, grp['id'], h(grp['label'])))
        cards = ''.join(vocab_card(wd, grp.get('src', '')) for wd in grp['words'])
        panels.append('<div class="person-content%s" id="vc2-%s">'
                      '<p class="zh-hint note">📖 出处：<span class="src">%s</span></p>'
                      '<div class="vocab-grid">%s</div></div>'
                      % (a, grp['id'], h(grp.get('src', '')), cards))
    rows = ''.join('<tr><td class="vt-de" lang="de">%s</td><td class="vt-cn">%s</td></tr>'
                   % (word_html(wd['w']), h(wd['cn']))
                   for grp in v['groups'] for wd in grp['words'])
    n = sum(len(g['words']) for g in v['groups'])
    return '''    <section id="vocab2">
      <h2 class="section-title"><span class="num">2</span> 📗 词汇卡片 E2 · Entdecken 2 <span class="src src-lg">%s</span></h2>
      <p class="zh-hint">%s</p>
      <div class="person-tabs">%s</div>%s
      %s
      <div id="e2Table" style="display:none"><div class="vocab-table-wrap"><table class="vocab-table">%s</table></div></div>
    </section>
''' % (h(v.get('src', '')), h(v.get('instruction', '')), ''.join(tabs), ''.join(panels),
       tools_buttons(['<button class="btn ghost" onclick="toggleBox(\'e2Table\')">📋 展开全表（%d 词）</button>' % n]),
       rows)


# ---------------------------------------------------------------- 4 blitz
def sec_blitz(d):
    cards = ''.join(
        '<div class="blitz-card" onclick="this.classList.toggle(\'open\')">'
        '<div class="bz-cn">%s</div><div class="bz-hint">%s</div>'
        '<div class="bz-de" lang="de">%s</div>'
        '<div class="bz-src"><span class="src">%s</span></div></div>'
        % (h(b['cn']), h(b['hint']), h(b['de']), h(b.get('src', '')))
        for b in d['blitz'])
    return '''    <section id="blitz">
      <h2 class="section-title"><span class="num">3</span> ⚡ Blitzrunde · 抢答热身</h2>
      <p class="zh-hint">老师念中文，学生抢答德语；先说出正确形式（含冠词 / 支配格）的小组得 1 分。点卡片揭示答案。</p>
      <div class="timer-bar">
        <span class="timer" id="blitzTimer">30</span>
        <button class="btn" onclick="startTimer('blitzTimer',30)">▶ 计时开始</button>
        <button class="btn ghost" onclick="stopTimer('blitzTimer')">■ 停止</button>
        <button class="btn ghost" onclick="resetTimer('blitzTimer',30)">↺ 重置</button>
      </div>
      <div class="blitz-grid">%s</div>
    </section>
''' % cards


# ---------------------------------------------------------------- 5 connect
def sec_connect(d):
    out = []
    for gi, cg in enumerate(d['connectGrids']):
        idx = list(range(len(cg['pairs'])))
        # 中文侧乱序：固定种子保证每次生成一致（可复现）
        random.Random(300 + gi).shuffle(idx)
        left = ''.join('<div class="c-item de" data-pair="%d" data-gid="%d" lang="de" onclick="cClick(this)">%s</div>'
                       % (i, gi, h(p[0])) for i, p in enumerate(cg['pairs']))
        right = ''.join('<div class="c-item cn" data-pair="%d" data-gid="%d" onclick="cClick(this)">%s</div>'
                        % (j, gi, h(cg['pairs'][j][1])) for j in idx)
        out.append('''      <div class="connect-game">
        <h3>%s <span class="src src-lg">%s</span></h3>
        <p class="zh-hint">点左列德语，再点右列中文，配对成功变绿</p>
        <div class="connect-field">
          <div class="connect-col">%s</div><div class="connect-col">%s</div>
        </div>
        <div class="connect-score">匹配：<span id="cg-cnt-%d">0</span> / %d</div>
      </div>''' % (h(cg['title']), h(cg.get('src', '')), left, right, gi, len(cg['pairs'])))
    return '''    <section id="connect">
      <h2 class="section-title"><span class="num">4</span> 🔗 连线配对 · Vernetzen</h2>
      <p class="zh-hint">配对成功变绿；点错会红闪，可重试。整组完成后可让学生朗读整组词。</p>
%s
    </section>
''' % '\n'.join(out)


# ---------------------------------------------------------------- 6 mindmap
def sec_mindmap(d):
    mm = d['mindmap']
    pool = ''.join('<span class="mm-chip" data-c="%s" onclick="mmSelect(this)">%s</span>'
                   % (w['c'], h(w['w'])) for w in mm['words'])
    boxes = ''.join(
        '<div class="mm-box" data-cat="%s" onclick="mmDrop(this)">'
        '<div class="mm-head">%s %s</div><div class="mm-items"></div></div>'
        % (c['id'], c['icon'], h(c['label'])) for c in mm['cats'])
    return '''    <section id="mindmap">
      <h2 class="section-title"><span class="num">5</span> 🗺️ %s <span class="src src-lg">%s</span></h2>
      <p class="zh-hint">%s</p>
      <p class="zh-hint note">操作：先点词块（变蓝），再点分类框放进去；点框里的词块可拿回词池。</p>
      <div class="mm-pool" id="mmPool">%s</div>
      <div class="mm-board">%s</div>
      %s
    </section>
''' % (h(mm['title']), h(mm.get('src', '')), h(mm['instruction']), pool, boxes,
       tools_buttons(['<button class="btn" onclick="mmCheck()">✓ 检查归类</button>',
                      '<button class="btn ghost" onclick="mmReset()">↺ 重新开始</button>',
                      '<span id="mmResult" class="kw-result"></span>']))


# ---------------------------------------------------------------- 7 luecken (Ü2)
def sec_luecken(d):
    lk = d['luecken']
    by_n = {g['n']: g for g in lk['gaps']}

    def repl(m):
        n = int(m.group(1))
        g = by_n.get(n, {})
        return ('<span class="cloze-blank" data-idx="%d" data-ph="(%d)" data-ans="%s" data-alt="%s" '
                'onclick="clozeClick(this)">(%d)</span>'
                % (n, n, esc_attr(g.get('answer', '')), esc_attr('|'.join(g.get('alt', []))), n))

    paras = []
    for p in lk['text']:
        paras.append('<p class="cloze-p">%s</p>' % re.sub(r'\{\{(\d+)\}\}', repl, h(p)))
    bank = ''.join('<span class="bank-chip" onclick="bankFill(this)">%s</span>' % h(w) for w in lk['bank'])
    zh = ''.join('<li><b>%d</b> %s</li>' % (g['n'], h(g['zh'])) for g in lk['gaps'])
    return '''    <section id="luecken">
      <h2 class="section-title"><span class="num">6</span> ✍️ %s <span class="src src-lg">%s</span></h2>
      <p class="zh-hint">%s</p>
      <p class="zh-hint note">操作：先点句子里的空位（蓝色下划线），再点词语库里的词填进去；再点空位可清空。</p>
      <div class="bank-box"><strong>词语库 Wortbank：</strong>%s</div>
%s
      %s
      <div class="kw-tools"><button class="btn ghost" onclick="toggleBox('lkZh')">💡 中文提示（逐空）</button></div>
      <div id="lkZh" style="display:none"><ul class="lk-zh">%s</ul></div>
    </section>
''' % (h(lk['title']), h(lk.get('src', '')), h(lk['instruction']), bank, '\n'.join(paras),
       tools_buttons(['<button class="btn" onclick="clozeCheck()">✓ 检查</button>',
                      '<button class="btn ghost" onclick="clozeReveal()">👁 显示答案</button>',
                      '<button class="btn ghost" onclick="clozeClear()">↺ 清空</button>',
                      '<span id="clozeResult" class="kw-result"></span>']),
       zh)


# ---------------------------------------------------------------- 8 eigenschaften
def sec_eigenschaften(d):
    e = d['eigenschaften']
    rows = []
    for i, item in enumerate(e['table']):
        if item.get('given'):
            right = '<td class="es-a es-given" lang="de">%s</td>' % h(item['a'])
        else:
            right = ('<td><div class="fill-input-line">'
                     '<input class="fill-input es-input" data-ans="%s" placeholder="Adjektiv…" lang="de" '
                     'onkeydown="if(event.key===\'Enter\')esCheckInput(this)">'
                     '<button class="fill-check" onclick="esCheckInput(this)">✓</button>'
                     '<span class="fill-result"></span></div></td>'
                     % esc_attr(item['a']))
        rows.append('<tr><td class="es-n" lang="de">%s</td>%s</tr>' % (h(item['n']), right))
    nouns = [t['n'] for t in e['table']]
    opts = ''.join('<option value="%s">%s</option>' % (esc_attr(n), h(n)) for n in nouns)
    mrows = []
    for item in e['match']:
        mrows.append('''      <div class="es-match-row">
        <div class="es-d" lang="de"><b>%s)</b> %s</div>
        <div class="es-sel-line">
          <select class="es-select" data-ans="%s" onchange="esMarkSelect(this)">
            <option value="">请选择 Nomen …</option>%s
          </select>
          <span class="fill-result"></span>
        </div>
      </div>''' % (h(item['n']), h(item['d']), esc_attr(item['ans']), opts))
    return '''    <section id="eigenschaften">
      <h2 class="section-title"><span class="num">7</span> 🧩 %s <span class="src src-lg">%s</span></h2>
      <p class="zh-hint note">① 把名词的形容词形式填进右栏（灰色的已给出，是示范）。</p>
      <div class="vocab-table-wrap"><table class="es-table">
        <thead><tr><th>Nomen 名词</th><th>Adjektiv 形容词</th></tr></thead>
        <tbody>%s</tbody></table></div>
      <p class="zh-hint note">② 读描述，从 12 个名词里选出对应的那个（下拉框）。</p>
%s
      %s
      <div class="highlight-box">📌 %s</div>
    </section>
''' % (h(e['title']), h(e.get('src', '')), ''.join(rows), '\n'.join(mrows),
       tools_buttons(['<button class="btn" onclick="esCheckAll()">✓ 全部检查</button>',
                      '<button class="btn ghost" onclick="esShowAll()">👁 显示答案</button>',
                      '<button class="btn ghost" onclick="esClearAll()">↺ 清空</button>',
                      '<span id="esResult" class="kw-result"></span>']),
       h(e.get('note', '')))


# ---------------------------------------------------------------- 9 softskills (Ü2)
def sec_softskills(d):
    s = d['softskills']

    def repl(m):
        n = int(m.group(1))
        return '<span class="ss-slot" data-n="%d">(%d) ______</span>' % (n, n)

    paras = ['<p class="cloze-p">%s</p>' % re.sub(r'\{\{(\d+)\}\}', repl, h(p)) for p in s['text']]
    cards = []
    for g in s['gaps']:
        opts = ''.join('<span class="ss-opt" onclick="ssPick(this,%d)">%s</span>' % (g['n'], h(o))
                       for o in g['options'])
        cards.append('''      <div class="fill-item ss-item" data-n="%d">
        <div class="ss-head">(%d)</div>
        <div class="ss-opts">%s</div>
        <div class="fill-input-line">
          <input class="fill-input ss-input" data-ans="%s" placeholder="从上面选一个，或自己写…" lang="de"
                 onkeydown="if(event.key==='Enter')ssCheckInput(this)">
          <button class="fill-check" onclick="ssCheckInput(this)">✓</button>
          <span class="fill-result"></span>
        </div>
        <div class="ss-zh">💡 %s</div>
      </div>''' % (g['n'], g['n'], opts, esc_attr(g['answer']), h(g['zh'])))
    return '''    <section id="softskills">
      <h2 class="section-title"><span class="num">8</span> 🎯 %s <span class="src src-lg">%s</span></h2>
      <p class="zh-hint">%s</p>
%s
%s
      %s
    </section>
''' % (h(s['title']), h(s.get('src', '')), h(s['instruction']), '\n'.join(paras), '\n'.join(cards),
       tools_buttons(['<button class="btn" onclick="ssCheckAll()">✓ 全部检查</button>',
                      '<button class="btn ghost" onclick="ssShowAll()">👁 显示答案</button>',
                      '<button class="btn ghost" onclick="ssClearAll()">↺ 清空</button>',
                      '<span id="ssResult" class="kw-result"></span>']))


# ---------------------------------------------------------------- 10 umformen (Ü9)
def sec_umformen(d):
    u = d['umformen']
    cards, sb_cards, chunks_doc = [], [], []
    for i, it in enumerate(u['items']):
        cards.append('''      <div class="um-card">
        <div class="um-top"><span class="um-n">%s)</span><span class="um-pat" lang="de">%s</span>%s</div>
        <div class="um-src" lang="de">%s</div>
        <div class="um-tip">💡 %s</div>
        <textarea class="um-ta" rows="3" placeholder="Deine Umformung …" lang="de"></textarea>
        <div class="kw-tools">
          <button class="btn ghost" onclick="umShow(%d)">👁 看参考答案</button>
          <button class="btn ghost" onclick="umClear(%d)">↺ 清空</button>
        </div>
        <div class="um-ans" id="um-ans-%d" style="display:none" lang="de">%s</div>
      </div>''' % (h(it['n']), h(it['pattern']),
                   ('<span class="src">%s</span>' % h(u.get('src', ''))) if u.get('src') else '',
                   h(it['src']),
                   h(it['tip']), i, i, i, h(it['ans'])))
        # 语序拼装：词块 = 参考答案首个变体按空格切分（数据原值，不增删词）
        first = it['ans'].split('｜')[0].strip()
        chunks = first.split()
        chunks_doc.append(chunks)
        chips = ''.join('<span class="sb-chunk" data-i="%d" onclick="sbPick(this,%d)" lang="de">%s</span>'
                        % (k, i, h(c)) for k, c in enumerate(chunks))
        sb_cards.append('''      <div class="sb-card">
        <div class="sb-zh"><b>%s)</b> <span class="um-pat" lang="de">%s</span> 语序拼装</div>
        <div class="sb-pool" id="sb-pool-%d">%s</div>
        <div class="sb-line" id="sb-line-%d"></div>
        <div class="sb-actions">
          <button class="btn" onclick="sbCheck(%d)">✓ 检查语序</button>
          <button class="btn ghost" onclick="sbUndo(%d)">↶ 撤回</button>
          <button class="btn ghost" onclick="sbReset(%d)">↺ 重排</button>
          <button class="btn ghost" onclick="sbShow(%d)">👁 参考语序</button>
          <span class="fill-result" id="sb-res-%d"></span>
        </div>
      </div>''' % (h(it['n']), h(it['pattern']), i, chips, i, i, i, i, i, i))
    return '''    <section id="umformen">
      <h2 class="section-title"><span class="num">9</span> 🔤 %s <span class="src src-lg">%s</span></h2>
      <p class="zh-hint">%s</p>
%s
      %s
      <div id="umSb" style="display:none">
        <p class="zh-hint note">词块取自参考答案（教材 / 教师课件原文），按空格切分，未增删任何词。德语语序常有多解，核对时以参考译文为准。</p>
%s
      </div>
    </section>
''' % (h(u['title']), h(u.get('src', '')), h(u['instruction']), '\n'.join(cards),
       tools_buttons(['<button class="btn ghost" onclick="toggleBox(\'umSb\')">🔤 语序拼装（选做）</button>']),
       '\n'.join(sb_cards))


# ---------------------------------------------------------------- 11 redemittel
def sec_redemittel(d):
    r = d['redemittel']

    def col(c, cid):
        chips = ''.join('<span class="rm-chip" onclick="rmPick(this)">%s</span>' % h(x) for x in c['items'])
        return ('<div class="rm-col" id="%s"><div class="rm-head">%s'
                '<button class="btn tiny ghost" onclick="rmCopy(\'%s\',this)">📋 复制</button></div>'
                '<div class="rm-body">%s</div></div>' % (cid, h(c['label']), cid, chips))

    vor = ''.join(col(c, 'rmV%d' % i) for i, c in enumerate(r['vorteile']['cols']))
    sta = ''.join(col(c, 'rmS%d' % i) for i, c in enumerate(r['statistik']['cols']))
    return '''    <section id="redemittel">
      <h2 class="section-title"><span class="num">10</span> 💬 表达库 · Redemittel</h2>
      <p class="zh-hint">点一条表达高亮，方便学生跟读；老师可点「复制」把整栏拿去做板书。表达全部取自教材 / 教师课件原文。</p>
      <h3 class="rm-title">%s <span class="src">%s</span></h3>
      <div class="rm-grid rm-grid-2">%s</div>
      <h3 class="rm-title">%s <span class="src">%s</span></h3>
      <div class="rm-grid rm-grid-4">%s</div>
    </section>
''' % (h(r['vorteile']['title']), h(r['vorteile'].get('src', '')), vor,
       h(r['statistik']['title']), h(r['statistik'].get('src', '')), sta)


# ---------------------------------------------------------------- 12 berufe (Ü3)
def sec_berufe(d):
    b = d['berufe']
    cards = ''.join('<div class="vc-card br-card" onclick="flipCard(this)"><div class="vc-inner">'
                    '<div class="vc-front" lang="de">%s</div>'
                    '<div class="vc-back">%s</div></div></div>' % (h(t['de']), h(t['cn']))
                    for t in b['tasks'])
    ex = ''.join('<div class="br-line"><span class="br-who">%s</span>'
                 '<span class="br-say" lang="de">%s</span></div>' % (h(a), h(t))
                 for a, t in b['example'])
    pc = ''.join('<li lang="de">%s</li>' % h(x) for x in b['procontra_example'])
    return '''    <section id="berufe">
      <h2 class="section-title"><span class="num">11</span> 🃏 %s <span class="src src-lg">%s</span></h2>
      <p class="zh-hint">%s</p>
      <p class="zh-hint note">操作：点卡片翻面看中文任务；说出职业名之前不许把职业说出来。</p>
      <div class="vocab-grid br-grid">%s</div>
      <div class="text-card" style="margin-top:12px">
        <h3>🗨️ 示例对话 Beispiel</h3>%s
      </div>
      <div class="text-card" style="margin-top:12px">
        <h3>⚖️ 优缺点示例（Pros &amp; Contras）</h3><ul class="br-pc">%s</ul>
      </div>
    </section>
''' % (h(b['title']), h(b.get('src', '')), h(b['instruction']), cards, ex, pc)


# ---------------------------------------------------------------- 13 uebersetzen (Ü11)
def sec_uebersetzen(d):
    u = d['uebersetzen']
    cards = []
    for i, s in enumerate(u['sentences']):
        cards.append('''        <div class="tc-card" onclick="flipTrans(this)">
          <div class="tc-inner">
            <div class="tc-front"><span class="tc-num">%d</span>
              <div class="tc-zh">%s</div><div class="tc-tip">💡 %s</div></div>
            <div class="tc-back"><span class="tc-num">%d</span>
              <div class="tc-de" lang="de">%s</div></div>
          </div>
        </div>''' % (i + 1, h(s['zh']), h(s['tip']), i + 1, h(s['de'])))
    return '''    <section id="uebersetzen">
      <h2 class="section-title"><span class="num">12</span> 🎯 %s <span class="src src-lg">%s</span></h2>
      <p class="zh-hint">先自己译，再点卡片翻面核对参考译文。译法不唯一，句型正确、意义完整即算对。</p>
      <div class="highlight-box">📄 中文原文：<br>%s</div>
      <div class="translation-grid">%s</div>
      %s
      <div class="full-de" id="fullDe" style="display:none"><p class="de-full" lang="de">%s</p></div>
    </section>
''' % (h(u['title']), h(u.get('src', '')), h(u['zhFull']), '\n'.join(cards),
       tools_buttons(['<button class="btn ghost" onclick="toggleBox(\'fullDe\')">👁 整段参考译文</button>']),
       h(u['deFull']))


# ---------------------------------------------------------------- 14 spiele
def sec_spiele(d):
    games = ''.join('<div class="game-card"><div class="game-name">%s <span class="game-time">%s</span></div>'
                    '<p>%s</p></div>' % (h(g['name']), h(g['time']), h(g['desc']))
                    for g in d['klassenspiele'])
    return '''    <section id="spiele">
      <h2 class="section-title"><span class="num">13</span> 🏆 课堂游戏 &amp; 计分板</h2>
      <p class="zh-hint">点「+1 / −1」记分，比分在投影上实时可见；计时器用于控场。</p>
      <div class="scoreboard">
        <div class="team"><div class="team-name">Team A</div><div class="team-score" id="scoreA">0</div>
          <div class="team-btns"><button class="btn" onclick="addScore('A',1)">+1</button>
          <button class="btn ghost" onclick="addScore('A',-1)">−1</button></div></div>
        <div class="team"><div class="team-name">Team B</div><div class="team-score" id="scoreB">0</div>
          <div class="team-btns"><button class="btn" onclick="addScore('B',1)">+1</button>
          <button class="btn ghost" onclick="addScore('B',-1)">−1</button></div></div>
        <div class="team reset-team"><button class="btn ghost" onclick="resetScore()">↺ 比分归零</button>
          <div class="timer" id="classTimer">30</div>
          <button class="btn tiny" onclick="startTimer('classTimer',30)">▶ 30s</button></div>
      </div>
      <div class="games-grid">%s</div>
    </section>
''' % games


# ---------------------------------------------------------------- CSS
EXTRA_CSS = '''
  /* ===== 出处标注（逐题标教材坐标，投影时可回溯）===== */
  .src {
    display: inline-block; font-size: 13px; line-height: 1.5; color: #5f6672;
    background: #f4f6f8; border: 1px solid #e1e5ea; border-radius: 4px;
    padding: 4px 6px; margin: 0 4px; max-width: 100%; overflow-wrap: anywhere;
    vertical-align: middle; font-weight: 500;
  }
  .src-lg { font-size: 14px; padding: 4px 10px; color: #5f6672; }
  .kw-result { font-size: 15px; font-weight: 600; color: #0b56b8; }
  .btn { white-space: nowrap; padding: 8px 16px; border-radius: 8px; border: none; background: #1a73e8;
         color: #fff; font-size: 15px; cursor: pointer; transition: background .15s; }
  .btn:hover { background: #1660c4; }
  .btn.ghost { background: #fff; color: #0b56b8; border: 1px solid #c9d9f5; }
  .btn.ghost:hover { background: #e8f0fe; }
  .btn.tiny { padding: 4px 10px; font-size: 13px; min-height: 32px; }
  .kw-tools { display: flex; align-items: center; gap: 8px; margin: 12px 0; flex-wrap: wrap; }

  /* ===== 词汇全表 ===== */
  .vocab-table-wrap { overflow-x: auto; }
  .vocab-table { width: 100%; border-collapse: collapse; margin-top: 8px; background: #fff; }
  .vocab-table td { border-bottom: 1px solid #eef0f2; padding: 8px; vertical-align: top;
                    font-size: var(--fs-body); }
  .vocab-table .vt-de { color: #111; font-weight: 600; white-space: nowrap; width: 34%; }
  .vocab-table .vt-cn { color: #444; }
  .vc-w { font-weight: 700; }
  .vc-note { font-size: max(13px, .86em); font-weight: 400; color: #5f6672;
             margin-left: .28em; }
  .vc-note.vc-pl { white-space: nowrap; }
  .vc-phon { font-style: italic; }

  /* ===== Blitz 抢答 ===== */
  .blitz-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
  .blitz-card { background: #fff; border-radius: 10px; padding: 12px; cursor: pointer;
                box-shadow: 0 1px 3px rgba(0,0,0,.06); border-left: 4px solid #fbbc04;
                transition: background .2s, border-color .2s; display: flex; flex-direction: column; }
  .blitz-card .bz-cn { font-size: var(--fs-body); font-weight: 600; }
  .blitz-card .bz-hint { font-size: var(--fs-sm); color: #5f6672; margin-top: 4px; }
  .blitz-card .bz-de { display: none; margin-top: 8px; padding-top: 8px; border-top: 1px dashed #ddd;
                       color: #0b56b8; font-weight: 700; font-size: var(--fs-word); }
  .blitz-card .bz-src { margin-top: auto; padding-top: 8px; }
  .blitz-card.open { border-left-color: #27ae60; background: #f6fdf7; }
  .blitz-card.open .bz-de { display: block; }

  /* ===== Timer ===== */
  .timer-bar { display: flex; align-items: center; gap: 8px; margin: 0 0 12px; flex-wrap: wrap; }
  .timer { font-size: 34px; font-weight: 700; color: #0b56b8; min-width: 68px; text-align: center;
           background: #eef4ff; border-radius: 10px; padding: 4px 8px; font-variant-numeric: tabular-nums; }
  .timer.warn { color: #b3261e; background: #fdecea; }

  /* ===== 填空 / 检查 ===== */
  .fill-item { background: #fff; border-radius: 10px; padding: 12px 16px; margin-bottom: 8px;
               box-shadow: 0 1px 3px rgba(0,0,0,.05); }
  .fill-zh { font-size: var(--fs-body); color: #5f6672; margin: 4px 0; }
  .fill-input-line { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .fill-input { flex: 1 1 140px; min-width: 0; padding: 8px 10px; border: 1px solid #ccd2da;
                border-radius: 8px; font-size: var(--fs-body); outline: none; }
  .fill-input:focus { border-color: #1a73e8; }
  .fill-input.ok { background: #e8f8e8; border-color: #27ae60; }
  .fill-input.bad { background: #fdecea; border-color: #e74c3c; }
  .fill-check { padding: 8px 12px; border: 1px solid #1a73e8; border-radius: 8px; background: #e8f0fe;
                color: #0b56b8; cursor: pointer; font-size: 15px; min-height: 36px; }
  .fill-result { font-size: 15px; min-width: 20px; }
  .fill-result.correct { color: #146c2e; }
  .fill-result.wrong { color: #b3261e; }

  /* ===== Cloze 完形（Ü2 动词填空）===== */
  .cloze-p { font-size: var(--fs-body); line-height: 2.1; margin: 0 0 12px; }
  .cloze-blank { display: inline-block; min-width: 104px; text-align: center; border-bottom: 2px solid #1a73e8;
                 color: #0b56b8; font-weight: 600; cursor: pointer; padding: 0 4px; }
  .cloze-blank.filled { color: #1d1d1f; border-bottom-color: #27ae60; }
  .cloze-blank.ok { background: #e8f8e8; }
  .cloze-blank.bad { background: #fdecea; border-bottom-color: #e74c3c; color: #b3261e; }
  .cloze-blank.sel { background: #e8f0fe; }
  .bank-box { background: #f8f9fa; border-radius: 8px; padding: 8px 12px; font-size: var(--fs-body);
              margin: 12px 0; }
  .bank-chip { display: inline-block; background: #fff; border: 1px solid #c9d9f5; color: #0b56b8;
               border-radius: 14px; padding: 6px 14px; margin: 4px; cursor: pointer; font-size: 15px; }
  .bank-chip:hover { background: #e8f0fe; }
  .lk-zh { margin: 8px 0 0; padding-left: 20px; }
  .lk-zh li { font-size: var(--fs-body); line-height: 1.7; }

  /* ===== Mindmap 词场 ===== */
  .mm-pool { display: flex; flex-wrap: wrap; gap: 8px; background: #fff; border-radius: 10px;
             padding: 12px; box-shadow: 0 1px 3px rgba(0,0,0,.06); margin-bottom: 12px; }
  .mm-chip { background: #fff; border: 1px solid #ddd; border-radius: 16px; padding: 6px 14px;
             font-size: 15px; cursor: pointer; transition: background .15s, border-color .15s; }
  .mm-chip:hover { border-color: #1a73e8; }
  .mm-chip.sel { background: #e8f0fe; border-color: #1a73e8; }
  .mm-chip.ok { background: #e8f8e8; border-color: #27ae60; }
  .mm-chip.bad { background: #fdecea; border-color: #e74c3c; }
  .mm-board { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: var(--sp-3); }
  .mm-box { background: #fff; border: 2px dashed #dcdce2; border-radius: 12px; padding: 8px; min-height: 96px; }
  .mm-head { font-weight: 600; font-size: 15px; color: #0b56b8; margin-bottom: 4px; }
  .mm-items { display: flex; flex-wrap: wrap; gap: 4px; min-height: 34px; }
  .mm-items .mm-chip { font-size: 14px; padding: 4px 10px; }

  /* ===== Eigenschaften 属性 ===== */
  .es-table { width: 100%; border-collapse: collapse; background: #fff; margin: 8px 0 16px; }
  .es-table th { background: #f0f4ff; font-weight: 600; font-size: 15px; text-align: left;
                 border: 1px solid #e8e8ed; padding: 8px 12px; }
  .es-table td { border: 1px solid #e8e8ed; padding: 8px 12px; vertical-align: middle; }
  .es-table .es-n { font-weight: 600; width: 40%; }
  .es-given { color: #5f6672; background: #fafbfc; }
  .es-input { max-width: 320px; }
  .es-match-row { background: #fff; border-radius: 10px; padding: 12px 16px; margin-bottom: 8px;
                  box-shadow: 0 1px 3px rgba(0,0,0,.05); }
  .es-d { font-size: var(--fs-body); line-height: 1.7; }
  .es-sel-line { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-top: 8px; }
  .es-select { flex: 1 1 200px; min-width: 0; padding: 8px 10px; border: 1px solid #ccd2da;
               border-radius: 8px; font-size: 15px; background: #fff; }
  .es-select.ok { background: #e8f8e8; border-color: #27ae60; }
  .es-select.bad { background: #fdecea; border-color: #e74c3c; }

  /* ===== Soft Skills 三选一 ===== */
  .ss-slot { color: #0b56b8; font-weight: 600; }
  .ss-item { border-left: 3px solid #fbbc04; }
  .ss-head { font-weight: 700; color: #0b56b8; font-size: 15px; }
  .ss-opts { display: flex; flex-wrap: wrap; gap: 8px; margin: 8px 0; }
  .ss-opt { background: #fff; border: 1px solid #c9d9f5; color: #0b56b8; border-radius: 14px;
            padding: 6px 14px; cursor: pointer; font-size: 15px; }
  .ss-opt:hover { background: #e8f0fe; }
  .ss-opt.on { background: #e8f0fe; border-color: #1a73e8; font-weight: 600; }
  .ss-zh { font-size: var(--fs-sm); color: #5f6672; margin-top: 8px; }

  /* ===== Umformungen 改写 ===== */
  .um-card { background: #fff; border-radius: 10px; padding: 16px; margin-bottom: 12px;
             box-shadow: 0 1px 3px rgba(0,0,0,.05); }
  .um-top { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .um-n { font-weight: 700; color: #0b56b8; font-size: 18px; }
  .um-pat { background: #eef4ff; color: #17427f; border-radius: 8px; padding: 4px 10px;
            font-size: 15px; font-weight: 600; }
  .um-src { font-size: var(--fs-body); line-height: 1.75; margin: 8px 0; }
  .um-tip { font-size: var(--fs-sm); color: #5f6672; }
  .um-ta { width: 100%; min-height: 76px; margin-top: 8px; padding: 8px 10px; border: 1px solid #ccd2da;
           border-radius: 8px; font-size: var(--fs-body); font-family: inherit; resize: vertical; }
  .um-ans { background: #f6fbf7; border-left: 3px solid #27ae60; border-radius: 0 8px 8px 0;
            padding: 12px 16px; margin-top: 4px; font-size: var(--fs-body); line-height: 1.75; }

  /* ===== Satzbau 语序拼装 ===== */
  .sb-card { background: #fff; border-radius: 10px; padding: 16px; margin-bottom: 12px;
             box-shadow: 0 1px 3px rgba(0,0,0,.05); }
  .sb-zh { font-size: var(--fs-body); font-weight: 500; }
  .sb-pool { display: flex; flex-wrap: wrap; gap: 8px; margin: 8px 0; }
  .sb-chunk { background: #eef4ff; border: 1px solid #c9d9f5; color: #17427f; border-radius: 8px;
              padding: 6px 10px; font-size: var(--fs-body); cursor: pointer; }
  .sb-chunk:hover { background: #e0ecff; }
  .sb-line { min-height: 52px; border-bottom: 2px solid #e0e0e6; padding: 4px;
             display: flex; flex-wrap: wrap; gap: 4px; align-items: center; }
  .sb-line .sb-chunk { background: #fff; border-color: #27ae60; color: #146c2e; }
  .sb-actions { display: flex; align-items: center; gap: 8px; margin-top: 8px; flex-wrap: wrap; }
  .sb-line.ok .sb-chunk { background: #e8f8e8; }
  .sb-line.bad .sb-chunk { background: #fdecea; border-color: #e74c3c; color: #b3261e; }

  /* ===== Redemittel 表达库 ===== */
  .rm-title { font-size: var(--fs-h3); margin: 20px 0 8px; }
  .rm-grid { display: grid; gap: var(--sp-3); }
  .rm-grid-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .rm-grid-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
  .rm-col { background: #fff; border-radius: 10px; padding: 12px; box-shadow: 0 1px 3px rgba(0,0,0,.06); }
  .rm-head { font-weight: 600; font-size: 15px; color: #0b56b8; margin-bottom: 8px;
             display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .rm-body { display: flex; flex-wrap: wrap; gap: 8px; }
  .rm-chip { background: #f8f9fa; border: 1px solid #e1e5ea; border-radius: 10px; padding: 8px 12px;
             font-size: var(--fs-body); cursor: pointer; line-height: 1.5; }
  .rm-chip:hover { border-color: #1a73e8; }
  .rm-chip.on { background: #e8f0fe; border-color: #1a73e8; color: #17427f; font-weight: 600; }

  /* ===== Beruferaten 猜职业 ===== */
  .br-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .br-card .vc-front, .br-card .vc-back { min-height: 82px; font-size: var(--fs-body); font-weight: 600; }
  .br-line { display: flex; gap: 8px; align-items: flex-start; margin-bottom: 8px; }
  .br-who { font-weight: 700; color: #0b56b8; flex-shrink: 0; }
  .br-say { font-size: var(--fs-body); line-height: 1.7; }
  .br-pc { margin: 8px 0 0; padding-left: 20px; }
  .br-pc li { font-size: var(--fs-body); line-height: 1.7; }

  /* ===== 计分 & 游戏 ===== */
  .scoreboard { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
  .team { flex: 1 1 150px; background: #fff; border-radius: 12px; padding: 12px; text-align: center;
          box-shadow: 0 1px 3px rgba(0,0,0,.06); }
  .team-name { font-size: 15px; color: #5f6672; }
  .team-score { font-size: 46px; font-weight: 700; color: #0b56b8; line-height: 1.1; }
  .team-btns { display: flex; gap: 8px; justify-content: center; }
  .games-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--sp-2); }
  .game-card { background: #fff; border-radius: 10px; padding: 12px; box-shadow: 0 1px 3px rgba(0,0,0,.06);
               display: flex; flex-direction: column; }
  .game-name { font-weight: 600; font-size: 15px; margin-bottom: 4px; }
  .game-time { font-size: 13px; color: #0b56b8; background: #eef4ff; border-radius: 10px; padding: 4px 8px;
               white-space: nowrap; }
  .game-card p { font-size: var(--fs-body); color: #5f6672; margin: 4px 0 0; line-height: 1.65; }

  /* ===== 连线 ===== */
  .connect-game { background: #fff; border-radius: 10px; padding: 16px; margin-bottom: 12px;
                  box-shadow: 0 1px 3px rgba(0,0,0,.06); }
  .connect-game h3 { font-size: var(--fs-h3); margin: 0 0 4px; }
  .connect-field { display: flex; gap: 24px; justify-content: center; }
  .connect-col { display: flex; flex-direction: column; gap: 8px; min-width: 130px; flex: 1 1 0; }
  .c-item { padding: 8px 12px; border: 1px solid #ddd; border-radius: 8px; text-align: center;
            cursor: pointer; font-size: var(--fs-body); transition: background .15s, border-color .15s;
            background: #fff; overflow-wrap: anywhere; }
  .c-item:hover { border-color: #1a73e8; }
  .c-item.selected { border-color: #1a73e8; background: #e8f0fe; font-weight: 500; }
  .c-item.matched { border-color: #27ae60; background: #e8f8e8; color: #146c2e; cursor: default; }
  .badflash { background: #fdecea !important; border-color: #e74c3c !important; }
  .connect-score { text-align: center; font-size: 15px; color: #5f6672; margin-top: 12px; }

  /* ===== 译文折叠 ===== */
  .full-de { background: #f6fbf7; border-left: 3px solid #27ae60; border-radius: 0 8px 8px 0;
             padding: 12px 16px; margin: 8px 0; }
  .de-full { font-size: var(--fs-body); line-height: 1.85; margin: 0; }
  .tc-tip { font-size: var(--fs-sm); color: #5f6672; margin-top: 4px; }
  .tc-zh { font-size: var(--fs-body); color: #1d1d1f; }
  .tc-de { font-size: var(--fs-word); color: #1d1d1f; font-weight: 500; line-height: 1.6; }
  .tc-front .src, .tc-back .src { margin-bottom: 4px; }

  /* ===== 流程表 ===== */
  .flow-table { width: 100%; border-collapse: collapse; font-size: 15px; margin-top: 8px; }
  .flow-table td { border-bottom: 1px solid #eee; padding: 8px 4px; vertical-align: top; }
  .flow-table .fl-t { color: #0b56b8; font-weight: 600; white-space: nowrap; width: 96px; }
  .home-card { cursor: pointer; }
  .zh-hint { font-size: var(--fs-body); color: #5f6672; margin: 0 0 12px; }
  .zh-hint.note { font-size: 15px; color: #5f6672; }

  /* ===== 投影放大控件（仅宽屏；默认收成小圆钮，点击展开、8 秒自动收起）===== */
  .proj-ctl { display: none; position: fixed; right: 14px; bottom: 14px; z-index: 150; align-items: center; gap: 4px; }
  .proj-mini { width: 42px; height: 42px; border-radius: 999px; border: 1px solid #e1e5ea;
               background: rgba(255,255,255,.97); box-shadow: 0 4px 14px rgba(0,0,0,.12);
               font-size: 13px; font-weight: 700; color: #333; cursor: pointer; padding: 0; }
  .proj-mini:hover { background: #e8f0fe; color: #1a73e8; }
  .proj-body { display: none; align-items: center; gap: 4px; padding: 4px 8px; background: rgba(255,255,255,.97);
               border: 1px solid #e1e5ea; border-radius: 999px; box-shadow: 0 4px 14px rgba(0,0,0,.12); }
  .proj-ctl.open .proj-body { display: inline-flex; }
  .proj-ctl.open .proj-mini { display: none; }
  .proj-body button { border: none; background: #f1f3f5; border-radius: 999px; cursor: pointer;
                      font-size: 15px; font-weight: 600; color: #333; padding: 8px 12px; min-height: 34px; }
  .proj-body button:hover { background: #e8f0fe; color: #1a73e8; }
  .proj-body .proj-label { font-size: 13px; color: #5f6672; padding: 0 4px; min-width: 76px; text-align: center; }
  @media (min-width: 1100px) { .proj-ctl { display: inline-flex; } body { padding-bottom: 88px; } }

  /* ===== 容器与导航（自适应）===== */
  .top-nav { max-width: 1440px; }
  @media (min-width: 1000px) { .container { max-width: min(1080px, 95vw); } }
  .nav-links.show { max-height: calc(100vh - 48px); overflow-y: auto; }
  /* 桌面/平板：导航允许换行（14 项在窄桌面放不下一行时自动折行），
     字号收到 14px 让 1366/1440/1920 仍能单行放下，避免 nav 内部横向滚动 */
  @media (min-width: 601px) {
    .top-nav { height: auto; min-height: 48px; flex-wrap: wrap; padding: 8px 12px; }
    .nav-links { flex-wrap: wrap; overflow: visible; row-gap: 4px; }
    .nav-links button { padding: 6px 10px; font-size: 14px; }
  }
  @media (max-width: 900px) {
    .connect-field { gap: 12px; }
    .rm-grid-4 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .es-input { max-width: 100%; }
    /* 触控设备（窄屏）把词条出处按钮抬到 34px 以上，手指能点到 */
    .vc-detail { width: 34px; height: 34px; font-size: 15px; opacity: .85; }
    .vc-card .vc-detail { opacity: .85; }
  }
  @media (max-width: 820px) {
    .mm-board { grid-template-columns: 1fr; }
    .rm-grid-2 { grid-template-columns: 1fr; }
    .blitz-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .games-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .br-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .connect-col { min-width: 88px; }
    .c-item { padding: 8px; font-size: 15px; }
  }
  @media (max-width: 700px) {
    .person-tabs { flex-wrap: wrap; gap: 4px; }
    .person-btn { flex: 1 1 46%; font-size: 15px; padding: 8px 12px; }
    .section-title { flex-wrap: wrap; }
    .vocab-grid { grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); }
    .cloze-p { line-height: 2.2; }
    .cloze-blank { min-width: 88px; }
    .rm-grid-4, .rm-grid-2 { grid-template-columns: 1fr; }
    .connect-field { gap: 8px; }
    .connect-col { min-width: 0; }
    .c-item { font-size: 14px; padding: 6px; }
    .games-grid, .blitz-grid, .br-grid { grid-template-columns: 1fr; }
    /* 属性表在窄屏改用固定布局，格内自适应换行，彻底消除表格撑宽页面 */
    .es-table { table-layout: fixed; }
    .es-table th, .es-table td { padding: 6px 8px; }
    .es-table .es-n { width: 46%; overflow-wrap: anywhere; }
    .es-table .es-input { width: 100%; min-width: 0; max-width: 100%; }
  }
  @media (max-width: 560px) {
    p, li, .zh-hint, .cloze-p, .tc-zh, .bz-cn, .um-src, .es-d { line-height: 1.9; }
    .team-score { font-size: 38px; }
    .timer { font-size: 28px; }
  }
  @media (min-width: 1500px) {
    body { font-size: 21px; }
    .main { max-width: 1420px; }
    .container { max-width: min(1360px, 94vw); }
    .hero h1 { font-size: 46px; }
    .hero .sub { font-size: 23px; }
    .text-card h3 { font-size: 28px; }
    .flow-table { font-size: 19px; }
    .obj-box { font-size: 18px; }
    .obj-box ul { line-height: 1.9; }
    .home-grid { grid-template-columns: repeat(3, 1fr); gap: 12px; }
    .vocab-table td { font-size: 19px; }
    .nav-links button { font-size: 16px; padding: 8px 16px; }
    .vc-front, .vc-back { min-height: 108px; }
  }
  @media (min-width: 2200px) {
    .main { max-width: 1800px; }
    .container { max-width: min(1720px, 92vw); }
    .hero h1 { font-size: 56px; }
    .hero .sub { font-size: 26px; }
    .text-card h3 { font-size: 32px; }
    .flow-table { font-size: 21px; }
    .nav-links button { font-size: 18px; padding: 8px 16px; }
    .vocab-table td { font-size: 23px; }
    .top-nav { max-width: 2100px; }
  }
  @media (hover: none) {
    .btn, .person-btn, .hamburger { min-height: 42px; }
    .bank-chip, .mm-chip, .ss-opt, .c-item, .sb-chunk, .rm-chip { min-height: 34px; }
    .vc-card .vc-detail { opacity: 1; }
    .vc-detail { width: 36px; height: 36px; font-size: 15px; }
    .fill-check { min-height: 42px; }
  }

  /* ===== 灰阶令牌/对比度 =====
     模板里的 #999（hero .meta / .text-card p / .vp-close）在浅底上只有 2.6–2.9:1，
     未达 WCAG AA 4.5:1 → 统一到灰阶令牌 #5f6672（白底 6.4:1） */
  .hero .meta, .text-card p, .vp-close { color: #5f6672; }

  /* ===== 视觉质量层（灰阶统一 #5f6672 / 卡片等高 / 字号令牌）===== */
  .vocab-grid { align-items: stretch; }
  /* 德语长复合词（如 Verantwortungsbewusstsein）不得把栅格撑宽页面：
     卡片与词面允许在词内断行，配合 lang=de 的连字符规则优先在音节处断 */
  .vc-card { min-width: 0; }
  .vc-front, .vc-back, .vc-w, .vc-note { overflow-wrap: anywhere; }
  .blitz-grid, .games-grid, .home-grid, .br-grid { grid-auto-rows: 1fr; }
  .text-card, .game-card, .blitz-card, .rm-col { height: 100%; }
  .zh-hint, .zh-hint.note, .fill-zh, .ss-zh, .game-card p, .text-card p, p, li, .vt-cn, .vt-de,
  .c-item, .bank-box, .br-say, .br-pc li, .lk-zh li, .um-src, .um-tip, .es-d, .sb-zh, .tc-zh,
  .rm-chip, .ss-opt, .mm-chip, .bank-chip, .cloze-p, .de-full, .tc-de {
    font-size: var(--fs-body) !important; line-height: 1.7;
  }
  .meta, .mm-head, .team-name, .fl-t, td, .game-time, .highlight-box, .btn, .person-btn,
  .vc-note, .es-select, .fill-input, .fill-check { font-size: var(--fs-sm) !important; }
  .src, .game-time, .team-name, .vt-de .vc-note { font-size: var(--fs-cap) !important; }
  h1, .hero h1 { font-size: var(--fs-h1) !important; }
  h2, h3, .section-title, .rm-title, .connect-game h3 { font-size: var(--fs-h3) !important; }
  .vc-w { font-weight: 700; }
  /* 词条出处按钮：模板里是 20×20 / 10px（悬停才显形）→ 抬高到可读可点 */
  .vc-detail { width: 28px; height: 28px; font-size: 13px; right: 2px; bottom: 2px; }
  /* 对比度：模板 .vc-back 的蓝字 #1a73e8 在 #e8f0fe 底上只有 3.93:1（AA 需 4.5）
     → 背面中文改用正文黑（15:1），蓝底作为「已翻面」的视觉信号仍然保留 */
  .vc-back { color: #1d1d1f; }
  /* 对比度：白字在 #27ae60 上只有 2.87:1 → 绿色序号盘改用深绿 #146c2e（6.6:1） */
  .tc-back .tc-num { background: #146c2e; }
  /* 句卡序号：模板 22×22 / 11px → 抬到 ≥12px 字号地板 */
  .tc-num { width: 28px; height: 28px; line-height: 28px; font-size: 13px; }
  .bz-de, .um-pat, .es-table .es-n { font-size: var(--fs-word) !important; }
  .um-pat { font-size: var(--fs-body) !important; font-weight: 600; }
  .es-table .es-n { font-size: var(--fs-body) !important; font-weight: 600; }
  .vc-front, .vc-back, .tc-de, .blitz-card .bz-de { font-size: var(--fs-word) !important; }

  /* ===== 换行质量层 ===== */
  p, li, .zh-hint, .tc-zh, .bz-cn, .es-d, .um-src, .de-full, .highlight-box, .text-card p, .game-card p {
    text-wrap: pretty; line-height: 1.85; line-break: strict;
  }
  /* 注意：text-wrap 是 text-wrap-mode 的简写，会把 white-space:nowrap 顶回 wrap，
     所以 nowrap 语义的元素（.vc-note / .vt-de / .fl-t）一律不放进上面的组 */
  .vc-note, .vt-de, .fl-t, .cloze-blank, .game-time { white-space: nowrap; }
  .vc-note { white-space: normal; }
  .vc-note.vc-pl { white-space: nowrap; }
  h1, h2, h3, h4, .section-title, .game-name, .mm-head, .rm-title, .rm-head { text-wrap: balance; }
  .um-src, .um-ans, .es-d, .br-say, .tc-de, .de-full, .sb-chunk, [lang="de"] {
    hyphens: auto; -webkit-hyphens: auto; overflow-wrap: break-word;
  }
  .lk-zh li, .br-pc li, .obj-box ul li, .game-card ul li { padding-left: 1.5em; text-indent: -1.5em; }
'''


# ---------------------------------------------------------------- JS
EXTRA_JS = '''
let selLeft = null, selRight = null;
/* 键盘可用：输入框 / 下拉回车即判题（textarea 回车仍是换行，不劫持） */
document.addEventListener('keydown', function(e){
  if (e.key !== 'Enter') return;
  const el = e.target;
  if (!el || el.tagName !== 'INPUT') return;
  if (el.closest('.es-select-line')) return;
  if (el.dataset.ans !== undefined && el.closest('.fill-input-line')){
    e.preventDefault();
    fillCheck(el, '.fill-input-line');
  }
});
document.addEventListener('keydown', function(e){
  if (e.key !== 'Enter') return;
  const el = e.target;
  if (el && el.tagName === 'SELECT' && el.dataset.ans !== undefined){ e.preventDefault(); esMarkSelect(el); }
});
function flipCard(el){ el.classList.toggle('flipped'); }
function flipTrans(el){ el.classList.toggle('flipped'); }
function toggleBox(id){ const b = document.getElementById(id); if (b) b.style.display = (b.style.display === 'none' ? 'block' : 'none'); }
function norm(s){
  return (s === undefined || s === null ? '' : String(s)).toUpperCase().trim()
    .replace(/\\s+/g, ' ')
    .replace(/Ä/g, 'AE').replace(/Ö/g, 'OE').replace(/Ü/g, 'UE').replace(/ß/g, 'SS');
}
/* ---- 词汇分组 tab ---- */
function switchVocabTab(id, btn){
  const sec = btn.closest('section');
  sec.querySelectorAll(':scope > .person-content').forEach(function(p){ p.classList.remove('active'); });
  const panel = sec.querySelector('#' + id);
  if (panel) panel.classList.add('active');
  sec.querySelectorAll(':scope > .person-tabs .person-btn').forEach(function(b){ b.classList.remove('active'); });
  btn.classList.add('active');
}
/* ---- 词条面板 ---- */
function showVocab(w, cn, ex){
  document.getElementById('vpWord').textContent = w;
  document.getElementById('vpZh').textContent = cn;
  document.getElementById('vpEx').textContent = ex || '';
  document.getElementById('vocabPanel').classList.add('show');
  document.getElementById('vocabOverlay').classList.add('show');
}
function hideVocab(){
  document.getElementById('vocabPanel').classList.remove('show');
  document.getElementById('vocabOverlay').classList.remove('show');
}
/* ---- 计时器 ---- */
const timers = {};
function startTimer(id, sec){
  stopTimer(id);
  let t = sec;
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = t; el.classList.remove('warn');
  timers[id] = setInterval(function(){
    t--; el.textContent = t;
    if (t <= 5) el.classList.add('warn');
    if (t <= 0){ stopTimer(id); el.textContent = '0'; }
  }, 1000);
}
function stopTimer(id){ if (timers[id]) { clearInterval(timers[id]); delete timers[id]; } }
function resetTimer(id, sec){
  stopTimer(id);
  const el = document.getElementById(id);
  if (el){ el.textContent = sec; el.classList.remove('warn'); }
}
/* ---- 计分板 ---- */
const scores = {A: 0, B: 0};
function addScore(t, d){
  scores[t] = Math.max(0, scores[t] + d);
  document.getElementById('score' + t).textContent = scores[t];
}
function resetScore(){
  scores.A = 0; scores.B = 0;
  document.getElementById('scoreA').textContent = '0';
  document.getElementById('scoreB').textContent = '0';
}
/* ---- 连线配对 ---- */
function cClick(el){
  if (el.classList.contains('matched')) return;
  const side = el.classList.contains('de') ? 'L' : 'R';
  const gid = el.dataset.gid;
  if (side === 'L'){
    if (selLeft) selLeft.classList.remove('selected');
    selLeft = el; el.classList.add('selected');
  } else {
    if (selRight) selRight.classList.remove('selected');
    selRight = el; el.classList.add('selected');
  }
  if (selLeft && selRight && selLeft.dataset.gid === selRight.dataset.gid){
    if (selLeft.dataset.pair === selRight.dataset.pair){
      selLeft.classList.remove('selected'); selRight.classList.remove('selected');
      selLeft.classList.add('matched'); selRight.classList.add('matched');
      const cnt = document.getElementById('cg-cnt-' + gid);
      cnt.textContent = parseInt(cnt.textContent, 10) + 1;
      selLeft = null; selRight = null;
    } else {
      const a = selLeft, b = selRight;
      a.classList.add('badflash'); b.classList.add('badflash');
      setTimeout(function(){ a.classList.remove('badflash', 'selected'); b.classList.remove('badflash', 'selected'); }, 420);
      selLeft = null; selRight = null;
    }
  }
}
/* ---- Ü2 完形（词库填词）---- */
let clozeSel = null;
function clozeClick(el){
  if (el.classList.contains('filled')){
    el.textContent = el.dataset.ph;
    el.classList.remove('filled', 'ok', 'bad', 'sel');
    clozeSel = null;
    return;
  }
  document.querySelectorAll('#luecken .cloze-blank').forEach(function(b){ b.classList.remove('sel'); });
  clozeSel = el; el.classList.add('sel');
}
function bankFill(chip){
  if (!clozeSel){
    const r = document.getElementById('clozeResult');
    if (r) r.textContent = '请先点句子里的空位，再点词库里的词（投影时不用弹窗）';
    return;
  }
  clozeSel.textContent = chip.textContent;
  clozeSel.classList.add('filled');
  clozeSel.classList.remove('sel', 'ok', 'bad');
  clozeSel = null;
}
function clozeCheck(){
  let n = 0, tot = 0, empty = 0;
  document.querySelectorAll('#luecken .cloze-blank').forEach(function(b){
    tot++;
    if (!b.classList.contains('filled')){ empty++; b.classList.remove('ok', 'bad'); return; }
    const alts = (b.dataset.alt || '').split('|').filter(Boolean).map(norm);
    const ok = norm(b.textContent) === norm(b.dataset.ans) || alts.indexOf(norm(b.textContent)) >= 0;
    b.classList.remove('ok', 'bad'); b.classList.add(ok ? 'ok' : 'bad');
    if (ok) n++;
  });
  document.getElementById('clozeResult').textContent =
    '正确 ' + n + ' / ' + tot + ' 空' + (empty ? '（还有 ' + empty + ' 空未填）' : '');
}
function clozeReveal(){
  document.querySelectorAll('#luecken .cloze-blank').forEach(function(b){
    b.textContent = b.dataset.ans;
    b.classList.add('filled'); b.classList.remove('bad', 'sel'); b.classList.add('ok');
  });
  document.getElementById('clozeResult').textContent = '已显示参考答案（教师用）';
}
function clozeClear(){
  document.querySelectorAll('#luecken .cloze-blank').forEach(function(b){
    b.textContent = b.dataset.ph;
    b.classList.remove('filled', 'ok', 'bad', 'sel');
  });
  clozeSel = null;
  document.getElementById('clozeResult').textContent = '';
}
/* ---- 词场归类 ---- */
let mmSel = null;
function mmSelect(el){
  if (el.parentNode.classList.contains('mm-items')){
    document.getElementById('mmPool').appendChild(el);
    el.classList.remove('ok', 'bad');
    return;
  }
  if (mmSel) mmSel.classList.remove('sel');
  mmSel = el; el.classList.add('sel');
}
function mmDrop(box){
  if (!mmSel) return;
  box.querySelector('.mm-items').appendChild(mmSel);
  mmSel.classList.remove('sel', 'ok', 'bad');
  mmSel = null;
}
function mmCheck(){
  let ok = 0, tot = 0;
  document.querySelectorAll('#mindmap .mm-board .mm-box').forEach(function(box){
    const cat = box.dataset.cat;
    box.querySelectorAll('.mm-chip').forEach(function(ch){
      tot++;
      const right = ch.dataset.c === cat;
      ch.classList.remove('ok', 'bad'); ch.classList.add(right ? 'ok' : 'bad');
      if (right) ok++;
    });
  });
  const left = document.querySelectorAll('#mmPool .mm-chip').length;
  document.getElementById('mmResult').textContent =
    '归类正确 ' + ok + ' / ' + tot + (left ? '（还有 ' + left + ' 个未归类）' : '');
}
function mmReset(){
  const pool = document.getElementById('mmPool');
  document.querySelectorAll('#mindmap .mm-board .mm-chip').forEach(function(ch){
    ch.classList.remove('ok', 'bad'); pool.appendChild(ch);
  });
  document.getElementById('mmResult').textContent = '';
}
/* ---- Eigenschaften ---- */
function fillCheck(el, scopeSel){
  const scope = el.closest(scopeSel);
  const inp = el.tagName === 'INPUT' ? el : scope.querySelector('input');
  const res = scope.querySelector('.fill-result');
  const val = inp.value.trim();
  const ok = !!val && norm(val) === norm(inp.dataset.ans);
  inp.classList.remove('ok', 'bad'); inp.classList.add(ok ? 'ok' : 'bad');
  if (res){
    res.textContent = ok ? '✓ richtig' : '✗ 再想想';
    res.className = 'fill-result ' + (ok ? 'correct' : 'wrong');
  }
  return ok;
}
function esCheckInput(el){ fillCheck(el, '.fill-input-line'); }
function esMarkSelect(sel){
  const val = sel.value;
  sel.classList.remove('ok', 'bad');
  if (!val) return;
  sel.classList.add(norm(val) === norm(sel.dataset.ans) ? 'ok' : 'bad');
}
function esCheckAll(){
  let ok = 0, tot = 0;
  document.querySelectorAll('#eigenschaften .es-input').forEach(function(inp){
    tot++;
    const good = !!inp.value.trim() && norm(inp.value) === norm(inp.dataset.ans);
    inp.classList.remove('ok', 'bad'); inp.classList.add(good ? 'ok' : 'bad');
    const res = inp.closest('.fill-input-line').querySelector('.fill-result');
    if (res){ res.textContent = good ? '✓' : (inp.value.trim() ? '✗' : ''); res.className = 'fill-result ' + (good ? 'correct' : 'wrong'); }
    if (good) ok++;
  });
  document.querySelectorAll('#eigenschaften .es-select').forEach(function(sel){
    tot++;
    const good = !!sel.value && norm(sel.value) === norm(sel.dataset.ans);
    sel.classList.remove('ok', 'bad'); sel.classList.add(good ? 'ok' : 'bad');
    if (good) ok++;
  });
  document.getElementById('esResult').textContent = '正确 ' + ok + ' / ' + tot + ' 题';
}
function esShowAll(){
  document.querySelectorAll('#eigenschaften .es-input').forEach(function(inp){
    inp.value = inp.dataset.ans; inp.classList.remove('bad'); inp.classList.add('ok');
    const res = inp.closest('.fill-input-line').querySelector('.fill-result');
    if (res){ res.textContent = ''; res.className = 'fill-result'; }
  });
  document.querySelectorAll('#eigenschaften .es-select').forEach(function(sel){
    sel.value = sel.dataset.ans; sel.classList.remove('bad'); sel.classList.add('ok');
  });
  document.getElementById('esResult').textContent = '已显示参考答案';
}
function esClearAll(){
  document.querySelectorAll('#eigenschaften .es-input').forEach(function(inp){
    inp.value = ''; inp.classList.remove('ok', 'bad');
    const res = inp.closest('.fill-input-line').querySelector('.fill-result');
    if (res){ res.textContent = ''; res.className = 'fill-result'; }
  });
  document.querySelectorAll('#eigenschaften .es-select').forEach(function(sel){
    sel.value = ''; sel.classList.remove('ok', 'bad');
  });
  document.getElementById('esResult').textContent = '';
}
/* ---- Soft Skills 三选一 ---- */
function ssItem(el){ return el.closest('.ss-item'); }
function ssPick(chip, n){
  const item = document.querySelector('#softskills .ss-item[data-n="' + n + '"]');
  if (!item) return;
  item.querySelectorAll('.ss-opt').forEach(function(c){ c.classList.remove('on'); });
  chip.classList.add('on');
  const inp = item.querySelector('input');
  inp.value = chip.textContent.trim();
  inp.classList.remove('ok', 'bad');
  const res = item.querySelector('.fill-result');
  if (res){ res.textContent = ''; res.className = 'fill-result'; }
}
function ssCheckInput(el){ fillCheck(el, '.fill-input-line'); }
function ssCheckAll(){
  let ok = 0, tot = 0;
  document.querySelectorAll('#softskills .ss-item').forEach(function(item){
    tot++;
    const inp = item.querySelector('input');
    const good = !!inp.value.trim() && norm(inp.value) === norm(inp.dataset.ans);
    inp.classList.remove('ok', 'bad'); inp.classList.add(good ? 'ok' : 'bad');
    const res = item.querySelector('.fill-result');
    if (res){
      res.textContent = good ? '✓ richtig' : (inp.value.trim() ? '✗ 再想想' : '');
      res.className = 'fill-result ' + (good ? 'correct' : 'wrong');
    }
    if (good) ok++;
  });
  document.getElementById('ssResult').textContent = '正确 ' + ok + ' / ' + tot + ' 空';
}
function ssShowAll(){
  document.querySelectorAll('#softskills .ss-item').forEach(function(item){
    const inp = item.querySelector('input');
    inp.value = inp.dataset.ans; inp.classList.remove('bad'); inp.classList.add('ok');
    item.querySelectorAll('.ss-opt').forEach(function(c){
      c.classList.toggle('on', norm(c.textContent) === norm(inp.dataset.ans));
    });
    const res = item.querySelector('.fill-result');
    if (res){ res.textContent = ''; res.className = 'fill-result'; }
  });
  document.getElementById('ssResult').textContent = '已显示参考答案';
}
function ssClearAll(){
  document.querySelectorAll('#softskills .ss-item').forEach(function(item){
    const inp = item.querySelector('input');
    inp.value = ''; inp.classList.remove('ok', 'bad');
    item.querySelectorAll('.ss-opt').forEach(function(c){ c.classList.remove('on'); });
    const res = item.querySelector('.fill-result');
    if (res){ res.textContent = ''; res.className = 'fill-result'; }
  });
  document.getElementById('ssResult').textContent = '';
}
/* ---- Ü9 改写 ---- */
function umShow(i){ const b = document.getElementById('um-ans-' + i); if (b) b.style.display = 'block'; }
function umClear(i){
  const b = document.getElementById('um-ans-' + i);
  if (b) b.style.display = 'none';
  const card = b ? b.closest('.um-card') : null;
  if (card){ const ta = card.querySelector('.um-ta'); if (ta) ta.value = ''; }
}
/* ---- 语序拼装 ---- */
function sbPick(el, i){
  const line = document.getElementById('sb-line-' + i);
  const pool = document.getElementById('sb-pool-' + i);
  if (el.parentNode === pool) line.appendChild(el); else pool.appendChild(el);
  line.classList.remove('ok', 'bad');
}
function sbUndo(i){
  const line = document.getElementById('sb-line-' + i);
  const last = line.lastElementChild;
  if (last) sbPick(last, i);
}
function sbReset(i){
  const pool = document.getElementById('sb-pool-' + i);
  const line = document.getElementById('sb-line-' + i);
  Array.prototype.slice.call(line.children).forEach(function(ch){ pool.appendChild(ch); });
  line.classList.remove('ok', 'bad');
  document.getElementById('sb-res-' + i).textContent = '';
}
function sbCheck(i){
  const line = document.getElementById('sb-line-' + i);
  const got = Array.prototype.slice.call(line.children).map(function(ch){ return ch.textContent.trim(); });
  const want = DOC.sb[i];
  const left = document.getElementById('sb-pool-' + i).children.length;
  const res = document.getElementById('sb-res-' + i);
  const same = got.length === want.length && got.every(function(g, k){ return g === want[k]; });
  line.classList.remove('ok', 'bad'); line.classList.add(same ? 'ok' : 'bad');
  res.textContent = same ? '✓ 与参考译文一致' : (left ? '⚠ 还有 ' + left + ' 个词块没放上（语序常有多解，请对照参考语序）' : '⚠ 与参考译文语序不同（德语语序常有多解，请对照参考语序）');
  res.className = 'fill-result ' + (same ? 'correct' : 'wrong');
}
function sbShow(i){
  const line = document.getElementById('sb-line-' + i);
  const pool = document.getElementById('sb-pool-' + i);
  Array.prototype.slice.call(line.children).forEach(function(ch){ pool.appendChild(ch); });
  DOC.sb[i].forEach(function(txt){
    Array.prototype.slice.call(pool.children).some(function(ch){
      if (ch.textContent.trim() === txt && ch.parentNode === pool){ line.appendChild(ch); return true; }
      return false;
    });
  });
  line.classList.remove('bad'); line.classList.add('ok');
  const res = document.getElementById('sb-res-' + i);
  res.textContent = '参考语序';
  res.className = 'fill-result correct';
}
/* ---- Redemittel ---- */
function rmPick(el){ el.classList.toggle('on'); }
function rmCopy(id, btn){
  const el = document.getElementById(id);
  if (!el) return;
  const txt = Array.prototype.slice.call(el.querySelectorAll('.rm-chip'))
    .map(function(c){ return c.textContent.trim(); }).join('\\n');
  const done = function(){
    if (!btn) return;
    const old = btn.textContent;
    btn.textContent = '✓ 已复制';
    setTimeout(function(){ btn.textContent = old; }, 1500);
  };
  const fallback = function(){
    try {
      const ta = document.createElement('textarea');
      ta.value = txt; document.body.appendChild(ta); ta.select();
      document.execCommand('copy'); document.body.removeChild(ta); done();
    } catch (e) { alert('复制失败，请手动选择文本'); }
  };
  if (navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(txt).then(done, fallback);
  } else { fallback(); }
}
'''


# ---------------------------------------------------------------- core JS
CORE_JS = '''
function switchSection(id){
  document.querySelectorAll('section').forEach(function(s){ s.classList.remove('active'); });
  const el = document.getElementById(id);
  if (el) el.classList.add('active');
  document.querySelectorAll('.nav-links button').forEach(function(b){ b.classList.remove('active'); });
  const idx = SECTIONS.indexOf(id);
  const btns = document.querySelectorAll('.nav-links button');
  if (btns[idx]) btns[idx].classList.add('active');
  const pf = document.getElementById('progressFill');
  if (pf) pf.style.width = ((idx + 1) / SECTIONS.length * 100) + '%';
  const nl = document.getElementById('navLinks');
  if (nl) nl.classList.remove('show');
  window.scrollTo(0, 0);
}
function toggleNav(){
  const nl = document.getElementById('navLinks');
  if (nl) nl.classList.toggle('show');
}
/* ===== 投影模式：整体放大（课堂现场用，宽屏才显示） ===== */
let projScale = 1;
try { projScale = parseFloat(localStorage.getItem('l8proj') || '1') || 1; } catch (e) { projScale = 1; }
const PROJ_STEPS = [1, 1.15, 1.3, 1.5];
function applyProj(){
  document.body.style.zoom = projScale;
  const lb = document.getElementById('projLabel');
  if (lb) lb.textContent = (projScale === 1 ? '标准' : '投影 ' + Math.round(projScale * 100) + '%');
}
let projTimer = null;
function armProj(){
  clearTimeout(projTimer);
  projTimer = setTimeout(function(){ document.getElementById('projCtl').classList.remove('open'); }, 8000);
}
function projToggle(e){
  if (e) e.stopPropagation();
  const c = document.getElementById('projCtl');
  c.classList.toggle('open');
  if (c.classList.contains('open')) armProj();
}
document.addEventListener('click', function(e){
  const c = document.getElementById('projCtl');
  if (c && !c.contains(e.target)) c.classList.remove('open');
});
function projStep(d){
  let i = PROJ_STEPS.indexOf(projScale);
  if (i < 0) i = 0;
  i = Math.min(PROJ_STEPS.length - 1, Math.max(0, i + d));
  projScale = PROJ_STEPS[i];
  try { localStorage.setItem('l8proj', String(projScale)); } catch (e) {}
  applyProj(); armProj();
}
function projReset(){
  projScale = 1;
  try { localStorage.setItem('l8proj', '1'); } catch (e) {}
  applyProj(); armProj();
}
/* 导航高度自适应：单行 / 换行 / 汉堡三种形态下正文都不被遮住 */
function syncNavPad(){
  const nav = document.querySelector('.top-nav');
  if (!nav) return;
  document.body.style.paddingTop = Math.max(76, nav.offsetHeight + 28) + 'px';
}
window.addEventListener('resize', syncNavPad);
window.addEventListener('load', function(){ syncNavPad(); applyProj(); });
window.addEventListener('orientationchange', function(){ setTimeout(syncNavPad, 250); });
const SECTIONS = __SECTIONS__;
'''

# ---------------------------------------------------------------- assemble
def main():
    with open(DATA_FILE, encoding='utf-8') as f:
        d = json.load(f)

    secs = [('home', '首页'), ('vocab', '📇 E1 词汇'), ('vocab2', '📗 E2 词汇'), ('blitz', '⚡ 抢答'),
            ('connect', '🔗 连线'), ('mindmap', '🗺️ 词场'), ('luecken', '✍️ 动词填空'),
            ('eigenschaften', '🧩 属性配对'), ('softskills', '🎯 软技能'), ('umformen', '🔤 改写'),
            ('redemittel', '💬 表达库'), ('berufe', '🃏 猜职业'), ('uebersetzen', '🎯 中译德'),
            ('spiele', '🏆 游戏')]

    css = open(os.path.join(DIR, 'template_css.css'), encoding='utf-8').read()
    css = css.replace('</style>', EXTRA_CSS + '</style>')

    nav = ('<nav><div class="top-nav"><div class="logo" style="cursor:pointer" onclick="switchSection(\'home\')">'
           '<span class="logo-icon">🎓</span><span>Lektion 8 · Berufe</span></div>'
           '<div class="nav-links" id="navLinks">')
    for sid, lbl in secs:
        nav += '<button onclick="switchSection(\'%s\')">%s</button>' % (sid, lbl)
    nav += ('</div><button class="hamburger" onclick="toggleNav()">☰</button></div>'
            '<div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div></nav>')

    body = (sec_home(d) + sec_vocab(d) + sec_vocab2(d) + sec_blitz(d) + sec_connect(d) +
            sec_mindmap(d) + sec_luecken(d) + sec_eigenschaften(d) + sec_softskills(d) +
            sec_umformen(d) + sec_redemittel(d) + sec_berufe(d) + sec_uebersetzen(d) + sec_spiele(d))

    sb = [it['ans'].split('｜')[0].strip().split() for it in d['umformen']['items']]
    data_js = json.dumps({'sb': sb}, ensure_ascii=False)
    core_js = CORE_JS.replace('__SECTIONS__', json.dumps([s[0] for s in secs]))

    html = ('<!DOCTYPE html>\n<html lang="zh-CN" data-cw-profile="interaction">\n<head>\n'
            '<meta charset="UTF-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1.0">\n'
            '<title>Lektion 8 · Berufe und Berufswahl · 课堂互动课件</title>\n'
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
            '<script>\nconst DOC = ' + data_js + ';\n' + core_js + '\n' + EXTRA_JS + '\n</script>\n'
            '</body>\n</html>\n')

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(html)

    print('Generated: %s (%d bytes)' % (OUT, len(html)))

    # --- JS 语法自检（vm.compileFunction） ---
    js = html[html.find('<script>') + 8: html.rfind('</script>')]
    r = subprocess.run(['node', '-e',
                        'try{require("vm").compileFunction(JSON.parse(process.argv[1]));console.log("JS OK")}'
                        'catch(e){console.log("JS ERROR: "+e.message.substring(0,200))}',
                        json.dumps(js)], capture_output=True, text=True, timeout=20)
    print(r.stdout.strip() or r.stderr[:300])

    # --- section 配对 + id 完整性 ---
    print('sections open=%d close=%d' % (html.count('<section'), html.count('</section>')))
    for sid, _ in secs:
        assert 'id="%s"' % sid in html, 'missing section ' + sid
    print('all %d section ids present' % len(secs))

    # --- 数据量统计（与 JSON 对照） ---
    print('nav items = %d' % len(secs))
    print('E1 words = %d | E2 words = %d | blitz = %d | connect pairs = %s | mindmap = %d词/%d类'
          % (sum(len(g['words']) for g in d['vocabGroups']),
             sum(len(g['words']) for g in d['vocabGroupsE2']['groups']),
             len(d['blitz']),
             [len(g['pairs']) for g in d['connectGrids']],
             len(d['mindmap']['words']), len(d['mindmap']['cats'])))
    print('luecken gaps = %d (bank %d) | eigenschaften table = %d / match = %d | softskills = %d'
          % (len(d['luecken']['gaps']), len(d['luecken']['bank']),
             len(d['eigenschaften']['table']), len(d['eigenschaften']['match']),
             len(d['softskills']['gaps'])))
    print('umformen = %d | redemittel cols = %d+%d | berufe tasks = %d | uebersetzung sentences = %d | games = %d'
          % (len(d['umformen']['items']), len(d['redemittel']['vorteile']['cols']),
             len(d['redemittel']['statistik']['cols']), len(d['berufe']['tasks']),
             len(d['uebersetzen']['sentences']), len(d['klassenspiele'])))
    print('vc-card = %d | cloze-blank = %d | input[data-ans] = %d | css %d bytes'
          % (html.count('class="vc-card'), html.count('cloze-blank'),
             html.count('data-ans='), len(css)))


if __name__ == '__main__':
    main()
