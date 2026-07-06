#!/usr/bin/env python3
"""
德语课件生成器 v1.0
读取 data.json → 生成完整 HTML 课件 + 学习通测试 TXT

用法:
  python3 build.py lektion9.json
  输出: lektion9.html + lektion9-test.txt
"""

import json, sys, os, re

def load_template(path):
    """Load template parts"""
    with open(os.path.join(os.path.dirname(__file__), path)) as f:
        return f.read()

def escape_js(s):
    """Escape string for JS single-quoted string"""
    return s.replace("'", "\\'").replace('\n', ' ')

def escape_html(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def make_vocab_span(key, word, cn, de_example):
    """Generate vocab-word HTML span with onclick handler"""
    js_args = "'{0}','{1}','{2}'".format(escape_js(key), escape_js(cn), escape_js(de_example))
    return '<span class="vocab-word" onclick="showVocab(' + chr(39) + escape_js(key) + chr(39) + ',' + chr(39) + escape_js(cn) + chr(39) + ',' + chr(39) + escape_js(de_example) + chr(39) + ')">' + word + '<button class="speak-btn" onclick="event.stopPropagation();speakWord(' + chr(39) + escape_js(word) + chr(39) + ')" title="听发音">🔊</button></span>'

def gen_home(data):
    """Generate home section"""
    m = data['meta']
    html = '''    <section id="home" class="active">\n'''
    html += '''      <div class="hero">\n'''
    html += '''        <h1>Lektion {lek} · {title}</h1>\n'''.format(lek=m['lektion'], title=m['title'])
    html += '''        <p class="sub">{sub}</p>\n'''.format(sub=m['subtitle'])
    html += '''        <p class="meta">教材课文 · 词汇 · 语法 · 练习</p>\n'''
    html += '''      </div>\n'''
    html += '''      <div class="home-grid">\n'''

    cards = [
        ('text', '📖 课文讲解', '教材原文 + 重点词汇 + 德文概要'),
        ('vocab', '📝 重点词汇', '可点击词汇 + 翻转卡片 + 词汇配对'),
        ('grammar', '🔤 语法·{t}'.format(t=m['grammarTopic']), '并列连词用法详解 + 例句'),
        ('exercise', '✏️ 练习', '词汇练习 + 配对游戏'),
    ]
    for sec_id, title, desc in cards:
        html += '''        <div class="text-card" onclick="switchSection('{id}')" style="cursor:pointer">\n'''.format(id=sec_id)
        html += '''          <h3>{t}</h3>\n'''.format(t=title)
        html += '''          <p>{d}</p>\n'''.format(d=desc)
        html += '''        </div>\n'''

    html += '''      </div>\n'''

    html += '''      <div style="margin-top:16px;padding:12px 16px;background:var(--card-bg);border-radius:var(--radius);box-shadow:var(--shadow);font-size:14px;color:var(--text-light)">\n'''
    html += '''        <strong style="color:var(--text)">学习目标：</strong>\n'''
    html += '''        <ul style="margin:8px 0 0 16px;padding:0;line-height:1.6">\n'''
    for obj in m['objectives']:
        html += '''          <li>{o}</li>\n'''.format(o=obj)
    html += '''        </ul>\n'''
    html += '''      </div>\n'''
    html += '''    </section>\n'''
    return html

def gen_text(data):
    """Generate text section with vocab spans"""
    html = '''    <section id="text">\n'''
    html += '''      <h2 class="section-title"><span class="num">1</span> ''' + data['meta']['sectionTitles']['text'] + '''</h2>\n'''

    for t in data['texts']:
        html += '''      <div class="text-card">\n'''
        html += '''        <h3>{t}</h3>\n'''.format(t=t['title'])
        if 'subTitle' in t:
            html += '''        <p class="zh" style="font-size:14px;margin:-6px 0 10px">{s}</p>\n'''.format(s=t['subTitle'])
        if 'by' in t:
            html += '''        <p class="zh" style="font-size:13px;margin:-6px 0 10px;color:#888">—— {by}</p>\n'''.format(by=t['by'])
        html += '''        <div class="de">\n'''
        for p in t['paragraphs']:
            # Parse %%key%% markers
            parsed = p
            for v in data['vocab']:
                marker = '%%' + v['key'] + '%%'
                if marker in parsed:
                    span = make_vocab_span(v['key'], v.get('word', v['key']), v['cn'], v.get('de', ''))
                    parsed = parsed.replace(marker, span)
            html += '''          <p>{p}</p>\n'''.format(p=parsed)
        html += '''        </div>\n'''
        if 'summary' in t:
            html += '''        <div class="highlight-box">{s}</div>\n'''.format(s=t['summary'])
        html += '''      </div>\n'''

    html += '''    </section>\n'''
    return html

def gen_vocab(data):
    """Generate vocab section with cards"""
    html = '''    <section id="vocab">\n'''
    html += '''      <h2 class="section-title"><span class="num">2</span> ''' + data['meta']['sectionTitles']['vocab'] + '''</h2>\n'''

    # Group vocab by text
    groups = {}
    for i, t in enumerate(data['texts']):
        gid = 'T' + str(i+1)
        groups[gid] = {'title': 'T{num}'.format(num=i+1), 'items': []}

    # Find which text uses each vocab word
    for v in data['vocab']:
        # Simple: assign to first text that contains the key
        assigned = False
        for i, t in enumerate(data['texts']):
            gid = 'T' + str(i+1)
            key_marker = '%%' + v['key'] + '%%'
            for p in t['paragraphs']:
                if key_marker in p:
                    groups[gid]['items'].append(v)
                    assigned = True
                    break
            if assigned:
                break
        if not assigned:
            # Put in first group
            groups['T1']['items'].append(v)

    # Generate person tabs
    html += '''      <div class="person-tabs">\n'''
    first = True
    for gid, g in groups.items():
        if not g['items']:
            continue
        active = ' active' if first else ''
        html += '''        <button class="person-btn{active}" onclick="switchPerson('{gid}')">{title}</button>\n'''.format(active=active, gid=gid, title=g['title'])
        first = False
    html += '''      </div>\n'''

    # Generate vocab grids
    for gid, g in groups.items():
        if not g['items']:
            continue
        html += '''      <div class="person-content" id="vocab-{gid}">\n'''.format(gid=gid)
        html += '''        <div class="vocab-grid" id="vocab-grid-{gid}">\n'''.format(gid=gid)
        for v in g['items']:
            word = v.get('word', v['key'])
            cn = v['cn']
            de_ex = v.get('de', '')
            html += '''          <div class="vocab-card" onclick="this.classList.toggle('flipped')">\n'''
            html += '''            <div class="card-inner">\n'''
            html += '''              <div class="card-front">{w}</div>\n'''.format(w=word)
            html += '''              <div class="card-back">{cn}{de}</div>\n'''.format(cn=cn, de=('<br>' + de_ex if de_ex else ''))
            html += '''            </div>\n'''
            html += '''          </div>\n'''
        html += '''        </div>\n'''
        html += '''      </div>\n'''

    html += '''    </section>\n'''
    return html

def gen_grammar(data):
    """Generate grammar section"""
    html = '''    <section id="grammar">\n'''
    html += '''      <h2 class="section-title"><span class="num">3</span> ''' + data['meta']['sectionTitles']['grammar'] + '''</h2>\n'''

    for table in data['grammar']['tables']:
        html += '''      <div class="grammar-table-wrapper">\n'''
        html += '''        <h3>{t}</h3>\n'''.format(t=table['title'])
        html += '''        <table class="grammar-table">\n'''
        html += '''          <thead><tr>\n'''
        for h in table['headers']:
            html += '''            <th>{h}</th>\n'''.format(h=h)
        html += '''          </tr></thead>\n'''
        html += '''          <tbody>\n'''
        for row in table['rows']:
            html += '''            <tr>\n'''
            for cell in row:
                c_fixed = re.sub(r'%%([^%]+)%%', r'<strong>\1</strong>', cell)
                html += '''              <td>''' + c_fixed + '''</td>\n'''
            html += '''            </tr>\n'''
        html += '''          </tbody>\n'''
        html += '''        </table>\n'''
        html += '''      </div>\n'''

    if 'examples' in data['grammar']:
        html += '''      <div class="grammar-examples" style="margin-top:16px">\n'''
        html += '''        <h3>例句</h3>\n'''
        for ex in data['grammar']['examples']:
            html += '''        <div class="grammar-example">\n'''
            html += '''          <div class="de">{de}</div>\n'''.format(de=ex['de'])
            html += '''          <div class="zh">{zh}</div>\n'''.format(zh=ex['zh'])
            html += '''        </div>\n'''
        html += '''      </div>\n'''

    html += '''    </section>\n'''
    return html

def gen_exercise(data):
    """Generate exercise section with quiz and matching game"""
    html = '''    <section id="exercise">\n'''
    html += '''      <h2 class="section-title"><span class="num">4</span> ''' + data['meta']['sectionTitles']['exercise'] + '''</h2>\n'''

    # Quiz
    for i, q in enumerate(data['quiz']):
        n = i + 1
        html += '''      <div class="quiz-card">\n'''
        html += '''        <div class="q-text">{n}. {q}</div>\n'''.format(n=n, q=q['q'])
        html += '''        <div class="options">\n'''
        for j, opt in enumerate(q['options']):
            letter = chr(65 + j)  # A, B, C, D
            html += '''          <div class="opt" onclick="checkQuiz(this,{n},{j})">{letter}. {opt}</div>\n'''.format(n=n, j=j, letter=letter, opt=opt)
        html += '''        </div>\n'''
        html += '''        <div class="q-answer">答案：{ans}</div>\n'''.format(ans=q['answer'])
        html += '''        <button class="show-answer-btn" onclick="this.previousElementSibling.classList.toggle('show')">显示答案</button>\n'''
        html += '''      </div>\n'''

    # Matching game
    if data.get('matchingPairs'):
        html += '''      <div style="margin-top:24px">\n'''
        html += '''        <h3>词汇配对 · Wortpaare</h3>\n'''
        html += '''        <p class="zh" style="margin-bottom:8px">点击两张卡片配对德语词和中文释义</p>\n'''
        html += '''        <div id="match-game" style="max-width:600px;margin:0 auto">\n'''
        for n, (de, zh) in enumerate(data['matchingPairs']):
            idx = n + 1
            html += '''          <div class="match-card de" data-pair="{i}" onclick="matchClick(this)">{de}</div>\n'''.format(i=idx, de=de)
            html += '''          <div class="match-card zh" data-pair="{i}" onclick="matchClick(this)">{zh}</div>\n'''.format(i=idx, zh=zh)
        html += '''        </div>\n'''
        html += '''      </div>\n'''

    html += '''    </section>\n'''
    return html

def gen_vocab_data_js(data):
    """Generate the vocabData JS variable"""
    js = 'var vocabData = {\n'
    for i, t in enumerate(data['texts']):
        gid = 'T' + str(i+1)
        js += "  '{}': [\n".format(gid)
        for v in data['vocab']:
            assigned = False
            for p in t['paragraphs']:
                if '%%' + v['key'] + '%%' in p:
                    assigned = True
                    break
            if not assigned and i == 0:
                # Check if assigned to any text
                any_assigned = False
                for ti, tt in enumerate(data['texts']):
                    for p in tt['paragraphs']:
                        if '%%' + v['key'] + '%%' in p:
                            any_assigned = True
                            break
                if any_assigned:
                    continue
            if not assigned:
                continue
            word = v.get('word', v['key'])
            cn = escape_js(v['cn'])
            de_ex = escape_js(v.get('de', ''))
            de_ex = escape_js(v.get("de", ""))
            jsl = "    { word: " + chr(39) + escape_js(word) + chr(39) + ", cn: " + chr(39) + cn + chr(39) + ", de: " + chr(39) + de_ex + chr(39) + " },\n"
            js += jsl
            js += jsl
        js += "  ],\n"
    js += '};\n'
    return js

def gen_nav(data):
    """Generate navigation bar"""
    m = data['meta']
    labels = m.get('navLabels', ['首页','课文讲解','重点词汇','语法','练习'])
    sec_ids = ['home','text','vocab','grammar','exercise']
    html = '<nav>\n'
    html += '  <div class="top-nav">\n'
    html += '    <div class="logo" style="cursor:pointer" onclick="switchSection(\'home\')">\n'
    html += '      <span class="logo-icon">🎓</span>\n'
    html += '      <span>Lektion {lek}</span>\n'.format(lek=m['lektion'])
    html += '    </div>\n'
    html += '    <div class="nav-links" id="navLinks">\n'
    for sid, label in zip(sec_ids, labels):
        html += '      <button onclick="switchSection(\'{id}\')">{label}</button>\n'.format(id=sid, label=label)
    html += '    </div>\n'
    html += '    <button class="hamburger" onclick="toggleNav()">☰</button>\n'
    html += '  </div>\n'
    html += '</nav>\n'
    return html

def gen_test_txt(data):
    """Generate 学习通 format test .txt"""
    lines = []
    m = data['meta']
    lines.append('新经典德语 · 第二册 · Lektion {lek} 小测'.format(lek=m['lektion']))
    lines.append(m['title'])
    lines.append('')

    # Quiz
    quiz = data.get('quiz', [])
    n_quiz = len(quiz)
    total = n_quiz * 3
    lines.append('一、单选题（每题3分，共{}分）'.format(total))
    lines.append('')
    for i, q in enumerate(quiz):
        n = i + 1
        lines.append('{n}. {q}'.format(n=n, q=q['q']))
        for j, opt in enumerate(q['options']):
            letter = chr(65 + j)
            lines.append('{letter}. {opt}'.format(letter=letter, opt=opt))
        lines.append('答案：{ans}'.format(ans=q['answer']))
        lines.append('')

    if data.get('matchingPairs'):
        pairs = data['matchingPairs']
        n_pairs = len(pairs)
        total2 = n_pairs * 2
        lines.append('二、词汇配对（每题2分，共{}分）'.format(total2))
        lines.append('')
        for i, (de, zh) in enumerate(pairs):
            n = i + 1
            lines.append('{n}. {de}'.format(n=n, de=de))
            lines.append('答案：{zh}'.format(zh=zh))
            lines.append('')

    # Grammar fill
    lines.append('三、语法填空（每空2分，共10分）')
    lines.append('')
    lines.append('填入合适的并列连词(und/oder/aber/denn/sondern)：')
    lines.append('')
    lines.append('1. Ich möchte nicht studieren, ______ eine Ausbildung machen.')
    lines.append('答案：sondern')
    lines.append('')
    lines.append('2. Er lernt Deutsch, ______ er will in Berlin studieren.')
    lines.append('答案：denn')
    lines.append('')
    lines.append('3. Sie arbeitet gern in der Werkstatt, ______ ihr Kollege lieber im Büro.')
    lines.append('答案：aber')
    lines.append('')
    lines.append('4. Möchtest du Ingenieur ______ Arzt werden?')
    lines.append('答案：oder')
    lines.append('')
    lines.append('5. Er macht eine Ausbildung ______ sammelt praktische Erfahrung.')
    lines.append('答案：und')

    return '\n'.join(lines)

def build(data_file):
    """Main build function"""
    dir_path = os.path.dirname(os.path.abspath(__file__))
    
    with open(data_file, encoding='utf-8') as f:
        data = json.load(f)
    
    m = data['meta']
    base_name = os.path.splitext(os.path.basename(data_file))[0]
    
    # Load template parts
    css = load_template('template_css.css')
    nav = gen_nav(data)
    js_raw = load_template('template_js.js')
    
    # Generate sections
    home = gen_home(data)
    text = gen_text(data)
    vocab = gen_vocab(data)
    grammar = gen_grammar(data)
    exercise = gen_exercise(data)
    
    # Generate vocab data JS
    vocab_data_js = gen_vocab_data_js(data)
    
    # Clean up template CSS (add new rules)
    # Add answer toggle CSS if not present
    if '.q-answer{display:none' not in css.replace(' ', ''):
        css = css.replace('</style>', '\n  .q-answer{display:none;margin-top:8px;padding:6px 12px;background:#f0f7ff;border-radius:6px;font-size:14px;color:var(--primary);font-weight:600;text-align:center}\n  .q-answer.show{display:block}\n  .show-answer-btn{display:block;margin:6px auto 0;padding:4px 14px;background:var(--primary);color:#fff;border:none;border-radius:6px;font-size:13px;cursor:pointer}\n</style>')

    # Assemble final HTML
    html = '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n'
    html += '<meta charset="UTF-8">\n'
    html += '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
    html += '<title>Lektion {lek} · {title} · 交互式课件</title>\n'.format(lek=m['lektion'], title=m['title'])
    html += css
    html += '</head>\n<body data-lektion="L' + str(m['lektion']) + '">\n'
    html += nav
    html += '\n<div class="main">\n<div class="container">\n<div class="text-cards">\n'
    html += home
    html += text
    html += vocab
    html += grammar
    html += exercise
    html += '</div>\n</div>\n</div>\n'
    html += '<div class="vocab-panel" id="vocabPanel">\n'
    html += '  <div class="vocab-panel-header">\n'
    html += '    <span id="vocabPanelWord" class="vocab-panel-word"></span>\n'
    html += '    <button onclick="hideVocab()" style="background:none;border:none;font-size:20px;cursor:pointer;color:#999">&times;</button>\n'
    html += '  </div>\n'
    html += '  <div id="vocabPanelCN" class="vocab-panel-cn"></div>\n'
    html += '  <div id="vocabPanelDE" class="vocab-panel-de"></div>\n'
    html += '</div>\n'
    html += '<div class="vocab-overlay" id="vocabOverlay" onclick="hideVocab()"></div>\n'
    html += '<script>\n'
    html += vocab_data_js
    html += '\n'
    html += js_raw
    html += '</script>\n'
    html += '</body>\n</html>\n'

    # Write HTML
    out_html = os.path.join(dir_path, base_name + '.html')
    with open(out_html, 'w', encoding='utf-8') as f:
        f.write(html)
    
    # Write test
    test = gen_test_txt(data)
    out_txt = os.path.join(dir_path, base_name + '-test.txt')
    with open(out_txt, 'w', encoding='utf-8') as f:
        f.write(test)
    
    print(f'✅ Generated: {out_html} ({len(html)} bytes)')
    print(f'✅ Generated: {out_txt} ({len(test)} bytes)')
    
    # Verify
    import subprocess
    js_start = html.find('<script>') 
    js_end = html.rfind('</script>')
    if js_start >= 0 and js_end >= 0:
        js_only = html[js_start+8:js_end]
        r = subprocess.run(['node', '-e',
            'try{require("vm").compileFunction(JSON.parse(process.argv[1]));console.log("OK")}catch(e){console.log(e.message.substring(0,80))}',
            json.dumps(js_only)], capture_output=True, text=True, timeout=5)
        print(f'JS: {r.stdout.strip() or r.stderr[:80]}')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: python3 build.py <data.json>')
        sys.exit(1)
    build(sys.argv[1])
