#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""l1_make_data.py — 把 Lektion 1 的既有数据源汇总成互动课件要用的四个 JSON

数据源（均在 workspace-main/tools/）：
  l1_unterricht_data.py  —— 八个词场 / 构词线索 / 句型库 9 条 / 语法六讲
  l1_unterricht_tasks.py —— 学以致用 A–E（介词填空 / 改写 / 中译德 / 采访）
  modul1_jiaoan_vocab.py —— 教材词表 Vokabeln 1-6（S.18）/ 1-9（S.29）共 77 词
课文原文：archive/german-teaching/lektion1-texte/texte-verbatim.md（逐字）
输出：
  l1-data.json     课文 + 词卡 + 语法 + 连线 + 填空 + 快问快答 + 翻译卡
  l1-vocab.json    词场表 + 句型库 + 搭配连线 + 练习 9 完形 + 学以致用造句
  l1-text-zh.json  课文逐句参考译文（键 = 德文原句）
  l1-vocab-zh.json 词场例句参考译文（键 = 教材例句）
"""
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = '/home/gem/workspace/agent/workspace-main/tools'
sys.path.insert(0, HERE)

import l1_sents as LS
import l1_text_src as SRC
from l1_zh_src import T1_ZH, T2_ZH


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


D = load(os.path.join(TOOLS, 'l1_unterricht_data.py'), 'l1d')
T = load(os.path.join(TOOLS, 'l1_unterricht_tasks.py'), 'l1t')
V = load(os.path.join(TOOLS, 'modul1_jiaoan_vocab.py'), 'l1v')

SENTS = LS.all_sentences()
assert len(SENTS['t1']) == len(T1_ZH), 'T1 译文条数 %d ≠ 句子数 %d' % (len(T1_ZH), len(SENTS['t1']))
assert len(SENTS['t2']) == len(T2_ZH), 'T2 译文条数 %d ≠ 句子数 %d' % (len(T2_ZH), len(SENTS['t2']))
ZH = {k: dict(zip(SENTS[k], (T1_ZH if k == 't1' else T2_ZH))) for k in ('t1', 't2')}

# ───────────────────────────────────────── 词场 / 词条
ROW_KEYS = ('w', 'cn', 'coll', 'ex', 'exZh', 'src')


def wf_rows(group):
    return [dict(zip(ROW_KEYS, r[:6])) for r in group['rows']]


WORTFELDER = [{'id': g['no'], 'label': '%s %s' % (g['no'], g['title']), 'lead': g['sub'],
               'src': ' · '.join(dict.fromkeys([x['src'] for x in wf_rows(g)])),
               'rows': wf_rows(g)} for g in D.WORTFELDER]

ROW_BY_KEY = {r['w']: r for g in WORTFELDER for r in g['rows']}

# ───────────────────────────────────────── 点词查义（自动标注：按 forms 在课文里命中）
# 值 = 该词条在课文里出现的形态；空列表 = 不在课文里出现，不参与标注
FORMS = {
    # W1 童年与时代
    'die Kindheit, -en': ['Kindheit'],
    'die Nachkriegszeit': ['Nachkriegszeit'],
    'der Krieg, -e': ['Krieg'],
    'die Armut': ['Armut'],
    'die Trümmer (Pl.)': ['Trümmer'],
    'das Wirtschaftswunder': ['Wirtschaftswunder'],
    'die Generation, -en': ['Generation'],
    'auf|wachsen': ['aufwächst', 'aufgewachsen'],
    'geprägt sein von + D': ['geprägt'],
    # W2 家庭与生计
    'der Handwerksbetrieb, -e': ['Handwerksbetrieb'],
    'die Versorgung': ['Versorgung'],
    'die Auslandsreise, -n': ['Auslandsreise'],
    'der Ausflug, ¨-e': ['Ausflüge'],
    'selbstgebaut': ['selbstgebauten', 'selbstgebaute'],
    'sich kümmern um + A': ['kümmern'],
    'besuchen': ['besuchen', 'besucht'],
    'beschäftigt sein': ['beschäftigt'],
    'halbtags arbeiten': ['halbtags'],
    'alle Hände voll zu tun haben': ['alle Hände voll zu tun'],
    'keinen Boden unter den Füßen haben': ['keinen Boden unter den Füßen'],
    # W3 安全与自由
    'die Sicherheit': ['Sicherheit'],
    'der Sicherheitsgurt, -e': ['Sicherheitsgurte'],
    'die Kindersicherung, -en': ['Kindersicherung'],
    'die Steckdose, -n': ['Steckdosen'],
    'der Helm, -e': ['Helm'],
    'die Seifenkiste, -n': ['Seifenkisten'],
    'die Bremse, -n': ['Bremse'],
    'die Freiheit': ['Freiheit'],
    'auf eigenen Beinen stehen': ['auf eigenen Beinen stehen'],
    'feststellen': ['feststellen'],
    'auf die leichte Schulter nehmen': ['auf die leichte Schulter genommen'],
    'Angst haben, dass …': ['Angst'],
    # W4 学校与教育
    'die Disziplin': ['Disziplin'],
    'die Gehorsamkeit': ['Gehorsamkeit'],
    'die Ohrfeige, -n': ['Ohrfeigen'],
    'selbstständig': ['selbstständig'],
    'fordern': ['gefordert'],
    'entwickeln': ['entwickeln'],
    'überprüfen': ['überprüfen'],
    'vermitteln': ['vermitteln'],
    'sich auszeichnen durch + A': ['auszeichnet'],
    'bestrebt sein, etw. zu tun': ['bestrebt'],
    'keine Seltenheit sein': ['Seltenheit'],
    # W5 课余与朋友
    'die Streiterei, -en': ['Streitereien'],
    'klären': ['klären'],
    'die Verabredung, -en': ['Verabredungen'],
    'vereinbaren': ['vereinbart'],
    'der Treffpunkt, -e': ['Treffpunkten'],
    'das Brettspiel, -e': ['Brettspiele'],
    'unvorstellbar': ['unvorstellbar'],
    'der Baustein, -e': ['Bausteinen'],
    'die Puppe, -n': ['Puppen'],
    'ins Freie gehen': ['ins Freie'],
    # W6 阅读与想象
    'die Detektivgeschichte, -n': ['Detektivgeschichten'],
    'das Heft, -e': ['Hefte'],
    'lesen': ['lese', 'lesen'],
    'die Magie': ['Magie'],
    'die magische Welt': ['magischen Welt'],
    'die Freizeit': ['Freizeit'],
    'träumen von + D': ['träume'],
    'bekommen': ['bekommen'],
    # W7 幸福与感受
    'das Glück': ['Glück'],
    'glücklich': ['glückliche', 'glücklich'],
    'das Glücksgefühl, -e': ['Glücksgefühl', 'Glücksgefühle'],
    'die Entscheidung, -en': ['Entscheidungen'],
    'streben nach + D': ['streben'],
    'vorübergehend': ['vorübergehend'],
    'der Traum, ¨-e': ['Traum'],
    'entfalten': ['entfalten'],
    'auslösen': ['auslöst'],
    # W8 关系与社会
    'die Beziehung, -en': ['Beziehungen', 'Beziehung'],
    'die Harmonie': ['Harmonie'],
    'der Kollege, -n': ['Kollegen'],
    'der Nachbar, -n': ['Nachbarn'],
    'die Zufallsbegegnung, -en': ['Zufallsbegegnungen'],
    'das Schicksal': ['Schicksal'],
    'verknüpft sein mit + D': ['verknüpft'],
    'der Mitbürger, -': ['Mitbürger'],
    'der Frieden': ['Frieden'],
    'die Einstellung, -en': ['Einstellung'],
    'herrschen': ['herrscht'],
    'die Selbstverwirklichung': ['Selbstverwirklichung'],
    'die Zugehörigkeit': ['Zugehörigkeit'],
    'sich auswirken auf + A': ['auswirken'],
    'zusammen|hängen mit + D': ['zusammenhängen'],
}

# 词场没覆盖、但课文里值得点开的词（本次新写释义与搭配；出处即课文原句）
EXTRA_GLOSS = [
    ('die Realschule, -n', '实科中学', ['Realschule'], 'eine Realschule besuchen'),
    ('das Elektrogeschäft, -e', '电器店', ['Elektrogeschäft'], 'in einem Elektrogeschäft arbeiten'),
    ('die Zahnarztpraxis, -praxen', '牙科诊所', ['Zahnarztpraxis'], 'in einer Zahnarztpraxis arbeiten'),
    ('die Kita, -s', '幼儿园（Kindertagesstätte 的简称）', ['Kita'], 'zur Kita gebracht werden'),
    ('das Glücksempfinden', '幸福感（感受本身）', ['Glücksempfinden'], 'das Glücksempfinden beeinflussen'),
    ('erläutern', '解释，说明', ['erläutern'], 'etwas näher erläutern'),
    ('umfassend', '全面的，广泛的', ['umfassende'], 'eine umfassende Frage'),
    ('prosperierend', '繁荣的', ['prosperierenden'], 'in einem prosperierenden Land'),
    ('die Wahrnehmung, -en', '感知；看法', ['Wahrnehmung'], 'eine Wahrnehmung beeinflusst das Glück'),
    ('die Pflege', '维护，照料（无复数）', ['Pflege'], 'die Pflege menschlicher Beziehungen'),
    ('die Paarbeziehung, -en', '伴侣关系', ['Paarbeziehungen'], 'eine Paarbeziehung'),
    ('der Kulturkreis, -e', '文化圈', ['Kulturkreise', 'Kulturkreisen'], 'aus anderen Kulturkreisen'),
]


def sent_index():
    """把句子按序号登记，供翻译卡与例句抽取引用"""
    return {k: {i + 1: s for i, s in enumerate(SENTS[k])} for k in ('t1', 't2')}


IDX = sent_index()


def zh_of(key, n):
    return ZH[key][IDX[key][n]]


def build_glossar():
    out = []
    for g in WORTFELDER:
        for r in g['rows']:
            forms = FORMS.get(r['w'])
            if not forms:
                continue
            out.append({'w': r['w'], 'zh': r['cn'], 'forms': forms,
                        'ex': r['ex'], 'def': r['coll']})
    for w, zh, forms, coll in EXTRA_GLOSS:
        ex = next((s for k in ('t1', 't2') for s in SENTS[k] if any(f in s for f in forms)), '')
        out.append({'w': w, 'zh': zh, 'forms': forms, 'ex': ex, 'def': coll})
    return out


GLOSS_T1 = [e for e in build_glossar()
            if any(f in ' '.join(SENTS['t1']) for f in e['forms'])]
GLOSS_T2 = [e for e in build_glossar()
            if any(f in ' '.join(SENTS['t2']) for f in e['forms'])]

# ───────────────────────────────────────── 课文 JSON
T1_STRUCTURE = [
    ('①', 'Familie und Arbeit', '家庭与工作：Oma 讲战前的手工作坊与母亲打工，Emilie 讲父母的职业与周末安排'),
    ('②', 'Sicherheit', '安全：Oma 讲当年没人管孩子的安全，Emilie 讲父母管得太紧、自己没有自由'),
    ('③', 'Schule', '学校：过去要求纪律与服从、体罚常见；今天要求独立思考，老师鼓励提问'),
    ('④', 'Freizeit und Freunde', '课余与朋友：过去放学就在街上、自己约玩；今天大量用数字媒体，也爱桌游和户外'),
    ('⑤', 'Lesen', '阅读：过去书很少，一本米老鼠小册子就是宝贝；今天读侦探、小马和哈利·波特'),
    ('⑥', 'Sonntag und Glück', '星期天与幸福：过去一家人散步、去教堂就是幸福；今天能做自己的决定、家庭出游让她幸福'),
]
T1_QUOTES = [
    ('①', 'S.14 · Oma', 10, '母亲忙得团团转：alle Hände voll zu tun 是这一课最好用的惯用语之一。'),
    ('②', 'S.14 · Oma', 19, '「没当回事」：auf die leichte Schulter nehmen，后面常跟第四格宾语。'),
    ('②', 'S.14 · Emilie', 28, 'wann 开头的反问句，语气是抱怨而不是真在问时间。'),
    ('③', 'S.14 · Emilie', 33, 'sein + zu + Infinitiv：不说谁做，把任务挂到「想法」上。'),
    ('④', 'S.15 · Oma', 38, 'sich lassen + Infinitiv：不说谁解决，说「可以自己解决」。'),
    ('⑥', 'S.15 · Emilie', 54, 'was 引导的主语从句：Was bedeutet Glück für mich?'),
]
T2_STRUCTURE = [
    ('1', 'Einstieg', '开场与核心问题：Was macht einen Menschen glücklich?'),
    ('2', 'Generationen', '代际对比：过去简单生活就够，今天要得越来越多'),
    ('3', 'Kultur', '文化差异：63 国研究，西方重个人成就，东亚重和谐'),
    ('4', 'Harmonie', '什么叫「和谐」：牢固积极的关系带来联结感与归属感'),
    ('5', 'China', '中国的答案：个人幸福与国家命运相连，个人也能反过来影响幸福'),
]
T2_QUOTES = [
    ('1', 'S.25 · Prof. Liu', 8, 'Wer 引导的主语从句 = 「凡是……的人」，与 was 从句形成人/事对照。'),
    ('2', 'S.25 · Lukas', 12, 'je + 比较级, desto + 比较级：拥有的越多，想要的越多。'),
    ('3', 'S.25 · Prof. Liu', 21, 'gelten als：被视为……。注意 als 后面的格与主格一致。'),
    ('4', 'S.26 · Prof. Liu', 27, 'sich auswirken auf + A：对……产生影响，主语常是某事物。'),
    ('4', 'S.26 · Prof. Liu', 28, 'ebenso … wie：和……一样；这里是全课的对比句型总收口。'),
    ('5', 'S.26 · Prof. Liu', 39, 'verknüpft sein mit + D：与……紧密相连。'),
]

T1 = {
    'title': 'Kindheit seit den 50er Jahren des 20. Jahrhunderts bis heute',
    'kind': 'Text 1', 'sub': '两代人的童年 · 双声部对照', 'page_note': 'S.13–S.15',
    'lead': '课文是双声部：Oma（战后一代）与 Emilie（Z 世代）就同一组话题各说一段，教材用 ①–⑥ 切成六格。'
            '读的时候盯住一件事：同一件事，两代人是怎么说的。',
    'provenance': '课文逐字取自教材 S.13–S.15（含 Landeskunde 小框），页码与段落号可翻书核对。',
    'intro': [{'who': w, 'sents': LS.split_sents(t)} for w, t in SRC.T1_INTRO],
    'blocks': [{'no': b['no'], 'page': b['page'], 'topic': b['topic'],
                'oma': LS.split_sents(b['oma']), 'emilie': LS.split_sents(b['emilie'])}
               for b in SRC.T1_BLOCKS],
    'landeskunde': LS.split_sents(SRC.T1_LANDESKUNDE),
    'structure': [{'n': n, 'de': de, 'cn': cn} for n, de, cn in T1_STRUCTURE],
    'quotes': [{'n': '段落 %s' % n, 'src': src, 'de': SENTS['t1'][i - 1],
                'zh': zh_of('t1', i), 'tip': tip} for n, src, i, tip in T1_QUOTES],
    'glossar': GLOSS_T1,
}

T2 = {
    'title': 'Was macht einen Menschen glücklich?',
    'kind': 'Text 2', 'sub': '专访 · 关于幸福的采访', 'page_note': 'S.25–S.26',
    'lead': '交换生 Lukas 采访心理学专家刘教授。课文分五步推进：核心问题 → 代际差别 → 文化差别 → '
            '「和谐」到底指什么 → 中国的答案。',
    'provenance': '课文逐字取自教材 S.25–S.26（练习 9 的五个空已按上下文填入，非教材答案页，见本节末尾说明）。',
    'lead_sents': LS.split_sents(SRC.T2_LEAD),
    'dialogue': [{'who': w, 'sents': LS.split_sents(t)} for w, t in LS.t2_sources()],
    'structure': [{'n': n, 'de': de, 'cn': cn} for n, de, cn in T2_STRUCTURE],
    'quotes': [{'n': '第 %s 步' % n, 'src': src, 'de': SENTS['t2'][i - 1],
                'zh': zh_of('t2', i), 'tip': tip} for n, src, i, tip in T2_QUOTES],
    'glossar': GLOSS_T2,
}

# ───────────────────────────────────────── 词卡（教材词表 77 词）
VOCAB_GROUPS = [
    {'label': '📘 Vokabeln 1-6', 'src': V.L1A[1],
     'words': [{'w': w, 'cn': cn} for w, cn in V.L1A[2]]},
    {'label': '📗 Vokabeln 1-9', 'src': V.L1B[1],
     'words': [{'w': w, 'cn': cn} for w, cn in V.L1B[2]]},
]

# ───────────────────────────────────────── 语法六讲
GRAMMAR_UNITS = [{
    'no': u['no'], 'title': u['title'], 'want': u['want'], 'rule': u['rule'],
    'steps': u['steps'],
    'ex': [{'de': e[0], 'zh': e[1], 'src': e[2]} for e in u['ex']],
    'wrong': [{'bad': w[0], 'good': w[1]} for w in u['wrong']],
    'quiz': [{'q': q[0], 'a': q[1]} for q in u['quiz']],
} for u in D.GRAMMATIK]

# ───────────────────────────────────────── 连线（教材原文里能背下来的整块）
def clean(w):
    w = re.sub(r',\s*[¨\-][A-Za-z\-]*\s*$', '', w)          # 去掉复数/变音标注
    w = re.sub(r'\s*\([^()]*\)\s*$', '', w)
    return w.strip()


CONNECT = [
    {'title': '① Omas童年 · 关键词', 'src': '教材 S.13–S.15 · 词场 W1–W2',
     'pairs': [[clean(ROW_BY_KEY[k]['w']), ROW_BY_KEY[k]['cn'].split('（')[0]]
               for k in ('die Nachkriegszeit', 'das Wirtschaftswunder', 'die Trümmer (Pl.)',
                         'der Handwerksbetrieb, -e', 'die Versorgung', 'die Auslandsreise, -n',
                         'der Ausflug, ¨-e', 'alle Hände voll zu tun haben',
                         'keinen Boden unter den Füßen haben', 'die Armut')]},
    {'title': '② 安全与学校 · 关键词', 'src': '教材 S.14 · 词场 W3–W4',
     'pairs': [[clean(ROW_BY_KEY[k]['w']), ROW_BY_KEY[k]['cn'].split('（')[0]]
               for k in ('die Sicherheit', 'der Helm, -e', 'die Seifenkiste, -n',
                         'die Bremse, -n', 'auf eigenen Beinen stehen', 'die Disziplin',
                         'die Gehorsamkeit', 'die Ohrfeige, -n', 'sich auszeichnen durch + A',
                         'auf die leichte Schulter nehmen')]},
    {'title': '③ 幸福与关系 · 关键词', 'src': '教材 S.25–S.26 · 词场 W7–W8',
     'pairs': [[clean(ROW_BY_KEY[k]['w']), ROW_BY_KEY[k]['cn'].split('（')[0]]
               for k in ('das Glücksgefühl, -e', 'die Beziehung, -en', 'die Harmonie',
                         'die Zufallsbegegnung, -en', 'die Zugehörigkeit',
                         'die Selbstverwirklichung', 'die Einstellung, -en',
                         'das Schicksal', 'sich auswirken auf + A',
                         'zusammen|hängen mit + D')]},
    {'title': '④ 构词 · 形容词/动词 → 名词', 'src': '教材 Lektion 1 · G1（-heit / -keit / -ung）',
     'pairs': [['sicher', 'die Sicherheit'], ['kindlich → Kind', 'die Kindheit'],
               ['möglich', 'die Möglichkeit'], ['freundlich', 'die Freundlichkeit'],
               ['offen', 'die Offenheit'], ['zufrieden', 'die Zufriedenheit'],
               ['entscheiden', 'die Entscheidung'], ['versorgen', 'die Versorgung'],
               ['erleben', 'das Erlebnis'], ['gehören', 'die Zugehörigkeit']]},
]

# ───────────────────────────────────────── 介词与连词填空（学以致用 B）
B_TIP = {
    1: 'geprägt sein von + 第三格', 2: 'sich kümmern um + 第四格', 3: 'Angst haben, dass … 从句连词',
    4: 'sich heraushalten aus + 第三格', 5: 'sich auszeichnen durch + 第四格',
    6: 'Spaß an + 第三格（an + dem = am）', 7: 'streben nach + 第三格',
    8: 'sich auswirken auf + 第四格', 9: 'verknüpft sein mit + 第三格',
    10: 'zusammenhängen mit + 第三格', 11: 'es kommt auf + 第四格 an',
    12: 'lassen 后接不带 zu 的不定式',
}
LUECKEN = {
    'title': '介词与连词填空 · Präpositionen ergänzen',
    'src': '教材 Lektion 1 · 介词搭配练习（本页自编，答案在附录 C）',
    'instruction': '每空填一个词。这一课最容易丢分的就是介词：填完把整句读一遍再核对。',
    'items': [{'de': d, 'ans': a.split(' ', 1)[1], 'zh': B_TIP[i]}
              for i, (d, a) in enumerate(zip(T.AUFGABE_B['items'], T.AUFGABE_B['answer']), 1)],
}

# ───────────────────────────────────────── 快问快答（课文理解）
QUIZ = {
    'title': '快问快答 · Textverständnis',
    'src': '教材 S.13–S.15 / S.25–S.26 · Text 1 / Text 2（改编）',
    'instruction': '读题后先自己答，再点选项。全是课文里的信息，答不出就回去点那一句的译文。',
    'items': [
        {'q': 'Wovon war Omas Kindheit geprägt?',
         'opts': ['von der Nachkriegszeit, Armut und Trümmern',
                  'von der Generation Z und dem Smartphone',
                  'von Auslandsreisen und Brettspielen',
                  'von einer modernen Schule mit jungen Lehrern'], 'a': 0},
        {'q': 'Was musste Omas Vater nach dem Krieg aufgeben?',
         'opts': ['seinen eigenen Handwerksbetrieb', 'seine Wohnung',
                  'sein Studium', 'seine Stelle als Manager'], 'a': 0},
        {'q': 'Was war laut Oma früher mit der Sicherheit der Kinder?',
         'opts': ['Sie wurde auf die leichte Schulter genommen.',
                  'Sie stand im Mittelpunkt der Erziehung.',
                  'Sie war gesetzlich genau geregelt.',
                  'Sie kümmerte niemanden, weil es keine Kinder gab.'], 'a': 0},
        {'q': 'Worüber ärgert sich Emilie?',
         'opts': ['Ihre Eltern kümmern sich zu sehr um sie.',
                  'Ihre Eltern interessieren sich nicht für sie.',
                  'Ihre Lehrerin ist zu streng.',
                  'Sie hat zu wenige Bücher.'], 'a': 0},
        {'q': 'Wie war der Unterricht laut Oma?',
         'opts': ['Disziplin und Gehorsamkeit waren gefordert.',
                  'Die Schüler durften selbstständig nachdenken.',
                  'Es gab keine Hausaufgaben.',
                  'Nur Mädchen mussten still sitzen.'], 'a': 0},
        {'q': 'Was ist Emilie an ihrer Lehrerin wichtig?',
         'opts': ['Offenheit, Freundlichkeit und Aufgeschlossenheit',
                  'Strenge und Disziplin',
                  'dass sie keine Fehler korrigiert',
                  'dass sie jeden Tag Prüfungen schreibt'], 'a': 0},
        {'q': 'Wie verabredeten sich Oma und ihre Freunde?',
         'opts': ['untereinander in der Schule oder an festen Treffpunkten',
                  'über die Eltern per Brief',
                  'nur über das Telefon',
                  'über soziale Netzwerke'], 'a': 0},
        {'q': 'Was bedeutet Glück für Emilie?',
         'opts': ['die Freiheit, selbständige Entscheidungen treffen zu können',
                  'möglichst viele Auslandsreisen',
                  'der beste Schulabschluss',
                  'jeden Tag bei den Großeltern zu sein'], 'a': 0},
        {'q': 'Was ist laut Frau Prof. Liu in westlichen Ländern die verbreitete Einstellung?',
         'opts': ['Glücksgefühle hängen mehr mit persönlichem Erfolg zusammen.',
                  'Glück kommt allein von der Familie.',
                  'Glück ist eine Frage des Wetters.',
                  'Nur Harmonie mit anderen macht glücklich.'], 'a': 0},
        {'q': 'Was versteht Frau Prof. Liu unter „Harmonie“?',
         'opts': ['starke und positive Beziehungen, die Verbundenheit und Zugehörigkeit vermitteln',
                  'möglichst wenig Kontakt zu Nachbarn',
                  'Erfolg im Beruf über alles',
                  'die Suche nach dem eigenen Vorteil'], 'a': 0},
        {'q': 'Womit ist das persönliche Glück in China eng verknüpft?',
         'opts': ['mit dem Schicksal des Landes', 'mit dem Wetter',
                  'mit dem Auslandsstudium', 'mit der Anzahl der Freunde'], 'a': 0},
        {'q': 'Welche Wege zum Glück nennt Frau Prof. Liu?',
         'opts': ['Musik hören, Sport treiben und gute soziale Beziehungen',
                  'mehr Geld verdienen und mehr besitzen',
                  'möglichst viele Reisen',
                  'Fernsehen und Computerspiele'], 'a': 0},
    ],
}

# ───────────────────────────────────────── 翻译卡（课文原句，先自己译再翻面）
TRANS_PICKS = [
    ('t1', 2, 'geprägt sein von + D：被动里的「被……塑造」', 'S.13 · Oma'),
    ('t1', 10, 'alle Hände voll zu tun haben：固定搭配，主语是人', 'S.14 ① · Oma'),
    ('t1', 19, 'wurde … genommen：被动过去时；auf die leichte Schulter nehmen', 'S.14 ② · Oma'),
    ('t1', 20, 'sich lassen + Infinitiv：不说谁做，只说「可以」', 'S.14 ② · Oma'),
    ('t1', 27, 'Angst haben, dass …：dass 从句动词到句末', 'S.14 ② · Emilie'),
    ('t1', 33, 'sein + zu + Infinitiv：把任务挂到「想法」上（必须/可以）', 'S.14 ③ · Oma'),
    ('t1', 34, 'einzig und allein：加强语气，说话的权利只属于老师', 'S.14 ③ · Oma'),
    ('t1', 38, 'sich lassen + Infinitiv 的过去时 ließen sich：可以自己解决', 'S.15 ④ · Oma'),
    ('t1', 52, 'großes Glück war … gehabt zu haben：完成不定式', 'S.15 ⑥ · Oma'),
    ('t2', 8, 'wer 引导主语从句 = 「凡是……的人」', 'S.25 · Prof. Liu'),
    ('t2', 12, 'je + 比较级, desto + 比较级', 'S.25 · Lukas'),
    ('t2', 19, 'Es wurde gezeigt, dass …：无人称被动 + dass 从句', 'S.25 · Prof. Liu'),
    ('t2', 27, 'sich auswirken auf + A：对……产生影响', 'S.26 · Prof. Liu'),
    ('t2', 28, 'ebenso … wie：和……一样；全课的对比句型收口', 'S.26 · Prof. Liu'),
    ('t2', 40, 'verknüpft sein mit + D：与……紧密相连', 'S.26 · Prof. Liu'),
]
TRANSLATION = {
    'title': '翻译卡 · Übersetzen',
    'instruction': '先自己把德文译成中文，再点卡片翻面核对。翻面之前别急着点。',
    'note': '卡片全部是课文原句，出处写在正面；背面是参考译文，写法不唯一，意思对即可。',
    'cards': [{'de': IDX[k][n], 'zh': zh_of(k, n), 'tip': tip, 'src': src}
              for k, n, tip, src in TRANS_PICKS],
}

# ───────────────────────────────────────── 元信息
META = {
    'lektion': '1',
    'title': 'Rund um das Glück',
    'subtitle': 'Lektion 1 · 童年与幸福 · Text 1 两代人的童年 · Text 2 关于幸福的采访',
    'source': '《新经典德语》Modul 1 · Lektion 1 „Rund um das Glück“（Text 1 S.13–S.15 · Text 2 S.25–S.26）',
    'objectives': [
        '读懂双声部课文：Oma 与 Emilie 就家庭、安全、学校、课余、阅读、幸福六件事各说一段',
        '读懂一篇采访：核心问题 → 代际 → 文化 → 和谐 → 中国，五步推进',
        '用 geprägt sein von / sich lassen / sein + zu / 关系从句 / wer-was 从句说自己的事',
        '掌握本课 16 条介词搭配，写句子时不丢介词',
        '能用 -heit / -keit / -ung 把一个形容词或动词变成名词（sicher → die Sicherheit）',
    ],
    'flow': [
        '📖 课文 T1：先读两代人的童年，卡住了点句子看译文，点虚线词看释义与例句',
        '👤 课文 T2：读访谈，按五步抓脉络（练习 9 的五个空已按上下文填入）',
        '🃏 词汇：八个词场（含搭配与教材例句）+ 教材词表 77 词快速过词',
        '🧩 句型库：九条句型，每条骨架 + 三句例句 + 换槽练习 + 常见错法',
        '🔤 语法六讲：每讲四件事（想干什么 → 一句话规则 → 三步 → 三十秒自测）',
        '🔗 连线 + ✍️ 填空 + ✍️ 学以致用 + ✅ 快问快答 + 🎯 翻译卡：五轮检验与巩固',
    ],
}

DATA = {
    'meta': META, 't1': T1, 't2': T2,
    'vocab': {'src': '教材 Lektion 1 · Vokabeln 1-6（S.18）+ Vokabeln 1-9（S.29），共 77 词',
              'groups': VOCAB_GROUPS},
    'grammar': {'units': GRAMMAR_UNITS},
    'connectGrids': CONNECT,
    'luecken': LUECKEN,
    'quiz': QUIZ,
    'translation': TRANSLATION,
}

# ───────────────────────────────────────── l1-vocab.json（词场 + 句型 + 完形 + 造句）
SM_GROUP = [
    ('sm-1', 'A · 说「什么塑造了谁」与「和……一样」',
     ['geprägt sein von + D', 'ebenso … wie / anders als … / im Gegensatz zu + D']),
    ('sm-2', 'B · 不说谁做：两种被动替代', ['sich lassen + Infinitiv', 'sein + zu + Infinitiv']),
    ('sm-3', 'C · 从句与固定搭配', ['关系从句：名词 + der/die/das …', 'wer … / was …（主语从句）',
                                   'je + 比较级 …, desto + 比较级 …', 'es kommt auf + A an',
                                   'sich auswirken auf + A']),
]
SM_BY_PATTERN = {s['pattern']: s for s in D.SATZMUSTER}
SATZMUSTER_GROUPS = [{
    'id': gid, 'label': lab, 'src': '教材 Lektion 1 · Text 1（S.13–S.15）/ Text 2（S.25–S.26）',
    'note': '每条给四样：骨架（方括号可换）、用法（什么时候说这句）、三句例句（带出处）、以及常错的地方。',
    'items': [{
        'no': SM_BY_PATTERN[p]['no'], 'pattern': SM_BY_PATTERN[p]['pattern'],
        'fn': SM_BY_PATTERN[p]['fn'], 'use': SM_BY_PATTERN[p]['use'],
        'ex': [{'de': e[0], 'zh': e[1], 'src': e[2]} for e in SM_BY_PATTERN[p]['ex']],
        'slots': [{'de': s[0], 'zh': s[1]} for s in SM_BY_PATTERN[p]['slots']],
        'wrong': [{'bad': w[0], 'good': w[1]} for w in SM_BY_PATTERN[p]['wrong']],
    } for p in pats],
} for gid, lab, pats in SM_GROUP]

# 语序工坊：句子全部取自课文原句（键 = 课文位置，词块 = 手工切分，拼接必须逐字等于原句）
WERKSTATT = [
    ('t1', 2, '课文 · Oma', '我的童年是被战后岁月塑造的，只有贫穷、废墟，以及学校和家庭里的暴力经历。',
     ['Meine Kindheit', 'war', 'von der Nachkriegszeit', 'geprägt,', 'nur Armut, Trümmer, Gewalterfahrung',
      'in Schule und Familie.']),
    ('t1', 10, '课文 · Oma', '她忙得不可开交。',
     ['Sie', 'hatte', 'alle Hände voll', 'zu tun.']),
    ('t1', 19, '课文 · Oma', '过去人们没把孩子的安全当回事。',
     ['Die Sicherheit der Kinder', 'wurde', 'früher', 'auf die leichte Schulter', 'genommen.']),
    ('t1', 34, '课文 · Emilie', '自己的观点要去发展、去检验。',
     ['Eigene Ideen', 'sind', 'zu entwickeln', 'und', 'zu überprüfen.']),
    ('t1', 38, '课文 · Oma', '我们放学后大多离开家，一整天待在街上。',
     ['Wir', 'verließen', 'meist nach der Schule', 'die Wohnung', 'und', 'verbrachten', 'den ganzen Tag',
      'auf der Straße.']),
    ('t2', 8, '课文 · Prof. Liu', '有足够吃的、有安全的家，就已经觉得幸福了。',
     ['Wer genug zu essen und ein sicheres Zuhause hatte,', 'empfand', 'schon', 'Glück.']),
    ('t2', 12, '课文 · Lukas', '我们拥有的越多，想要的也越多。',
     ['Je mehr', 'wir', 'haben,', 'desto mehr', 'wollen', 'wir.']),
    ('t2', 27, '课文 · Prof. Liu', '甚至偶遇也能对我们的幸福感产生好的影响。',
     ['Sogar Zufallsbegegnungen', 'können', 'sich', 'günstig', 'auf unser Glücksempfinden', 'auswirken.']),
]
for _k, _n, _c, _zh, _ch in WERKSTATT:
    assert ' '.join(_ch) == IDX[_k][_n], '语序工坊词块与课文原句不一致：%s' % _ch

SATZMUSTER = {
    'title': '句型库 · Satzmuster',
    'instruction': '九条句型全部从课文里长出来。每条给四样：骨架（方括号可换）、什么时候用、'
                   '三句例句（带出处）、最常见的错法。练法：先遮住例句，用骨架说一句自己的事，再对例句。',
    'groups': SATZMUSTER_GROUPS,
    'werkstatt': {
        'title': '🔧 语序工坊 · 点词块组句',
        'note': '句子全部取自课文。先读中文，再把词块按德语语序点进下面的空行，然后点「检查语序」。'
                '两条死规律：变位动词占第二位；从句动词到句末。',
        'items': [{'cat': c, 'zh': zh, 'chunks': ch, 'src': '教材 ' + ('S.13–S.15' if k == 't1' else 'S.25–S.26')}
                  for k, n, c, zh, ch in WERKSTATT],
    },
}

# 搭配连线：中文逐条对应（教材搭配 × 词场释义），第二格那行说明不参与
KOLL_ZH = {
    'sich kümmern um + A': '照顾，操心',
    'sich auswirken auf + A': '对……产生影响',
    'es kommt auf + A an': '取决于……（关键在……）',
    'sich auszeichnen durch + A': '以……著称',
    'sich heraushalten aus + D': '不插手某事',
    'geprägt sein von + D': '由……塑造',
    'träumen von + D': '梦想，做梦',
    'verknüpft sein mit + D': '与……紧密相连',
    'zusammenhängen mit + D': '与……有关',
    'zufrieden sein mit + D': '对……满意',
    'streben nach + D': '追求',
    'beitragen zu + D': '有助于',
    'Beziehung / Einstellung zu + D': '对……的关系／态度',
    'Angst haben vor + D': '害怕某事',
}
KOLLOKATIONEN = {
    'title': '🔗 搭配连线 · Was passt zusammen?',
    'instruction': '左边是搭配，右边是中文。这一课丢分大半丢在介词上——把整块搭配背下来，写句子时不用现拼。',
    'src': '教材 Lektion 1 · 介词搭配清单（按支配格汇总，见上课版附录 B）',
    'pairs': [[r[1], KOLL_ZH[r[1]]] for r in T.APPENDIX_B['rows'] if r[1] in KOLL_ZH],
}

# 练习 9：五个空的正确词块（顺序 = 正文里 [[1]]…[[5]] 的出现顺序）
_CLZ_ANS = {
    'Was die Menschen in einem Land glücklich macht': [[1]],
}
REDE_CLOZE = {
    'title': '练习 9 · 完形（教材 S.25–S.26）',
    'instruction': '教材原题是「听录音填空」（Hören Sie und ergänzen Sie den Text mit den angegebenen Satzteilen）。'
                   '这里没有音频，改用词库：先点句子里的空位，再点上面的词块填进去，最后点「检查」。'
                   '词块只有五个，空也正好五个。',
    'src': '教材 S.25–S.26 · 练习 9 原文',
    'bank': [SRC.EX9_CHUNKS[2], SRC.EX9_CHUNKS[1], SRC.EX9_CHUNKS[0],
             SRC.EX9_CHUNKS[4], SRC.EX9_CHUNKS[3]],
    'blocks': [{'p': SRC.T2_LEAD, 'ans': []}] + [
        {'p': '%s: %s' % (w, t), 'ans': [LS.CHUNK[i] for i in range(1, 6)
                                         if '[[%d]]' % i in t]}
        for w, t in SRC.T2_DIALOGUE],
}

REWRITE_PAT = [
    ('[Der Text] lässt sich [leicht lesen].', 'sich lassen + 不定式；主语是被处理的东西，不加 von'),
    ('[Die Hausaufgaben] sind bis Freitag [zu machen].', 'sein + zu + 不定式 = 必须／可以；被动替代'),
    ('Ich habe einen Freund, [der in Berlin studiert].', '先行词 der Freund（阳性）→ 从句主语用 der'),
    ('Die Lehrerin, [die ich gestern getroffen habe], ist sehr freundlich.', '从句里 sie = die Lehrerin，阴性一/四格同形'),
    ('Was mich glücklich macht, [ist] Musik.', 'was 从句整体作主语 → 主句动词紧跟其后'),
    ('Je mehr ich übe, desto besser [spreche ich].', 'desto 后面先动词，再主语'),
    ('Beim Lernen kommt es auf [die Methode] an.', 'es kommt auf + A an；an 是可分前缀，站句末'),
    ('Die Ideen sind [zu entwickeln] und [zu überprüfen].', '两个动词各自都要带 zu'),
]
SCHREIB = {
    'title': '✍️ 改写 + 中译德 · 把句型用出去',
    'instruction': '左边是原句与要求，中间给骨架，右边自己写。写完点「参考写法」对照——'
                   '写得不一样但语法对，就是对的。',
    'rewrite': [{'de': it[0], 'zh': it[1], 'pat': pat, 'ph': ph, 'ref': ans.split(' ', 1)[1]}
                for (it, ans, (pat, ph)) in zip(T.AUFGABE_C['items'], T.AUFGABE_C['answer'], REWRITE_PAT)],
    'translate': [{'zh': cn, 'pat': '', 'ph': '先想这一课哪个句型能用上，再动笔',
                   'ref': ans.split(' ', 1)[1]}
                  for cn, ans in zip(T.AUFGABE_D['items'], T.AUFGABE_D['answer'])],
    'interview': {
        'title': '🎤 采访一位同学 · 六个问题（教材 E3）',
        'instruction': '把六个问题问完记下来，下一次课用德语汇报两三条。回答时尽量用这一课的句型：'
                       'was 从句、wer 从句、es kommt auf … an、sich auswirken auf、ebenso … wie。',
        'items': [{'k': '问题 %d' % (i + 1), 'de': ln.strip(),
                   'pat': '[Was] mich glücklich macht, ist … / Es kommt auf … an.',
                   'ph': '先答一句，再补一句理由（weil / dass 从句）'}
                  for i, ln in enumerate([x for x in T.AUFGABE_E['tasks'][2][1].split('\n')[1:] if x.strip()])],
    },
}

VOCAB_JSON = {
    'meta': {'lektion': '1', 'title': 'Rund um das Glück',
             'source': '教材 Lektion 1 · Vokabeln 1-6（S.18）/ 1-9（S.29）与 Text 1 / Text 2',
             'provenance': '词场按主题重排自教材词表；每条搭配与例句注明出处，带 S. 的是课文原句。'},
    'wortfelder': {
        'title': '词汇精讲 · Wortschatz im Kontext',
        'instruction': '八个词场：每条给「词条 → 中文 → 常用搭配 → 教材例句」。'
                       '背词先背搭配——说出口的从来不是孤零零一个词。点词条格可看例句与中文译文。',
        'src': '教材 Lektion 1 · Text 1（S.13–S.15）/ Text 2（S.25–S.26）八个词场',
        'groups': WORTFELDER,
    },
    'wortbildung': {
        'title': D.WORTBILDUNG['title'], 'lead': D.WORTBILDUNG['lead'],
        'header': D.WORTBILDUNG['header'],
        'rows': [list(r) for r in D.WORTBILDUNG['rows']],
        'note': D.WORTBILDUNG['note'],
    },
    'satzmuster': SATZMUSTER,
    'kollokationen': KOLLOKATIONEN,
    'rede_cloze': REDE_CLOZE,
    'schreibwerkstatt': SCHREIB,
}

TEXT_ZH = {'t1': ZH['t1'], 't2': ZH['t2']}

VOCAB_ZH = {'ex': {r['ex']: r['exZh'] for g in WORTFELDER for r in g['rows'] if r['ex'] and r['exZh']}}
for e in build_glossar():
    if e['ex'] and e['ex'] not in VOCAB_ZH['ex']:
        VOCAB_ZH['ex'][e['ex']] = ZH['t1'].get(e['ex'], '') or ZH['t2'].get(e['ex'], '')

assert len(LUECKEN['items']) == 12, '介词填空应为 12 题'
assert sum(len(b['ans']) for b in REDE_CLOZE['blocks']) == 5, '练习 9 应为 5 个空'
assert len(KOLLOKATIONEN['pairs']) == 14, '搭配连线应为 14 对，实为 %d' % len(KOLLOKATIONEN['pairs'])

if __name__ == '__main__':
    for name, obj in (('l1-data.json', DATA), ('l1-vocab.json', VOCAB_JSON),
                      ('l1-text-zh.json', TEXT_ZH), ('l1-vocab-zh.json', VOCAB_ZH)):
        with open(os.path.join(HERE, name), 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=1)
        print('%-18s %7d bytes' % (name, os.path.getsize(os.path.join(HERE, name))))
    print('glossar t1=%d t2=%d | 译文 t1=%d t2=%d | 词条例句译文=%d'
          % (len(GLOSS_T1), len(GLOSS_T2), len(ZH['t1']), len(ZH['t2']), len(VOCAB_ZH['ex'])))
