#!/usr/bin/env python3
"""
Build.py v2.0 — 德语课件生成器
- 移除 TTS/SRS 语音功能
- 课文分页展示 (Prev/Next)
- 词汇改为点击弹出 overlay 面板
- 新增填空 (fill-gap) + 连线匹配 (connect-grid) 练习
- 进度条导航
"""

import json, sys, os, re, subprocess

DIR = os.path.dirname(os.path.abspath(__file__))

def load(path):
    with open(os.path.join(DIR, path), encoding='utf-8') as f:
        return f.read()

def js_str(s):
    return s.replace("'", "\\'").replace('\n', ' ').replace('\r', '')

def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def vocab_span(key, word, cn, de_ex):
    a = chr(39)
    return '<span class="v-word" onclick="showVocab(' + a + js_str(key) + a + ',' + a + js_str(cn) + a + ',' + a + js_str(de_ex) + a + ')">' + word + '</span>'

def render_para(p, vocab):
    out = p
    for v in vocab:
        m = '%%' + v['key'] + '%%'
        if m in out:
            sp = vocab_span(v['key'], v.get('word', v['key']), v['cn'], v.get('de', ''))
            out = out.replace(m, sp)
    return out

# ============= SECTION GENERATORS =============

def gen_nav(data):
    m = data['meta']
    secs = ['home', 'text', 'vocab', 'grammar', 'exercise', 'translation']
    labels = m.get('navLabels', ['首页', '课文讲解', '重点词汇', '语法', '练习', '翻译卡片'])
    h = '<nav><div class="top-nav">'
    h += '<div class="logo" style="cursor:pointer" onclick="switchSection(\'home\')">'
    h += '<span class="logo-icon">\U0001f393</span><span>Lektion ' + str(m['lektion']) + '</span></div>'
    h += '<div class="nav-links" id="navLinks">'
    for sid, lbl in zip(secs, labels):
        h += '<button onclick="switchSection(\'{id}\')">{l}</button>'.format(id=sid, l=lbl)
    h += '</div>'
    h += '<button class="hamburger" onclick="toggleNav()">\u2630</button>'
    h += '</div>'
    h += '<div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>'
    h += '</nav>'
    return h

def gen_home(data):
    m = data['meta']
    h = '    <section id="home" class="active">\n'
    h += '      <div class="hero">\n'
    h += '        <h1>Lektion {lek} \u00b7 {t}</h1>\n'.format(lek=m['lektion'], t=m['title'])
    h += '        <p class="sub">{s}</p>\n'.format(s=m['subtitle'])
    h += '        <p class="meta">\u6559\u6750\u8bfe\u6587 \u00b7 \u8bcd\u6c47 \u00b7 \u8bed\u6cd5 \u00b7 \u7ec3\u4e60</p>\n'
    h += '      </div>\n'

    # Overview cards
    h += '      <div class="home-grid">\n'
    cards = [
        ('text', '\U0001f4d6 \u8bfe\u6587\u8bb2\u89e3', '\u6559\u6750\u539f\u6587 + \u91cd\u70b9\u8bcd\u6c47 + \u5fb7\u6587\u6982\u8981'),
        ('vocab', '\U0001f4dd \u91cd\u70b9\u8bcd\u6c47', '\u53ef\u70b9\u51fb\u67e5\u8bcd + \u8bcd\u6c47\u7f51\u683c'),
        ('grammar', '\U0001f524 \u8bed\u6cd5\u00b7{t}'.format(t=m['grammarTopic']), '\u5e76\u5217\u8fde\u8bcd\u7528\u6cd5\u8be6\u89e3 + \u4f8b\u53e5'),
        ('exercise', '\u270f\ufe0f \u7ec3\u4e60', '\u8bcd\u6c47\u7ec3\u4e60 + \u914d\u5bf9\u6e38\u620f + \u586b\u7a7a'),
    ]
    for sid, t, d in cards:
        h += '        <div class="text-card" onclick="switchSection(\'{id}\')" style="cursor:pointer">\n'.format(id=sid)
        h += '          <h3>{t}</h3>\n'.format(t=t)
        h += '          <p>{d}</p>\n'.format(d=d)
        h += '        </div>\n'
    h += '      </div>\n'

    # Objectives
    if m.get('objectives'):
        h += '      <div class="obj-box">\n'
        h += '        <strong>\u5b66\u4e60\u76ee\u6807\uff1a</strong>\n'
        h += '        <ul>\n'
        for o in m['objectives']:
            h += '          <li>{o}</li>\n'.format(o=o)
        h += '        </ul>\n'
        h += '      </div>\n'
    h += '    </section>\n'
    return h

