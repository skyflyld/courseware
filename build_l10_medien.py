#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_l10_medien.py — Lektion 10《Funktionen der Massenmedien》互动课件生成器
输入: l10-data.json
输出: lektion10-funktionen-der-massenmedien.html（单文件，自包含 CSS/JS，零外部请求）

基底: 复用 build_l8_berufe.py（设计令牌 / 投影挡位 / 词卡 / 连线 / 面板）
      + build_l8_t1t2.py（读词查义面板样式、段落结构、透明卡片）
与 L9 同一条链、同一套共用基底（Sky 2026-09-20 指令）。
原子原则: 一个脚本 → 一个产物；不在产物上做增量修补。
数据纪律: 德文/中文一律取 l10-data.json 原值，不改写、不补造。
"""
import json
import os
import random
import re
import subprocess

import build_l8_berufe as base
import build_l8_t1t2 as t12

DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(DIR, 'l10-data.json')
OUT = os.path.join(DIR, 'lektion10-funktionen-der-massenmedien.html')

esc_attr = base.esc_attr
tools_buttons = base.tools_buttons
_js = t12._js_str


def h(s):
    """正文转义 + 分隔符「·」禁用行首（换行质量层做法 4：不换行空格粘住前文）。"""
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
    out, last = [], 0
    for m in re.finditer(r'%%(.+?)%%', text):
        surface, key = m.group(1).split('|')
        out.append(h(text[last:m.start()]))
        e = gmap.get(key)
        out.append(_gloss_span(e, surface) if e else h(surface))
        last = m.end()
    out.append(h(text[last:]))
    return ''.join(out)


def gmap_of(t):
    return {e['w']: e for e in t.get('glossar', [])}


def gh(text):
    """语法例句里的 %%…%% → 加粗强调"""
    return re.sub(r'%%(.+?)%%', r'<b class="gh">\1</b>', h(text))


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
    cards = [
        ('text', '📰 课文 · Funktionen der Massenmedien',
         '七段读懂「媒体为社会做了什么」· %d 个重点词可点' % len(d['text']['glossar'])),
        ('vocab', '🃏 词汇卡', '%d 词分 %d 组 · 点卡翻面' % (n_vocab, len(d['vocab']['groups']))),
        ('grammar', '🔤 语法', 'um … zu / damit / 两者区别（三张表）'),
        ('connect', '🔗 连线配对', '%d 组 · %d 对' % (len(d['connectGrids']), n_pairs)),
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
      <div class="highlight-box">🎬 怎么用：点顶部导航切节；课文里带虚线的德语词点一下出释义与例句；词卡点一下翻面；连线配完变绿；翻译卡先自己译再翻面核对。投影时点右下角 A± 放大。</div>
      <div class="home-grid">%s</div>
      <div class="obj-box"><strong>学习目标 Lernziele：</strong><ul>%s</ul></div>
      <div class="text-card" style="margin-top:12px">
        <h3>🧭 学习路线（建议 40 分钟走完）</h3>
        <table class="flow-table">%s</table>
      </div>
    </section>
''' % (h(m['title']), h(m['subtitle']), h(m['source']), g, objs, ''.join(rows))


# ---------------------------------------------------------------- 2 课文
def sec_text(d):
    t = d['text']
    gm = gmap_of(t)
    paras = ''.join('<p class="cloze-p" lang="de">%s</p>' % gloss_render(p, gm) for p in t['paras'])
    return '''    <section id="text">
      <h2 class="section-title"><span class="num">1</span> 📰 %s <span class="src src-lg">%s · %s</span></h2>
      <p class="zh-hint">%s</p>
      <p class="zh-hint">✏️ 带虚线的德文词点一下，弹出中文释义和这词在课文里的原句。</p>
      <div class="text-card read-card">%s</div>
      <p class="zh-hint note">📌 %s</p>
    </section>
''' % (h(t['title']), h(t['kind']), h(t['sub']), h(t['lead']), paras, h(t['provenance']))


# ---------------------------------------------------------------- 3 词汇卡
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
                      '<p class="zh-hint note">📖 出处：<span class="src">%s</span></p>'
                      '<div class="vocab-grid">%s</div></div>'
                      % (a, grp['id'], h(grp.get('src', '')), cards))
    rows = ''.join('<tr><td class="vt-de" lang="de">%s</td><td class="vt-cn">%s</td></tr>'
                   % (base.word_html(wd['w']), h(wd['cn']))
                   for grp in groups for wd in grp['words'])
    n = sum(len(g['words']) for g in groups)
    return '''    <section id="vocab">
      <h2 class="section-title"><span class="num">2</span> 🃏 %s</h2>
      <p class="zh-hint">%s</p>
      <p class="zh-hint note">教材标注：<b>( )</b> 词尾 / 复数形式，<b>¨</b> 变音，<b>...</b> 省略词干，<b>+A / +D</b> 支配格。标注已降权显示，主词为黑体。</p>
      <div class="person-tabs">%s</div>%s
      %s
      <div id="l10Table" style="display:none"><div class="vocab-table-wrap"><table class="vocab-table">%s</table></div></div>
      <p class="zh-hint note">来源：%s</p>
    </section>
''' % (h(v['title']), h(v['instruction']), ''.join(tabs), ''.join(panels),
       tools_buttons(['<button class="btn ghost" onclick="toggleBox(\'l10Table\')">📋 展开全表（%d 词）</button>' % n]),
       rows, h(v['src']))


# ---------------------------------------------------------------- 4 语法
def sec_grammar(d):
    g = d['grammar']
    tables = []
    for tb in g['tables']:
        head = ''.join('<th>%s</th>' % h(c) for c in tb['headers'])
        rows = ''.join('<tr>%s</tr>' % ''.join('<td lang="de">%s</td>' % gh(c) for c in r)
                       for r in tb['rows'])
        tables.append('<div class="text-card"><h3>%s <span class="src">%s</span></h3>'
                      '<div class="vocab-table-wrap">'
                      '<table class="tb"><tr>%s</tr>%s</table></div></div>'
                      % (h(tb['title']), h(tb.get('src', '')), head, rows))
    ex = ''.join('<div class="rm-item"><div class="rm-de" lang="de">%s</div><div class="rm-cn">%s</div></div>'
                 % (h(e['de']), h(e['zh'])) for e in g['examples'])
    return '''    <section id="grammar">
      <h2 class="section-title"><span class="num">3</span> 🔤 语法 · Grammatik</h2>
      <p class="zh-hint">三张表连着看：先用 um … zu（主语一致），再用 damit（主语不同），最后看两者的区别。表里<b class="gh">加粗</b>的就是这一行的语法点。</p>
      %s
      <div class="text-card">
        <h3>🗣️ 例句 · Beispiele（读一遍，注意加粗处）</h3>
        %s
      </div>
    </section>
''' % (''.join(tables), ex)


# ---------------------------------------------------------------- 5 连线
def sec_connect(d):
    out = []
    for gi, cg in enumerate(d['connectGrids']):
        idx = list(range(len(cg['pairs'])))
        random.Random(910 + gi).shuffle(idx)          # 固定种子，保证生成可复现
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
      <h2 class="section-title"><span class="num">4</span> 🔗 连线配对 · Vernetzen</h2>
      <p class="zh-hint">四组各连一遍（概念 / 五大功能 / 核心动词 / 形容词与搭配）。整组连完，照着左列把德文读一遍。</p>
%s
    </section>
''' % '\n'.join(out)


# ---------------------------------------------------------------- 6 翻译卡
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
      <h2 class="section-title"><span class="num">5</span> 🎯 %s</h2>
      <p class="zh-hint">%s</p>
      <p class="zh-hint note">参考译文由课件编写者译出，非教材标准答案；重点词已在句中加粗。</p>
      <div class="translation-grid">%s</div>
    </section>
''' % (h(t['title']), h(t['instruction']), '\n'.join(cards))


# ---------------------------------------------------------------- CSS / JS 追加
CSS_L10 = '''
  /* ===== 语法强调 / 翻译卡排版 ===== */
  .gh { color: #123a72; font-weight: 700; }
  .tc-front .rm-cn { font-size: var(--fs-body); line-height: 1.6; }
  .translation-grid { align-items: stretch; }
  .tc-card { min-width: 0; }
  .tc-front, .tc-back { overflow-wrap: anywhere; }
  /* 词条出处按钮（继承 L9 实测修法）：基底 ≤900px 想抬到 34px 但被后面无条件的 28px 覆盖
     （同为单类选择器，后来的胜）→ 手机只有 28px。这里无条件抬到 36px，省掉与基底重复的断点。
     按钮在卡片右下角，德语长词折两行时末行会钻到按钮底下（L9 实测水平重叠 25px）→
     两面底部留出按钮带（36px + 4px 间隙）。 */
  .vc-card .vc-detail, .vc-detail { width: 36px; height: 36px; font-size: 15px; opacity: .9; }
  .vc-front, .vc-back { padding-bottom: 40px; }
'''


# ---------------------------------------------------------------- assemble
def main():
    with open(DATA_FILE, encoding='utf-8') as f:
        d = json.load(f)

    secs = [('home', '首页'), ('text', '📰 课文'), ('vocab', '🃏 词汇卡'), ('grammar', '🔤 语法'),
            ('connect', '🔗 连线'), ('translation', '🎯 翻译卡')]

    css = open(os.path.join(DIR, 'template_css.css'), encoding='utf-8').read()
    css = css.replace('</style>', base.EXTRA_CSS + t12.CSS_EXTRA + CSS_L10 + '</style>')

    nav = ('<nav><div class="top-nav"><div class="logo" style="cursor:pointer" onclick="switchSection(\'home\')">'
           '<span class="logo-icon">🎓</span><span>Lektion 10 · Massenmedien</span></div>'
           '<div class="nav-links" id="navLinks">')
    for sid, lbl in secs:
        nav += '<button onclick="switchSection(\'%s\')">%s</button>' % (sid, lbl)
    nav += ('</div><button class="hamburger" onclick="toggleNav()">☰</button></div>'
            '<div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div></nav>')

    body = (sec_home(d) + sec_text(d) + sec_vocab(d) + sec_grammar(d) +
            sec_connect(d) + sec_translation(d))

    core_js = base.CORE_JS.replace('__SECTIONS__', json.dumps([s[0] for s in secs]))

    html = ('<!DOCTYPE html>\n<html lang="zh-CN" data-cw-profile="interaction">\n<head>\n'
            '<meta charset="UTF-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1.0">\n'
            '<title>Lektion 10 · Funktionen der Massenmedien · 互动课件</title>\n'
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
            + t12.JS_EXTRA + '\n</script>\n</body>\n</html>\n')

    # 学生向措辞归一化（共用基底里的教师向旧措辞，只在本产物上定点替换）
    for _a, _b in [('已显示参考答案（教师用）', '已显示参考答案'),
                   ('（课堂现场用，宽屏才显示）', '（宽屏才显示）'),
                   ('（投影时不用弹窗）', '')]:
        html = html.replace(_a, _b)

    # 换行质量：模板字面量里的「 · 」禁用行首（同 h() 做法 4）
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

    print('vc-card = %d (词表 %d) | gl = %d (glossar %d) | c-item = %d (pairs %d)'
          % (html.count('class="vc-card"'), sum(len(g['words']) for g in d['vocab']['groups']),
             html.count('class="gl"'), len(d['text']['glossar']),
             html.count('class="c-item'), sum(len(g['pairs']) for g in d['connectGrids']) * 2))
    print('tc-card = %d | tb tables = %d | src 标注 = %d'
          % (html.count('class="tc-card"'), len(d['grammar']['tables']), html.count('class="src')))
    assert html.count('class="tc-card"') == len(d['translation']['cards'])


if __name__ == '__main__':
    main()
