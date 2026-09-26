#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_l9_bewerbung.py — Lektion 9《Fit für die Bewerbung!》互动课件生成器
输入: l9-data.json
输出: lektion9-fit-fuer-die-bewerbung.html（单文件，自包含 CSS/JS，零外部请求）

基底: 复用 build_l8_berufe.py（设计令牌 / 投影挡位 / 词卡 / 连线 / 面板）
      + build_l8_t1t2.py（读词查义面板样式、选择题件 qz-*、表格 tb、段落结构 stp、透明卡片）
两页共用基底 = Sky 2026-09-20 指令「按两页共用的最新基底做，按 L9 的内容挑组件」。
原子原则: 一个脚本 → 一个产物；不在产物上做增量修补。
数据纪律: 德文/中文一律取 l9-data.json 原值，不改写、不补造。
"""
import json
import os
import random
import re
import subprocess

import build_l8_berufe as base
import build_l8_t1t2 as t12

DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(DIR, 'l9-data.json')
VOCAB_FILE = os.path.join(DIR, 'l9-vocab.json')          # 词汇/句型强化层（2026-09-26）
SB_DOC = []                                              # 句型工坊参考答案（按语序拼装的词块）


def slot_html(s):
    """句型骨架里的 [槽] 渲染成可换槽高亮。"""
    import re as _re
    return _re.sub(r'\[([^\[\]]+)\]', r'<span class="slot">\1</span>', h(s))


def wf_rows(rows):
    """词场表行：词条 / 中文（含易错提示）/ 常用搭配 / 教材例句。"""
    out = []
    for r in rows:
        note = ('<div class="wf-note">⚠ %s</div>'
                % h(r['note']).replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>')) \
            if r.get('note') else ''
        ex = ('%s' % h(r['ex'])) if r.get('ex') else '<span class="wf-none">（教材原页无此句）</span>'
        out.append('<tr><td class="wf-w" data-l="词条" lang="de">%s</td>'
                   '<td class="wf-cn" data-l="中文">%s%s</td>'
                   '<td class="wf-coll" data-l="搭配" lang="de">%s</td>'
                   '<td class="wf-ex" data-l="例句" lang="de">%s</td></tr>'
                   % (word_html(r['w']), h(r['cn']), note, h(r['coll']), ex))
    return ''.join(out)


def wf_table(rows):
    return ('<div class="vocab-table-wrap" style="overflow-x:auto"><table class="tb wf-table">'
            '<tr><th>词条</th><th>中文</th><th>常用搭配</th><th>教材例句</th></tr>%s</table></div>'
            % wf_rows(rows))


def sm_items(items):
    """句型条：功能标签 + 骨架（槽位高亮）+ 中文 + 用法提示 + 出处。"""
    return ''.join('''      <div class="sm-item">
        <div class="sm-fn">%s <span class="src">%s</span></div>
        <div class="sm-de" lang="de">%s</div>
        <div class="sm-zh">%s</div>
        <div class="sm-tip">💡 %s</div>
      </div>''' % (h(it['fn']), h(it['src']), slot_html(it['de']), h(it['zh']), h(it['tip']))
                    for it in items)


def sb_cards(items):
    """句型工坊：词块点选拼句（复用 L8 的 sb-* 组件与 JS）。"""
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
OUT = os.path.join(DIR, 'lektion9-fit-fuer-die-bewerbung.html')

h = base.h
esc_attr = base.esc_attr
tools_buttons = base.tools_buttons
_js = t12._js_str


def h(s):
    """正文转义 + 分隔符「·」禁用行首（换行质量层做法 4：用不换行空格粘住前文）。
    实测？grammar 表题「时间介词 · Zeitpräpositionen」在 390px 会以「·」开头起行。"""
    return base.h(str(s)).replace(' ·', '\u00a0·')


# ---------------------------------------------------------------- 读词查义
def _gloss_span(e, surface):
    ex = e.get('ex', '')
    if e.get('def'):
        ex = ex + '\n释义：' + e['def']
    return ('<span class="gl" title="点一下看释义与例句" '
            'onclick="event.stopPropagation();showVocab(%s)">%s</span>'
            % (','.join(_js(x) for x in (e.get('w', ''), e.get('zh', ''), ex)), h(surface)))


def gloss_render(text, gmap):
    """%%surface|key%% → 可点词（key 查词表；查不到就原样显示）"""
    out, last = [], 0
    for m in re.finditer(r'%%(.+?)%%', text):
        surface, key = m.group(1).split('|')
        out.append(h(text[last:m.start()]))
        e = gmap.get(key)
        out.append(_gloss_span(e, surface) if e else h(surface))
        last = m.end()
    out.append(h(text[last:]))
    return ''.join(out)


def vocab_card(wd, src):
    return base.vocab_card(wd, src)


def word_html(w):
    return base.word_html(w)


def gmap_of(t):
    return {e['w']: e for e in t.get('glossar', [])}


def plain(text):
    return re.sub(r'%%(.+?)%%', lambda m: m.group(1).split('|')[0], text)


def gh(text):
    """语法例句里的 %%…%% → 加粗强调（德语动词/介词）"""
    return re.sub(r'%%(.+?)%%', r'<b class="gh">\1</b>', h(text))


# ---------------------------------------------------------------- 1 home
def sec_home(d, v9):
    m = d['meta']
    objs = ''.join('<li>%s</li>' % h(x) for x in m['objectives'])
    rows = []
    for item in m['flow']:
        a, b = item.split('：', 1) if '：' in item else (item, '')
        rows.append('<tr><td class="fl-t">%s</td><td>%s</td></tr>' % (h(a), h(b)))
    n_vocab = sum(len(g['words']) for g in d['vocab']['groups'])
    n_pairs = sum(len(g['pairs']) for g in d['connectGrids'])
    wf = v9['wortfelder']
    n_wf = sum(len(g['rows']) for g in wf['groups'])
    n_sm = sum(len(g['items']) for g in v9['satzmuster']['groups'])
    n_sb = len(v9['satzmuster']['werkstatt']['items'])
    cards = [
        ('t1', '📖 Text 1 · 求职信', 'Anna 的求职信：学业 → 实践 → 能力，%d 个重点词可点' % len(d['t1']['glossar'])),
        ('t2', '👤 Text 2 · 面试', 'Max 的面试对话：五个阶段 + %d 个重点词可点' % len(d['t2']['glossar'])),
        ('vocab', '📚 词汇精讲', '%d 词条分 %d 个词场 · 带搭配与教材例句' % (n_wf, len(wf['groups']))),
        ('satzmuster', '🧩 句型库', '求职信 + 面试两套句型 · %d 条 + %d 句语序工坊' % (n_sm, n_sb)),
        ('grammar', '🔤 语法', 'lassen 四种用法 + 六个时间介词'),
        ('connect', '🔗 连线配对', '%d 组 · %d 对（含搭配连线）' % (len(d['connectGrids']), n_pairs)),
        ('luecken', '✍️ 介词填空', '%d 空 · 输入后点 ✓ 核对' % len(d['luecken']['items'])),
        ('anwenden', '✍️ 学以致用', '一封求职信完形 + 换槽造句（开放，不判对错）'),
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
      <div class="highlight-box">🎬 怎么用：点顶部导航切节；课文里带虚线的德语词点一下出释义与例句；词卡点一下翻面；练习写完点「检查」。投影时点右下角 A± 放大。</div>
      <div class="home-grid">%s</div>
      <div class="obj-box"><strong>学习目标 Lernziele：</strong><ul>%s</ul></div>
      <div class="text-card" style="margin-top:12px">
        <h3>🧭 学习路线（建议 45 分钟走完）</h3>
        <table class="flow-table">%s</table>
      </div>
    </section>
''' % (h(m['title']), h(m['subtitle']), h(m['source']), g, objs, ''.join(rows))


# ---------------------------------------------------------------- 2 课文 T1
def sec_t1(d):
    t = d['t1']
    gm = gmap_of(t)
    paras = ''.join('<p class="cloze-p" lang="de">%s</p>' % gloss_render(p, gm) for p in t['paras'])
    struct = ''.join(
        '<div class="stp"><span class="stp-n">%s</span><span class="stp-fn" lang="de">%s</span>'
        '<div class="rm-cn">%s</div></div>' % (h(s['n']), h(s['de']), h(s['cn']))
        for s in t['structure'])
    quotes = ''.join(
        '<div class="qt"><div class="qt-h">%s <span class="src">%s</span></div>'
        '<div class="qt-de" lang="de">»%s«</div><div class="qt-zh">%s</div></div>'
        % (h(q['n']), h(q['src']), h(q['de']), h(q['zh'])) for q in t['quotes'])
    return '''    <section id="t1">
      <h2 class="section-title"><span class="num">1</span> 📖 %s <span class="src src-lg">%s · %s</span></h2>
      <p class="zh-hint">%s</p>
      <p class="zh-hint">✏️ 带虚线的德文词点一下，弹出中文释义和这词在课文里的原句。</p>
      <div class="text-card read-card">%s</div>
      <p class="zh-hint note">📌 %s</p>
      <div class="text-card">
        <h3>✉️ 求职信的九个部分（按课文顺序）</h3>
        %s
      </div>
      <div class="text-card">
        <h3>💬 信里可以直接套用的原句</h3>
        %s
      </div>
    </section>
''' % (h(t['title']), h(t['kind']), h(t['sub']), h(t['lead']), paras, h(t['provenance']), struct, quotes)


# ---------------------------------------------------------------- 3 课文 T2
def sec_t2(d):
    t = d['t2']
    gm = gmap_of(t)
    parts = []
    for turn in t['dialogue']:
        de = gloss_render(turn['de'], gm)
        who = turn['who']
        if not who:
            parts.append('<p class="cloze-p dlg-lead" lang="de">%s</p>' % de)
        elif who == 'Max fragt':
            parts.append('<div class="dlg-turn r"><span class="dlg-who">Max（反问）</span>'
                         '<p class="dlg-de" lang="de">%s</p></div>' % de)
        elif who.startswith('Max'):
            parts.append('<div class="dlg-turn r"><span class="dlg-who">Max</span>'
                         '<p class="dlg-de" lang="de">%s</p></div>' % de)
        else:
            parts.append('<div class="dlg-turn l"><span class="dlg-who">Personalchefin</span>'
                         '<p class="dlg-de" lang="de">%s</p></div>' % de)
    struct = ''.join(
        '<div class="stp"><span class="stp-n">%s</span><span class="stp-fn" lang="de">%s</span>'
        '<div class="rm-cn">%s</div></div>' % (h(s['n']), h(s['de']), h(s['cn']))
        for s in t['structure'])
    quotes = ''.join(
        '<div class="qt"><div class="qt-h">%s <span class="src">%s</span></div>'
        '<div class="qt-de" lang="de">%s</div><div class="qt-zh">%s</div></div>'
        % (h(q['n']), h(q['src']), h(q['de']), h(q['zh'])) for q in t['quotes'])
    return '''    <section id="t2">
      <h2 class="section-title"><span class="num">2</span> 👤 %s <span class="src src-lg">%s · %s</span></h2>
      <p class="zh-hint">%s</p>
      <div class="text-card read-card dlg-card">%s</div>
      <p class="zh-hint note">📌 %s</p>
      <div class="text-card">
        <h3>🤝 面试的五个阶段（对应对话里的位置）</h3>
        %s
      </div>
      <div class="text-card">
        <h3>💬 面试里值得背下来的原话</h3>
        %s
      </div>
    </section>
''' % (h(t['title']), h(t['kind']), h(t['sub']), h(t['lead']), ''.join(parts),
       h(t['provenance']), struct, quotes)


# ------------------------------------------------- 4 词汇精讲（词场表 + 词卡）
def sec_vocab(d, v9):
    v = d['vocab']
    wf = v9['wortfelder']
    groups = v['groups']

    # (a) 词场表（新层：词条带语法标注 + 中文 + 搭配 + 教材例句）
    #     标签与面板必须是 section 的直接子元素（interaction-contract：verify_interaction 按
    #     sec.children 数面板；同节第二组标签会与它互踩——故本节只有这一组标签）
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

    # (b) 课文词卡（保留：快速过词，点卡翻面；不用标签——同节只能有一组标签）
    cgroups = []
    for grp in groups:
        cards = ''.join(vocab_card(wd, grp.get('src', '')) for wd in grp['words'])
        cgroups.append('<h4 class="card-h">%s <span class="wf-cnt">%d</span>'
                       ' <span class="src">%s</span></h4><div class="vocab-grid">%s</div>'
                       % (h(grp['label']), len(grp['words']), h(grp.get('src', '')), cards))

    # (c) 全表（词场全量，含搭配——比旧全表多一列信息）
    full = ''.join('<tr class="wf-grp"><td colspan="4">%s <span class="src">%s</span></td></tr>%s'
                   % (h(g['label']), h(g['src']), wf_rows(g['rows'])) for g in wf['groups'])
    n_wf = sum(len(g['rows']) for g in wf['groups'])
    return '''    <section id="vocab">
      <h2 class="section-title"><span class="num">3</span> 📚 %s <span class="src src-lg">%s</span></h2>
      <p class="zh-hint">%s</p>
      <p class="zh-hint note">教材标注：<b>( )</b> 词尾 / 复数形式，<b>¨</b> 变音，<b>+A / +D</b> 支配格；标注降权显示，主词为黑体。</p>
      <div class="person-tabs">%s</div>%s
      <h3 class="sub-h">🃏 快速过词 · 课文核心 %d 词</h3>
      <p class="zh-hint">上面按词场讲，这里按课文顺序过一遍。点卡翻面看中文；右下 ▶ 看词条与出处。</p>
      %s
      %s
      <div id="l9Table" style="display:none"><div class="vocab-table-wrap" style="overflow-x:auto"><table class="tb wf-table">%s</table></div></div>
      <p class="zh-hint note">来源：%s</p>
    </section>
''' % (h(wf['title']), h(wf['src']), h(wf['instruction']), ''.join(tabs), ''.join(panels),
       sum(len(g['words']) for g in groups), ''.join(cgroups),
       tools_buttons(['<button class="btn ghost" onclick="toggleBox(\'l9Table\')">📋 展开全表（%d 词条 · 含搭配）</button>' % n_wf]),
       full, h(v['src']))


# ------------------------------------------------- 4b 句型库（新增）
def sec_satzmuster(v9):
    sm = v9['satzmuster']
    tabs, panels = [], []
    for i, g in enumerate(sm['groups']):
        a = ' active' if i == 0 else ''
        tabs.append('<button class="person-btn%s" onclick="switchVocabTab(\'vc2-%s\',this)">%s'
                    '<span class="wf-cnt">%d</span></button>'
                    % (a, g['id'], h(g['label']), len(g['items'])))
        panels.append('<div class="person-content%s" id="vc2-%s">'
                      '<p class="zh-hint">%s</p>'
                      '<p class="zh-hint note">📖 出处：<span class="src">%s</span></p>%s</div>'
                      % (a, g['id'], h(g['note']), h(g['src']), sm_items(g['items'])))
    wk = sm['werkstatt']
    return '''    <section id="satzmuster">
      <h2 class="section-title"><span class="num">4</span> 🧩 %s <span class="src src-lg">教材 · Redemittel（求职信） / Text 2（面试）</span></h2>
      <p class="zh-hint">%s</p>
      <div class="person-tabs">%s</div>%s
      <h3 class="sub-h">%s</h3>
      <p class="zh-hint">%s</p>
      %s
    </section>
''' % (h(sm['title']), h(sm['instruction']), ''.join(tabs), ''.join(panels),
       h(wk['title']), h(wk['note']), sb_cards(wk['items']))


# ------------------------------------------------- 8 学以致用（新增）
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
        paras.append('<p class="cloze-p" lang="de">%s</p>' % txt)

    def sw_block(items):
        out = []
        for i, x in enumerate(items):
            out.append('''      <div class="fill-item sw-item">
        <div class="fill-zh">%d. <b>%s</b></div>
        <div class="sm-de sw-pat" lang="de">%s</div>
        <div class="fill-input-line">
          <textarea class="um-ta" rows="2" placeholder="%s" lang="de"></textarea>
        </div>
        <div class="kw-tools">
          <button class="btn ghost" onclick="refShow(this)">💬 参考写法</button>
          <span class="um-tip">%s</span>
        </div>
        <div class="ref-box" style="display:none"><span class="ref-lbl">参考写法</span>
          <span lang="de">%s</span></div>
      </div>''' % (i + 1, h(x['k']), slot_html(x['pat']), esc_attr(x['ph']), h(x['ph']), h(x['ref'])))
        return ''.join(out)

    sw = v9['schreibwerkstatt']
    return '''    <section id="anwenden">
      <h2 class="section-title"><span class="num">8</span> ✍️ %s</h2>
      <p class="zh-hint">%s</p>
      <p class="zh-hint note">📖 出处：<span class="src">%s</span></p>
      <div class="clz-box" id="clz-rede">
        <div class="bank-box"><strong>Wortbank：</strong>%s</div>
        %s
        %s
      </div>
      <h3 class="sub-h">%s</h3>
      <p class="zh-hint">%s</p>
      %s
      <h3 class="sub-h">%s</h3>
      %s
    </section>
''' % (h(rc['title']), h(rc['instruction']), h(rc['src']), bank, '\n'.join(paras),
       base.tools_buttons(['<button class="btn" onclick="clzCheck(\'clz-rede\')">✓ 检查</button>',
                           '<button class="btn ghost" onclick="clzReveal(\'clz-rede\')">👁 显示答案</button>',
                           '<button class="btn ghost" onclick="clzClear(\'clz-rede\')">↺ 清空</button>',
                           '<span id="clz-rede-res" class="kw-result"></span>']),
       h(sw['title']), h(sw['instruction']), sw_block(sw['items']),
       h(sw['interview']['title']), sw_block(sw['interview']['items']))


# ---------------------------------------------------------------- 5 语法
def sec_grammar(d):
    g = d['grammar']
    tables = []
    for tb in g['tables']:
        head = ''.join('<th>%s</th>' % h(c) for c in tb['headers'])
        rows = ''.join('<tr>%s</tr>' % ''.join('<td lang="de">%s</td>' % gh(c) for c in r)
                       for r in tb['rows'])
        tables.append('<div class="text-card"><h3>%s <span class="src">%s</span></h3>'
                      '<div class="vocab-table-wrap" style="overflow-x:auto">'
                      '<table class="tb"><tr>%s</tr>%s</table></div></div>'
                      % (h(tb['title']), h(tb.get('src', '')), head, rows))
    ex = ''.join('<div class="rm-item"><div class="rm-de" lang="de">%s</div><div class="rm-cn">%s</div></div>'
                 % (h(e['de']), h(e['zh'])) for e in g['examples'])
    return '''    <section id="grammar">
      <h2 class="section-title"><span class="num">5</span> 🔤 语法 · Grammatik</h2>
      <p class="zh-hint">两张表各看一遍，再顺着下面五个例句读出声。表里<b class="gh">加粗</b>的就是这一行的语法点。</p>
      %s
      <div class="text-card">
        <h3>🗣️ 例句 · Beispiele（读一遍，注意加粗处）</h3>
        %s
      </div>
    </section>
''' % (''.join(tables), ex)


# ---------------------------------------------------------------- 6 连线
def sec_connect(d):
    out = []
    for gi, cg in enumerate(d['connectGrids']):
        idx = list(range(len(cg['pairs'])))
        random.Random(900 + gi).shuffle(idx)          # 固定种子，保证每次生成一致（可复现）
        left = ''.join('<div class="c-item de" data-pair="%d" data-gid="%d" lang="de" onclick="cClick(this)">%s</div>'
                       % (i, gi, h(p[0])) for i, p in enumerate(cg['pairs']))
        right = ''.join('<div class="c-item cn" data-pair="%d" data-gid="%d" onclick="cClick(this)">%s</div>'
                        % (j, gi, h(cg['pairs'][j][1])) for j in idx)
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
      <p class="zh-hint">%d 组各连一遍（最后一组是本课动词搭配）：点左列德语，再点右列中文。整组连完，照着左列把德文读一遍。</p>
%s
    </section>
''' % (len(d['connectGrids']), '\n'.join(out))


# ---------------------------------------------------------------- 7 介词填空
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


# ---------------------------------------------------------------- 8 快问快答
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
      <div class="qz-box" id="qz-l9">%s</div>
      %s
    </section>
''' % (h(q['title']), h(q['src']), h(q['instruction']), items,
       tools_buttons(['<button class="btn" onclick="qzCheck(\'qz-l9\')">✓ 检查</button>',
                      '<button class="btn ghost" onclick="qzClear(\'qz-l9\')">↺ 清空</button>',
                      '<span id="qz-l9-res" class="kw-result"></span>']))


# ---------------------------------------------------------------- 9 翻译卡
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


# ---------------------------------------------------------------- CSS / JS 追加
CSS_L9 = '''
  /* ===== 语法强调 / 交际用语卡 / 对话排版 ===== */
  .gh { color: #123a72; font-weight: 700; }
  .qt { border-left: 3px solid #1a73e8; padding-left: 12px; margin: 10px 0; }
  .qt-h { font-weight: 700; font-size: var(--fs-sm); color: #123a72; margin-bottom: 4px; }
  .qt-de { font-size: var(--fs-body); line-height: 1.75; }
  .qt-zh { color: #3c4450; font-size: var(--fs-sm); margin-top: 4px; }
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
  .lk-item .lk-de { font-size: var(--fs-word); line-height: 1.9; margin: 0 0 8px; }
  .lk-item { border-left: 3px solid #1a73e8; }
  .tc-front .rm-cn { font-size: var(--fs-body); line-height: 1.6; }
  .translation-grid { align-items: stretch; }
  .tc-card { min-width: 0; }
  .tc-front, .tc-back { overflow-wrap: anywhere; }
  /* 词条出处按钮：base 在 ≤900px 想抬到 34px，但被它后面那条无条件的 28px 覆盖了
     （同为单类选择器，后来的胜）→ 手机上只有 28px，手指不好点。
     这里直接无条件抬到 36px：省掉一个与基底重复断点的 @media（check_courseware 不允许重复断点）。
     按钮在卡片右下角，德语长词折成两行时末行会钻到按钮底下（实测水平重叠 25px）→
     两面底部留出按钮带（36px + 4px 间隙），文字就再也压不到按钮上。 */
  .vc-card .vc-detail, .vc-detail { width: 36px; height: 36px; font-size: 15px; opacity: .9; }
  .vc-front, .vc-back { padding-bottom: 40px; }

  /* ===== 词场表 / 句型库 / 学以致用（2026-09-26 词汇+句型强化层） ===== */
  .card-h { margin: 16px 0 8px; font-size: var(--fs-sm); color: #17427f; }
  .wf-cnt { display: inline-block; font-size: var(--fs-cap); background: #e8f0fe; color: #17427f;
            border-radius: 8px; padding: 0 8px; margin-left: 4px; vertical-align: 1px; }
  .wf-table { width: 100%; table-layout: fixed; font-size: var(--fs-sm); }
  .wf-table th { background: #eef3fa; color: #17427f; font-size: var(--fs-cap); text-align: left; }
  .wf-table th:nth-child(1), .wf-table td:nth-child(1) { width: 21%; }
  .wf-table th:nth-child(2), .wf-table td:nth-child(2) { width: 26%; }
  .wf-table th:nth-child(3), .wf-table td:nth-child(3) { width: 25%; }
  .wf-w { font-weight: 700; color: #123a72; hyphens: auto; -webkit-hyphens: auto; }
  /* 词条列窄（21%），长复合词必须断——但要按德语音节断（Bewerbungs-unterlagen），
     不能用基底的 overflow-wrap:anywhere（会断成「Bewerbungsunterlage|n」孤字） */
  .wf-table .wf-w, .wf-table .wf-coll, .wf-table .wf-ex { overflow-wrap: break-word; }
  /* 词条主体是 <span class="vc-w">，基底直接给它 overflow-wrap:anywhere（作用于子元素，
     td 上的规则靠继承盖不住）——这里直接点名它，改回 break-word + 音节连字符 */
  .wf-table .vc-w { overflow-wrap: break-word; hyphens: auto; -webkit-hyphens: auto; }
  /* 词场表的语法标注一律不断行（(Pl.) / (nur Sg) / (in +A)）——
     基底里 .vc-note 是 overflow-wrap:anywhere（词卡窄列需要），这里列宽足够，钉成不断行 */
  .wf-w .vc-note { white-space: nowrap; }
  /* 标注用灰阶令牌 #5f6672（#7d8797 在白/浅灰底只有 3.3:1，未达 WCAG AA） */
  .wf-w .vc-note { color: #5f6672; font-weight: 400; font-size: var(--fs-cap); white-space: nowrap; }
  .wf-cn { color: #1d1d1f; }
  .wf-note { color: #8a6d1f; background: #fdf7e6; border-radius: 6px; padding: 4px 8px;
             margin-top: 4px; font-size: var(--fs-cap); line-height: 1.6; }
  .wf-coll { color: #3c4450; }
  .wf-ex { color: #3c4450; }
  .wf-none { color: #5f6672; }
  .wf-grp td { background: #17427f; color: #fff; font-weight: 700; border-radius: 0; }
  /* 手机：四列表格改成逐词块（词条一行放得下 → 不再在词内断行）
     640 是本页新断点（不与模板/base 的 480/560/600/620/700/… 重复） */
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
  }
  .sub-h { margin: 16px 0 8px; font-size: var(--fs-body); color: #123a72; }
  .sm-item { background: #fff; border: 1px solid #e3e6eb; border-left: 3px solid #17427f;
             border-radius: 10px; padding: 12px 16px; margin-bottom: 12px; }
  .sm-fn { font-weight: 700; color: #17427f; font-size: var(--fs-sm); margin-bottom: 8px; }
  .sm-de { font-size: var(--fs-word); line-height: 1.85; margin: 0 0 8px; color: #111; }
  .sm-de .slot { background: #fff3cf; border-bottom: 2px solid #d9a300; padding: 0 2px;
                 border-radius: 3px; }
  .sm-zh { color: #3c4450; font-size: var(--fs-sm); }
  .sm-tip { color: #5f6672; font-size: var(--fs-sm); line-height: 1.7; margin-top: 8px; }
  .sm-cat { font-weight: 700; color: #17427f; }
  .sw-item { border-left: 3px solid #2e7d32; }
  .sw-pat { font-size: var(--fs-body); line-height: 1.8; background: #f8fafc;
            border-radius: 8px; padding: 8px 12px; margin: 8px 0; }
  #anwenden .fill-zh { font-size: var(--fs-body); }
  #anwenden .um-ta { width: 100%; font-family: inherit; font-size: var(--fs-body); padding: 8px 12px;
                     border: 1px solid #cfd6e0; border-radius: 8px; }
'''


JS_L9 = '''
/* ===== 介词填空（逐题核对）===== */
function lkCheck(el){
  const line = el.closest('.fill-input-line');
  const inp = line.querySelector('input');
  const res = line.querySelector('.fill-result');
  const val = inp.value.trim();
  const ok = !!val && norm(val) === norm(inp.dataset.ans);
  inp.classList.remove('ok', 'bad'); inp.classList.add(ok ? 'ok' : 'bad');
  if (res){ res.textContent = ok ? '✓ richtig' : (val ? '✗ 再想想' : ''); res.className = 'fill-result ' + (ok ? 'correct' : 'wrong'); }
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

    # 搭配连线并入连线节（数据结构与 connectGrids 同形）
    d['connectGrids'].append({'title': v9['kollokationen']['title'],
                              'src': v9['kollokationen']['src'],
                              'pairs': v9['kollokationen']['pairs']})

    secs = [('home', '首页'), ('t1', '📖 T1 求职信'), ('t2', '👤 T2 面试'), ('vocab', '📚 词汇精讲'),
            ('satzmuster', '🧩 句型库'),
            ('grammar', '🔤 语法'), ('connect', '🔗 连线'), ('luecken', '✍️ 填空'),
            ('anwenden', '✍️ 学以致用'), ('quiz', '✅ 快问快答'), ('translation', '🎯 翻译卡')]

    css = open(os.path.join(DIR, 'template_css.css'), encoding='utf-8').read()
    css = css.replace('</style>', base.EXTRA_CSS + t12.CSS_EXTRA + CSS_L9 + '</style>')

    nav = ('<nav><div class="top-nav"><div class="logo" style="cursor:pointer" onclick="switchSection(\'home\')">'
           '<span class="logo-icon">🎓</span><span>Lektion 9 · Bewerbung</span></div>'
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
            '<title>Lektion 9 · Fit für die Bewerbung! · 互动课件</title>\n'
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
            + t12.JS_EXTRA + '\n' + JS_L9 + '\n</script>\n</body>\n</html>\n')

    # 学生向措辞归一化：共用基底（build_l8_berufe / build_l8_t1t2）里带有教师向旧措辞，
    # 那两页不归本次改动管，故在本产物上定点替换。
    for _a, _b in [('已显示参考答案（教师用）', '已显示参考答案'),
                   ('（课堂现场用，宽屏才显示）', '（宽屏才显示）'),
                   ('（投影时不用弹窗）', '')]:
        html = html.replace(_a, _b)

    # 换行质量：模板字面量里的「 · 」分隔符禁用行首（同 h() 的做法 4）。
    # 实测 390px：章节标题右侧的「Text 1 · Bewerbungsschreiben · 安娜准备了一封求职信」
    # 会以「·」起行（wrap_audit forbiddenStart）。粘到前一个词上即可。
    html = html.replace(' · ', '\u00a0· ')

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(html)
    print('Generated: %s (%d bytes)' % (OUT, len(html)))

    # --- JS 语法自检 ---
    js = html[html.find('<script>') + 8: html.rfind('</script>')]
    r = subprocess.run(['node', '-e',
                        'try{require("vm").compileFunction(JSON.parse(process.argv[1]));console.log("JS OK")}'
                        'catch(e){console.log("JS ERROR: "+e.message.substring(0,200))}',
                        json.dumps(js)], capture_output=True, text=True, timeout=20)
    print(r.stdout.strip() or r.stderr[:300])

    # --- 结构自检 ---
    print('sections open=%d close=%d' % (html.count('<section'), html.count('</section>')))
    for sid, _ in secs:
        assert 'id="%s"' % sid in html, 'missing section ' + sid
    print('all %d section ids present | nav items = %d' % (len(secs), len(secs)))
    assert '%%' not in html, '标记未替换干净'

    # --- 数据量核对 ---
    print('vc-card = %d (词表 %d) | gl = %d (glossar %d) | c-item = %d (pairs %d)'
          % (html.count('class="vc-card"'), sum(len(g['words']) for g in d['vocab']['groups']),
             html.count('class="gl"'), len(d['t1']['glossar']) + len(d['t2']['glossar']),
             html.count('class="c-item'), sum(len(g['pairs']) for g in d['connectGrids']) * 2))
    print('lk-item = %d | qz-item = %d | tc-card = %d | stp = %d | qt = %d'
          % (html.count('lk-item'), html.count('class="qz-item"'), html.count('class="tc-card"'),
             html.count('class="stp"'), html.count('class="qt"')))
    assert html.count('class="tc-card"') == len(d['translation']['cards'])


if __name__ == '__main__':
    main()
