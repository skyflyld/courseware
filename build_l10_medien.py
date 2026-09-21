#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_l10_medien.py — Lektion 10《Diese Medien sind mir wichtig!》互动课件生成器
输入: l10-data.json（由 make_l10_data.py 从教材页 OCR 取证生成）
输出: lektion10-funktionen-der-massenmedien.html（单文件，自包含 CSS/JS，零外部请求）

基底（两页共用）：build_l8_berufe.py（设计令牌 / 词卡 / 连线 / 面板 / 投影挡位）
                + build_l8_t1t2.py（读词查义面板、词库完形 clz-*、参考写法 refShow、表格 tb、stp）
                + build_l9_bewerbung.py（qt 引用块 / gh 语法加粗 / vc-detail 触控尺寸修订）
原子原则：一个脚本 → 一个产物；不在产物上做增量修补。
数据纪律：德文/中文一律取 l10-data.json 原值，不改写、不补造。
"""
import json
import os
import random
import re
import subprocess

import build_l8_berufe as base
import build_l8_t1t2 as t12
import build_l9_bewerbung as l9

DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(DIR, 'l10-data.json')
OUT = os.path.join(DIR, 'lektion10-funktionen-der-massenmedien.html')

h = l9.h
esc_attr = base.esc_attr
tools_buttons = base.tools_buttons
gloss_text = t12.gloss_text
gloss_index = t12.gloss_index
gloss_word = t12.gloss_word


# 词卡排版：主词与第一个标注之间用不换行空格粘住，避免 360px 窄屏下
# 「verschmelzen」+ 换行 + 「(verschmilzt, …)」的孤立括号（标注折断）。
# 只在本页生效，不动共用基底（不影响 L8/L9 已上线页面）。
_orig_word_html = base.word_html
_PREP_TAIL = re.compile(r'\s*(\+(?:[^()\s]+(?:\s+[^()\s]+)*))\s*$')


def _word_html_noglue(w):
    tail = ''
    m = _PREP_TAIL.search(str(w))
    if m:
        tail, w = m.group(1), str(w)[:m.start()]
    out = _orig_word_html(w)
    if tail:
        out += '<span class="vc-note"> %s</span>' % h(tail)
    for cls in ('vc-note', 'vc-note vc-phon', 'vc-note vc-pl'):
        out = out.replace('</span><span class="%s">' % cls, '</span>\u00a0<span class="%s">' % cls)
    return out


base.word_html = _word_html_noglue


def _js(x):
    return t12._js_str(x)


def _gloss_span(e, surface):
    """点词面板：词 / 中文 / 例句 + 出处（教材词表 or 课件补充）。"""
    ex = e.get('ex', '')
    if e.get('src'):
        ex = ('例：' + ex + '\n出处：' + e['src']) if ex else ('出处：' + e['src'])
    return ('<span class="gl" title="点一下看释义与例句" '
            'onclick="event.stopPropagation();showVocab(%s)">%s</span>'
            % (','.join(_js(x) for x in (e.get('w', ''), e.get('zh', ''), ex)), h(surface)))


t12._gloss_span = _gloss_span          # 让 t12.gloss_text / gloss_word 用本页风格
l9._gloss_span = _gloss_span


# ---------------------------------------------------------------- 1 home
def sec_home(d):
    m = d['meta']
    objs = ''.join('<li>%s</li>' % h(x) for x in m['objectives'])
    rows = []
    for item in m['flow']:
        a, b = item.split('：', 1) if '：' in item else (item, '')
        rows.append('<tr><td class="fl-t">%s</td><td>%s</td></tr>' % (h(a), h(b)))
    n_vocab = sum(len(g['words']) for g in d['vocab']['groups'])
    n_pairs = sum(len(g['pairs']) for g in d['connectGrids'])
    n_ex = len(d['t1ex']['groups']) + len(d['t2ex']['groups'])
    cards = [
        ('t1', '📖 T1 课文 · 沟通的今昔', '%s 段 · %d 个可点词 · %d 空答案印在横线上'
         % (len(d['t1']['cloze']), len(d['t1']['glossar']), sum(len(b['ans']) for b in d['t1']['cloze']))),
        ('t1ex', '✍️ T1 练习', '%d 组：完形 / 配对 / 归纳表 / 被动改主动 / 填空 / 翻译' % len(d['t1ex']['groups'])),
        ('t2', '📺 T2 课文 · 大众传媒的功能', '%s 段 · %d 个可点词 · 五种功能'
         % (len(d['t2']['cloze']), len(d['t2']['glossar']))),
        ('t2ex', '✅ T2 练习', '%d 组：完形 / 功能归类 / um…zu·damit / 动词填空 / 翻译' % len(d['t2ex']['groups'])),
        ('vocab', '🃏 词汇卡', '%d 词分 %d 组 · 点卡翻面' % (n_vocab, len(d['vocab']['groups']))),
        ('grammar', '🔤 语法', '%d 张表：被动语态 / zu 不定式 / um…zu 与 damit' % len(d['grammar']['tables'])),
        ('connect', '🔗 连线配对', '%d 组 · %d 对' % (len(d['connectGrids']), n_pairs)),
        ('translation', '🎯 翻译卡', '%d 张课文关键句 · 先自己译再翻面' % len(d['translation']['cards'])),
    ]
    g = ''.join('<div class="text-card home-card" onclick="switchSection(\'%s\')"><h3>%s</h3><p>%s</p></div>'
                % (i, t, s) for i, t, s in cards)
    return '''    <section id="home" class="active">
      <div class="hero">
        <h1>%s</h1>
        <p class="sub">%s</p>
        <p class="meta">%s</p>
      </div>
      <div class="highlight-box">🎬 怎么用：点顶部导航切节；课文里带虚线的德语词点一下出释义与例句；词卡点一下翻面；练习写完点「✓ 检查」；投影时点右下角 A± 放大。</div>
      <div class="home-grid">%s</div>
      <div class="obj-box"><strong>学习目标 Lernziele：</strong><ul>%s</ul></div>
      <div class="text-card" style="margin-top:12px">
        <h3>🧭 学习路线（建议 45 分钟走完，共 %d 组练习）</h3>
        <table class="flow-table">%s</table>
      </div>
    </section>
''' % (h(m['title']), h(m['subtitle']), h(m['source']), g, objs, n_ex, ''.join(rows))


# ---------------------------------------------------------------- 课文（读）
def read_paras(t, pairs):
    """阅读页：[[n]] → 答案印在横线上（.ans-w），其余关键词自动可点。"""
    out, n = [], 0
    for blk in t['cloze']:
        txt = gloss_text(blk['p'], pairs)
        for a in blk['ans']:
            n += 1
            txt = txt.replace('[[%d]]' % n,
                              '<span class="ans-w">%s</span>' % gloss_word(a, pairs), 1)
        out.append('<p class="cloze-p" lang="de">%s</p>' % txt)
    return ''.join(out)


def struct_html(t):
    return ''.join(
        '<div class="stp"><span class="stp-n">%s</span><span class="stp-fn" lang="de">%s</span>'
        '<div class="rm-cn">%s</div></div>' % (h(s['n']), h(s['de']), h(s['cn']))
        for s in t['structure'])


def quotes_html(t):
    return ''.join(
        '<div class="qt"><div class="qt-h">%s <span class="src">%s</span></div>'
        '<div class="qt-de" lang="de">%s</div><div class="qt-zh">%s</div></div>'
        % (h(q['n']), h(q['src']), h(q['de']), h(q['zh'])) for q in t['quotes'])


def bank_static(bank):
    if not bank:
        return ''
    return ('<div class="bank-box"><strong>教材词库 Wortbank（%d 词）：</strong>%s</div>'
            % (len(bank), ''.join('<span class="bank-chip static">%s</span>' % h(w) for w in bank)))


def sec_t1(d):
    t = d['t1']
    pairs = gloss_index(t['glossar'])
    return '''    <section id="t1">
      <h2 class="section-title"><span class="num">1</span> 📖 %s <span class="src src-lg">%s · %s</span></h2>
      <p class="zh-hint">%s</p>
      <p class="zh-hint">✏️ 带虚线的德文词点一下，弹出中文释义和这词在课文里的原句。带<b>蓝色下划线</b>的词是教材 Ü6 的填空词，已直接印在横线上。</p>
      %s
      <div class="text-card read-card">%s</div>
      <p class="zh-hint note">📌 %s</p>
      <div class="text-card">
        <h3>🕰️ 五个时间节点（课文脉络）</h3>
        %s
      </div>
      <div class="text-card">
        <h3>💬 这篇课文最该背下来的句子</h3>
        %s
      </div>
    </section>
''' % (h(t['title']), h(t['kind']), h(t['sub']), h(t['lead']), bank_static(t['bank']),
       read_paras(t, pairs), h(t['provenance']), struct_html(t), quotes_html(t))


def sec_t2(d):
    t = d['t2']
    pairs = gloss_index(t['glossar'])
    qbox = ('<div class="text-card qbox"><h3>❓ 教材 S.300 旁注里的两个问题</h3>'
            '<p class="zh-hint">%s</p>%s<p class="zh-hint note">答案看第 7 节「语法」的'
            '<b>um … zu 与 damit 选择条件</b>表。</p></div>'
            % (h(t['qbox']),
               ''.join('<div class="qt-de" lang="de">• %s</div>' % h(x) for x in t['qbex'])))
    return '''    <section id="t2">
      <h2 class="section-title"><span class="num">3</span> 📺 %s <span class="src src-lg">%s · %s</span></h2>
      <p class="zh-hint">%s</p>
      %s
      <div class="text-card read-card">%s</div>
      <div class="text-card box-card">
        <h3>📌 旁注框（教材 S.300 原文照录）</h3>
        <p class="box-de" lang="de">%s</p>
      </div>
      <p class="zh-hint note">📌 %s</p>
      <div class="text-card">
        <h3>🎯 五种功能（课文的五条线）</h3>
        %s
      </div>
      <div class="text-card">
        <h3>💬 这篇课文最该背下来的句子</h3>
        %s
      </div>
      %s
    </section>
''' % (h(t['title']), h(t['kind']), h(t['sub']), h(t['lead']), bank_static(t['bank']),
       read_paras(t, pairs), h(t['box']), h(t['provenance']), struct_html(t), quotes_html(t), qbox)


# ---------------------------------------------------------------- 练习渲染件
def alt_list(alt_map, n):
    v = alt_map.get(str(n), [])
    return '|'.join(v) if isinstance(v, list) else str(v)


def clone_paras(blocks, alt_map):
    """[[n]] → 输入的填空格（kind=fill 用）。"""
    out, n = [], 0
    for blk in blocks:
        p, ans = blk['p'], blk['ans']
        for a in ans:
            n += 1
            w = max(112, min(420, len(a) * 11 + 34))
            p = p.replace('[[%d]]' % n,
                          '<input class="bf-in" style="width:%dpx" data-ans="%s" data-alt="%s" '
                          'lang="de" spellcheck="false" autocomplete="off" '
                          'oninput="bfGrow(this)">' % (w, esc_attr(a), esc_attr(alt_list(alt_map, n))), 1)
        out.append('<p class="cloze-p" lang="de">%s</p>' % p)
    return ''.join(out)


def tag_paras(raw, alt_map):
    """kind=fill 且自带 paras（形如 [p, ans, alt] 或 [p, ans]）。"""
    out = []
    for item in raw:
        p, ans = item[0], item[1]
        alts = item[2] if len(item) > 2 else []
        for k, a in enumerate(ans):
            w = max(112, min(420, len(a) * 11 + 34))
            al = alts[k] if k < len(alts) else ''
            p = p.replace('<%d>' % (k + 1),
                          '<input class="bf-in" style="width:%dpx" data-ans="%s" data-alt="%s" '
                          'lang="de" spellcheck="false" autocomplete="off" '
                          'oninput="bfGrow(this)">' % (w, esc_attr(a), esc_attr(al)), 1)
        out.append('<p class="cloze-p" lang="de">%s</p>' % p)
    return ''.join(out)


def chip_paras(blocks, alt_map, key):
    """kind=cloze：[[n]] → 可点空格 + 词库碎片。"""
    out, n = [], 0
    for blk in blocks:
        p = blk['p']
        for a in blk['ans']:
            n += 1
            p = p.replace('[[%d]]' % n,
                          '<span class="cloze-blank" data-ph="(%d)" data-ans="%s" data-alt="%s" '
                          'onclick="clzClick(this)">(%d)</span>' % (n, esc_attr(a), esc_attr(alt_list(alt_map, n)), n), 1)
        out.append('<p class="cloze-p" lang="de">%s</p>' % p)
    return ''.join(out)


def connect_html(gid, pairs, title=None, src=None):
    idx = list(range(len(pairs)))
    random.Random(700 + gid).shuffle(idx)
    left = ''.join('<div class="c-item de" data-pair="%d" data-gid="%d" lang="de" onclick="cClick(this)">%s</div>'
                   % (i, gid, h(p[0])) for i, p in enumerate(pairs))
    right = ''.join('<div class="c-item cn" data-pair="%d" data-gid="%d" onclick="cClick(this)">%s</div>'
                    % (j, gid, h(pairs[j][1])) for j in idx)
    head = ''
    if title:
        head = '<h3>%s%s</h3>' % (h(title), (' <span class="src src-lg">%s</span>' % h(src)) if src else '')
    return ('''      <div class="connect-game">%s
        <div class="connect-field"><div class="connect-col">%s</div><div class="connect-col">%s</div></div>
        <div class="connect-score">匹配：<span id="cg-cnt-%d">0</span> / %d</div>
      </div>''' % (head, left, right, gid, len(pairs)))


def note_html(txt, warn=False):
    if not txt:
        return ''
    return '<p class="zh-hint note%s">%s</p>' % (' warn' if warn else '', h(txt))


def blocks_of(ex, d):
    """练习组的填空段落：ref 指课文，或自带 paras（[[n]] 形式 / [p, ans] 形式）。
    返回 ({'p','ans'} 列表, alt 映射)。"""
    if ex.get('ref'):
        t = d[ex['ref']]
        return t['cloze'], (ex.get('alt') or t.get('alt', {}))
    raw = ex.get('paras') or []
    if raw and isinstance(raw[0], dict):
        return raw, (ex.get('alt') or {})
    return [{'p': r[0], 'ans': r[1]} for r in raw], (ex.get('alt') or {})


def render_group(ex, gid, d):
    """一个练习组 → HTML。gid 用于互不冲突的 DOM id / 连线组号。"""
    kind = ex['kind']
    m = re.match(r'(Ü[\d.]+)\s*(.*)', ex['title'])
    badge, tname = (m.group(1), m.group(2)) if m else ('', ex['title'])
    head = ('<div class="ex-group" id="ex%d">'
            '<h3 class="ex-title"><span class="ex-num">%s</span> %s '
            '<span class="src src-lg">%s</span></h3><p class="zh-hint">%s</p>'
            % (gid, h(badge), h(tname), h(ex['src']), h(ex['instruction'])))
    warn = '推定' in (ex.get('note') or '')
    body = ''

    if kind in ('fill', 'cloze'):
        bank = ex.get('bank') or []
        alt_map = ex.get('alt') or {}
        if bank:
            if kind == 'cloze':
                chips = ''.join('<span class="bank-chip" onclick="clzFill(\'clz-%d\', this)">%s</span>'
                                % (gid, h(w)) for w in bank)
                bank_html = ('<div class="bank-box"><strong>Wortbank（%d 词）：</strong>%s</div>'
                             % (len(bank), chips))
            else:
                bank_html = ('<div class="bank-box"><strong>Wortbank（%d 词，需要变位）：</strong>%s</div>'
                             % (len(bank), ''.join('<span class="bank-chip static">%s</span>' % h(w)
                                                   for w in bank)))
        else:
            bank_html = ('<p class="zh-hint note">原题为听力填空，<b>教材没有词库</b>：'
                         '先自己按上下文填，再点「👁 显示答案」对照。</p>')
        if kind == 'cloze':
            blocks, am = blocks_of(ex, d)
            paras = chip_paras(blocks, am, gid)
            body = ('<div class="clz-box" id="clz-%d">%s%s%s</div>'
                    % (gid, bank_html, paras,
                       tools_buttons(['<button class="btn" onclick="clzCheck(\'clz-%d\')">✓ 检查</button>' % gid,
                                      '<button class="btn ghost" onclick="clzReveal(\'clz-%d\')">👁 显示答案</button>' % gid,
                                      '<button class="btn ghost" onclick="clzClear(\'clz-%d\')">↺ 清空</button>' % gid,
                                      '<span id="clz-%d-res" class="kw-result"></span>' % gid])))
        else:
            if ex.get('ref'):
                blocks, am = blocks_of(ex, d)
                paras = clone_paras(blocks, am)
            else:
                paras = tag_paras(ex['paras'], {})
            body = ('<div class="bf-box" id="bf-%d">%s%s%s</div>'
                    % (gid, bank_html, paras,
                       tools_buttons(['<button class="btn" onclick="bfCheck(\'bf-%d\')">✓ 检查</button>' % gid,
                                      '<button class="btn ghost" onclick="bfReveal(\'bf-%d\')">👁 显示答案</button>' % gid,
                                      '<button class="btn ghost" onclick="bfClear(\'bf-%d\')">↺ 清空</button>' % gid,
                                      '<span id="bf-%d-res" class="kw-result"></span>' % gid])))

    elif kind == 'match':
        body = connect_html(gid, ex['pairs'])
        if ex.get('table'):
            tb = ex['table']
            body += ('<div class="text-card"><h4>%s <span class="src">%s</span></h4>'
                     '<table class="tb"><tr>%s</tr>%s</table></div>'
                     % (h(tb['title']), h(tb['src']),
                        ''.join('<th>%s</th>' % h(c) for c in tb['headers']),
                        ''.join('<tr>%s</tr>' % ''.join('<td lang="de">%s</td>' % h(c) for c in r)
                                for r in tb['rows'])))

    elif kind == 'table':
        rows = ''
        for r in ex['rows']:
            cells = ''.join('<td lang="de">%s</td>' % h(c) for c in r)
            rows += '<tr>%s</tr>' % cells
        body = ('<div class="tb-wrap ans-hide">'
                '<div class="vocab-table-wrap" style="overflow-x:auto"><table class="tb">'
                '<tr>%s</tr>%s</table></div>'
                '<div class="kw-tools"><button class="btn ghost" onclick="tblToggle(this)">'
                '👁 显示参考归纳</button><span class="zh-hint note">灰底处是参考答案</span></div></div>'
                % (''.join('<th>%s</th>' % h(c) for c in ex['headers']), rows))
        if ex.get('beispiel'):
            body += ('<div class="text-card"><h4>教材 Beispiel（原文照录）</h4>%s</div>'
                     % ''.join('<div class="qt-de" lang="de"><b>%s</b> %s</div>' % (h(a), h(b))
                               for a, b in ex['beispiel']))

    elif kind == 'open':
        if ex.get('beispiel'):
            body += ('<div class="text-card"><h4>教材 Beispiel</h4><div class="qt-de" lang="de">%s</div></div>'
                     % h(ex['beispiel']))
        for i, it in enumerate(ex['items'], 1):
            body += ('<div class="fill-item open-item">'
                     '<p class="lk-de" lang="de"><b>%s)</b> %s</p>'
                     '<div class="fill-input-line">'
                     '<input class="fill-input" lang="de" spellcheck="false" placeholder="写你的主动句 / 目的句…">'
                     '<button class="fill-check" onclick="refShow(this)">💬 参考写法</button>'
                     '<span class="fill-result"></span></div>'
                     '<div class="ref-box" style="display:none"><span class="ref-lbl">参考写法</span>'
                     '<div lang="de">%s</div></div></div>'
                     % (chr(96 + i), h(it[0]), h(it[1])))

    elif kind == 'trans':
        for i, it in enumerate(ex['items'], 1):
            body += ('<div class="fill-item open-item">'
                     '<p class="lk-de" lang="de"><b>%d)</b> %s</p>'
                     '<div class="fill-input-line">'
                     '<button class="fill-check" onclick="refShow(this)">💬 参考译文</button>'
                     '<span class="fill-result"></span></div>'
                     '<div class="ref-box" style="display:none"><span class="ref-lbl">参考译文</span>'
                     '<div>%s</div></div></div>' % (i, h(it[0]), h(it[1])))

    elif kind == 'quiz':
        opts = ex['opts']
        items = ''
        for i, (q, a) in enumerate(ex['items']):
            items += ('<div class="qz-item" data-a="%d"><p class="qz-q" lang="de">%s</p>'
                      '<div class="qz-opts">%s</div></div>'
                      % (a, h(q), ''.join('<span class="qz-opt" onclick="qzPick(this)" lang="de">%s</span>'
                                          % h(o) for o in opts)))
        body = ('<div class="qz-box" id="qz-%d">%s</div>%s'
                % (gid, items,
                   tools_buttons(['<button class="btn" onclick="qzCheck(\'qz-%d\')">✓ 检查</button>' % gid,
                                  '<button class="btn ghost" onclick="qzClear(\'qz-%d\')">↺ 清空</button>' % gid,
                                  '<span id="qz-%d-res" class="kw-result"></span>' % gid])))

    if ex.get('redemittel'):
        rm = ex['redemittel']
        body += ('<div class="text-card"><h4>%s</h4>%s</div>'
                 % (h(rm['title']),
                    ''.join('<div class="rm-item"><div class="rm-de" lang="de">%s</div>'
                            '<div class="rm-tip">%s</div></div>' % (h(a), h(b)) for a, b in rm['items'])))
    return head + body + note_html(ex.get('note'), warn) + '</div>'


def sec_ex(d, key, num):
    ex = d[key]
    gid0 = 10 if key == 't1ex' else 100
    groups = ''.join(render_group(g, gid0 + i, d) for i, g in enumerate(ex['groups']))
    return '''    <section id="%s">
      <h2 class="section-title"><span class="num">%d</span> %s <span class="src src-lg">%s</span></h2>
      <p class="zh-hint">%s</p>
%s
    </section>
''' % (key, num, h(ex['title']), h(ex['src']), h(ex['instruction']), groups)


# ---------------------------------------------------------------- 词汇卡
def sec_vocab(d):
    v = d['vocab']
    groups = v['groups']
    tabs, panels = [], []
    for i, grp in enumerate(groups):
        a = ' active' if i == 0 else ''
        tabs.append('<button class="person-btn%s" onclick="switchVocabTab(\'vc-%s\',this)">%s</button>'
                    % (a, grp['id'], h(grp['label'])))
        cards = ''.join(base.vocab_card(wd, grp.get('src', '')) for wd in grp['words'])
        panels.append('<div class="person-content%s" id="vc-%s">'
                      '<p class="zh-hint note">📖 出处：<span class="src">%s</span>（%d 词）</p>'
                      '<div class="vocab-grid">%s</div></div>'
                      % (a, grp['id'], h(grp.get('src', '')), len(grp['words']), cards))
    rows = ''.join('<tr><td class="vt-de" lang="de">%s</td><td class="vt-cn">%s</td></tr>'
                   % (base.word_html(wd['w']), h(wd['cn']))
                   for grp in groups for wd in grp['words'])
    n = sum(len(g['words']) for g in groups)
    return '''    <section id="vocab">
      <h2 class="section-title"><span class="num">6</span> 🃏 %s</h2>
      <p class="zh-hint">%s</p>
      <p class="zh-hint note">教材标注：<b>( )</b> 词尾 / 复数形式，<b>¨</b> 变音，<b>...</b> 省略词干，<b>+A / +D</b> 支配格，<b>nur Sg</b> 仅单数，<b>[ ]</b> 读音。标注已降权显示，主词为黑体。</p>
      <div class="person-tabs">%s</div>%s
      %s
      <div id="l10Table" style="display:none"><div class="vocab-table-wrap" style="overflow-x:auto"><table class="vocab-table">%s</table></div></div>
      <p class="zh-hint note">来源：%s</p>
    </section>
''' % (h(v['title']), h(v['instruction']), ''.join(tabs), ''.join(panels),
       tools_buttons(['<button class="btn ghost" onclick="toggleBox(\'l10Table\')">📋 展开全表（%d 词）</button>' % n]),
       rows, h(v['src']))


# ---------------------------------------------------------------- 语法
def sec_grammar(d):
    g = d['grammar']
    tables = []
    for tb in g['tables']:
        head = ''.join('<th>%s</th>' % h(c) for c in tb['headers'])
        rows = ''.join('<tr>%s</tr>' % ''.join('<td lang="de">%s</td>' % l9.gh(c) for c in r)
                       for r in tb['rows'])
        tables.append('<div class="text-card"><h3>%s <span class="src">%s</span></h3>'
                      '<div class="vocab-table-wrap" style="overflow-x:auto">'
                      '<table class="tb"><tr>%s</tr>%s</table></div></div>'
                      % (h(tb['title']), h(tb.get('src', '')), head, rows))
    ex = ''.join('<div class="rm-item"><div class="rm-de" lang="de">%s</div>'
                 '<div class="rm-cn">%s</div></div>' % (h(e['de']), h(e['zh'])) for e in g['examples'])
    return '''    <section id="grammar">
      <h2 class="section-title"><span class="num">7</span> 🔤 语法 · Grammatik</h2>
      <p class="zh-hint">六张表按顺序看：被动语态 → 被动改主动 → zu 不定式 → um…zu → damit → 二者怎么选。表里<b class="gh">加粗</b>的就是这一行的语法点。最后六个例句读出声。</p>
      %s
      <div class="text-card">
        <h3>🗣️ 例句 · Beispiele（读一遍，注意加粗处）</h3>
        %s
      </div>
    </section>
''' % (''.join(tables), ex)


# ---------------------------------------------------------------- 连线
def sec_connect(d):
    out = []
    for gi, cg in enumerate(d['connectGrids']):
        out.append(connect_html(gi, cg['pairs'], cg['title'], cg.get('src', '')))
    return '''    <section id="connect">
      <h2 class="section-title"><span class="num">8</span> 🔗 连线配对 · Vernetzen</h2>
      <p class="zh-hint">点左列德语，再点右列中文，配对成功变绿；点错会红闪一下，可重试。三组各连一遍。</p>
%s
    </section>
''' % '\n'.join(out)


# ---------------------------------------------------------------- 翻译卡
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
      <h2 class="section-title"><span class="num">9</span> 🎯 %s</h2>
      <p class="zh-hint">%s</p>
      <p class="zh-hint note">%s</p>
      <div class="translation-grid">%s</div>
    </section>
''' % (h(t['title']), h(t['instruction']), h(t['note']), '\n'.join(cards))


# ---------------------------------------------------------------- CSS / JS
CSS_L10 = '''
  /* ===== 练习组 ===== */
  .ex-group { background: #fbfcfe; border: 1px solid #e3e6eb; border-radius: 12px;
              padding: 12px 14px; margin: 14px 0; }
  .ex-title { font-size: var(--fs-h3); margin: 0 0 6px; display: flex; flex-wrap: wrap;
              align-items: baseline; gap: 8px; }
  .ex-num { display: inline-block; background: #1a73e8; color: #fff; border-radius: 8px;
            padding: 2px 10px; font-size: var(--fs-cap); font-weight: 700; }
  .bank-chip.static { background: #f8f9fa; border-style: dashed; color: #3c4450; cursor: default; }
  .bank-chip.static:hover { background: #f8f9fa; }
  /* 行内填空格（需要变位 / 无词库时用） */
  .bf-in { display: inline-block; min-width: 112px; max-width: 100%; border: 0;
           border-bottom: 2px solid #0b56b8; background: #f4f8fe; border-radius: 4px 4px 0 0;
           font: inherit; font-weight: 700; color: #123a72; padding: 2px 6px; text-align: center;
           min-height: 34px; }
  .bf-in::placeholder { color: #aab2bd; font-weight: 400; }
  .bf-in:focus { outline: 2px solid #1a73e8; outline-offset: 1px; background: #fff; }
  .bf-in.ok { border-bottom-color: #146c2e; background: #e6f4ea; color: #146c2e; }
  .bf-in.bad { border-bottom-color: #b3261e; background: #fdecea; color: #a51c17; }
  /* 表格里的隐藏答案 */
  .ans-hide .hid { color: transparent; background: #eef1f5; border-radius: 4px; }
  .ans-hide .hid::selection { color: transparent; }
  .tb-wrap .kw-tools { margin: 8px 0 0; }
  /* 提示 / 旁注 */
  .zh-hint.warn { background: #fff8e6; border-left: 4px solid #b8860b; border-radius: 0 6px 6px 0;
                  padding: 8px 12px; color: #4a3a10; }
  .box-card .box-de { font-size: var(--fs-body); line-height: 1.8; margin: 0; background: #f7f8fa;
                      border-left: 4px solid #6a1b9a; border-radius: 0 8px 8px 0; padding: 10px 12px; }
  .qbox h3 { color: #6a1b9a; }
  .open-item .lk-de { font-size: var(--fs-body); line-height: 1.9; margin: 0 0 8px; }
  .open-item { border-left: 3px solid #1a73e8; }
  .ex-group .connect-game { margin: 12px 0 4px; }
  .ex-group .text-card { margin: 10px 0 0; }
  .ex-group h4 { font-size: var(--fs-body); font-weight: 700; margin: 0 0 8px; color: #1a3d6d; }
  /* 行宽控制（技能 §20.3 闸门 5：正文单行 ≤75 字符）——德语长句不控行宽很难读。
     ch 取的是「0」字宽，德语小写均宽更窄，故 58ch ≈ 72 字符/行，才真正落到 ≤75。 */
  .read-card .cloze-p, .clz-box .cloze-p, .bf-box .cloze-p,
  .rm-de, .open-item .lk-de, .qt-de, .tc-de, .box-de { max-width: 58ch; }
  .hero .meta { max-width: 56ch; }
  .bf-box .cloze-p, .read-card .cloze-p { line-height: 1.95; }
'''

JS_L10 = '''
/* ===== 行内填空（需变位 / 无词库） ===== */
function bfGrow(el){
  const n = (el.value || '').length;
  el.style.width = Math.max(112, Math.min(460, n * 11 + 34)) + 'px';
}
function bfCheck(boxId){
  const box = document.getElementById(boxId);
  if (!box) return;
  let ok = 0, tot = 0, empty = 0;
  box.querySelectorAll('.bf-in').forEach(function(inp){
    tot++;
    const v = (inp.value || '').trim();
    if (!v){ empty++; inp.classList.remove('ok','bad'); return; }
    const alts = (inp.dataset.alt || '').split('|').filter(Boolean).map(norm);
    const good = norm(v) === norm(inp.dataset.ans) || alts.indexOf(norm(v)) >= 0;
    inp.classList.remove('ok','bad'); inp.classList.add(good ? 'ok' : 'bad');
    if (good) ok++;
  });
  const r = document.getElementById(boxId + '-res');
  if (r){ r.textContent = '正确 ' + ok + ' / ' + tot + ' 空' + (empty ? '（还有 ' + empty + ' 空未填）' : ''); r.className = 'kw-result'; }
}
function bfReveal(boxId){
  const box = document.getElementById(boxId);
  if (!box) return;
  box.querySelectorAll('.bf-in').forEach(function(inp){
    inp.value = inp.dataset.ans;
    inp.classList.remove('bad'); inp.classList.add('ok');
    bfGrow(inp);
  });
  const r = document.getElementById(boxId + '-res');
  if (r){ r.textContent = '已显示参考答案'; r.className = 'kw-result'; }
}
function bfClear(boxId){
  const box = document.getElementById(boxId);
  if (!box) return;
  box.querySelectorAll('.bf-in').forEach(function(inp){
    inp.value = ''; inp.classList.remove('ok','bad'); bfGrow(inp);
  });
  const r = document.getElementById(boxId + '-res');
  if (r) r.textContent = '';
}
/* ===== 表格答案显隐 ===== */
function tblToggle(btn){
  const w = btn.closest('.tb-wrap');
  if (!w) return;
  const hid = w.classList.toggle('ans-hide');
  btn.textContent = hid ? '👁 显示参考归纳' : '🙈 收起答案';
}
'''


# ---------------------------------------------------------------- assemble
def main():
    with open(DATA_FILE, encoding='utf-8') as f:
        d = json.load(f)

    secs = [('home', '首页'), ('t1', '📖 T1 课文'), ('t1ex', '✍️ T1 练习'),
            ('t2', '📺 T2 课文'), ('t2ex', '✅ T2 练习'), ('vocab', '🃏 词汇卡'),
            ('grammar', '🔤 语法'), ('connect', '🔗 连线'), ('translation', '🎯 翻译卡')]

    css = open(os.path.join(DIR, 'template_css.css'), encoding='utf-8').read()
    css = css.replace('</style>', base.EXTRA_CSS + t12.CSS_EXTRA + l9.CSS_L9 + CSS_L10 + '</style>')

    nav = ('<nav><div class="top-nav"><div class="logo" style="cursor:pointer" onclick="switchSection(\'home\')">'
           '<span class="logo-icon">📺</span><span>Lektion 10 · Massenmedien</span></div>'
           '<div class="nav-links" id="navLinks">')
    for sid, lbl in secs:
        nav += '<button onclick="switchSection(\'%s\')">%s</button>' % (sid, lbl)
    nav += ('</div><button class="hamburger" onclick="toggleNav()">☰</button></div>'
            '<div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div></nav>')

    body = (sec_home(d) + sec_t1(d) + sec_ex(d, 't1ex', 2) + sec_t2(d) + sec_ex(d, 't2ex', 4)
            + sec_vocab(d) + sec_grammar(d) + sec_connect(d) + sec_translation(d))
    # 行首禁则：省略号/斜杠前的不换行空格——避免「um / … zu」「Ü4 /」把符号挤到行首（§20 换行质量）
    body = body.replace(' …', '\u00a0…').replace(' / ', '\u00a0/ ')

    core_js = base.CORE_JS.replace('__SECTIONS__', json.dumps([s[0] for s in secs]))

    html = ('<!DOCTYPE html>\n<html lang="zh-CN" data-cw-profile="interaction">\n<head>\n'
            '<meta charset="UTF-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1.0">\n'
            '<title>Lektion 10 · Diese Medien sind mir wichtig! · 互动课件</title>\n'
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
            '<script>\nconst DOC = {};\n' + core_js + '\n' + base.EXTRA_JS + '\n'
            + t12.JS_EXTRA + '\n' + JS_L10 + '\n</script>\n</body>\n</html>\n')

    for _a, _b in [('已显示参考答案（教师用）', '已显示参考答案'),
                   ('（课堂现场用，宽屏才显示）', '（宽屏才显示）'),
                   ('（投影时不用弹窗）', '')]:
        html = html.replace(_a, _b)

    html = html.replace(' · ', '\u00a0· ')

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
    print('all %d section ids present | nav items = %d' % (len(secs), len(secs)))
    assert '%%' not in html, '标记未替换干净'
    for ch in ('<1>', '<2>', '[[1]]'):
        assert ch not in html, '占位符未替换: ' + ch

    n_vc = sum(len(g['words']) for g in d['vocab']['groups'])
    n_pair = sum(len(g['pairs']) for g in d['connectGrids']) + \
        sum(len(g['pairs']) for g in d['t1ex']['groups'] if g['kind'] == 'match')
    print('vc-card = %d (词表 %d) | gl = %d (词条 %d+%d) | c-item = %d (对 %d×2)'
          % (html.count('class="vc-card"'), n_vc, html.count('class="gl"'),
             len(d['t1']['glossar']), len(d['t2']['glossar']),
             html.count('class="c-item'), n_pair))
    print('bf-in = %d | cloze-blank = %d | qz-item = %d | tc-card = %d | stp = %d | qt = %d | ex-group = %d'
          % (html.count('class="bf-in"'), html.count('cloze-blank'), html.count('class="qz-item"'),
             html.count('class="tc-card"'), html.count('class="stp"'), html.count('class="qt'),
             html.count('class="ex-group"')))
    assert html.count('class="tc-card"') == len(d['translation']['cards'])
    assert html.count('class="ex-group"') == len(d['t1ex']['groups']) + len(d['t2ex']['groups'])


if __name__ == '__main__':
    main()