def gen_text(data):
    h = '    <section id="text">\n'
    h += '      <h2 class="section-title"><span class="num">1</span> ' + data['meta']['sectionTitles']['text'] + '</h2>\n'

    for t in data['texts']:
        h += '      <div class="text-card">\n'
        h += '        <h3>{title}</h3>\n'.format(title=t['title'])
        if t.get('subTitle'):
            h += '        <p class="zh sub">{s}</p>\n'.format(s=t['subTitle'])
        if t.get('by'):
            h += '        <p class="zh by">\u2014\u2014 {by}</p>\n'.format(by=t['by'])

        # Pages: split paragraphs into pages
        # Default: 1 page with all paragraphs, or use pages from JSON
        pages = t.get('pages', [t['paragraphs']])
        total_pages = len(pages)
        text_id = t['id'] if 'id' in t else data['texts'].index(t)

        if total_pages > 1:
            h += '        <div class="text-pager" id="tp-{id}">\n'.format(id=text_id)
            for pi, page_paras in enumerate(pages):
                h += '          <div class="text-page" data-page="{pi}" style="display:{s}">\n'.format(pi=pi, s='block' if pi == 0 else 'none')
                for para in page_paras:
                    h += '            <p>{p}</p>\n'.format(p=render_para(para, data['vocab']))
                h += '          </div>\n'
            h += '          <div class="text-pager-nav">\n'
            h += '            <button class="tp-btn" onclick="prevPage(\'{id}\')" id="tp-prev-{id}" disabled>\u2039</button>\n'.format(id=text_id)
            h += '            <span class="tp-info" id="tp-info-{id}">1 / {t}</span>\n'.format(id=text_id, t=total_pages)
            h += '            <button class="tp-btn" onclick="nextPage(\'{id}\')" id="tp-next-{id}">\u203a</button>\n'.format(id=text_id)
            h += '          </div>\n'
            h += '        </div>\n'
        else:
            h += '        <div class="de">\n'
            for para in pages[0]:
                h += '          <p>{p}</p>\n'.format(p=render_para(para, data['vocab']))
            h += '        </div>\n'

        if t.get('summary'):
            h += '        <div class="highlight-box">{s}</div>\n'.format(s=t['summary'])
        h += '      </div>\n'

    h += '    </section>\n'
    return h

def gen_vocab(data):
    h = '    <section id="vocab">\n'
    h += '      <h2 class="section-title"><span class="num">2</span> ' + data['meta']['sectionTitles']['vocab'] + '</h2>\n'

    # Group by text
    groups = {}
    for i, t in enumerate(data['texts']):
        gid = 'T' + str(i + 1)
        groups[gid] = {'title': t.get('id', gid), 'items': []}

    for v in data['vocab']:
        assigned = False
        for i, t in enumerate(data['texts']):
            gid = 'T' + str(i + 1)
            for p in t.get('paragraphs', []):
                if '%%' + v['key'] + '%%' in p:
                    groups[gid]['items'].append(v)
                    assigned = True
                    break
            if assigned:
                break
        if not assigned:
            groups['T1']['items'].append(v)

    # Tabs
    first = True
    for gid, g in groups.items():
        if not g['items']:
            continue
        a = ' active' if first else ''
        first = False
        h += '      <div class="person-tabs">\n'
        h += '        <button class="person-btn{a}" onclick="switchVocabTab(\'{id}\')">{t}</button>\n'.format(a=a, id=gid, t=g['title'])
        h += '      </div>\n'
        h += '      <div class="person-content{a}" id="vc-{id}">\n'.format(a=a, id=gid)
        h += '        <div class="vocab-grid">\n'
        for v in g['items']:
            word = v.get('word', v['key'])
            a1 = chr(39)
            h += '          <div class="vc-card" onclick="flipCard(this)">\n'
            h += '            <div class="vc-inner">\n'
            h += '              <div class="vc-front">{w}</div>\n'.format(w=word)
            h += '              <div class="vc-back">{c}</div>\n'.format(c=v['cn'])
            h += '            </div>\n'
            h += '            <button class="vc-detail" onclick=\'event.stopPropagation();showVocab(' + a1 + js_str(word) + a1 + ',' + a1 + js_str(v['cn']) + a1 + ',' + a1 + js_str(v.get('de', '')) + a1 + ')\'>\u25b6</button>\n'
            h += '          </div>\n'
        h += '        </div>\n'
        h += '      </div>\n'

    h += '    </section>\n'
    return h

