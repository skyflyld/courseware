#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_l10_data.py — Lektion 10《Diese Medien sind mir wichtig!》数据层
产出: l10-data.json（教材 S.291–296 + S.299–303 逐页取证 → 数据）

取证纪律（技能 §19 阶段 1–3）：
  · 11 页扫描件（3072×4096，无文字层）双引擎 OCR 交叉：DeepSeek-V4.1-Flash + qwen3-vl-plus
  · 词表原文留档 l10-quellen/ocr/vokabeln-s296.txt / vokabeln-s303.txt（含修订单）
  · 课文正文（T1 S.291–292 / T2 S.299–300）逐字取自 OCR 两份一致的结果，不改写、不补造
  · 练习填空的答案：T2 Ü4 / Ü5 / Ü9.2 由教材自带词库直接推出（词库 = 教材自身的答案集）；
    无词库的听力填空（Ü9.1 / Ü11）与口语任务（Ü8 表 / Ü9 改写 / Ü10 翻译）标注为「参考答案·推定」
"""
import json
import pathlib
import re

DIR = pathlib.Path(__file__).parent
OCR = DIR / 'l10-quellen' / 'ocr'
OUT = DIR / 'l10-data.json'

# ================================================================ 词表
def vocab_lines(fn):
    ls = [l for l in (OCR / fn).read_text(encoding='utf-8').splitlines() if '|' in l]
    return [tuple(x.strip() for x in l.split('|', 1)) for l in ls]


CASE = r'(?:A|D|G|Akk|Dat|Gen)'
# 与基底 build_l8_berufe.TOK_RE 同口径：只剥离「完整的」标注 token。
# 不能写成 `\+\s*\S.*`——那会把 "verschmelzen (+A) +zu Dat" 从括号内那个 + 开始切，
# 切出 "verschmelzen (" 这种带半个括号的碎词（2026-09-21 实测坑）。
ANN_PAT = re.compile(
    r'\s*(?:\([^()]*\)|\[[^\]]*\]'
    r'|\+\s*[^()\s]+(?:\s+[^()\s]+)*'   # +A / +für Akk / +zu Dat / +als+A（不允许跨括号）
    r'|-\S*|\.\.\.\S*|nur Sg|meist Sg|selten Pl|meist Pl|Pl)\s*$')


ENTRIES296 = []
ENTRIES303 = []


def entries_of(v):
    return [{'w': clean_w(w), 'raw': w, 'cn': cn} for w, cn in v]


def clean_w(full):
    """去掉教材词条尾部的标注（复数词尾 / 读音 / 支配格 / nur Sg / …），留主词。"""
    s = full.strip()
    while True:
        m = ANN_PAT.search(s)
        if not m or m.start() == 0:
            break
        s = s[:m.start()].strip()
    return s or full.strip()


V296 = vocab_lines('vokabeln-s296.txt')
V303 = vocab_lines('vokabeln-s303.txt')

ENTRIES296 = entries_of(V296)
ENTRIES303 = entries_of(V303)
PAIRS296 = [(e['w'], e['cn']) for e in ENTRIES296]
PAIRS303 = [(e['w'], e['cn']) for e in ENTRIES303]

# 不规则形的补漏（词干正则抓不到的）
FORMS_EXTRA = {
    'schreiben': ['geschrieben', 'schrieb', 'schreiben'],
    'schicken': ['geschickt', 'schickte', 'schicken'],
    'an/kommen': ['ankamen', 'ankommt', 'ankommen', 'kam'],
    'ab/lösen': ['abzulösen', 'ablösen', 'abgelöst'],
    'jd/etw ist nicht wegzudenken': ['wegzudenken'],
    'jd/etw ist nicht wegzudenken.': ['wegzudenken'],
    'sich leisten': ['leisten', 'leisten konnte'],
    'denken': ['gedacht', 'denken'],
    'ablehnen': ['abgelehnt'],
    'beweisen': ['bewiesen'],
    'empfehlen': ['empfohlen', 'empfehlen'],
    'bilden': ['bildet', 'bilden', 'gebildet'],
    'unterhalten': ['unterhalten', 'unterhält'],
    'sich bilden': ['bilden', 'bildet'],
    'verbreiten': ['verbreiten', 'verbreitet'],
    'verwenden': ['verwendet', 'verwenden'],
    'ausschalten': ['ausschalten', 'ausgeschaltet'],
    'prägen': ['prägten', 'prägt', 'geprägt'],
    'gewiss': ['gewisse', 'gewissen'],
    'bestimmt': ['bestimmte', 'bestimmten'],
    'fehlend': ['fehlend'],
    'global': ['globalen', 'global'],
    'aktuell': ['aktuelle', 'aktuelle'],
    'traditionellerweise': ['Traditionellerweise', 'traditionellerweise'],
    'der Laden': ['Läden', 'Laden'],
    'die Glotze': ['Glotze'],
    'das Sonnenbad': ['Sonnenbad'],
    'einerseits ... andererseits': ['einerseits', 'andererseits'],
    'zum einen ... zum anderen': ['Zum einen', 'zum anderen', 'zum einen'],
    '-bar': ['-bar'],
}

# 教材词表未列、但课文里影响理解的常用词（标注为课件补充）
EXTRAS = {
    'das Museum': '博物馆',
    'besichtigen': '参观',
    'die Entwicklung': '发展、演变',
    'die Kommunikation': '沟通、交流',
    'menschlich': '人类的',
    'der Zug': '火车',
    'der Brief': '信',
    'die Antwort': '回答、答复',
    'das Gerät': '设备、器具',
    'das Handy': '手机',
    'der Sender': '电台/电视台；发射台',
    'schwarz-weiß': '黑白的（当时的电视）',
    'das Internet': '互联网',
    'das Haushaltsgerät': '家用电器',
    'das Straßenbild': '街景',
    'digital': '数字的',
    'das Briefschreiben': '写信',
    'unbezahlbar': '昂贵得付不起的',
    'selbstverständlich': '理所当然的、不言而喻的',
    'üblich': '通常的、常见的',
    'der Zugang': '进入、接触的机会',
    'der Rundfunk': '广播',
    'die Presse': '新闻界、报刊',
    'das Fernsehen': '电视',
    'die Massenmedien': '大众传媒（复数）',
    'das Publikum': '公众、受众',
    'die Gesellschaft': '社会',
    'die Aufgabe': '任务',
    'die Öffentlichkeit': '公众、公共领域',
    'die Diskussion': '讨论',
    'die Entscheidung': '决定、决策',
    'die Kritik': '批评',
    'die Unterhaltung': '娱乐',
    'die Bildung': '教育',
    'die Kultur': '文化',
    'das Konzert': '音乐会',
    'die Oper': '歌剧',
    'die Theateraufführung': '戏剧演出',
    'der Film': '电影',
    'die Meinung': '意见、观点',
    'das Interesse': '兴趣；利益',
    'die Interessengruppe': '利益集团',
    'der Nutzer': '使用者',
    'zugänglich': '可获得的、可接触的',
    'vollständig': '完整的、全面的',
    'erfüllen': '完成、履行',
    'der Zuschauer': '观众',
    'die Studie': '研究',
    'das Medium': '媒介',
    'der Vorteil': '优点、好处',
    'der Nachteil': '缺点、不利之处',
    'das Wissen': '知识',
    'die Erfahrung': '经验',
    'das Gebiet': '领域',
    'fehlerhaft': '有错误的',
    'das Verhalten': '行为、举止',
    'die Nutzerin': '女使用者',
    'die Meinungsfreiheit': '言论自由',
    'unverzichtbar': '不可或缺的',
    'der Bestandteil': '组成部分',
    'die Vernetzung': '互联、网络化',
    'die Kommunikationsform': '沟通形式',
    'das Luxusgut': '奢侈品',
    'einrichten': '设立、布置',
    'verfügbar': '可用的',
    'die Quelle': '来源',   # 若词表已有则词表优先
    'der Inhalt': '内容',
    'die Nachricht': '消息、报道',
    'die Information': '信息',
    'persönlich': '个人的',
    'der Horizont': '视野、眼界',
}


def forms_of(w, text):
    """从课文里找出该词条实际出现过的形态（词干/名词前缀匹配 + 补漏表）。"""
    pats = []
    base = w
    if '/' in base:
        base = base.split('/')[-1]
    if base.startswith(('der ', 'die ', 'das ')):
        base = base.split(' ', 1)[1]
    if base.endswith('en') and ' ' not in base:
        pats.append(base[:-2] + r'\w*')
    elif base.endswith('n') and ' ' not in base and len(base) > 4:
        pats.append(base[:-1] + r'\w*')
    else:
        pats.append(re.escape(base) + r'\w*')
    pats.append(re.escape(base))
    pats += [re.escape(x) for x in FORMS_EXTRA.get(w, [])]
    found = []
    for p in pats:
        try:
            found += re.findall(r'(?<![A-Za-zÄÖÜäöüß])' + p + r'(?![A-Za-zÄÖÜäöüß])', text)
        except re.error:
            continue
    return sorted(set(found), key=lambda s: -len(s))


SENT_SPLIT = re.compile(r'(?<=[.!?])(?:[“"»)\]]*)\s+')


def sentence_with(text, surface):
    for s in SENT_SPLIT.split(text):
        if re.search(r'(?<![A-Za-zÄÖÜäöüß])' + re.escape(surface) + r'(?![A-Za-zÄÖÜäöüß])', s):
            return s.strip()
    return ''


def build_glossar(text, pairs, extra_src, vlist_src):
    """课文正文 → 词条表（教材词表优先，未列词走补充表）。"""
    gl, seen = [], set()
    for w, cn in pairs:
        if w in seen:
            continue
        fs = forms_of(w, text)
        if not fs:
            continue
        seen.add(w)
        gl.append({'w': w, 'zh': cn, 'forms': fs + [w],
                   'ex': sentence_with(text, fs[0]), 'src': vlist_src})
    for w, cn in EXTRAS.items():
        if w in seen:
            continue
        fs = forms_of(w, text)
        if not fs:
            continue
        seen.add(w)
        gl.append({'w': w, 'zh': cn, 'forms': fs + [w],
                   'ex': sentence_with(text, fs[0]), 'src': extra_src})
    return gl


# ================================================================ 课文 T1（S.291–292 · Ü6）
T1_PARAS = [
    ('Yang Fang und Laura besichtigen heute das „Museum für Kommunikation Berlin“. Durch einen '
     'geführten Rundgang [[1]] sie über die Entwicklung der menschlichen Kommunikation [[2]].',
     ['werden', 'informiert']),
    ('Vor 100 Jahren [[3]] viele Briefe [[4]] und mit der Post [[5]], wenn man sich gegenseitig '
     'Nachrichten überbringen wollte. Die Post [[6]] allerdings nicht wie heute mit extrem '
     'schnellen Zügen oder sogar mit Flugzeugen [[7]], sondern mit Dampfschiffen, Eisenbahnen '
     'oder sogar auch mit Pferden und Kutschen. So dauerte es sehr lange, bis die Briefe ankamen. '
     'Die Menschen mussten oft wochenlang auf Antworten warten. Das ist für uns kaum denkbar, oder?',
     ['wurden', 'geschrieben', 'geschickt', 'wurde', 'transportiert']),
    ('1923 fand eine bahnbrechende Erfindung ihren Weg nach Deutschland: Das Radio. Im Gegensatz '
     'zu heute war das Gerät damals nicht für alle selbstverständlich. Eine gewisse Zeit lang '
     'musste jedes Radio [[8]] [[9]]. In den 1970er Jahren entwickelte sich das Radio langsam zu '
     'einem üblichen Haushaltsgerät. Alle hatten so Zugang zu Musik, Nachrichten und Hörspielen. '
     'Die Familien versammelten sich rund um das Radio und lauschten dem Programm. Denn damals '
     'gab es zu Hause noch keinen Fernseher …',
     ['genehmigt', 'werden']),
    ('Um 1950 begann das Fernsehen, das Radio langsam als beliebtestes Medium [[10]]. Aber auch das '
     'Fernsehen, damals noch in schwarz-weiß, war anfangs nicht für jeden zugänglich. Viele '
     'Familien konnten [[11]] so ein teures Gerät gar nicht [[12]]. In Schaufenstern mancher Läden '
     '[[13]] Fernseher [[14]]. Deshalb standen oft viele Menschen vor den Scheiben und schauten '
     'sich die Nachrichten an. Es gab auch nur bestimmte Sender. Diese konnten an einer Hand '
     '[[15]] [[16]]. Kaum vorstellbar, dass wir heute über 60 Sender zur Auswahl haben, oder?',
     ['abzulösen', 'sich', 'leisten', 'wurden', 'aufgestellt', 'abgezählt', 'werden']),
    ('Noch bis 1970 hatten viele deutsche Familien kein eigenes Telefon. Für viele war das ein '
     'unbezahlbarer Luxusgegenstand. Es [[17]] viele öffentliche Telefonzellen [[18]]. Diese '
     'prägten ab 1920 das Straßenbild. Heute sieht man kaum noch welche in den deutschen Städten. '
     'Denn heute [[19]] fast immer mit dem Handy [[20]].',
     ['wurden', 'errichtet', 'wird', 'telefoniert']),
    ('Spätestens mit dem globalen Durchbruch des Internets seit 1990 [[21]] die menschliche '
     'Kommunikation grundlegend [[22]]. Für viele Menschen war es damals eine große Umstellung, '
     'die neuen technischen Geräte überall im Alltag zu benutzen. Mittlerweile sind sie aus dem '
     'Leben nicht mehr [[23]]. Kinder wachsen mit den digitalen Medien auf und alte '
     'Kommunikationswege, wie das Briefschreiben oder das Radio, [[24]] immer mehr von neuen '
     'Medien [[25]].',
     ['wurde', 'verändert', 'wegzudenken', 'werden', 'ersetzt']),
]

T1_BANK = ['errichten', 'informieren', 'telefonieren', 'schicken', 'transportieren', 'ersetzen',
           'sich leisten', 'genehmigen', 'aufstellen', 'wegdenken', 'abzählen', 'verändern',
           'schreiben', 'ablösen']

T1_ALT = {3: ['wurden'], 6: ['wurde'], 10: ['abzulösen', 'ablösen'], 11: ['sich'],
          19: ['wird'], 21: ['wurde'], 24: ['werden']}

# ================================================================ 课文 T2（S.299–300 · Ü4）
T2_PARAS = [
    ('Yang Fang und Laura schauen sich im Museum einen Film über die verschiedenen Funktionen '
     'der Massenmedien an.', []),
    ('Traditionellerweise werden Presse, Rundfunk und Fernsehen als Massenmedien bezeichnet. Ihr '
     'gemeinsames Merkmal ist, aktuelle Inhalte mit technischen Hilfsmitteln einem breiten '
     'Publikum zugänglich zu machen. In Deutschland sollen die Massenmedien mehrere Aufgaben '
     'erfüllen und wichtige Funktionen für die Gesellschaft ausüben:', []),
    ('• Zum einen sollen sie [[1]] über Politik, Wirtschaft und Kultur verbreiten. Die '
     'Massenmedien sollen das Publikum so vollständig, sachlich und verständlich wie möglich '
     '[[2]], damit ihre Nutzerinnen und Nutzer öffentliche Ereignisse verfolgen können.',
     ['Informationen', 'informieren']),
    ('• Bei der [[3]] sollen die Massenmedien dafür sorgen, dass Fragen von öffentlichem Interesse '
     'in freier und offener Diskussion erörtert werden und dass Meinungen verschiedener '
     'Interessengruppen in die Öffentlichkeit kommen.', ['Meinungsbildung']),
    ('• Außerdem übernehmen die Massenmedien eine [[4]] und [[5]]. Sie sollen politische '
     'Entscheidungen hinterfragen und Missstände [[6]], um dadurch die Arbeit der Politikerinnen '
     'und Politiker zu [[7]].', ['Kritikfunktion', 'Kontrollfunktion', 'kritisieren', 'kontrollieren']),
    ('• Zu den weiteren Aufgaben der Massenmedien gehören aber auch [[8]] und [[9]]. Die '
     'Massenmedien bieten viel Kultur: Im Fernsehen werden z. B. Dokumentationen, Reportagen und '
     'Magazine, Konzerte, Opern, Theateraufführungen und anspruchsvolle Filme gezeigt. Man '
     'schaltet ein, um sich einerseits zu [[10]] und um sich andererseits auch zu [[11]] und zu '
     'entspannen.', ['Bildung', 'Unterhaltung', 'bilden', 'unterhalten']),
]

T2_BANK = ['Meinungsbildung', 'kritisieren', 'bilden', 'Information', 'Bildung', 'kontrollieren',
           'unterhalten', 'Kritikfunktion', 'Unterhaltung', 'Kontrollfunktion', 'informieren']

T2_BOX = ('Die Medien und die Personen hinter den Medien arbeiten nicht automatisch neutral oder '
          'ohne eigene Interessen. Daher ist es wichtig, dass man gegenüber den Medien eine '
          'kritische Haltung einnimmt und bereit ist, nach Möglichkeit verschiedene Darstellungen '
          'zu vergleichen.')

T2_QBOX = ('Welches logische Subjekt haben die beiden unterstrichenen Satzteile? Was ist der '
           'Gebrauchsunterschied zwischen um … zu und damit?')

T2_QBEX = ['Er ist in die Stadt gezogen, um hier zu arbeiten.',
           'Er ist in die Stadt gezogen, damit seine Kinder mehr Bildungschancen haben.']


# ================================================================ 课后练习（教材 S.293–295 / S.300–302）
T1EX = [
    {'n': 1, 'kind': 'fill',
     'title': 'Ü6 词库完形：用对形态（被动 / zu 不定式）',
     'src': '教材 S.291–292 · Ü6',
     'instruction': '合上课文再填一遍。词库里 14 个词要用对形态：被动语态的助动词 werden 要自己变位（共 10 个空），'
                    '可分动词的 zu 要插在中间（如 abzulösen）。填完点「✓ 检查」，卡住就点「👁 显示答案」。',
     'bank': T1_BANK, 'ref': 't1',
     'note': '答案依据：教材 Ü6 自带词库（14 词全部用到）+ 被动语态与 zu 不定式的形态规则；'
             '助动词 werden 的原形未在词库内，需自行变位。'},

    {'n': 2, 'kind': 'match',
     'title': 'Ü7 Wendungen 与释义配对',
     'src': '教材 S.293 · Ü7',
     'instruction': '点左列德语固定搭配，再点右列中文释义，配对成功变绿。',
     'note': '教材原题给出的是 A–E 五条德语定义（见下表）。右列中文为按教材定义改写，便于先建立意义。',
     'pairs': [
         ['Zugang zu etwas haben', '能接触、能获得某物（有机会看到/听到等）'],
         ['dem Programm lauschen', '专心听节目'],
         ['etwas ablösen', '接替某事（接管职务、位置、任务）'],
         ['sich etwas (nicht) leisten können', '（不）买得起某物，（没）有足够钱买'],
         ['etwas ist aus etwas nicht mehr wegzudenken', '某人/某物再也无法想象会缺少'],
     ],
     'table': {'title': '教材原文定义（A–E，原文照录）', 'src': '教材 S.293 · Ü7',
               'headers': ['定义', '原文'],
               'rows': [['A', 'dem Programm genau zuhören'],
                        ['B', '(nicht) genug Geld zum Kauf von etwas haben'],
                        ['C', 'sich jemanden / etwas nicht als fehlend vorstellen (können)'],
                        ['D', 'die Tätigkeit, den Dienst, die Stellung übernehmen'],
                        ['E', 'Möglichkeit haben, jemanden / etwas zu sehen, hören usw.']]}},

    {'n': 3, 'kind': 'table',
     'title': 'Ü8 Globalverständnis：五种媒体的功能与今昔',
     'src': '教材 S.293 · Ü8',
     'instruction': '原题是口语问答（Fragen Sie und antworten Sie）：先自己按课文说一遍，再点「👁 显示参考归纳」对照下表的归纳。',
     'note': '⚠️ 下表是按课文归纳的参考答案，不是教材标准答案（原题无标准答案）；灰底处即答案。',
     'headers': ['Medium', 'Funktion', 'früher', 'heute'],
     'rows': [
         ['Brief', 'Nachrichten überbringen',
          'mit Dampfschiffen, Eisenbahnen, Pferden und Kutschen transportiert; wochenlang auf Antworten warten',
          'kaum noch – E-Mails und Messenger ersetzen den Brief'],
         ['Radio', 'Musik, Nachrichten und Hörspiele senden: informieren und unterhalten',
          'musste genehmigt werden, war nicht für alle selbstverständlich; die Familien versammelten sich rund um das Radio',
          'übliches Haushaltsgerät, viele Sender zur Auswahl'],
         ['Fernsehen', 'Informationen und Unterhaltung, auch Kultur: Dokumentationen und Filme',
          'schwarz-weiß und teuer, nur wenige Sender; die Menschen schauten durch die Schaufenster',
          'über 60 Sender zur Auswahl; aus dem Alltag nicht mehr wegzudenken'],
         ['Telefon', 'mit anderen Menschen sprechen',
          'unbezahlbarer Luxusgegenstand; öffentliche Telefonzellen prägten das Straßenbild',
          'fast immer mit dem Handy'],
         ['Internet', 'alle Medien: Information, Kommunikation, Kultur',
          'seit 1990 der globale Durchbruch; eine große Umstellung für viele Menschen',
          'digitale Medien sind nicht mehr wegzudenken'],
     ],
     'beispiel': [['A', 'Was wird mit Briefen gemacht? / Was kann man mit Briefen machen?'],
                  ['B', 'Mit Briefen werden Nachrichten überbracht. / Mit Briefen kann man Nachrichten überbringen.'],
                  ['A', 'Wie wurden Briefe früher transportiert?'],
                  ['B', 'Früher wurden Briefe mit Dampfschiffen, Eisenbahnen oder sogar mit Pferden und Kutschen transportiert.']]},

    {'n': 4, 'kind': 'open',
     'title': 'Ü9 被动句改主动句',
     'src': '教材 S.294 · Ü9',
     'instruction': '把下列被动句改成主动句（教材只给了 Beispiel）。自己写一遍，再点「💬 参考写法」对照。'
                    '主动句通常用 man 作主语；若被动句里有 von + Dativ，也可以把施事直接提为主语。',
     'note': '⚠️ 教材未附答案：下面是参考写法，不唯一，语法正确、意义不变即可。',
     'beispiel': 'Vor 100 Jahren wurden viele Briefe geschrieben und mit der Post geschickt. '
                 '→ Vor 100 Jahren schrieb man viele Briefe und schickte sie mit der Post.',
     'items': [
         ['Die Post wurde nicht mit extrem schnellen Zügen oder sogar mit Flugzeugen transportiert.',
          'Man transportierte die Post nicht mit extrem schnellen Zügen oder sogar mit Flugzeugen.'],
         ['Eine gewisse Zeit lang musste jedes Radio genehmigt werden.',
          'Eine gewisse Zeit lang musste man jedes Radio genehmigen.'],
         ['In Schaufenstern mancher Läden wurden Fernseher aufgestellt.',
          'In Schaufenstern mancher Läden stellte man Fernseher auf.'],
         ['Die Fernsehsender konnten an einer Hand abgezählt werden.',
          'Man konnte die Fernsehsender an einer Hand abzählen.'],
         ['Es wurden viele öffentliche Telefonzellen errichtet.',
          'Man errichtete viele öffentliche Telefonzellen.'],
         ['Heute wird fast immer mit dem Handy telefoniert.',
          'Heute telefoniert man fast immer mit dem Handy.'],
         ['Spätestens mit dem globalen Durchbruch des Internets seit 1990 wurde die menschliche '
          'Kommunikation grundlegend verändert.',
          'Spätestens mit dem globalen Durchbruch des Internets seit 1990 veränderte man die '
          'menschliche Kommunikation grundlegend.'],
         ['Alte Kommunikationswege werden immer mehr von neuen Medien ersetzt.',
          'Immer mehr neue Medien ersetzen alte Kommunikationswege.'],
     ]},

    {'n': 5, 'kind': 'fill',
     'title': 'Ü11 Intelligente Nutzer：媒体素养填空',
     'src': '教材 S.295 · Ü11.1',
     'instruction': '原题是听力填空，教材没有词库。先自己按上下文填，再点「👁 显示答案」对照。',
     'bank': [],
     'paras': [('Massenmedien sind die wichtigste <1> der Menschen. Schon seit ihren Anfängen '
                'fordern die Massenmedien <2> Nutzer. In Zeiten von Algorithmen, „Fake News“ usw. '
                'ist es umso wichtiger, dass man lernt, sich trotz der <3> im Netz <4> zu '
                'verhalten und mit dem manipulativen Potenzial der Massenmedien <5> umzugehen. Es '
                'ist beispielsweise notwendig, Quellen zu <6> und Nachrichten <7> aufzunehmen.',
                ['Informationsquelle', 'kritische', 'Informationsflut', 'verantwortungsvoll',
                 'kritisch', 'überprüfen', 'sachlich'],
                ['Informationsquelle', 'kritische|mündige|aufmerksame', 'Informationsflut|Fake News',
                 'verantwortungsvoll', 'kritisch', 'überprüfen', 'sachlich|kritisch'])],
     'note': '⚠️ 音频未含在照片内，教材也没有词库：答案为按单元词汇（fordern / verantwortungsvoll / '
             'manipulativ / überprüfen / Quelle / Fake News）与上下文推定，请以教材配套音频原文为准。'},

    {'n': 6, 'kind': 'trans',
     'title': 'Ü10 翻译：媒体今昔（德译中）',
     'src': '教材 S.295 · Ü10',
     'instruction': '先自己译，再点「💬 参考译文」核对。译法不唯一，意思完整、句子通顺即可。',
     'note': '⚠️ 教材未附译文：以下是参考译文（非教材标准答案）。',
     'items': [
         ['Zunächst waren Radio und Fernsehen nicht für alle Menschen zugänglich; viele Familien '
          'konnten sich diese „Luxusgüter“ nicht leisten.',
          '起初，广播和电视并不是所有人都能接触到的；许多家庭买不起这些"奢侈品"。'],
         ['Im Vergleich zu heute gab es damals nur wenige verfügbare Sender, und oft hatte nicht '
          'jede Familie ein eigenes Telefon, sodass öffentliche Telefonzellen eingerichtet wurden.',
          '与今天相比，当时可用的频道很少；而且往往并非每个家庭都有自己的电话，因此设立了公共电话亭。'],
         ['Heute hat die globale Vernetzung die Kommunikationsweise der Menschen grundlegend verändert.',
          '今天，全球互联从根本上改变了人们的沟通方式。'],
         ['Die alten Kommunikationsformen werden nach und nach durch neue Formen ersetzt.',
          '旧的沟通形式正逐渐被新的形式所取代。'],
         ['Verschiedene digitale Medien sind mittlerweile ein unverzichtbarer Bestandteil unseres '
          'Alltags geworden.',
          '各种数字媒体如今已成为我们日常生活中不可或缺的组成部分。'],
     ],
     'redemittel': {'title': 'Redemittel · 比较今昔（教材 S.294 · Ü8.2）',
                    'items': [
                        ['Die Post wurde allerdings nicht wie heute mit extrem schnellen Zügen '
                         'oder mit Flugzeugen transportiert.', '教材原文句'],
                        ['Im Gegensatz zu heute wurde die Post vor 100 Jahren mit Pferden und '
                         'Kutschen transportiert.', '教材 Beispiel'],
                    ]}},
]

T2EX = [
    {'n': 1, 'kind': 'cloze', 'ref': 't2',
     'title': 'Ü4 词库完形：大众传媒的五种功能',
     'src': '教材 S.299–300 · Ü4',
     'instruction': '先点句子里的空位，再点词库里的词；整段填完点「✓ 检查」。11 个词库词对应 11 个空，全部用到。',
     'bank': T2_BANK,
     'alt': {1: ['Informationen', 'Information']},
     'note': '答案依据：教材 Ü4 自带词库（11 词与 11 空一一对应）。'
             '提示：教材词库按原形给出，其中 Information 在句子里要用复数 Informationen'
             '（点「👁 显示答案」看规范形式），填 Information 也算对。'},

    {'n': 2, 'kind': 'cloze',
     'title': 'Ü5 语义填空：功能句里的动词',
     'src': '教材 S.300 · Ü5',
     'instruction': '先点空位再点词库。9 个词库词对应 9 个空。',
     'bank': ['kritisieren', 'bilden', 'kontrollieren', 'diskutieren', 'unterhalten',
              'verbreiten', 'Entspannung', 'erweitern', 'informieren'],
     'paras': [
         ('a) Weil die Massenmedien neues Wissen und wichtige Erfahrungen aus verschiedenen '
          'Gebieten des Lebens [[1]], kann sich das Publikum schnell über die gesellschaftliche '
          'Entwicklung [[2]].', ['verbreiten', 'informieren']),
         ('b) Die Massenmedien sollen die Entscheidungen von Politikerinnen und Politikern [[3]] '
          'und fehlerhaftes Verhalten [[4]].', ['kontrollieren', 'kritisieren']),
         ('c) Wenn die Massenmedien über Fragen des öffentlichen Interesses frei und offen [[5]], '
          'können sie den Bürgerinnen und Bürgern helfen, sich aktiv dazu eine Meinung zu [[6]].',
          ['diskutieren', 'bilden']),
         ('d) Das Publikum benutzt häufig das große Kulturangebot der Massenmedien, um den '
          'persönlichen Horizont zu [[7]] und sich gut zu [[8]] oder [[9]] zu finden.',
          ['erweitern', 'unterhalten', 'Entspannung']),
     ],
     'note': '答案依据：教材 Ü5 自带词库（9 词与 9 空一一对应）。'},

    {'n': 3, 'kind': 'quiz',
     'title': 'Ü5 功能归类：这句话属于哪种功能？',
     'src': '教材 S.300 · Ü5（答案依据：S.301 Ü7 提示框列出的五个功能）',
     'instruction': '上面四句分别对应哪一种媒体功能？选一个再点「✓ 检查」。',
     'opts': ['Informationsfunktion', 'Meinungsbildungsfunktion', 'Kritik- und Kontrollfunktion',
              'Bildungsfunktion', 'Unterhaltungsfunktion'],
     'items': [['a) neues Wissen und wichtige Erfahrungen verbreiten', 0],
               ['b) Entscheidungen kontrollieren und fehlerhaftes Verhalten kritisieren', 2],
               ['c) frei und offen diskutieren, damit sich die Bürger eine Meinung bilden', 1],
               ['d) Kulturangebot nutzen, Horizont erweitern, sich unterhalten', 4]],
     'note': '五个功能名取自教材 S.301 Ü7 旁的提示框（Informationsfunktion / Meinungsbildungsfunktion / '
             'Bildungsfunktion / Kritik- und Kontrollfunktion / Unterhaltungsfunktion）。'},

    {'n': 4, 'kind': 'open',
     'title': 'Ü6 用 um … zu 和 damit 造句',
     'src': '教材 S.301 · Ü6',
     'instruction': '每一条都要造两句：一句 um … zu + Infinitiv，一句 damit + Nebensatz（被动形式）。'
                    '先自己写，再点「💬 参考写法」对照。注意：主语一致用 um … zu，主语不同用 damit。',
     'note': '⚠️ 教材只给了第 1 条的 Beispiel（原文照录）；第 2–6 条为按同一句型推导的参考写法。',
     'beispiel': 'Wir brauchen die Massenmedien, um aktuelle Inhalte mit technischen Hilfsmitteln '
                 'einem breiten Publikum zugänglich zu machen.\nWir brauchen die Massenmedien, damit '
                 'aktuelle Inhalte mit technischen Hilfsmitteln einem breiten Publikum zugänglich '
                 'gemacht werden.',
     'items': [
         ['aktuelle Inhalte mit technischen Hilfsmitteln einem breiten Publikum zugänglich machen',
          'Wir brauchen die Massenmedien, um aktuelle Inhalte mit technischen Hilfsmitteln einem '
          'breiten Publikum zugänglich zu machen.\nWir brauchen die Massenmedien, damit aktuelle '
          'Inhalte mit technischen Hilfsmitteln einem breiten Publikum zugänglich gemacht werden.'],
         ['Informationen über Politik, Wirtschaft und Kultur verbreiten',
          'Wir brauchen die Massenmedien, um Informationen über Politik, Wirtschaft und Kultur zu '
          'verbreiten.\nWir brauchen die Massenmedien, damit Informationen über Politik, Wirtschaft '
          'und Kultur verbreitet werden.'],
         ['frei und offen über Fragen von öffentlichem Interesse diskutieren',
          'Wir brauchen die Massenmedien, um frei und offen über Fragen von öffentlichem Interesse '
          'zu diskutieren.\nWir brauchen die Massenmedien, damit frei und offen über Fragen von '
          'öffentlichem Interesse diskutiert wird.'],
         ['politische Entscheidungen hinterfragen und Missstände kritisieren',
          'Wir brauchen die Massenmedien, um politische Entscheidungen zu hinterfragen und '
          'Missstände zu kritisieren.\nWir brauchen die Massenmedien, damit politische '
          'Entscheidungen hinterfragt und Missstände kritisiert werden.'],
         ['die Arbeit der Politikerinnen und Politiker kontrollieren',
          'Wir brauchen die Massenmedien, um die Arbeit der Politikerinnen und Politiker zu '
          'kontrollieren.\nWir brauchen die Massenmedien, damit die Arbeit der Politikerinnen und '
          'Politiker kontrolliert wird.'],
         ['sich bilden und sich unterhalten',
          'Wir brauchen die Massenmedien, um sich zu bilden und sich zu unterhalten.\n'
          'Wir brauchen die Massenmedien, damit man sich bildet und sich unterhält.'],
     ]},

    {'n': 7, 'kind': 'fill',
     'title': 'Ü9.2 电视的利与弊：动词填空',
     'src': '教材 S.302 · Ü9.2',
     'instruction': '词库给的是动词原形，要填进句子里变成正确的形态（被动、完成时、现在时……）。填完点「✓ 检查」。',
     'bank': ['denken', 'informieren', 'verwenden', 'empfehlen', 'ausschalten', 'ablehnen',
              'unterhalten', 'beweisen', 'machen', 'bilden'],
     'paras': [('Von Intellektuellen wird das Fernsehen oft <1>. Sie sagen, der Zuschauer wird '
                'nicht wirklich <2> und <3>, sondern zu einem passiven Konsumenten <4>, und der '
                '<5> sich keine eigene Meinung. Durch Studien wurde bereits <6>, dass Problemkinder '
                'oft TV-Vielseher sind. Wenn das Medium Fernsehen jedoch klug und richtig <7> wird, '
                'so meinen Medienforscher, hat es mehr Vor- als Nachteile. Die Eltern sollten den '
                'Kindern gute Sendungen <8>. Es wird oft zu wenig daran <9>, dass man den Apparat '
                'auch <10> kann.',
                ['abgelehnt', 'informiert', 'unterhalten', 'gemacht', 'bildet', 'bewiesen',
                 'verwendet', 'empfehlen', 'gedacht', 'ausschalten'],
                ['abgelehnt', 'informiert', 'unterhalten', 'gemacht', 'bildet', 'bewiesen',
                 'verwendet', 'empfehlen', 'gedacht', 'ausschalten'])],
     'note': '答案依据：教材 Ü9.2 自带 10 个动词词库，与 10 个空一一对应（bilden 与 unterhalten 两词'
             '在本段里各有被动与主动两种形态）。'},

    {'n': 5, 'kind': 'open',
     'title': 'Ü7 口述归纳：大众传媒的五种功能',
     'src': '教材 S.301 · Ü7',
     'instruction': '教材要求口头归纳，这里改成写：用下面给的三组词，把五种功能串成一段话。'
                    '写完点「💬 参考写法」对照。评定标准：五种功能都提到 + 用了 um … zu 或 damit + '
                    '至少两个衔接词（zum einen … zum anderen / außerdem / darüber hinaus / einerseits … '
                    'andererseits）。',
     'note': '⚠️ 教材只给了词与衔接手段，没有标准答案：以下参考写法按教材词表组织，非教材原文。',
     'beispiel': '可用词：informieren / unterhalten / bilden / kritisieren / kontrollieren …；'
                 'um … zu / damit …；zum einen … zum anderen / außerdem / darüber hinaus / auch / '
                 'einerseits … andererseits …；五种功能名：Informationsfunktion / '
                 'Meinungsbildungsfunktion / Bildungsfunktion / Kritik- und Kontrollfunktion / '
                 'Unterhaltungsfunktion。',
     'items': [
         ['参考写法 1（以功能名组织）',
          'Die Massenmedien haben mehrere Funktionen. Zum einen dienen sie der '
          'Informationsfunktion, denn sie verbreiten Nachrichten über Politik, Wirtschaft und '
          'Kultur. Zum anderen übernehmen sie die Meinungsbildungsfunktion, damit sich die '
          'Bürgerinnen und Bürger eine eigene Meinung bilden können. Außerdem haben sie eine '
          'Kritik- und Kontrollfunktion: Sie sollen politische Entscheidungen hinterfragen und '
          'Missstände kritisieren, um die Arbeit der Politikerinnen und Politiker zu kontrollieren. '
          'Darüber hinaus erfüllen sie die Bildungsfunktion, weil man sich mit ihrer Hilfe '
          'weiterbilden kann, und schließlich die Unterhaltungsfunktion, denn viele schalten das '
          'Fernsehen ein, um sich zu entspannen.'],
         ['参考写法 2（以动词组织）',
          'Massenmedien informieren, bilden und unterhalten. Einerseits verbreiten sie aktuelle '
          'Informationen, andererseits kritisieren und kontrollieren sie die Mächtigen. Man nutzt '
          'sie, um sich zu informieren und um sich zu bilden; zugleich schaltet man sie ein, um '
          'sich zu unterhalten. Wichtig ist dabei, dass man gegenüber den Medien eine kritische '
          'Haltung einnimmt.'],
     ]},

    {'n': 6, 'kind': 'fill',
     'title': 'Ü9.1 德国电视：填空（无词库）',
     'src': '教材 S.302 · Ü9.1',
     'instruction': '原题是听力填空，教材没有词库。先自己填，再点「👁 显示答案」对照。',
     'bank': [],
     'paras': [('Von allen Medien verbringen die Deutschen vor dem Fernseher die längste Zeit. '
                'Man sieht fern, um <1>, um <2> und um <3>. Das 1., das 2. und das 3. Programm '
                'sind die <4>-rechtlichen Sender. Um <5>, brauchen die Privatsender <6> und viele '
                'Zuschauer. Sie zeigen hauptsächlich leichte <7>, Sportsendungen und Fernsehserien. '
                'Arte ist der deutsch-französische <8>. Dieser bietet vor allem <9>: '
                'Dokumentationen, <10>, Opern, Theateraufführungen und anspruchsvolle <11>.',
                ['sich zu informieren', 'sich zu unterhalten', 'sich zu bilden', 'öffentlich',
                 'ihr Programm zu finanzieren', 'Werbeeinnahmen', 'Unterhaltung', 'Kulturkanal',
                 'Kultur', 'Reportagen', 'Filme'],
                ['sich zu informieren', 'sich zu unterhalten', 'sich zu bilden', 'öffentlich',
                 'ihr Programm zu finanzieren', 'Werbeeinnahmen', 'Unterhaltung', 'Kulturkanal',
                 'Kultur', 'Reportagen|Konzerte', 'Filme'])],
     'note': '⚠️ 音频未含在照片内：答案为按上下文推定（三大功能「获取信息 / 娱乐 / 增长知识」、'
             '公共广播 öffentlich-rechtlich、私营台靠广告、Arte 为德法文化频道），请以教材配套音频原文或'
             '听力原文为准。'},

    {'n': 7, 'kind': 'trans',
     'title': 'Ü8 翻译：大众传媒（德译中）',
     'src': '教材 S.302 · Ü8',
     'instruction': '先自己译，再点「💬 参考译文」核对。',
     'note': '⚠️ 教材未附译文：以下是参考译文（非教材标准答案）。',
     'items': [
         ['Traditionell werden Zeitung, Rundfunk und Fernsehen als Massenmedien betrachtet.',
          '传统上，报纸、广播和电视被视为大众传媒。'],
         ['Sie nutzen technische Mittel, um Nachrichten einer breiten Öffentlichkeit zu übermitteln.',
          '它们借助技术手段把新闻传递给广大的公众。'],
         ['Ihre Funktionen umfassen Informationsverbreitung, Meinungsbildung, Kritik und Kontrolle, '
          'Bildung und Unterhaltung.',
          '其功能包括信息传播、舆论形成、批评与监督、教育以及娱乐。'],
         ['Allerdings ist zu bedenken, dass Medien und die dahinterstehenden Personen nicht '
          'zwangsläufig altruistisch handeln; daher sollten wir eine kritische Haltung einnehmen '
          'und bereit sein, in möglichen Fällen unterschiedliche Berichte und Standpunkte '
          'miteinander zu vergleichen.',
          '不过应当考虑到，媒体以及媒体背后的人并不一定会无私行事；因此我们应当采取批判的态度，'
          '并愿意在可能的情况下把不同的报道和观点相互比较。'],
     ],
     'redemittel': {'title': 'Redemittel · 口头归纳媒体功能（教材 S.301 · Ü7 提示框，原文照录）',
                    'items': [
                        ['informieren / unterhalten / bilden / kritisieren / kontrollieren …', '可用动词'],
                        ['um … zu / damit …', '目的句'],
                        ['zum einen … zum anderen / außerdem / darüber hinaus / auch / '
                         'einerseits … andererseits …', '连接手段'],
                    ]}},
]


# ================================================================ 课文讲解（结构 / 重点句）
T1_STRUCT = [
    ['引言', 'Museum für Kommunikation Berlin',
     '杨芳和劳拉参观柏林通信博物馆；一次导览带她们走过人类沟通的发展史。'],
    ['1900', 'Briefe: Post, Dampfschiff, Eisenbahn, Pferd und Kutsche',
     '写信 → 寄信 → 等信：用轮船、铁路甚至马车运送，常常要等上几个星期。'],
    ['1923', 'Das Radio – eine bahnbrechende Erfindung',
     '收音机来到德国：起初并非人人都有，每台都必须获批；1970 年代才成为普通家用电器。'],
    ['1950', 'Das Fernsehen löst das Radio ab',
     '黑白电视又贵、频道又少；人们只能挤在商店橱窗前看新闻。'],
    ['1970', 'Das Telefon – vom Luxusgegenstand zum Handy',
     '电话曾是买不起的奢侈品，公共电话亭写进了街景；今天几乎人人用手机通话。'],
    ['1990', 'Der Durchbruch des Internets',
     '1990 年起互联网彻底改变了沟通；数字媒体已无法想象没有它的生活。'],
]

T1_QUOTES = [
    ['Passiv（现在时）', 'Durch einen geführten Rundgang werden sie über die Entwicklung der '
     'menschlichen Kommunikation informiert.',
     '在一次导览中，他们了解了人类沟通的发展历程。', '教材 S.291 · Text 1 · Ü6 第 1–2 空'],
    ['Passiv（过去时）', 'Vor 100 Jahren wurden viele Briefe geschrieben und mit der Post geschickt.',
     '100 年前人们写了很多信，并通过邮局寄出。', '教材 S.291 · Text 1 · Ü6 第 3–5 空'],
    ['Modalverb + Passiv', 'Eine gewisse Zeit lang musste jedes Radio genehmigt werden.',
     '有一段时间，每台收音机都必须获得许可。', '教材 S.292 · Text 1 · Ü6 第 8–9 空'],
    ['Infinitiv mit zu', 'Um 1950 begann das Fernsehen, das Radio langsam als beliebtestes Medium '
     'abzulösen.',
     '约 1950 年起，电视开始慢慢取代收音机成为最受欢迎的媒体。', '教材 S.292 · Text 1 · Ü6 第 10 空'],
    ['固定搭配', 'Mittlerweile sind sie aus dem Leben nicht mehr wegzudenken.',
     '如今它们已经无法想象会从生活中缺失。', '教材 S.292 · Text 1 · Ü6 第 23 空'],
]

T2_STRUCT = [
    ['引言', 'Massenmedien und ihr gemeinsames Merkmal',
     '报刊、广播、电视统称大众传媒：借助技术手段把最新内容带给广大受众。'],
    ['①', 'Informationsfunktion',
     '传播政治、经济、文化信息，尽可能全面、客观、易懂地告知受众。'],
    ['②', 'Meinungsbildungsfunktion',
     '让公共议题在自由公开的讨论中被探讨，让不同利益群体的意见进入公共领域。'],
    ['③', 'Kritik- und Kontrollfunktion',
     '追问政治决策、批评弊端，从而监督政治家的工作。'],
    ['④', 'Bildungsfunktion',
     '提供文化节目：纪录片、报道、杂志、音乐会、歌剧、戏剧演出和严肃影片。'],
    ['⑤', 'Unterhaltungsfunktion',
     '打开电视一为增长知识，二为娱乐放松。'],
    ['⚠️', 'Die Personen hinter den Medien',
     '媒体及其背后的人并非自动中立：要持批判态度，并愿意比较不同的表述。'],
]

T2_QUOTES = [
    ['Passiv + als', 'Traditionellerweise werden Presse, Rundfunk und Fernsehen als Massenmedien '
     'bezeichnet.', '传统上，报刊、广播和电视被称为大众传媒。',
     '教材 S.299 · Text 2 · Ü4（bezeichnen + als）'],
    ['Infinitiv mit zu', 'Ihr gemeinsames Merkmal ist, aktuelle Inhalte mit technischen Hilfsmitteln '
     'einem breiten Publikum zugänglich zu machen.',
     '它们的共同特征是：用技术手段让广大受众能获得最新内容。', '教材 S.299 · Text 2'],
    ['sollen + Infinitiv', 'Zum einen sollen sie Informationen über Politik, Wirtschaft und Kultur '
     'verbreiten.', '首先，它们应当传播政治、经济和文化方面的信息。', '教材 S.299 · Text 2 · Ü4 第 1 空'],
    ['sorgen dafür, dass', 'Bei der Meinungsbildung sollen die Massenmedien dafür sorgen, dass '
     'Fragen von öffentlichem Interesse in freier und offener Diskussion erörtert werden.',
     '在舆论形成方面，大众传媒应当让涉及公共利益的议题在自由公开的讨论中得到探讨。',
     '教材 S.299 · Text 2'],
    ['um … zu + Infinitiv', 'Sie sollen politische Entscheidungen hinterfragen und Missstände '
     'kritisieren, um dadurch die Arbeit der Politikerinnen und Politiker zu kontrollieren.',
     '它们应当追问政治决策、批评弊端，以此监督政治家的工作。', '教材 S.300 · Text 2 · Ü4'],
    ['einerseits … andererseits', 'Man schaltet ein, um sich einerseits zu bilden und um sich '
     'andererseits auch zu unterhalten und zu entspannen.',
     '人们打开电视，一方面是为了增长知识，另一方面也是为了娱乐和放松。',
     '教材 S.300 · Text 2 · Ü4 第 10–11 空'],
    ['Haltung einnehmen', 'Daher ist es wichtig, dass man gegenüber den Medien eine kritische '
     'Haltung einnimmt.', '因此，对媒体采取批判的态度是很重要的。', '教材 S.300 · Text 2（旁注框）'],
]

# ================================================================ 词表分组
VOCAB_GROUPS = [
    ['V1', '📱 媒体与设备 · Medien nutzen', 1, 22, PAIRS296, '教材 S.296 · Lektion 10 词汇表（Text 1 部分）'],
    ['V2', '📮 通信发展史 · Post & Verkehr', 23, 42, PAIRS296, '教材 S.296 · Lektion 10 词汇表（Text 1 部分）'],
    ['V3', '📡 从发明到网络 · Erfindung & Internet', 43, 64, PAIRS296, '教材 S.296 · Lektion 10 词汇表（Text 1 部分）'],
    ['V4', '🧠 媒体素养 · Kritisch nutzen', 65, 77, PAIRS296, '教材 S.296 · Lektion 10 词汇表（Text 1 部分）'],
    ['V5', '🗂️ 基础词汇 · Grundwortschatz', 1, 10, PAIRS303, '教材 S.303 · Lektion 10 词汇表（Text 2 部分）'],
    ['V6', '📺 功能与传播 · Funktionen', 11, 32, PAIRS303, '教材 S.303 · Lektion 10 词汇表（Text 2 部分）'],
    ['V7', '🎭 文化与评价 · Kultur & Haltung', 33, 52, PAIRS303, '教材 S.303 · Lektion 10 词汇表（Text 2 部分）'],
]

# ================================================================ 语法（按课文与练习归纳）
GRAMMAR_TABLES = [
    {'title': '被动语态：werden + 过去分词（Partizip II）',
     'src': '教材 Lektion 10 · Text 1 / Ü6 / Ü9 归纳（语法页未含在照片内）',
     'headers': ['时态', '构成', '课文例句', '中文'],
     'rows': [
         ['Präsens', 'werden + Partizip II',
          'Durch einen Rundgang %%werden%% sie %%informiert%%.', '他们被讲解/获得介绍。'],
         ['Präteritum', 'wurden + Partizip II',
          'Vor 100 Jahren %%wurden%% viele Briefe %%geschrieben%%.', '100 年前人们写了很多信。'],
         ['Perfekt', 'sein + Partizip II + worden',
          'Die Briefe %%sind%% mit der Post %%geschickt worden%%.', '这些信是经邮局寄出的。'],
         ['mit Modalverb', 'Modalverb + Partizip II + werden',
          'Jedes Radio %%musste%% %%genehmigt%% %%werden%%.', '每台收音机都必须获得许可。'],
         ['mit Agens', 'von + Dativ（施事）',
          'Alte Kommunikationswege werden %%von neuen Medien%% ersetzt.', '旧沟通方式被新媒体取代。'],
     ]},
    {'title': '被动 → 主动：man 作主语的改写',
     'src': '教材 S.294 · Ü9 归纳（教材只给 Beispiel）',
     'headers': ['被动句', '主动句（改写）', '要点'],
     'rows': [
         ['Vor 100 Jahren %%wurden%% viele Briefe %%geschrieben%% und mit der Post %%geschickt%%.',
          'Vor 100 Jahren %%schrieb%% man viele Briefe und %%schickte%% sie mit der Post.',
          '被动主语 → 主动宾语；施事用 man'],
         ['Es %%wurden%% viele Telefonzellen %%errichtet%%.',
          'Man %%errichtete%% viele Telefonzellen.', 'es 引导的被动句直接把宾语还原'],
         ['Alte Kommunikationswege werden %%von neuen Medien%% ersetzt.',
          '%%Neue Medien%% ersetzen alte Kommunikationswege.',
          '有 von + Dativ 时，施事可直接提为主语'],
     ]},
    {'title': 'Infinitiv mit zu（zu 不定式）',
     'src': '教材 Lektion 10 · Text 1 / Ü6 归纳',
     'headers': ['情形', '形式', '例句'],
     'rows': [
         ['一般动词', 'zu + Infinitiv',
          'Es ist wichtig, Quellen zu %%überprüfen%%.'],
         ['可分动词', '前缀 + zu + 词干（zu 插在中间）',
          'Das Fernsehen begann, das Radio %%abzulösen%%.'],
         ['带 zu 的固定搭配', 'bereit sein, … zu / beginnen, … zu / versuchen, … zu',
          'Man ist bereit, verschiedene Darstellungen zu %%vergleichen%%.'],
         ['zu + 形容词/名词', 'etwas ist (nicht) zu + Infinitiv',
          'Allerdings ist zu %%bedenken%%, dass …（值得考虑的是……）'],
     ]},
    {'title': 'um … zu + Infinitiv：表目的（主语一致）',
     'src': '教材 S.301 · Ü6 / Text 2 归纳',
     'headers': ['结构', '要点', '课文例句'],
     'rows': [
         ['主句 + , um … zu + Infinitiv', '两个动作的主语必须相同',
          'Man schaltet ein, um sich zu %%bilden%%.'],
         ['可分动词', 'zu 插在中间',
          'um neues Wissen zu %%verbreiten%%'],
         ['同时有两个目的', '第二个目的也用 um … zu，并且 um 要重复',
          'um sich einerseits zu %%bilden%% und um sich andererseits auch zu %%unterhalten%%'],
     ]},
    {'title': 'damit + 从句：表目的（主语可以不同）',
     'src': '教材 S.301 · Ü6 / Text 2 归纳',
     'headers': ['结构', '要点', '课文例句'],
     'rows': [
         ['主句 + , damit + 从句（动词居末）', '主句与从句主语不同时用 damit',
          'Er ist in die Stadt gezogen, damit seine Kinder mehr %%Bildungschancen haben%%.'],
         ['damit 从句用被动', '主语仍然不同，但从句是被动式',
          'damit Informationen %%verbreitet werden%%'],
         ['从句语序', '动词（或动词组合的最后一部分）位于句末', 'damit man sich %%bildet%%'],
     ]},
    {'title': 'um … zu 还是 damit？选择条件',
     'src': '教材 S.300 旁注两个问题 + S.301 Ü6',
     'headers': ['判断', '选择', '例句'],
     'rows': [
         ['两个句子主语相同', '→ um … zu + Infinitiv',
          'Wir brauchen die Massenmedien, um uns zu %%informieren%%.'],
         ['两个句子主语不同', '→ damit + 从句',
          'Wir brauchen die Massenmedien, damit das Publikum %%informiert wird%%.'],
         ['想强调“目的”且要被动', '→ damit + 从句（被动）',
          'damit aktuelle Inhalte %%zugänglich gemacht werden%%'],
     ]},
]

GRAMMAR_EXAMPLES = [
    ['Durch einen Rundgang werden sie über die Entwicklung der Kommunikation informiert.',
     '被动现在时：werden + 过去分词。'],
    ['Eine gewisse Zeit lang musste jedes Radio genehmigt werden.',
     '情态动词 + 被动：Modalverb + Partizip II + werden。'],
    ['Es wurden viele öffentliche Telefonzellen errichtet.',
     'es 引导的被动句，真正的主语在 werden 之后。'],
    ['Um 1950 begann das Fernsehen, das Radio langsam abzulösen.',
     'Infinitiv mit zu；可分动词 zu 放在中间。'],
    ['Man schaltet ein, um sich zu bilden und sich zu unterhalten.',
     'um … zu 表目的，主语一致。'],
    ['Er ist in die Stadt gezogen, damit seine Kinder mehr Bildungschancen haben.',
     'damit 表目的，两个主语不同。'],
]

# ================================================================ 连线（课文内容配对）
CONNECT_GRIDS = [
    {'title': '📅 通信时间轴 · Stationen der Kommunikation',
     'src': '教材 S.291–292 · Text 1（课文归纳）',
     'pairs': [['1900', 'Briefe: mit Dampfschiffen, Eisenbahnen, Pferden und Kutschen transportiert'],
               ['1923', 'Radio: eine bahnbrechende Erfindung, jedes Gerät musste genehmigt werden'],
               ['1950', 'Fernsehen: schwarz-weiß, teuer, nur bestimmte Sender'],
               ['1970', 'Telefon: vom Luxusgegenstand über die Telefonzelle zum Handy'],
               ['1990', 'Internet: der globale Durchbruch des Internets']]},
    {'title': '📺 媒体 ↔ 它做了什么 · Medium und Leistung',
     'src': '教材 S.291–292 · Text 1（课文归纳）',
     'pairs': [['Brief', 'Nachrichten überbringen – früher dauerte die Antwort wochenlang'],
               ['Radio', 'Musik, Nachrichten und Hörspiele senden; die Familie versammelte sich darum'],
               ['Fernsehen', 'Kultur zeigen: Dokumentationen, Reportagen, Opern und anspruchsvolle Filme'],
               ['Telefon', 'mit anderen Menschen sprechen – heute fast immer mit dem Handy'],
               ['Internet', 'Kommunikation und Information digital – nicht mehr wegzudenken']]},
    {'title': '🎯 五种功能 ↔ 中文 · Funktionen',
     'src': '教材 S.299–301 · Text 2 / Ü5 / Ü7',
     'pairs': [['Informationsfunktion', '信息功能：全面、客观、易懂地传播信息'],
               ['Meinungsbildungsfunktion', '舆论形成功能：让公共议题被自由公开地讨论'],
               ['Kritik- und Kontrollfunktion', '批评与监督功能：追问决策、批评弊端'],
               ['Bildungsfunktion', '教育功能：提供文化节目与知识'],
               ['Unterhaltungsfunktion', '娱乐功能：放松、消遣']]},
]

# ================================================================ 翻译卡
TRANSLATION_CARDS = [
    ['Durch einen geführten Rundgang werden sie über die Entwicklung der menschlichen '
     'Kommunikation informiert.', '在一次导览中，他们了解了人类沟通的发展历程。',
     '被动语态：werden + Partizip II', '教材 S.291 · Text 1'],
    ['Vor 100 Jahren wurden viele Briefe geschrieben und mit der Post geschickt.',
     '100 年前人们写了很多信，并通过邮局寄出。', '过去时被动 + 并列句', '教材 S.291 · Text 1'],
    ['Eine gewisse Zeit lang musste jedes Radio genehmigt werden.',
     '有一段时间，每台收音机都必须获得许可。', '情态动词 + 被动', '教材 S.292 · Text 1'],
    ['Um 1950 begann das Fernsehen, das Radio langsam als beliebtestes Medium abzulösen.',
     '约 1950 年起，电视开始慢慢取代收音机成为最受欢迎的媒体。', 'Infinitiv mit zu', '教材 S.292 · Text 1'],
    ['Viele Familien konnten sich so ein teures Gerät gar nicht leisten.',
     '许多家庭根本买不起这么贵的设备。', 'sich etwas leisten können', '教材 S.292 · Text 1'],
    ['Diese konnten an einer Hand abgezählt werden.',
     '这些（频道）用一只手就能数得过来。', '被动 + 情态动词；an einer Hand abzählen', '教材 S.292 · Text 1'],
    ['Mittlerweile sind sie aus dem Leben nicht mehr wegzudenken.',
     '如今它们已经无法想象会从生活中缺失。', 'nicht wegzudenken sein', '教材 S.292 · Text 1'],
    ['Alte Kommunikationswege werden immer mehr von neuen Medien ersetzt.',
     '旧的沟通方式越来越多地被新媒体取代。', '被动 + von + Dativ（施事）', '教材 S.292 · Text 1'],
    ['Traditionellerweise werden Presse, Rundfunk und Fernsehen als Massenmedien bezeichnet.',
     '传统上，报刊、广播和电视被称为大众传媒。', 'bezeichnen + als', '教材 S.299 · Text 2'],
    ['Ihr gemeinsames Merkmal ist, aktuelle Inhalte mit technischen Hilfsmitteln einem breiten '
     'Publikum zugänglich zu machen.',
     '它们的共同特征是：用技术手段让广大受众能获得最新内容。',
     'Infinitiv mit zu + 双宾语（Dativ/Akkusativ）', '教材 S.299 · Text 2'],
    ['Die Massenmedien sollen das Publikum so vollständig, sachlich und verständlich wie möglich '
     'informieren.', '大众传媒应当尽可能全面、客观、易懂地告知受众。', 'so … wie möglich', '教材 S.299 · Text 2'],
    ['Sie sollen politische Entscheidungen hinterfragen und Missstände kritisieren, um dadurch '
     'die Arbeit der Politikerinnen und Politiker zu kontrollieren.',
     '它们应当追问政治决策、批评弊端，以此监督政治家的工作。', 'um … zu + Infinitiv', '教材 S.300 · Text 2'],
    ['Man schaltet ein, um sich einerseits zu bilden und um sich andererseits auch zu unterhalten '
     'und zu entspannen.',
     '人们打开电视，一方面是为了增长知识，另一方面也是为了娱乐和放松。',
     'einerseits … andererseits；um … zu', '教材 S.300 · Text 2'],
    ['Daher ist es wichtig, dass man gegenüber den Medien eine kritische Haltung einnimmt.',
     '因此，对媒体采取批判的态度是很重要的。', 'eine Haltung einnehmen；dass 从句', '教材 S.300 · Text 2'],
]


# ================================================================ 组装
def cloze_of(paras):
    return [{'p': p, 'ans': a} for p, a in paras]


def check_numbering(paras, label):
    """[[n]] 编号必须与 ans 总数、顺序一一对上（防漏填/错位）。"""
    seq = []
    for p, a in paras:
        seq += [int(x) for x in re.findall(r'\[\[(\d+)\]\]', p)]
    n = sum(len(a) for _, a in paras)
    assert seq == list(range(1, n + 1)), '%s: 空号不连续 %s (共 %d 空)' % (label, seq[:40], n)
    return n


def fill_blanks(paras):
    """把 [[n]] 换回答案 → 用于查词条形态与例句（空白处也要能查到词）。"""
    out = []
    for p, ans in paras:
        i = [0]

        def rep(m, ans=ans, i=i):
            v = ans[i[0]]
            i[0] += 1
            return v

        out.append(re.sub(r'\[\[(\d+)\]\]', rep, p))
    return ' '.join(out)


def main():
    n1 = check_numbering(T1_PARAS, 'T1')
    n2 = check_numbering(T2_PARAS, 'T2')
    t1_text = fill_blanks(T1_PARAS)
    t2_text = fill_blanks(T2_PARAS) + ' ' + T2_BOX + ' ' + ' '.join(T2_QBEX)

    src_t1 = '教材 S.296 · Lektion 10 词汇表（Text 1 部分）'
    src_t2 = '教材 S.303 · Lektion 10 词汇表（Text 2 部分）'
    src_ex = '课件补充（教材词表未列，供理解用）'

    g1 = build_glossar(t1_text, PAIRS296, src_ex, src_t1)
    g2 = build_glossar(t2_text, PAIRS303, src_ex, src_t2)

    groups = []
    for gid, label, a, b, pairs, src in VOCAB_GROUPS:
        src_pairs = PAIRS296 if 'S.296' in src else PAIRS303
        ents = ENTRIES296 if 'S.296' in src else ENTRIES303
        words = []
        for i in range(a - 1, b):
            assert ents[i]['w'] == pairs[i][0], '词表切片错位: %s' % pairs[i][0]
            words.append({'w': ents[i]['raw'], 'cn': ents[i]['cn']})
        assert len(words) == b - a + 1, gid
        groups.append({'id': gid, 'label': label, 'src': src, 'words': words})

    d = {
        'meta': {
            'lektion': '10',
            'title': 'Diese Medien sind mir wichtig!',
            'subtitle': 'Lektion 10 · 大众传媒 · Text 1 沟通的今昔 · Text 2 大众传媒的功能',
            'source': '《新经典德语》第二册 Lektion 10 · Diese Medien sind mir wichtig!'
                      '（教材 S.291–296 · S.299–303）',
            'objectives': [
                '读懂 Text 1「Kommunikation früher und heute」：五个时间节点上的媒体与它带来的变化',
                '读懂 Text 2「Funktionen der Massenmedien」：五种功能各是什么、由哪些动词支撑',
                '会用被动语态（werden + 过去分词）描述过程，并能在被动句与主动句之间转换',
                '会用 um … zu / damit 表达目的，并说清两者的选择条件（主语是否一致）',
                '掌握本单元词表的高频词与固定搭配（S.296 77 条 / S.303 52 条）',
            ],
            'flow': [
                '① 🏠 首页：先看学习路线，45 分钟走完',
                '② 📖 T1 课文：读五个时间节点，点词看释义与课文原句',
                '③ ✍️ T1 练习：词库完形 → Wendungen 配对 → 归纳表 → 被动改主动 → 填空 → 翻译',
                '④ 📺 T2 课文：读五种功能，读旁注框里「媒体背后的人」',
                '⑤ ✅ T2 练习：词库完形 → 功能归类 → um…zu/damit 造句 → 动词填空 → 翻译',
                '⑥ 🃏 词汇卡：129 词分 7 组，点卡片翻面',
                '⑦ 🔤 语法：被动语态 + zu 不定式 + um…zu/damit 选择条件（6 张表）',
                '⑧ 🔗 连线：时间轴 / 媒体与功能 / 五种功能',
                '⑨ 🎯 翻译卡：14 张课文关键句，先自己译再翻面',
            ],
        },
        't1': {
            'title': 'Kommunikation früher und heute',
            'sub': '沟通的今昔',
            'kind': '教材 S.291–292 · Text 1 · Ü6',
            'lead': '博物馆导览串起一百多年：1900 写信等回信 → 1923 收音机 → 1950 电视 → 1970 电话 → '
                    '1990 互联网。读的时候盯住两点：谁是施事（被动语态），以及每样新东西取代了什么。',
            'cloze': cloze_of(T1_PARAS),
            'alt': {str(k): v for k, v in T1_ALT.items()},
            'bank': T1_BANK,
            'glossar': g1,
            'structure': [{'n': a, 'de': b, 'cn': c} for a, b, c in T1_STRUCT],
            'quotes': [{'n': a, 'de': b, 'zh': c, 'src': e} for a, b, c, e in T1_QUOTES],
            'provenance': '课文按教材 S.291–292（Ü6）逐字录入，填空词直接印在横线上；'
                          '填空的横线位置与词库 14 词均照教材。',
        },
        't1ex': {'title': 'Text 1 练习 · Ü6 / Ü7 / Ü8 / Ü9 / Ü11 / Ü10',
                 'instruction': '六组练习按教材顺序做：先完形（Ü6），再配对（Ü7），再看归纳表（Ü8），'
                                '然后练被动改主动（Ü9），最后做填空（Ü11）和翻译（Ü10）。',
                 'src': '教材 S.291–295 · Entdecken 1',
                 'groups': sorted(T1EX, key=lambda g: g['n'])},
        't2': {
            'title': 'Funktionen der Massenmedien',
            'sub': '大众传媒的功能',
            'kind': '教材 S.299–300 · Text 2 · Ü4',
            'lead': '这段文字本身就是教材 Ü4 的完形题：11 个空、11 个词库词一一对应。读的时候按'
                    '「信息 → 舆论形成 → 批评与监督 → 教育 → 娱乐」五条线抓，最后读旁注框：'
                    '媒体背后的人并不自动中立。',
            'cloze': cloze_of(T2_PARAS),
            'alt': {'1': ['Informationen', 'Information']},
            'bank': T2_BANK,
            'box': T2_BOX,
            'qbox': T2_QBOX,
            'qbex': T2_QBEX,
            'glossar': g2,
            'structure': [{'n': a, 'de': b, 'cn': c} for a, b, c in T2_STRUCT],
            'quotes': [{'n': a, 'de': b, 'zh': c, 'src': e} for a, b, c, e in T2_QUOTES],
            'provenance': '课文按教材 S.299–300（Ü4）逐字录入；11 个空位与 11 个词库词均照教材，'
                          '答案由词库一一对应推出。旁注框与语法问题框照抄自 S.300。',
        },
        't2ex': {'title': 'Text 2 练习 · Ü4 / Ü5 / Ü6 / Ü7 / Ü9 / Ü8',
                 'instruction': '先做完形（Ü4）与语义填空（Ü5，含功能归类），再到用 um…zu / damit 造句（Ü6）'
                                '与口述归纳（Ü7），最后做电视两个填空（Ü9）与翻译（Ü8）。',
                 'src': '教材 S.299–302 · Entdecken 2',
                 'groups': sorted(T2EX, key=lambda g: g['n'])},
        'vocab': {
            'title': '词汇卡 · Wortschatz Lektion 10',
            'instruction': '点卡片翻面看中文；卡片右下角 ▶ 看词条与出处。词条照教材词表原样录入，'
                           '标注（复数词尾 / 读音 / 支配格）已降权显示。',
            'src': '教材 S.296（77 条）· 教材 S.303（52 条）· 共 129 条',
            'groups': groups,
        },
        'grammar': {'tables': GRAMMAR_TABLES, 'examples': [
            {'de': a, 'zh': b} for a, b in GRAMMAR_EXAMPLES]},
        'connectGrids': CONNECT_GRIDS,
        'translation': {
            'title': '翻译卡 · Übersetzen',
            'instruction': '先自己译，再点卡片翻面核对参考译文。译法不唯一，句型正确、意义完整即算对。',
            'note': '德文句子取自课文与教材练习；中文为参考译文（非教材标准答案）。',
            'cards': [{'de': a, 'zh': b, 'tip': c, 'src': e} for a, b, c, e in TRANSLATION_CARDS],
        },
    }

    OUT.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')

    print('T1: %d 段 / %d 空 / 词库 %d 词 / 可点词条 %d' % (len(T1_PARAS), n1, len(T1_BANK), len(g1)))
    print('T2: %d 段 / %d 空 / 词库 %d 词 / 可点词条 %d' % (len(T2_PARAS), n2, len(T2_BANK), len(g2)))
    print('词卡 %d 条 / %d 组' % (sum(len(g['words']) for g in groups), len(groups)))
    print('练习组: T1 %d + T2 %d' % (len(T1EX), len(T2EX)))
    kinds = {}
    for ex in T1EX + T2EX:
        kinds[ex['kind']] = kinds.get(ex['kind'], 0) + 1
    print('练习类型:', kinds)
    print('语法表 %d / 连线 %d 组 %d 对 / 翻译卡 %d' % (
        len(GRAMMAR_TABLES), len(CONNECT_GRIDS), sum(len(g['pairs']) for g in CONNECT_GRIDS),
        len(TRANSLATION_CARDS)))
    print('未进词表的补充词:', [w for w in EXTRAS if w not in {e['w'] for e in g1 + g2}])
    bad = [e['raw'] for e in ENTRIES296 + ENTRIES303
           if any(c in e['w'] for c in '(+-[') or e['w'].endswith(('(', '+', '-')) or not e['w']]
    print('词条切分存疑:', bad if bad else '无')
    print('写给:', OUT)


if __name__ == '__main__':
    main()
