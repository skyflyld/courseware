#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_l7_wortschatz.py — Lektion 7 课堂互动课件生成器
输入: l7-wortschatz-spiele.json
输出: lektion7-wortschatz-spiele.html  (单文件, 自包含 CSS/JS)
原子原则: 一个脚本 → 一个产物, 不在产物上做增量修补。
"""
import json, os, sys, random, subprocess

DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(DIR, 'l7-wortschatz-spiele.json')
OUT = os.path.join(DIR, 'lektion7-wortschatz-spiele.html')

# ---------------------------------------------------------------- crossword
def build_crossword(words, seed=7):
    """贪心交叉布局: 返回 {(r,c):letter}, entries[(word,r,c,'H'/'V')]"""
    rng = random.Random(seed)
    best = None
    for attempt in range(60):
        order = sorted(words, key=lambda w: -len(w))
        if attempt:
            head = order[:3]
            rng.shuffle(head)
            order = head + order[3:]
        grid, entries, ok = {}, [], True
        for wi, w in enumerate(order):
            placed = False
            if not grid:
                for c, ch in enumerate(w):
                    grid[(0, c)] = ch
                entries.append((w, 0, 0, 'H'))
                continue
            cands = []
            for (r, c), ch in list(grid.items()):
                for i, wch in enumerate(w):
                    if wch != ch:
                        continue
                    for d in ('H', 'V'):
                        sr, sc = (r, c - i) if d == 'H' else (r - i, c)
                        # bounds check
                        if d == 'H' and (sc < -40 or sr < -40):
                            continue
                        cells = {(sr, sc + k) for k in range(len(w))} if d == 'H' else {(sr + k, sc) for k in range(len(w))}
                        # no conflict
                        bad = False
                        for k, wc in enumerate(w):
                            p = (sr, sc + k) if d == 'H' else (sr + k, sc)
                            if p in grid and grid[p] != wc:
                                bad = True
                                break
                        if bad:
                            continue
                        # crossing count + adjacency guard
                        cross = sum(1 for k, wc in enumerate(w)
                                    if ((sr, sc + k) if d == 'H' else (sr + k, sc)) in grid)
                        if cross != 1:
                            continue
                        # parallel-neighbour guard: cells before start / after end must be empty
                        before = (sr, sc - 1) if d == 'H' else (sr - 1, sc)
                        after = (sr, sc + len(w)) if d == 'H' else (sr + len(w), sc)
                        if before in grid or after in grid:
                            continue
                        # don't sit directly beside an existing parallel word
                        for k in range(len(w)):
                            p = (sr, sc + k) if d == 'H' else (sr + k, sc)
                            if p in grid:
                                continue
                            nb = [(p[0] - 1, p[1]), (p[0] + 1, p[1])] if d == 'H' else [(p[0], p[1] - 1), (p[0], p[1] + 1)]
                            for q in nb:
                                if q in grid:
                                    bad = True
                        if bad:
                            continue
                        cands.append((cross, -abs(sr) - abs(sc), sr, sc, d))
            if cands:
                cands.sort(reverse=True)
                _, _, sr, sc, d = cands[0]
                for k, wc in enumerate(w):
                    p = (sr, sc + k) if d == 'H' else (sr + k, sc)
                    grid[p] = wc
                entries.append((w, sr, sc, d))
                placed = True
            if not placed:
                ok = False
                break
        if ok:
            nwords = len(entries)
            span = (max(r for r, _ in grid) - min(r for r, _ in grid) + 1) * (max(c for _, c in grid) - min(c for _, c in grid) + 1)
            if best is None or nwords > len(best[1]) or (nwords == len(best[1]) and span < best[3]):
                best = (grid, entries, ok, span)
            if nwords == len(words):
                break
    return best

def number_grid(grid, entries):
    """给每个起始格编号（阅读顺序），返回 (num_map, numbered_entries)"""
    starts = {}
    for w, r, c, d in entries:
        starts.setdefault((r, c), []).append((w, r, c, d))
    num_map, out = {}, []
    n = 0
    for (r, c) in sorted(starts.keys()):
        n += 1
        num_map[(r, c)] = n
        for w, rr, cc, d in starts[(r, c)]:
            out.append((w, rr, cc, d, n))
    return num_map, out

# ---------------------------------------------------------------- helpers
def h(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))

def esc_attr(s):
    return h(s).replace('"', '&quot;')

# ---------------------------------------------------------------- sections
def sec_home(d):
    m = d['meta']
    o = ''.join('<li>%s</li>' % h(x) for x in m['objectives'])
    rows = ''.join('<tr><td class="fl-t">%s</td><td>%s</td><td>%s</td></tr>' % (h(a), h(b), h(c)) for a, b, c in m['flow'])
    cards = [
        ('vocab', '📇 词汇卡片', '%d 个核心词 · 分组翻转卡 + 例句' % sum(len(g['words']) for g in d['vocabGroups'])),
        ('blitz', '⚡ Blitzrunde 抢答', '中文提示 → 德语抢答 · 带计时器'),
        ('connect', '🔗 连线配对', '%d 组词网 · 点击左右配对' % len(d['connectGrids'])),
        ('kreuzwort', '🧩 Kreuzworträtsel', '教材 Ü2 · 15 个提示句填格'),
        ('satz', '✍️ Satzergänzung', '教材 Ü2 a–o 逐句核对'),
        ('hochschule', '🏛️ Hochschullandschaft', '教材 Ü1 · 词库完形填空'),
        ('mindmap', '🗺️ Mindmap', '教材 Ü3 · 5 类词网归类'),
        ('satzbau', '🧱 Satzbau 句型工坊', '6 个课文核心句型 · 组句检验'),
        ('uebersetzen', '🎯 翻译擂台', '教材 Ü9 · 中译德逐句核对'),
        ('spiele', '🏆 课堂游戏 & 计分板', '6 个课堂活动 + 双队计分'),
    ]
    g = ''.join('<div class="text-card" onclick="switchSection(\'%s\')" style="cursor:pointer"><h3>%s</h3><p>%s</p></div>' % (i, t, s) for i, t, s in cards)
    return '''    <section id="home" class="active">
      <div class="hero">
        <h1>Lektion 7 · Studium, Schule &amp; Wortschatz</h1>
        <p class="sub">%s</p>
        <p class="meta">%s</p>
      </div>
      <div class="home-grid">%s</div>
      <div class="obj-box"><strong>学习目标：</strong><ul>%s</ul></div>
      <div class="text-card" style="margin-top:12px">
        <h3>⏱️ 45 分钟课堂流程（建议）</h3>
        <table class="flow-table">%s</table>
      </div>
    </section>
''' % (h(d['meta']['subtitle']), h(d['meta']['source']), g, o, rows)

def sec_vocab(d):
    tabs, panels = [], []
    for i, grp in enumerate(d['vocabGroups']):
        a = ' active' if i == 0 else ''
        tabs.append('<button class="person-btn%s" onclick="switchVocabTab(\'%s\')">%s</button>' % (a, grp['id'], h(grp['label'])))
        cards = []
        for wd in grp['words']:
            cards.append(
                '<div class="vc-card" onclick="flipCard(this)"><div class="vc-inner">'
                '<div class="vc-front">%s</div><div class="vc-back">%s</div></div>'
                '<button class="vc-detail" title="例句" onclick="event.stopPropagation();showVocab(\'%s\',\'%s\',\'%s\')">▶</button></div>'
                % (h(wd['w']), h(wd['cn']), esc_attr(wd['w']), esc_attr(wd['cn']), esc_attr(wd['ex'])))
        panels.append('<div class="person-content%s" id="vc-%s"><div class="vocab-grid">%s</div></div>' % (a, grp['id'], ''.join(cards)))
    return '''    <section id="vocab">
      <h2 class="section-title"><span class="num">1</span> 词汇卡片 · Wortschatzkarten</h2>
      <p class="zh-hint">点击卡片翻转看中文，点右下 ▶ 看例句。读名词请带冠词，说动词请带支配格。</p>
      <div class="person-tabs">%s</div>%s
    </section>
''' % (''.join(tabs), ''.join(panels))

def sec_blitz(d):
    cards = ''.join(
        '<div class="blitz-card" onclick="this.classList.toggle(\'open\')">'
        '<div class="bz-cn">%s</div><div class="bz-hint">%s</div>'
        '<div class="bz-de">%s</div></div>' % (h(b['cn']), h(b['hint']), h(b['de']))
        for b in d['blitz'])
    return '''    <section id="blitz">
      <h2 class="section-title"><span class="num">2</span> ⚡ Blitzrunde · 抢答热身</h2>
      <p class="zh-hint">老师念中文，学生抢答德语，先说出正确形式（含冠词/支配格）的小组得 1 分。点击卡片揭示答案。</p>
      <div class="timer-bar">
        <span class="timer" id="blitzTimer">30</span>
        <button class="btn" onclick="startTimer('blitzTimer',30)">▶ 计时开始</button>
        <button class="btn ghost" onclick="stopTimer('blitzTimer')">■ 停止</button>
        <button class="btn ghost" onclick="resetTimer('blitzTimer',30)">↺ 重置</button>
      </div>
      <div class="blitz-grid">%s</div>
    </section>
''' % cards

def sec_connect(d):
    out = []
    for gi, cg in enumerate(d['connectGrids']):
        rng = random.Random(100 + gi)
        idx = list(range(len(cg['pairs'])))
        rng.shuffle(idx)
        left = ''.join('<div class="c-item de" data-pair="%d" data-gid="%d" onclick="cClick(this)">%s</div>' % (i, gi, h(p[0])) for i, p in enumerate(cg['pairs']))
        right = ''.join('<div class="c-item cn" data-pair="%d" data-gid="%d" onclick="cClick(this)">%s</div>' % (j, gi, h(cg['pairs'][j][1])) for j in idx)
        out.append('''      <div class="connect-game">
        <h3>%s</h3><p class="zh-hint">点左列德语，再点右列中文</p>
        <div class="connect-field">
          <div class="connect-col">%s</div><div class="connect-col">%s</div>
        </div>
        <div class="connect-score">匹配：<span id="cg-cnt-%d">0</span> / %d</div>
      </div>''' % (h(cg['title']), left, right, gi, len(cg['pairs'])))
    return '''    <section id="connect">
      <h2 class="section-title"><span class="num">3</span> 🔗 连线配对 · Vernetzen</h2>
      <p class="zh-hint">配对成功变绿；点错会有红闪，可重试。四组全部完成后可让学生朗读整组词。</p>
%s
    </section>
''' % '\n'.join(out)

def sec_kreuzwort(d, cw):
    grid, entries, ok, _ = cw
    num_map, numbered = number_grid(grid, entries)
    rows = [r for r, _ in grid]
    cols = [c for _, c in grid]
    r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
    body = []
    for r in range(r0, r1 + 1):
        tds = []
        for c in range(c0, c1 + 1):
            if (r, c) in grid:
                n = num_map.get((r, c), '')
                tds.append('<td class="kw-cell"><span class="kw-num">%s</span><input maxlength="1" data-r="%d" data-c="%d" data-ans="%s" oninput="kwInput(this)" onclick="kwSelect(this)"></td>' % (n, r, c, esc_attr(grid[(r, c)])))
            else:
                tds.append('<td class="kw-black"></td>')
        body.append('<tr>%s</tr>' % ''.join(tds))
    # clue lists
    ans2clue = {c['answer'].upper(): c for c in d['kreuzwort']['clues']}
    neg_clues, pos_clues = [], []
    for w, r, c, dr, n in sorted(numbered, key=lambda x: x[4]):
        cl = ans2clue.get(w, {'n': '', 'clue': w, 'zh': ''})
        item = ('<li data-word="%s"><b>%d</b> <span class="kw-tag">%s</span> %s <span class="kw-zh">%s</span>'
                '<button class="btn tiny" onclick="revealWord(this,\'%s\')">揭示</button></li>'
                % (esc_attr(w), n, h(cl.get('n', '')), h(cl['clue']), h(cl.get('zh', '')), esc_attr(w)))
        (pos_clues if dr == 'H' else neg_clues).append(item)
    bank = ''.join('<span class="bank-chip" onclick="bankClick(this)">%s</span>' % h(w) for w in d['kreuzwort']['wordbank'])
    return '''    <section id="kreuzwort">
      <h2 class="section-title"><span class="num">4</span> 🧩 %s</h2>
      <p class="zh-hint">%s</p>
      <div class="kw-tools">
        <button class="btn" onclick="kwCheck()">✓ 检查全部</button>
        <button class="btn ghost" onclick="kwReveal()">👁 显示答案</button>
        <button class="btn ghost" onclick="kwClear()">↺ 清空</button>
        <button class="btn ghost" onclick="kwZoom(-0.1)">🔍− 缩小</button>
        <button class="btn ghost" onclick="kwZoom(0.1)">🔍+ 放大</button>
        <button class="btn ghost" onclick="kwZoomReset()">100%%</button>
        <span id="kwResult" class="kw-result"></span>
      </div>
      <div class="kw-wrap">
        <div class="kw-left">
          <div class="kw-table-wrap"><table class="kw-table">%s</table></div>
          <div class="bank-box"><strong>词语库 Wortbank：</strong>%s</div>
        </div>
        <div class="kw-clues">
          <h4>Waagerecht →</h4><ol class="kw-list">%s</ol>
          <h4>Senkrecht ↓</h4><ol class="kw-list">%s</ol>
        </div>
      </div>
      <p class="zh-hint note">★ 说明：a–o 为教材 Ü2 原提示句；个别句子教材可能接受多个答案（如 b 也可为 „Jahr“），本格使用上表词语库中的写法，以教师用书为准。手机/平板可左右滑动查看完整网格。</p>
    </section>
''' % (h(d['kreuzwort']['title']), h(d['kreuzwort']['instruction']), ''.join(body),
       bank, ''.join(pos_clues), ''.join(neg_clues))

def sec_satz(d):
    items = []
    for i, c in enumerate(d['kreuzwort']['clues']):
        alts = c.get('alt', [])
        items.append('''      <div class="fill-item">
        <div class="fill-sentence"><b>%s)</b> %s</div>
        <div class="fill-zh">%s</div>
        <div class="fill-input-line">
          <input type="text" class="fill-input" id="sf-%d" placeholder="Antwort eingeben…" data-ans="%s" data-alt="%s" onkeydown="if(event.key==='Enter')checkSatz(%d)">
          <button class="fill-check" onclick="checkSatz(%d)">✓</button>
          <span class="fill-result" id="sf-res-%d"></span>
          <button class="btn tiny ghost" onclick="showOneSatz(%d)">答案</button>
        </div>
      </div>''' % (h(c['n']), h(c['clue']), h(c['zh']), i, esc_attr(c['answer']), esc_attr('|'.join(alts)), i, i, i, i))
    return '''    <section id="satz">
      <h2 class="section-title"><span class="num">5</span> ✍️ Satzergänzung · 句子填空（教材 Ü2 a–o）</h2>
      <p class="zh-hint">输入答案后按回车或点 ✓。大小写、变音符号（ä = ae）不敏感；同义答案也算对。</p>
      <div class="kw-tools">
        <button class="btn ghost" onclick="showAllSatz()">👁 显示全部答案</button>
        <button class="btn ghost" onclick="clearAllSatz()">↺ 清空</button>
        <span id="satzScore" class="kw-result"></span>
      </div>
%s
    </section>
''' % '\n'.join(items)

def sec_hochschule(d):
    hs = d['hochschule']
    paras = []
    for p in hs['text']:
        t = h(p)
        for i in range(len(hs['answers']), 0, -1):
            t = t.replace('[[%d]]' % i, '<span class="cloze-blank" data-idx="%d" data-ans="%s" onclick="clozeClick(this)">?</span>' % (i - 1, esc_attr(hs['answers'][i - 1])))
        paras.append('<p class="cloze-p">%s</p>' % t)
    bank = ''.join('<span class="bank-chip" onclick="bankFill(this)">%s</span>' % h(w) for w in hs['bank'])
    logos = ' '.join('<span class="logo-chip">🏛️ %s</span>' % h(l) for l in hs['logos'])
    return '''    <section id="hochschule">
      <h2 class="section-title"><span class="num">6</span> 🏛️ %s</h2>
      <p class="zh-hint">%s</p>
      <div class="bank-box"><strong>Logos：</strong>%s</div>
      %s
      <div class="bank-box"><strong>词语库 Wortbank：</strong>%s</div>
      <div class="kw-tools">
        <button class="btn" onclick="clozeCheck()">✓ 检查</button>
        <button class="btn ghost" onclick="clozeClear()">↺ 清空</button>
        <span id="clozeResult" class="kw-result"></span>
      </div>
      <div class="highlight-box">💡 %s</div>
    </section>
''' % (h(hs['title']), h(hs['instruction']), logos, '\n'.join(paras), bank, h(hs['note']))

def sec_mindmap(d):
    mm = d['mindmap']
    pool = ''.join('<span class="mm-chip" data-c="%s" onclick="mmSelect(this)">%s</span>' % (w['c'], h(w['w'])) for w in mm['words'])
    boxes = ''.join(
        '<div class="mm-box" data-cat="%s" onclick="mmDrop(this)"><div class="mm-head">%s %s</div><div class="mm-items"></div></div>'
        % (c['id'], c['icon'], h(c['label'])) for c in mm['cats'])
    return '''    <section id="mindmap">
      <h2 class="section-title"><span class="num">7</span> 🗺️ %s</h2>
      <p class="zh-hint">%s</p>
      <div class="mm-pool" id="mmPool">%s</div>
      <div class="mm-board">%s</div>
      <div class="kw-tools">
        <button class="btn" onclick="mmCheck()">✓ 检查归类</button>
        <button class="btn ghost" onclick="mmReset()">↺ 重新开始</button>
        <span id="mmResult" class="kw-result"></span>
      </div>
    </section>
''' % (h(mm['title']), h(mm['instruction']), pool, boxes)

def sec_satzbau(d):
    out = []
    for i, s in enumerate(d['satzbau']):
        rng = random.Random(200 + i)
        order = list(range(len(s['chunks'])))
        rng.shuffle(order)
        while order == sorted(order) and len(order) > 1:
            rng.shuffle(order)
        chips = ''.join('<span class="sb-chunk" data-i="%d" onclick="sbPick(this,%d)">%s</span>' % (k, i, h(s['chunks'][k])) for k in order)
        out.append('''      <div class="sb-card">
        <div class="sb-zh">%d. %s</div>
        <div class="sb-hint">句型：%s</div>
        <div class="sb-pool" id="sb-pool-%d">%s</div>
        <div class="sb-line" id="sb-line-%d"></div>
        <div class="sb-actions">
          <button class="btn" onclick="sbCheck(%d)">✓ 检查语序</button>
          <button class="btn ghost" onclick="sbUndo(%d)">↶ 撤回</button>
          <button class="btn ghost" onclick="sbReset(%d)">↺ 重排</button>
          <button class="btn ghost" onclick="sbShow(%d)">👁 答案</button>
          <span class="fill-result" id="sb-res-%d"></span>
        </div>
      </div>''' % (i + 1, h(s['zh']), h(s['pattern']), i, chips, i, i, i, i, i, i))
    return '''    <section id="satzbau">
      <h2 class="section-title"><span class="num">8</span> 🧱 Satzbau · 句型工坊</h2>
      <p class="zh-hint">点词块按正确语序排成德语句子；点已排的词块可撤回。语序错要说出「错在哪」。</p>
%s
    </section>
''' % '\n'.join(out)

def sec_uebersetzen(d):
    u = d['uebersetzen']
    cards = []
    for i, s in enumerate(u['sentences']):
        cards.append('''        <div class="tc-card" onclick="flipTrans(this)">
          <div class="tc-inner">
            <div class="tc-front"><span class="tc-num">%d</span><div class="tc-zh">%s</div><div class="tc-tip">💡 %s</div></div>
            <div class="tc-back"><span class="tc-num">%d</span><div class="tc-de">%s</div></div>
          </div>
        </div>''' % (i + 1, h(s['zh']), h(s['tip']), i + 1, h(s['de'])))
    return '''    <section id="uebersetzen">
      <h2 class="section-title"><span class="num">9</span> 🎯 %s</h2>
      <p class="zh-hint">先自己写，再点卡片核对参考译文。译法不唯一，句型正确、意义完整即算对。</p>
      <div class="translation-grid">%s</div>
      <div class="kw-tools"><button class="btn" onclick="toggleBox('fullDe')">👁 整段参考译文</button></div>
      <div class="full-de" id="fullDe" style="display:none"><p class="de-full">%s</p></div>
      <div class="highlight-box">💡 整段中文原文：<br>%s</div>
    </section>
''' % (h(u['title']), '\n'.join(cards), h(u['deFull']), h(u['zhFull']))

def sec_spiele(d):
    games = ''.join('<div class="game-card"><div class="game-name">%s <span class="game-time">%s</span></div><p>%s</p></div>'
                    % (h(g['name']), h(g['time']), h(g['desc'])) for g in d['klassenspiele'])
    return '''    <section id="spiele">
      <h2 class="section-title"><span class="num">10</span> 🏆 课堂游戏 &amp; 计分板</h2>
      <div class="scoreboard">
        <div class="team"><div class="team-name">Team A</div><div class="team-score" id="scoreA">0</div>
          <div class="team-btns"><button class="btn" onclick="addScore('A',1)">+1</button><button class="btn ghost" onclick="addScore('A',-1)">−1</button></div></div>
        <div class="team"><div class="team-name">Team B</div><div class="team-score" id="scoreB">0</div>
          <div class="team-btns"><button class="btn" onclick="addScore('B',1)">+1</button><button class="btn ghost" onclick="addScore('B',-1)">−1</button></div></div>
        <div class="team reset-team"><button class="btn ghost" onclick="resetScore()">↺ 比分归零</button>
          <div class="timer" id="classTimer" style="margin-top:8px">30</div>
          <button class="btn tiny" onclick="startTimer('classTimer',30)">▶ 30s</button></div>
      </div>
      <div class="games-grid">%s</div>
    </section>
''' % games

# ---------------------------------------------------------------- assemble
EXTRA_CSS = '''
  /* 投影与自适应微调（11 个导航项需要更宽的行、更大的正文衬度） */
  .top-nav { max-width: 1440px; }
  .nav-links button { padding: 8px 11px; }
  .flow-table { font-size: 15px; }
  .kw-list { font-size: 14px; }
  .kw-zh, .tc-tip, .zh-hint { font-size: 13.5px; }
  .zh-hint.note { font-size: 12.5px; color: #aaa; }
  .kw-left { display: flex; flex-direction: column; gap: 12px; min-width: 0; }
  .kw-wrap > * { min-width: 0; }
  .kw-table-wrap { max-width: 100%; overflow-x: auto; }
  .kw-left .bank-box { margin: 0; }
  .kw-left .bank-chip { font-size: 13.5px; }
  /* 窄屏：缩放填字网格，保证全部格子可见（zoom 参与布局，不会留白） */
  @media (max-width: 820px) {
    .kw-table { zoom: 0.82; }
    .kw-cell input { width: 26px; height: 26px; font-size: 13px; }
    .kw-black { width: 26px; height: 26px; }
    .connect-field { gap: 12px; }
  }
  @media (max-width: 500px) {
    .kw-table { zoom: 0.6; }
    .kw-cell input { width: 24px; height: 24px; font-size: 12px; }
    .kw-black { width: 24px; height: 24px; }
    .blitz-grid { grid-template-columns: 1fr; }
  }
  .zh-hint { font-size: 14px; color: #888; margin: 0 0 12px; }
  .flow-table { width: 100%; border-collapse: collapse; font-size: 14px; margin-top: 8px; }
  .flow-table td { border-bottom: 1px solid #eee; padding: 7px 6px; vertical-align: top; }
  .flow-table .fl-t { color: #1a73e8; font-weight: 600; white-space: nowrap; width: 62px; }
  .btn { padding: 7px 16px; border-radius: 8px; border: none; background: #1a73e8; color: #fff;
         font-size: 14px; cursor: pointer; transition: all .15s; }
  .btn:hover { filter: brightness(1.08); }
  .btn.ghost { background: #fff; color: #1a73e8; border: 1px solid #c9d9f5; }
  .btn.tiny { padding: 2px 9px; font-size: 12px; margin-left: 6px; }
  /* Blitz */
  .blitz-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 10px; }
  .blitz-card { background: #fff; border-radius: 10px; padding: 14px; cursor: pointer;
                box-shadow: 0 1px 3px rgba(0,0,0,.06); border-left: 4px solid #fbbc04; transition: all .2s; }
  .blitz-card .bz-cn { font-size: clamp(14px, 2vw, 19px); font-weight: 600; }
  .blitz-card .bz-hint { font-size: 12px; color: #aaa; margin-top: 2px; }
  .blitz-card .bz-de { display: none; margin-top: 8px; padding-top: 8px; border-top: 1px dashed #ddd;
                       color: #1a73e8; font-weight: 700; font-size: clamp(14px, 2vw, 19px); }
  .blitz-card.open { border-left-color: #27ae60; background: #f6fdf7; }
  .blitz-card.open .bz-de { display: block; }
  .timer-bar { display: flex; align-items: center; gap: 10px; margin: 0 0 14px; flex-wrap: wrap; }
  .timer { font-size: 34px; font-weight: 700; color: #1a73e8; min-width: 68px; text-align: center;
           background: #eef4ff; border-radius: 10px; padding: 2px 10px; font-variant-numeric: tabular-nums; }
  .timer.warn { color: #e74c3c; background: #fdecea; }
  /* Crossword */
  .kw-tools { display: flex; align-items: center; gap: 10px; margin: 0 0 12px; flex-wrap: wrap; }
  .kw-result { font-size: 14px; font-weight: 600; color: #1a73e8; }
  .kw-wrap { display: grid; grid-template-columns: minmax(280px, 1fr) minmax(280px, 1fr); gap: 18px; align-items: start; }
  .kw-table-wrap { overflow-x: auto; }
  .kw-table { border-collapse: collapse; margin: 0 auto; }
  .kw-table td { padding: 0; }
  .kw-cell { position: relative; }
  .kw-cell input { width: 30px; height: 30px; border: 1px solid #c9c9cf; text-align: center;
                   font-size: 15px; font-weight: 600; text-transform: uppercase; padding: 0;
                   background: #fff; outline: none; }
  .kw-cell input:focus { background: #e8f0fe; border-color: #1a73e8; }
  .kw-cell input.ok { background: #e8f8e8; border-color: #27ae60; }
  .kw-cell input.bad { background: #fdecea; border-color: #e74c3c; }
  .kw-num { position: absolute; top: -1px; left: 1px; font-size: 8px; color: #999; z-index: 2; }
  .kw-black { background: #ececf0; width: 30px; height: 30px; }
  .kw-clues h4 { margin: 10px 0 4px; font-size: 14px; color: #1a73e8; }
  .kw-list { list-style: none; margin: 0 0 10px; padding: 0; font-size: 13.5px; line-height: 1.55; }
  .kw-list li { padding: 4px 0; border-bottom: 1px dotted #eee; }
  .kw-tag { display: inline-block; min-width: 16px; color: #999; font-size: 12px; }
  .kw-zh { color: #999; font-size: 12px; display: block; }
  .bank-box { background: #f8f9fa; border-radius: 8px; padding: 10px 14px; font-size: 14px; margin: 12px 0; }
  .bank-chip { display: inline-block; background: #fff; border: 1px solid #c9d9f5; color: #1a73e8;
               border-radius: 14px; padding: 3px 12px; margin: 3px 4px; cursor: pointer; font-size: 14px; }
  .bank-chip:hover { background: #e8f0fe; }
  .bank-chip.used { opacity: .35; }
  .logo-chip { display: inline-block; background: #fff; border: 1px dashed #ddd; border-radius: 8px;
               padding: 3px 10px; margin: 3px 4px; font-size: 13px; color: #666; }
  /* Fill-in */
  .fill-item { background: #fff; border-radius: 10px; padding: 12px 16px; margin-bottom: 10px;
               box-shadow: 0 1px 3px rgba(0,0,0,.05); }
  .fill-sentence { font-size: clamp(14px, 2vw, 19px); line-height: 1.55; }
  .fill-zh { font-size: 13px; color: #999; margin: 2px 0 6px; }
  .fill-input { flex: 1; min-width: 160px; padding: 7px 10px; border: 1px solid #ddd; border-radius: 6px;
                font-size: 15px; outline: none; }
  .fill-input:focus { border-color: #1a73e8; }
  .fill-input.ok { background: #e8f8e8; border-color: #27ae60; }
  .fill-input.bad { background: #fdecea; border-color: #e74c3c; }
  .fill-result.correct { color: #27ae60; }
  .fill-result.wrong { color: #e74c3c; }
  /* Cloze */
  .cloze-p { font-size: clamp(14px, 2vw, 19px); line-height: 1.9; margin: 0 0 8px; }
  .cloze-blank { display: inline-block; min-width: 96px; text-align: center; border-bottom: 2px solid #1a73e8;
                 color: #1a73e8; font-weight: 600; cursor: pointer; padding: 0 6px; }
  .cloze-blank.filled { color: #1d1d1f; border-bottom-color: #27ae60; }
  .cloze-blank.ok { background: #e8f8e8; }
  .cloze-blank.bad { background: #fdecea; border-bottom-color: #e74c3c; color: #c0392b; }
  .cloze-blank.sel { background: #e8f0fe; }
  /* Mindmap */
  .mm-pool { display: flex; flex-wrap: wrap; gap: 8px; background: #fff; border-radius: 10px;
             padding: 14px; box-shadow: 0 1px 3px rgba(0,0,0,.06); margin-bottom: 14px; }
  .mm-chip { background: #fff; border: 1px solid #ddd; border-radius: 16px; padding: 5px 14px;
             font-size: 15px; cursor: pointer; transition: all .15s; }
  .mm-chip:hover { border-color: #1a73e8; }
  .mm-chip.sel { background: #e8f0fe; border-color: #1a73e8; }
  .mm-chip.ok { background: #e8f8e8; border-color: #27ae60; }
  .mm-chip.bad { background: #fdecea; border-color: #e74c3c; }
  .mm-board { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 12px; }
  .mm-box { background: #fff; border: 2px dashed #dcdce2; border-radius: 12px; padding: 10px; min-height: 96px; }
  .mm-head { font-weight: 600; font-size: 14px; color: #1a73e8; margin-bottom: 6px; }
  .mm-items { display: flex; flex-wrap: wrap; gap: 6px; min-height: 34px; }
  .mm-items .mm-chip { font-size: 14px; padding: 3px 10px; }
  /* Satzbau */
  .sb-card { background: #fff; border-radius: 10px; padding: 16px; margin-bottom: 12px;
             box-shadow: 0 1px 3px rgba(0,0,0,.05); }
  .sb-zh { font-size: clamp(14px, 2vw, 19px); font-weight: 500; }
  .sb-hint { font-size: 13px; color: #888; margin: 2px 0 10px; }
  .sb-pool { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 10px; }
  .sb-chunk { background: #eef4ff; border: 1px solid #c9d9f5; color: #17427f; border-radius: 8px;
              padding: 6px 12px; font-size: clamp(13px, 1.9vw, 18px); cursor: pointer; }
  .sb-chunk:hover { background: #e0ecff; }
  .sb-line { min-height: 46px; border-bottom: 2px solid #e0e0e6; padding: 6px 4px;
             display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
  .sb-line .sb-chunk { background: #fff; border-color: #27ae60; color: #1e7e34; }
  .sb-line .sb-chunk:hover { background: #fdecea; border-color: #e74c3c; }
  .sb-actions { display: flex; align-items: center; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
  .sb-line.ok .sb-chunk { background: #e8f8e8; }
  .sb-line.bad .sb-chunk { background: #fdecea; border-color: #e74c3c; color: #c0392b; }
  .tc-tip { font-size: 12px; color: #888; margin-top: 6px; }
  .full-de { background: #f6fbf7; border-left: 3px solid #27ae60; border-radius: 0 8px 8px 0;
             padding: 12px 16px; margin: 10px 0; }
  .de-full { font-size: clamp(14px, 2vw, 19px); line-height: 1.8; margin: 0; }
  /* Scoreboard & games */
  .scoreboard { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
  .team { flex: 1; min-width: 150px; background: #fff; border-radius: 12px; padding: 14px;
          text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,.06); }
  .team-name { font-size: 14px; color: #888; }
  .team-score { font-size: 46px; font-weight: 700; color: #1a73e8; line-height: 1.1; }
  .team-btns { display: flex; gap: 8px; justify-content: center; }
  .games-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 10px; }
  .game-card { background: #fff; border-radius: 10px; padding: 14px; box-shadow: 0 1px 3px rgba(0,0,0,.06); }
  .game-name { font-weight: 600; font-size: 15px; margin-bottom: 4px; }
  .game-time { font-size: 12px; color: #1a73e8; background: #eef4ff; border-radius: 10px; padding: 1px 8px; }
  .game-card p { font-size: 13.5px; color: #666; margin: 4px 0 0; line-height: 1.6; }
  @media (max-width: 760px) {
    .kw-wrap { grid-template-columns: 1fr; }
    .mm-board { grid-template-columns: 1fr; }
  }
'''

EXTRA_JS = '''
let selLeft = null, selRight = null;
function flipCard(el){ el.classList.toggle('flipped'); }
function switchVocabTab(id){
  document.querySelectorAll('.person-content').forEach(function(p){ p.classList.remove('active'); });
  document.getElementById('vc-'+id).classList.add('active');
  document.querySelectorAll('#vocab .person-btn').forEach(function(b){ b.classList.remove('active'); });
  event.currentTarget.classList.add('active');
}
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
/* ---- timer ---- */
const timers = {};
function startTimer(id, sec){
  stopTimer(id);
  let t = sec;
  const el = document.getElementById(id);
  el.textContent = t; el.classList.remove('warn');
  timers[id] = setInterval(function(){
    t--; el.textContent = t;
    if (t <= 5) el.classList.add('warn');
    if (t <= 0){ stopTimer(id); el.textContent = '0'; }
  }, 1000);
}
function stopTimer(id){ if (timers[id]) { clearInterval(timers[id]); delete timers[id]; } }
function resetTimer(id, sec){ stopTimer(id); const el = document.getElementById(id); el.textContent = sec; el.classList.remove('warn'); }
/* ---- connect ---- */
function cClick(el){
  if (el.classList.contains('matched')) return;
  const side = el.classList.contains('de') ? 'L' : 'R';
  const gid = el.dataset.gid;
  if (side === 'L'){
    if (selLeft){ selLeft.classList.remove('selected'); }
    selLeft = el; el.classList.add('selected');
  } else {
    if (selRight){ selRight.classList.remove('selected'); }
    selRight = el; el.classList.add('selected');
  }
  if (selLeft && selRight && selLeft.dataset.gid === selRight.dataset.gid){
    if (selLeft.dataset.pair === selRight.dataset.pair){
      selLeft.classList.remove('selected'); selRight.classList.remove('selected');
      selLeft.classList.add('matched'); selRight.classList.add('matched');
      const cnt = document.getElementById('cg-cnt-'+gid);
      cnt.textContent = parseInt(cnt.textContent, 10) + 1;
      selLeft = null; selRight = null;
    } else {
      const a = selLeft, b = selRight;
      a.classList.add('badflash'); b.classList.add('badflash');
      setTimeout(function(){ a.classList.remove('badflash','selected'); b.classList.remove('badflash','selected'); }, 420);
      selLeft = null; selRight = null;
    }
  }
}
/* ---- crossword ---- */
function kwNormalize(s){
  return (s || '').toUpperCase().trim()
    .replace(/Ä/g,'AE').replace(/Ö/g,'OE').replace(/Ü/g,'UE').replace(/ß/g,'SS');
}
function kwCells(){ return Array.prototype.slice.call(document.querySelectorAll('.kw-cell input')); }
function kwInput(inp){
  inp.value = inp.value.toUpperCase();
  inp.classList.remove('ok','bad');
  if (inp.value){
    const r = +inp.dataset.r, c = +inp.dataset.c;
    const next = kwCells().filter(function(x){
      const rr = +x.dataset.r, cc = +x.dataset.c;
      return (rr === r && cc === c + 1) || (rr === r + 1 && cc === c);
    })[0];
    if (next) next.focus();
  }
}
function kwSelect(){}
let kwZoomVal = null;
function kwZoom(delta){
  const t = document.querySelector('.kw-table');
  const cur = kwZoomVal === null ? (parseFloat(getComputedStyle(t).zoom) || 1) : kwZoomVal;
  kwZoomVal = Math.min(1.3, Math.max(0.35, Math.round((cur + delta) * 100) / 100));
  t.style.zoom = kwZoomVal;
}
function kwZoomReset(){ kwZoomVal = null; document.querySelector('.kw-table').style.zoom = ''; }
function kwCheck(){
  const entries = DOC.kwEntries, cellMap = {};
  kwCells().forEach(function(i){ cellMap[i.dataset.r + ',' + i.dataset.c] = i; });
  let solved = 0;
  entries.forEach(function(e){
    let all = true;
    const cells = [];
    for (let k = 0; k < e.word.length; k++){
      const r = e.dir === 'H' ? e.r : e.r + k;
      const c = e.dir === 'H' ? e.c + k : e.c;
      const inp = cellMap[r + ',' + c];
      cells.push(inp);
      if (!inp || kwNormalize(inp.value) !== kwNormalize(e.word[k])) all = false;
    }
    if (all){ solved++; cells.forEach(function(i){ i.classList.remove('bad'); i.classList.add('ok'); }); }
    else cells.forEach(function(i){ if (!i) return; i.classList.remove('ok'); if (i.value) i.classList.add('bad'); });
  });
  document.getElementById('kwResult').textContent = '已填对 ' + solved + ' / ' + entries.length + ' 个词';
}
function kwReveal(){
  kwCells().forEach(function(i){ i.value = i.dataset.ans; i.classList.remove('bad'); i.classList.add('ok'); });
  document.getElementById('kwResult').textContent = '已显示参考答案（教师用）';
}
function kwClear(){
  kwCells().forEach(function(i){ i.value = ''; i.classList.remove('ok','bad'); });
  document.getElementById('kwResult').textContent = '';
}
function revealWord(btn, word){
  const cellMap = {};
  kwCells().forEach(function(i){ cellMap[i.dataset.r + ',' + i.dataset.c] = i; });
  DOC.kwEntries.filter(function(e){ return e.word === word; }).forEach(function(e){
    for (let k = 0; k < e.word.length; k++){
      const r = e.dir === 'H' ? e.r : e.r + k;
      const c = e.dir === 'H' ? e.c + k : e.c;
      const inp = cellMap[r + ',' + c];
      if (inp){ inp.value = e.word[k]; inp.classList.add('ok'); }
    }
  });
}
/* ---- Satzergänzung ---- */
function showVocabPanel(){}
function checkSatz(i){
  const inp = document.getElementById('sf-' + i);
  const res = document.getElementById('sf-res-' + i);
  const ok = kwNormalize(inp.value) === kwNormalize(inp.dataset.ans) ||
             inp.dataset.alt.split('|').filter(Boolean).some(function(a){ return kwNormalize(a) === kwNormalize(inp.value); });
  inp.classList.remove('ok','bad'); inp.classList.add(ok ? 'ok' : 'bad');
  res.textContent = ok ? '✓ richtig' : '✗ 再想想（或点「答案」）';
  res.className = 'fill-result ' + (ok ? 'correct' : 'wrong');
}
function showOneSatz(i){
  const inp = document.getElementById('sf-' + i);
  inp.value = inp.dataset.ans; inp.classList.remove('bad'); inp.classList.add('ok');
}
function showAllSatz(){ DOC.satz.forEach(function(_, i){ showOneSatz(i); }); }
function clearAllSatz(){
  DOC.satz.forEach(function(_, i){
    const inp = document.getElementById('sf-' + i);
    inp.value = ''; inp.classList.remove('ok','bad');
    document.getElementById('sf-res-' + i).textContent = '';
  });
}
/* ---- Hochschullandschaft cloze ---- */
let clozeSel = null;
function clozeClick(el){
  if (el.classList.contains('filled')){ el.textContent = '?'; el.classList.remove('filled','ok','bad'); return; }
  document.querySelectorAll('.cloze-blank').forEach(function(b){ b.classList.remove('sel'); });
  clozeSel = el; el.classList.add('sel');
}
function bankFill(chip){
  if (!clozeSel){ alert('请先点一个空格，再点词库里的词。'); return; }
  clozeSel.textContent = chip.textContent;
  clozeSel.classList.add('filled'); clozeSel.classList.remove('sel','ok','bad');
  clozeSel = null;
}
function clozeCheck(){
  let n = 0, tot = 0;
  document.querySelectorAll('.cloze-blank').forEach(function(b){
    tot++;
    const ok = kwNormalize(b.textContent) === kwNormalize(b.dataset.ans);
    b.classList.remove('ok','bad'); b.classList.add(ok ? 'ok' : 'bad');
    if (ok) n++;
  });
  document.getElementById('clozeResult').textContent = '正确 ' + n + ' / ' + tot + ' 空';
}
function clozeClear(){
  document.querySelectorAll('.cloze-blank').forEach(function(b){
    b.textContent = '?'; b.classList.remove('filled','ok','bad','sel');
  });
  document.getElementById('clozeResult').textContent = '';
}
/* ---- Mindmap ---- */
let mmSel = null;
function mmSelect(el){
  if (el.parentNode.classList.contains('mm-items')){   // 从分类框取回
    document.getElementById('mmPool').appendChild(el);
    el.classList.remove('ok','bad');
    return;
  }
  if (mmSel) mmSel.classList.remove('sel');
  mmSel = el; el.classList.add('sel');
}
function mmDrop(box){
  if (!mmSel){ return; }
  box.querySelector('.mm-items').appendChild(mmSel);
  mmSel.classList.remove('sel','ok','bad');
  mmSel = null;
}
function mmCheck(){
  let ok = 0, tot = 0, done = 0;
  document.querySelectorAll('.mm-board .mm-box').forEach(function(box){
    const cat = box.dataset.cat;
    box.querySelectorAll('.mm-chip').forEach(function(ch){
      tot++;
      const right = ch.dataset.c === cat;
      ch.classList.remove('ok','bad'); ch.classList.add(right ? 'ok' : 'bad');
      if (right) ok++;
    });
  });
  done = document.querySelectorAll('#mmPool .mm-chip').length;
  document.getElementById('mmResult').textContent = '归类正确 ' + ok + ' / ' + tot + (done ? '（还有 ' + done + ' 个未归类）' : '');
}
function mmReset(){
  const pool = document.getElementById('mmPool');
  document.querySelectorAll('.mm-board .mm-chip').forEach(function(ch){
    ch.classList.remove('ok','bad'); pool.appendChild(ch);
  });
  document.getElementById('mmResult').textContent = '';
}
/* ---- Satzbau ---- */
function sbPick(el, i){
  const line = document.getElementById('sb-line-' + i);
  const pool = document.getElementById('sb-pool-' + i);
  if (el.parentNode === pool){ line.appendChild(el); }
  else { pool.appendChild(el); }
  line.classList.remove('ok','bad');
}
function sbUndo(i){ const line = document.getElementById('sb-line-' + i); const last = line.lastElementChild; if (last) sbPick(last, i); }
function sbReset(i){
  const pool = document.getElementById('sb-pool-' + i);
  const line = document.getElementById('sb-line-' + i);
  Array.prototype.slice.call(line.children).forEach(function(ch){ pool.appendChild(ch); });
  line.classList.remove('ok','bad');
  document.getElementById('sb-res-' + i).textContent = '';
}
function sbCheck(i){
  const line = document.getElementById('sb-line-' + i);
  const got = Array.prototype.slice.call(line.children).map(function(ch){ return ch.textContent.trim(); });
  const want = DOC.satzbau[i].chunks;
  const res = document.getElementById('sb-res-' + i);
  const ok = got.length === want.length && got.every(function(g, k){ return g === want[k].trim(); });
  line.classList.remove('ok','bad'); line.classList.add(ok ? 'ok' : 'bad');
  res.textContent = ok ? '✓ 语序正确' : '✗ 语序还不对，检查动词位置和从句语序';
  res.className = 'fill-result ' + (ok ? 'correct' : 'wrong');
}
function sbShow(i){
  const line = document.getElementById('sb-line-' + i);
  const pool = document.getElementById('sb-pool-' + i);
  Array.prototype.slice.call(line.children).forEach(function(ch){ pool.appendChild(ch); });
  DOC.satzbau[i].chunks.forEach(function(txt){
    Array.prototype.slice.call(pool.children).forEach(function(ch){
      if (ch.textContent.trim() === txt.trim() && ch.parentNode === pool) line.appendChild(ch);
    });
  });
  line.classList.remove('bad'); line.classList.add('ok');
  document.getElementById('sb-res-' + i).textContent = '参考语序';
  document.getElementById('sb-res-' + i).className = 'fill-result correct';
}
/* ---- misc ---- */
function flipTrans(el){ el.classList.toggle('flipped'); }
function toggleBox(id){ const b = document.getElementById(id); b.style.display = (b.style.display === 'none' ? 'block' : 'none'); }
const scores = {A: 0, B: 0};
function addScore(t, d){ scores[t] = Math.max(0, scores[t] + d); document.getElementById('score' + t).textContent = scores[t]; }
function resetScore(){ scores.A = 0; scores.B = 0; document.getElementById('scoreA').textContent = '0'; document.getElementById('scoreB').textContent = '0'; }
'''

def main():
    with open(DATA_FILE, encoding='utf-8') as f:
        d = json.load(f)

    cw = build_crossword([c['answer'] for c in d['kreuzwort']['clues']])
    grid, entries, ok, span = cw
    if not ok:
        print('WARNING: crossword could not place all words: %d/%d' % (len(entries), len(d['kreuzwort']['clues'])))
    print('crossword: %d/%d words placed' % (len(entries), len(d['kreuzwort']['clues'])))

    css = open(os.path.join(DIR, 'template_css.css'), encoding='utf-8').read()
    css = css.replace('</style>', EXTRA_CSS + '</style>')

    # nav
    secs = [('home', '首页'), ('vocab', '词汇卡片'), ('blitz', '⚡抢答'), ('connect', '🔗连线'),
            ('kreuzwort', '🧩填字'), ('satz', '✍️填空'), ('hochschule', '🏛️高校类型'),
            ('mindmap', '🗺️导图'), ('satzbau', '🧱句型'), ('uebersetzen', '🎯翻译'), ('spiele', '🏆游戏')]
    nav = '<nav><div class="top-nav"><div class="logo" style="cursor:pointer" onclick="switchSection(\'home\')">' \
          '<span class="logo-icon">🎓</span><span>Lektion 7 · Wortschatz</span></div><div class="nav-links" id="navLinks">'
    for sid, lbl in secs:
        nav += '<button onclick="switchSection(\'%s\')">%s</button>' % (sid, lbl)
    nav += '</div><button class="hamburger" onclick="toggleNav()">☰</button></div>' \
           '<div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div></nav>'

    body = (sec_home(d) + sec_vocab(d) + sec_blitz(d) + sec_connect(d) + sec_kreuzwort(d, cw) +
            sec_satz(d) + sec_hochschule(d) + sec_mindmap(d) + sec_satzbau(d) + sec_uebersetzen(d) + sec_spiele(d))

    kw_entries = [{'word': w, 'r': r, 'c': c, 'dir': dr} for (w, r, c, dr) in entries]
    data_js = json.dumps({'kwEntries': kw_entries, 'satz': [c['answer'] for c in d['kreuzwort']['clues']],
                          'satzbau': [{'chunks': s['chunks']} for s in d['satzbau']]}, ensure_ascii=False)

    core_js = '''
function switchSection(id){
  document.querySelectorAll('section').forEach(function(s){ s.classList.remove('active'); });
  const el = document.getElementById(id); if (el) el.classList.add('active');
  document.querySelectorAll('.nav-links button').forEach(function(b){ b.classList.remove('active'); });
  const idx = SECTIONS.indexOf(id);
  document.querySelectorAll('.nav-links button')[idx] && document.querySelectorAll('.nav-links button')[idx].classList.add('active');
  document.getElementById('progressFill').style.width = ((idx + 1) / SECTIONS.length * 100) + '%%';
  window.scrollTo(0, 0);
}
function toggleNav(){ document.getElementById('navLinks').classList.toggle('show'); }
const SECTIONS = %s;
''' % json.dumps([s[0] for s in secs])

    html = '''<!DOCTYPE html>
<html lang="zh-CN" data-cw-profile="interaction">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Lektion 7 · 词汇与翻译课堂互动课件 · Studium &amp; Schule</title>
%s
</head>
<body>
%s
<div class="main"><div class="container"><div class="text-cards">
%s
</div></div></div>
<div class="vocab-overlay" id="vocabOverlay" onclick="hideVocab()"></div>
<div class="vocab-panel" id="vocabPanel">
  <div class="vocab-panel-header"><span id="vpWord" class="vp-word"></span>
    <button onclick="hideVocab()" class="vp-close">&times;</button></div>
  <div id="vpZh" class="vp-zh"></div>
  <div id="vpEx" class="vp-ex"></div>
</div>
<script>
const DOC = %s;
%s
%s
</script>
</body>
</html>
''' % (css, nav, body, data_js, core_js, EXTRA_JS)

    # add badflash style
    html = html.replace('</style>', '  .badflash { background: #fdecea !important; border-color: #e74c3c !important; }\n</style>')

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(html)
    print('Generated: %s (%d bytes)' % (OUT, len(html)))

    # --- JS syntax check ---
    js = html[html.find('<script>') + 8: html.rfind('</script>')]
    r = subprocess.run(['node', '-e',
        'try{require("vm").compileFunction(JSON.parse(process.argv[1]));console.log("JS OK")}catch(e){console.log("JS ERROR: "+e.message.substring(0,120))}',
        json.dumps(js)], capture_output=True, text=True, timeout=15)
    print(r.stdout.strip() or r.stderr[:200])

    # --- section balance ---
    print('sections open=%d close=%d' % (html.count('<section'), html.count('</section>')))
    for sid in [s[0] for s in secs]:
        assert 'id="%s"' % sid in html, 'missing section ' + sid
    print('all %d section ids present' % len(secs))

if __name__ == '__main__':
    main()