def gen_grammar(data):
    h = '    <section id="grammar">\n'
    h += '      <h2 class="section-title"><span class="num">3</span> ' + data['meta']['sectionTitles']['grammar'] + '</h2>\n'

    for tbl in data['grammar']['tables']:
        h += '      <div class="grammar-table-wrapper">\n'
        h += '        <h3>{t}</h3>\n'.format(t=tbl['title'])
        h += '        <table class="grammar-table">\n'
        h += '          <thead><tr>'
        for th in tbl['headers']:
            h += '<th>{h}</th>'.format(h=th)
        h += '</tr></thead>\n'
        h += '          <tbody>\n'
        for row in tbl['rows']:
            h += '            <tr>'
            for cell in row:
                h += '<td>' + re.sub(r'%%([^%]+)%%', r'<strong>\1</strong>', cell) + '</td>'
            h += '</tr>\n'
        h += '          </tbody>\n'
        h += '        </table>\n'
        h += '      </div>\n'

    if data['grammar'].get('examples'):
        h += '      <div class="grammar-examples">\n'
        h += '        <h3>\u4f8b\u53e5</h3>\n'
        for ex in data['grammar']['examples']:
            h += '        <div class="grammar-example">\n'
            h += '          <div class="de">{d}</div>\n'.format(d=ex['de'])
            h += '          <div class="zh">{z}</div>\n'.format(z=ex['zh'])
            h += '        </div>\n'
        h += '      </div>\n'

    h += '    </section>\n'
    return h

def gen_exercise(data):
    h = '    <section id="exercise">\n'
    h += '      <h2 class="section-title"><span class="num">4</span> ' + data['meta']['sectionTitles']['exercise'] + '</h2>\n'

    # 1) Quiz
    if data.get('quiz'):
        for qi, q in enumerate(data['quiz']):
            n = qi + 1
            h += '      <div class="quiz-card">\n'
            h += '        <div class="q-text">{n}. {q}</div>\n'.format(n=n, q=q['q'])
            h += '        <div class="options">\n'
            for j, opt in enumerate(q['options']):
                letter = chr(65 + j)
                h += '          <div class="opt" onclick="checkQuiz(this,{n},{j})">{a}. {o}</div>\n'.format(n=n, j=j, a=letter, o=opt)
            h += '        </div>\n'
            h += '        <div class="q-answer">{a}</div>\n'.format(a=q['answer'])
            h += '        <button class="show-answer-btn" onclick="this.previousElementSibling.classList.toggle(\'show\')">\u663e\u793a\u7b54\u6848</button>\n'
            h += '      </div>\n'

    # 2) Connect grid
    if data.get('connectGrids'):
        for cgi, cg in enumerate(data['connectGrids']):
            h += '      <div class="connect-game">\n'
            h += '        <h3>{t}</h3>\n'.format(t=cg.get('title', '\u8fde\u7ebf\u5339\u914d'))
            h += '        <p class="zh">\u70b9\u51fb\u5de6\u5217\u5fb7\u6587\uff0c\u518d\u70b9\u51fb\u53f3\u5217\u4e2d\u6587\u8fdb\u884c\u5339\u914d</p>\n'
            h += '        <div class="connect-field" id="cg-{id}">\n'.format(id=cgi)
            h += '          <div class="connect-col" id="cg-de-{id}">\n'.format(id=cgi)
            for i, (de, _) in enumerate(cg['pairs']):
                h += '            <div class="c-item de" data-pair="{i}" data-gid="{id}" onclick="cClick(this)">{d}</div>\n'.format(i=i, id=cgi, d=de)
            h += '          </div>\n'
            h += '          <div class="connect-col" id="cg-cn-{id}">\n'.format(id=cgi)
            for i, (_, cn) in enumerate(cg['pairs']):
                h += '            <div class="c-item cn" data-pair="{i}" data-gid="{id}" onclick="cClick(this)">{c}</div>\n'.format(i=i, id=cgi, c=cn)
            h += '          </div>\n'
            h += '        </div>\n'
            h += '        <div class="connect-score" id="cg-score-{id}">\u5339\u914d\uff1a<span id="cg-cnt-{id}">0</span> / {t}</div>\n'.format(id=cgi, t=len(cg['pairs']))
            h += '      </div>\n'

    # 3) Fill-gap
    if data.get('fillGaps'):
        for fgi, fg in enumerate(data['fillGaps']):
            h += '      <div class="fill-game">\n'
            h += '        <h3>{t}</h3>\n'.format(t=fg.get('title', '\u586b\u7a7a\u7ec3\u4e60'))
            h += '        <p class="zh">\u5728\u7a7a\u767d\u5904\u586b\u5165\u5408\u9002\u7684\u8bcd\u6c47</p>\n'
            for i, item in enumerate(fg['items']):
                h += '        <div class="fill-item">\n'
                h += '          <div class="fill-sentence">{s}</div>\n'.format(s=item['sentence'])
                h += '          <div class="fill-input-line">\n'
                h += '            <input type="text" class="fill-input" id="fg-{gid}-{i}" placeholder="..." data-answer="{a}">\n'.format(gid=fgi, i=i, a=item['answer'])
                h += '            <button class="fill-check" onclick="checkFill({gid},{i})">\u2713</button>\n'.format(gid=fgi, i=i)
                h += '            <span class="fill-result" id="fg-res-{gid}-{i}"></span>\n'.format(gid=fgi, i=i)
                h += '          </div>\n'
                h += '        </div>\n'
            h += '      </div>\n'

    # 4) Matching game
    if data.get('matchingPairs'):
        h += '      <div class="match-game">\n'
        h += '        <h3>\u8bcd\u6c47\u914d\u5bf9 &middot; Wortpaare</h3>\n'
        h += '        <p class="zh">\u70b9\u51fb\u4e24\u5f20\u5361\u7247\u914d\u5bf9\u5fb7\u8bed\u8bcd\u548c\u4e2d\u6587\u91ca\u4e49</p>\n'
        h += '        <div id="match-game" style="max-width:600px;margin:0 auto">\n'
        for n, (de, zh) in enumerate(data['matchingPairs']):
            idx = n + 1
            h += '          <div class="match-card de" data-pair="{i}" onclick="matchClick(this)">{d}</div>\n'.format(i=idx, d=de)
            h += '          <div class="match-card zh" data-pair="{i}" onclick="matchClick(this)">{c}</div>\n'.format(i=idx, c=zh)
        h += '        </div>\n'
        h += '      </div>\n'

    h += '    </section>\n'
    return h

