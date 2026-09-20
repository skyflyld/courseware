#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_l9_data.py — 生成 l9-data.json（Lektion 9 互动课件的唯一数据源）
输入: example_lektion9.json（2026-07 旧版课件数据，内容源）
输出: l9-data.json
纪律:
  · 德文/中文一律取源数据原值，不改写、不补造。
  · 课文段落的重点词从源数据的 %%…%% 标记机械推导（并扩展为文中实际词形），不人工增删。
  · 例句一律取自课文原句（该词所在的那句），不用源数据里被截断的 example 字段。
  · 我新增的只有「组织与呈现」：分组、学习路线、中文提示、参考译文（页面已标注为参考译文）。
"""
import json
import os
import re

DIR = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(DIR, 'example_lektion9.json')
OUT = os.path.join(DIR, 'l9-data.json')

TOKEN = r'A-Za-z\u00c4\u00d6\u00dc\u00e4\u00f6\u00fc\u00df0-9\-'


def load():
    with open(SRC, encoding='utf-8') as f:
        return json.load(f)


def expand_mark(para, start, end):
    """把 %%…%% 标记扩展成它在文中实际的完整词形（如 Austauschstudium + s → Austauschstudiums）"""
    l = start
    while l > 0 and re.match('[' + TOKEN + ']', para[l - 1]):
        l -= 1
    r = end
    while r < len(para) and re.match('[' + TOKEN + ']', para[r]):
        r += 1
    return para[l:r]


def sentences(paras):
    out = []
    for p in paras:
        plain = re.sub(r'%%(.+?)%%', r'\1', p)
        for s in re.split(r'(?<=[.!?»])\s+', plain):
            s = s.strip()
            if s:
                out.append(s)
    return out


def example_sentence(key, sents, surface):
    """该词所在的课文原句（优先含实际词形的句子，退回含词干的句子）"""
    stem = re.sub(r'[^' + TOKEN + r']', '', surface)[:max(4, len(surface) - 2)]
    for s in sents:
        if surface in s:
            return s
    for s in sents:
        if stem and stem in s:
            return s
    return ''


def build_text(raw_text, voc_by_key):
    """把一段课文转成 {paras:[带 %%surface|key%% 的段落], glossar:[词条]}"""
    paras, forms = [], {}
    for p in raw_text['paragraphs']:
        out, last = [], 0
        for m in re.finditer(r'%%(.+?)%%', p):
            key = m.group(1)
            surface = expand_mark(p, m.start(1), m.end(1))
            out.append(p[last:m.start()])
            out.append('%%' + surface + '|' + key + '%%')
            last = m.end()
            forms[surface] = key
        out.append(p[last:])
        paras.append(''.join(out))

    sents = sentences(raw_text['paragraphs'])
    glossar = []
    for surface, key in forms.items():
        v = voc_by_key.get(key.lower())
        if not v:
            continue
        ex = example_sentence(key, sents, surface) or v.get('example', '')
        entry = {'w': v['key'], 'zh': v['cn'], 'forms': [surface], 'ex': ex}
        if v.get('phrase'):
            entry['def'] = v['phrase']
        glossar.append(entry)
    # 词条按课文出现顺序
    order = {s: i for i, s in enumerate(forms)}
    glossar.sort(key=lambda e: order.get(e['forms'][0], 999))
    return {'paras': paras, 'glossar': glossar}


def split_dialogue(paras):
    """T2 是对话：按说话人切成轮次（Max / Personalchefin / Max fragt）"""
    turns = []
    for p in paras:
        parts = re.split(r'(?=(?:Max(?: fragt)?|Personalchefin):)', p)
        for seg in parts:
            seg = seg.strip()
            if not seg:
                continue
            m = re.match(r'^(Max(?: fragt)?|Personalchefin):\s*(.*)$', seg, re.S)
            if m:
                turns.append({'who': m.group(1), 'de': m.group(2).strip()})
            else:
                turns.append({'who': '', 'de': seg})
    return turns


# ---------------------------------------------------------------- 分组（仅组织，不改词）
G1 = ['Sinologie', 'Betriebswirtschaft', 'Humboldt-Universität', 'Wintersemester',
      'Fremdsprachenuniversität', 'Austauschstudium', 'Kenntnisse', 'interkulturellen Kompetenzen']
G2 = ['Praktikum', 'Filiale', 'Erfahrungen', 'sammeln', 'Betreuung', 'Trainerassistentin',
      'Sportverein', 'Tätigkeiten', 'Aufgaben', 'Organisation', 'Veranstaltungen',
      'Organisationsfähigkeiten', 'Kreativität', 'Verantwortungsbewusstsein']
G3 = ['Briefkopf', 'Betreff', 'Anrede', 'Einleitung', 'Hauptteil', 'Schluss', 'Gruß',
      'Unterschrift', 'Anlagen', 'Kultur-Assistenz']
G4 = ['Stellenanzeige', 'bewerben', 'Vorstellungsgespräch', 'Geschäftsmann', 'Messebranche',
      'Bachelorstudium', 'kreativ', 'Umgangsformen', 'Kontakt', 'Geschäftskontakte',
      'Englisch', 'Französisch', 'Spanisch', 'Schwächen', 'Berufsanfänger', 'Erfahrung',
      'ungeduldig', 'Abteilungen', 'verdienen', 'Entscheidung']

LUECKEN_ZH = {
    1: '在某所大学学习 → 地点用 an + 第三格',
    2: '「自……以来」（持续到现在）→ 时间介词 + 第三格',
    3: '「通过」实习（手段、途径）→ 介词 + 第二格',
    4: '「在……期间」→ 介词 + 第二格',
    5: '「在」一个体育协会工作 → 地点介词 + 第三格',
    6: '「从……起」（将来）→ 介词 + 第三格',
}

TRANSLATION_EXTRA = [
    {'de': '»Mit großem Interesse habe ich Ihre Anzeige gelesen und möchte mich um diese Stelle '
           'bewerben, da sie optimal zu meinen Interessen und Fähigkeiten passt.«',
     'zh': '我怀着极大的兴趣读了贵公司的招聘广告，希望申请这一职位，因为它与我的兴趣和能力非常契合。',
     'tip': '求职信 Einleitung 的套用句：Interesse 表达兴趣 + da 从句说明理由。',
     'src': '教材课文 T1 原句（引号内为求职信原文）· 中文为参考译文'},
    {'de': '»Ich bin sicher, dass ich meine Kenntnisse und Erfahrungen gewinnbringend in Ihrer '
           'Institution einbringen kann.«',
     'zh': '我相信，我能把自己的知识和经验富有成效地贡献给贵机构。',
     'tip': '求职信 Hauptteil/Schluss 的套用句：dass 从句 + einbringen（贡献、带入）。',
     'src': '教材课文 T1 原句 · 中文为参考译文'},
    {'de': '»Über eine Einladung zu einem Vorstellungsgespräch würde ich mich sehr freuen.«',
     'zh': '如能获邀参加面试，我将非常高兴。',
     'tip': '求职信 Schluss 的套用句：über + Akk + würde sich freuen（虚拟式客气表达）。',
     'src': '教材课文 T1 原句 · 中文为参考译文'},
    {'de': 'Ich bin Berufsanfänger und habe noch wenig Erfahrung. Ich bin etwas ungeduldig, weil '
           'ich Dinge immer schnell voranschreiten sehen will.',
     'zh': '我是职场新人，经验还很少。我有点性急，因为我总希望事情能快点推进。',
     'tip': '面试谈「不足」的示范：先说事实，再补一句它带来的好处（下文接着说 einarbeiten）。',
     'src': '教材课文 T2 原句 · 中文为参考译文'},
    {'de': 'Für mich ist es am wichtigsten, dass ich die Stelle bekomme.',
     'zh': '对我来说，最重要的是能得到这个职位。',
     'tip': '面试谈薪水的收尾句：es ist am wichtigsten, dass …（把重点从钱挪回岗位）。',
     'src': '教材课文 T2 原句 · 中文为参考译文'},
]


def strip_marks(p):
    return re.sub(r'%%(.+?)%%', lambda m: m.group(1).split('|')[0], p)


def dialogue_quote(turns, need):
    """从切好的对话轮次里取含某词的那一轮（说话人是 Max）"""
    for t in turns:
        if t['who'].startswith('Max') and need in strip_marks(t['de']):
            return strip_marks(t['de'])
    raise AssertionError('dialogue quote not found: ' + need)


def main():
    d = load()
    voc_by_key = {v['key'].lower(): v for v in d['vocab']}
    by_key = {v['key']: v for v in d['vocab']}

    t1_raw = [t for t in d['texts'] if t['id'] == 'T1'][0]
    t2_raw = [t for t in d['texts'] if t['id'] == 'T2'][0]
    t1 = build_text(t1_raw, voc_by_key)
    t2 = build_text(t2_raw, voc_by_key)
    t2['dialogue'] = split_dialogue(t2['paras'])

    # 求职信九部分（取自课文原句与连线数据的中文释义）
    grid = d['connectGrids'][0]['pairs']
    t1_struct = [{'n': str(i + 1), 'de': a, 'cn': b} for i, (a, b) in enumerate(grid)]

    groups = [
        {'id': 'G1', 'label': '🎓 学业与交换 · Studium & Austausch', 'src': '教材 Lektion 9 · Entdecken 1',
         'words': [{'w': k, 'cn': by_key[k]['cn']} for k in G1]},
        {'id': 'G2', 'label': '💼 实践与能力 · Praxis & Fähigkeiten', 'src': '教材 Lektion 9 · Entdecken 1',
         'words': [{'w': k, 'cn': by_key[k]['cn']} for k in G2]},
        {'id': 'G3', 'label': '✉️ 求职信 · Bewerbungsschreiben', 'src': '教材 Lektion 9 · Entdecken 1',
         'words': [{'w': k, 'cn': by_key[k]['cn']} for k in G3]},
        {'id': 'G4', 'label': '🤝 面试 · Vorstellungsgespräch', 'src': '教材 Lektion 9 · Entdecken 2',
         'words': [{'w': k, 'cn': by_key[k]['cn']} for k in G4]},
    ]
    n_grouped = sum(len(g['words']) for g in groups)
    assert n_grouped == len(d['vocab']), '分组词数 %d ≠ 词表 %d' % (n_grouped, len(d['vocab']))
    assert set(w['w'] for g in groups for w in g['words']) == set(by_key), '分组与词表不一致'

    # 连线：求职信九部分 / 面试五阶段 / 词汇配对（源数据原值）
    grids = [
        {'title': '✉️ 求职信的九个部分 · Teile des Bewerbungsschreibens',
         'pairs': d['connectGrids'][0]['pairs'], 'src': '教材 Lektion 9 · Entdecken 1'},
        {'title': '🤝 面试五阶段 · Fünf Phasen',
         'pairs': d['connectGrids'][1]['pairs'], 'src': '教材 Lektion 9 · Entdecken 2'},
        {'title': '🔤 词汇配对 · Wortpaare',
         'pairs': d['matchingPairs'], 'src': '教材 Lektion 9 词汇表'},
    ]

    fg = d['fillGaps'][0]
    luecken = {
        'title': '介词与连词填空 · Präpositionen ergänzen',
        'instruction': '在空位里填入合适的介词或连词，写完点 ✓ 核对。答案不唯一时，只要格和意义都对就算对（如「an der Universität」也可说「an einer Universität」）。',
        'src': '教材 Lektion 9 课文改编练习',
        'items': [{'n': i + 1, 'de': it['sentence'], 'ans': it['answer'], 'zh': LUECKEN_ZH.get(i + 1, '')}
                  for i, it in enumerate(fg['items'])],
    }

    quiz = {
        'title': '快问快答 · Textverständnis',
        'instruction': '先选一个，再点「检查」；答错的题会标红，正确答案同时标绿。',
        'src': '教材 Lektion 9 · Text 1 / Text 2',
        'items': [{'q': q['q'], 'opts': q['options'], 'a': 'ABCD'.index(q['answer'])} for q in d['quiz']],
    }

    trans_cards = [{'de': e['de'], 'zh': e['zh'], 'tip': '时间介词与 lassen 的例句（语法部分）',
                    'src': '教材 Lektion 9 语法例句'}
                   for e in d['grammar']['examples']] + TRANSLATION_EXTRA

    # 课文中可直接套用的原句（德文照抄，中文为参考译文）
    t1_quotes = [
        {'n': 'Einleitung（引言）', 'de': TRANSLATION_EXTRA[0]['de'].strip('»«'),
         'zh': TRANSLATION_EXTRA[0]['zh'], 'src': '教材课文 T1 · 求职信原文'},
        {'n': 'Schluss（结尾）',
         'de': TRANSLATION_EXTRA[1]['de'].strip('»«') + ' ' + TRANSLATION_EXTRA[2]['de'].strip('»«'),
         'zh': TRANSLATION_EXTRA[1]['zh'] + ' ' + TRANSLATION_EXTRA[2]['zh'],
         'src': '教材课文 T1 · 求职信原文'},
    ]
    dialog = t2['dialogue']
    t2_quotes = [
        {'n': 'Selbstpräsentation（说强项）', 'de': dialogue_quote(dialog, 'kreativ'),
         'zh': '我很有创造力，总有很多好点子。此外我举止得体，能很快与人建立联系，善于倾听，也能说服别人。'
               + '这对业务往来很重要。我会英语、法语和西班牙语。',
         'src': '教材课文 T2 · Max 原话'},
        {'n': 'Schwächen（说不足）', 'de': dialogue_quote(dialog, 'ungeduldig'),
         'zh': '我是职场新人，经验还很少。我有点性急，因为我总希望事情能快点推进。'
               + '不过这也许并不坏：我能很快融入一家新公司。',
         'src': '教材课文 T2 · Max 原话'},
        {'n': 'Rückfragen（反问）', 'de': dialogue_quote(dialog, 'Abteilungen'),
         'zh': '您觉得，作为一名市场助理，也有机会了解其他部门，这样好吗？',
         'src': '教材课文 T2 · Max 原话'},
    ]

    data = {
        'meta': {
            'lektion': '9',
            'title': 'Fit für die Bewerbung!',
            'subtitle': 'Lektion 9 · 求职与应聘 · 求职信 · 面试',
            'source': '《新经典德语》第二册 Lektion 9 · Fit für die Bewerbung!',
            'objectives': [
                '读懂一封求职信：九个组成部分与常用表达',
                '读懂一场面试：五个阶段的推进与常问的话',
                '用 lassen 的四种用法表达「让…做」「可以…」「放下」「别做」',
                '掌握时间介词 seit / während / durch / ab / bei / vorher 的格与用法',
                '能用德语说出自己的经历、长处与不足（面试自我介绍的素材）',
            ],
            'flow': [
                '📖 课文 T1：先读 Anna 的求职信，点生词看释义与例句',
                '👤 课文 T2：读 Max 的面试对话，按五个阶段抓脉络',
                '🃏 词汇卡：52 词分四组，点卡片翻面',
                '🔤 语法：lassen 四种用法 + 六个时间介词',
                '🔗 连线：求职信九部分 / 面试五阶段 / 词汇配对',
                '✍️ 填空 + ✅ 快问快答 + 🎯 翻译卡：检验与巩固',
            ],
        },
        't1': {
            'title': 'Text 1 · Anna hat ein Bewerbungsschreiben vorbereitet',
            'sub': '安娜准备了一封求职信',
            'kind': 'Entdecken 1',
            'lead': '求职信的读法：先看她是谁（学业 → 实践 → 能力），再看信本身怎么写：九个组成 + 开头与结尾两句原话。点正文里带虚线的德文词，看释义和例句。',
            'paras': t1['paras'],
            'glossar': t1['glossar'],
            'structure': t1_struct,
            'quotes': t1_quotes,
            'provenance': '课文取自教材 Lektion 9 Entdecken 1；重点词按教材原文标记，未增删。',
        },
        't2': {
            'title': 'Text 2 · Max kommt nun zum Vorstellungsgespräch',
            'sub': '马克斯来参加面试',
            'kind': 'Entdecken 2',
            'lead': '面试的读法：按五个阶段走（Begrüßung → Smalltalk → Selbstpräsentation → Rückfragen → Verabschiedung）。注意 Max 怎么说自己的强项与不足，以及他反问的那两个问题。',
            'paras': t2['paras'],
            'dialogue': t2['dialogue'],
            'glossar': t2['glossar'],
            'structure': [{'n': str(i + 1), 'de': a, 'cn': b} for i, (a, b) in
                          enumerate(d['connectGrids'][1]['pairs'])],
            'quotes': t2_quotes,
            'provenance': '课文取自教材 Lektion 9 Entdecken 2；对话按说话人分行，原文一字未改。',
        },
        'vocab': {
            'title': '词汇卡 · Wortschatzkarten（52 词）',
            'instruction': '点卡片翻面看中文。名词请带冠词读（der/die/das），动词请带支配格（+A / +D）。',
            'src': '教材 Lektion 9 · Entdecken 1 / Entdecken 2 词汇表（共 52 条）',
            'groups': groups,
        },
        'grammar': d['grammar'],
        'connectGrids': grids,
        'luecken': luecken,
        'quiz': quiz,
        'translation': {
            'title': '翻译卡 · Übersetzen',
            'instruction': '先自己译，再点卡片翻面核对参考译文。译法不唯一，句型正确、意义完整即算对。',
            'note': '德文句子取自课文与语法例句；中文为参考译文（非教材标准答案）。',
            'cards': trans_cards,
        },
    }

    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    print('wrote %s (%d bytes)' % (OUT, os.path.getsize(OUT)))
    print('vocab groups: %s (共 %d 词)' % ([len(g['words']) for g in groups], n_grouped))
    print('t1 glossar=%d paras=%d | t2 glossar=%d dialogue=%d'
          % (len(t1['glossar']), len(t1['paras']), len(t2['glossar']), len(t2['dialogue'])))
    print('connect pairs: %s | luecken=%d | quiz=%d | translation=%d'
          % ([len(g['pairs']) for g in grids], len(luecken['items']), len(quiz['items']), len(trans_cards)))


if __name__ == '__main__':
    main()