def gen_translation(data):
    cards = data.get('translationCards', [])
    if not cards:
        return ''
    h = '    <section id="translation">\n'
    h += '      <h2 class="section-title"><span class="num">5</span> ' + data['meta']['sectionTitles'].get('translation', '\u9010\u53e5\u7ffb\u8bd1\u7ec3\u4e60') + '</h2>\n'
    h += '      <p class="zh" style="margin:0 0 12px;font-size:14px;color:#888">\u70b9\u51fb\u5361\u7247\u67e5\u770b\u7b54\u6848 \u00b7 \u5148\u81ea\u5df1\u8bd5\u8bd1\uff0c\u518d\u7ffb\u5f00\u6838\u5bf9</p>\n'
    h += '      <div class="translation-grid">\n'
    for i, tc in enumerate(cards):
        n = i + 1
        a1 = chr(39)
        h += '        <div class="tc-card" onclick="flipTrans(this)">\n'
        h += '          <div class="tc-inner">\n'
        h += '            <div class="tc-front">\n'
        h += '              <span class="tc-num">{n}</span>\n'.format(n=n)
        h += '              <div class="tc-de">{de}</div>\n'.format(de=tc['de'])
        h += '            </div>\n'
        h += '            <div class="tc-back">\n'
        h += '              <span class="tc-num">{n}</span>\n'.format(n=n)
        h += '              <div class="tc-zh">{zh}</div>\n'.format(zh=tc['zh'])
        if tc.get('vocab'):
            h += '              <div class="tc-vocab">\u7ec4\u8bcd\u2192 {v}</div>\n'.format(v=tc['vocab'])
        h += '            </div>\n'
        h += '          </div>\n'
        h += '        </div>\n'
    h += '      </div>\n'
    h += '    </section>\n'
    return h

def gen_test_txt(data):
    m = data['meta']
    lines = ['\u65b0\u7ecf\u5178\u5fb7\u8bed \u00b7 \u7b2c\u4e8c\u518c \u00b7 Lektion {lek} \u5c0f\u6d4b'.format(lek=m['lektion'])]
    lines.append(m['title'])
    lines.append('')

    quiz = data.get('quiz', [])
    if quiz:
        total = len(quiz) * 3
        lines.append('\u4e00\u3001\u5355\u9009\u9898\uff08\u6bcf\u98983\u5206\uff0c\u5171{total}\u5206\uff09'.format(total=total))
        lines.append('')
        for i, q in enumerate(quiz):
            n = i + 1
            lines.append('{n}. {q}'.format(n=n, q=q['q']))
            for j, opt in enumerate(q['options']):
                lines.append('{a}. {o}'.format(a=chr(65 + j), o=opt))
            lines.append('\u7b54\u6848\uff1a{ans}'.format(ans=q['answer']))
            lines.append('')

    pairs = data.get('matchingPairs', [])
    if pairs:
        total2 = len(pairs) * 2
        lines.append('\u4e8c\u3001\u8bcd\u6c47\u914d\u5bf9\uff08\u6bcf\u98982\u5206\uff0c\u5171{total}\u5206\uff09'.format(total=total2))
        lines.append('')
        for i, (de, zh) in enumerate(pairs):
            n = i + 1
            lines.append('{n}. {d}'.format(n=n, d=de))
            lines.append('\u7b54\u6848\uff1a{ans}'.format(ans=zh))
            lines.append('')

    return '\n'.join(lines)

def build(data_file):
    with open(data_file, encoding='utf-8') as f:
        data = json.load(f)

    m = data['meta']
    base = os.path.splitext(os.path.basename(data_file))[0]

    css = load('template_css.css')
    nav = gen_nav(data)
    js = load('template_js.js')

    home = gen_home(data)
    text = gen_text(data)
    vocab = gen_vocab(data)
    grammar = gen_grammar(data)
    exercise = gen_exercise(data)
    translation = gen_translation(data)

    # Assemble
    h = '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n'
    h += '<meta charset="UTF-8">\n'
    h += '<meta name="viewport" content="width=device-width,initial-scale=1.0">\n'
    h += '<title>Lektion {lek} \u00b7 {t} \u00b7 \u4ea4\u4e92\u5f0f\u8bfe\u4ef6</title>\n'.format(lek=m['lektion'], t=m['title'])
    h += css
    h += '</head>\n<body>\n'
    h += nav
    h += '<div class="main"><div class="container"><div class="text-cards">\n'
    h += home + text + vocab + grammar + exercise + translation
    h += '</div></div></div>\n'
    h += '<div class="vocab-overlay" id="vocabOverlay" onclick="hideVocab()"></div>\n'
    h += '<div class="vocab-panel" id="vocabPanel">\n'
    h += '  <div class="vocab-panel-header">\n'
    h += '    <span id="vpWord" class="vp-word"></span>\n'
    h += '    <button onclick="hideVocab()" class="vp-close">&times;</button>\n'
    h += '  </div>\n'
    h += '  <div id="vpZh" class="vp-zh"></div>\n'
    h += '  <div id="vpEx" class="vp-ex"></div>\n'
    h += '</div>\n'
    h += '<script>\n' + js + '\n</script>\n'
    h += '</body>\n</html>\n'

    out_html = os.path.join(DIR, base + '.html')
    with open(out_html, 'w', encoding='utf-8') as f:
        f.write(h)

    test = gen_test_txt(data)
    out_txt = os.path.join(DIR, base + '-test.txt')
    with open(out_txt, 'w', encoding='utf-8') as f:
        f.write(test)

    print('Generated: {html} ({size} bytes)'.format(html=out_html, size=len(h)))
    print('Generated: {txt} ({size} bytes)'.format(txt=out_txt, size=len(test)))

    # JS syntax check
    js_start = h.find('<script>')
    js_end = h.rfind('</script>')
    if js_start >= 0 and js_end >= 0:
        js_only = h[js_start + 8:js_end]
        r = subprocess.run(['node', '-e',
            'try{require("vm").compileFunction(JSON.parse(process.argv[1]));console.log("OK")}catch(e){console.log(e.message.substring(0,80))}',
            json.dumps(js_only)], capture_output=True, text=True, timeout=5)
        print('JS: {r}'.format(r=r.stdout.strip() or r.stderr[:80]))

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python3 build.py <data.json>')
        sys.exit(1)
    build(sys.argv[1])
