#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_l10_data.py — 生成 l10-data.json（Lektion 10《Funktionen der Massenmedien》互动课件的唯一数据源）
输入: example_lektion11_t2.json（2026-07 旧版课件数据，内容源；其 meta.lektion = "10"）
输出: l10-data.json
纪律:
  · 德文/中文一律取源数据原值，不改写、不补造。
  · 课文重点词从源数据的 %%…%% 标记机械推导（并扩展为文中实际词形），不人工增删。
  · 例句一律取自课文原句（该词所在的那句），不用源数据里被截断的 example 字段。
  · 我新增的只有「组织与呈现」：分组、学习路线、中文提示。
  · 出处标注只用可从手上证据读出来的编号；不可核实的留白（§18.8）。
"""
import json
import os
import re

DIR = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(DIR, 'example_lektion11_t2.json')
OUT = os.path.join(DIR, 'l10-data.json')

TOKEN = r'A-Za-z\u00c4\u00d6\u00dc\u00e4\u00f6\u00fc\u00df0-9\-'


def load():
    with open(SRC, encoding='utf-8') as f:
        return json.load(f)


def expand_mark(para, start, end):
    """把 %%…%% 标记扩展成它在文中实际的完整词形（如 Information + en → Informationen）"""
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
    stem = re.sub(r'[^' + TOKEN + r']', '', surface)[:max(4, len(surface) - 2)]
    for s in sents:
        if surface in s:
            return s
    for s in sents:
        if stem and stem in s:
            return s
    return ''


def build_text(raw_text, voc_by_key):
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
    order = {s: i for i, s in enumerate(forms)}
    glossar.sort(key=lambda e: order.get(e['forms'][0], 999))
    return {'paras': paras, 'glossar': glossar}


# ---------------------------------------------------------------- 分组（仅组织，不改词）
G1 = ['Traditionellerweise', 'Presse', 'Rundfunk', 'Fernsehen', 'Massenmedien', 'bezeichnet',
      'Merkmal', 'Inhalte', 'Hilfsmitteln', 'Publikum', 'zugänglich']
G2 = ['Aufgaben', 'erfüllen', 'Funktionen', 'Gesellschaft', 'ausüben', 'Informationen',
      'verbreiten', 'vollständig', 'sachlich', 'verständlich', 'informieren', 'Nutzerinnen',
      'Ereignisse', 'verfolgen']
G3 = ['Meinungsbildung', 'sorgen', 'Interesse', 'Diskussion', 'Meinungen', 'Interessengruppen',
      'Öffentlichkeit', 'Entscheidungen', 'hinterfragen', 'Missstände', 'aufdecken', 'kontrollieren']
G4 = ['Kultur', 'Dokumentationen', 'Reportagen', 'Opern', 'Theateraufführungen', 'bilden',
      'unterhalten', 'entspannen', 'neutral', 'kritische', 'Haltung', 'einnimmt', 'bereit',
      'Möglichkeit', 'Darstellungen', 'vergleichen', 'Bildungsfunktion', 'Interessen',
      'Kritik- und Kontrollfunktion', 'Nutzer', 'Unterhaltungsfunktion']

# 学习路线（我新增的组织层，不涉内容）
FLOW = [
    '课文：Funktionen der Massenmedien 七段 · 先通读，再点词看释义',
    '词汇卡：58 词分四组 · 点卡片翻面看中文',
    '语法：um … zu + Infinitiv / damit + Nebensatz / 用法区别',
    '连线：四个主题组 · 39 对（概念 / 五功能 / 核心动词 / 形容词与搭配）',
    '翻译卡：12 张 · 先自己译，再翻面核对参考译文',
]

# 中文提示（讲「怎么读」，不讲答案）
TEXT_LEAD = ('读法：先看大众传媒的定义（哪三种媒体、共同特征是什么），再按「五大功能」走一遍 —— '
             '信息 → 舆论 → 监督 → 教育 → 娱乐。注意每一段都在回答同一个问题：媒体为社会做了什么？')


def main():
    d = load()
    voc_by_key = {v['key'].lower(): v for v in d['vocab']}
    by_key = {v['key']: v for v in d['vocab']}

    raw = d['texts'][0]
    txt = build_text(raw, voc_by_key)

    groups = [
        {'id': 'G1', 'label': '📰 媒体与基本概念 · Medien & Grundbegriffe',
         'src': '教材 Lektion 10 · Funktionen der Massenmedien',
         'words': [{'w': k, 'cn': by_key[k]['cn']} for k in G1]},
        {'id': 'G2', 'label': '🎯 功能与信息 · Funktionen & Information',
         'src': '教材 Lektion 10 · Funktionen der Massenmedien',
         'words': [{'w': k, 'cn': by_key[k]['cn']} for k in G2]},
        {'id': 'G3', 'label': '🗣️ 舆论与监督 · Meinungsbildung & Kontrolle',
         'src': '教材 Lektion 10 · Funktionen der Massenmedien',
         'words': [{'w': k, 'cn': by_key[k]['cn']} for k in G3]},
        {'id': 'G4', 'label': '🎭 文化与娱乐 · Kultur & Unterhaltung',
         'src': '教材 Lektion 10 · Funktionen der Massenmedien',
         'words': [{'w': k, 'cn': by_key[k]['cn']} for k in G4]},
    ]
    n_grouped = sum(len(g['words']) for g in groups)
    assert n_grouped == len(d['vocab']), '分组词数 %d ≠ 词表 %d' % (n_grouped, len(d['vocab']))
    assert set(w['w'] for g in groups for w in g['words']) == set(by_key), '分组与词表不一致'

    grids = [{'title': g['title'], 'pairs': g['pairs'],
              'src': '教材 Lektion 10 · 改编练习'} for g in d['connectGrids']]

    GRAMMAR_SRC = {
        'um … zu + Infinitiv（目的从句·主语一致）': '教材 Lektion 10 · 语法（um … zu）',
        'damit + Nebensatz（目的从句·主语不同）': '教材 Lektion 10 · 语法（damit）',
        'Gebrauchsunterschied（用法区别）': '教材 Lektion 10 · 语法（用法区别）',
    }
    gram = dict(d['grammar'])
    gram['tables'] = [dict(tb, src=GRAMMAR_SRC.get(tb['title'], '教材 Lektion 10'))
                      for tb in d['grammar']['tables']]

    cards = [{'de': c['de'], 'zh': c['zh'], 'tip': c.get('vocab', ''),
              'src': '教材 Lektion 10 · 课文原句 · 中文为参考译文'} for c in d['translationCards']]

    meta = d['meta']
    out = {
        'meta': {
            'lektion': '10',
            'title': 'Lektion 10 · ' + meta['title'],
            'subtitle': meta['subtitle'],
            'source': '教材 Lektion 10《Funktionen der Massenmedien》· 课文 + 语法表 + 翻译练习（数据取自 2026-07 版课件数据）',
            'objectives': meta['objectives'],
            'flow': FLOW,
        },
        'text': {
            'title': 'Text · Funktionen der Massenmedien',
            'sub': '大众传媒的功能',
            'kind': 'Text · Funktionen der Massenmedien',
            'lead': TEXT_LEAD,
            'paras': txt['paras'],
            'glossar': txt['glossar'],
            'provenance': '课文取自教材 Lektion 10（Funktionen der Massenmedien）第 2 篇课文；重点词按原文标记。',
        },
        'vocab': {
            'title': '词汇卡 · Wortschatzkarten（%d 词）' % len(d['vocab']),
            'instruction': '点卡片翻面看中文。名词请带冠词读（der/die/das），动词请带支配格（+A / +D）。',
            'src': '教材 Lektion 10 · Funktionen der Massenmedien 词汇（共 %d 条）' % len(d['vocab']),
            'groups': groups,
        },
        'grammar': gram,
        'connectGrids': grids,
        'translation': {
            'title': '翻译卡 · Übersetzungskarten',
            'instruction': '先自己在纸上译一遍，再点卡片翻面核对参考译文（非教材标准答案）。',
            'src': '教材 Lektion 10 · 课文原句',
            'cards': cards,
        },
    }

    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('wrote %s (%d bytes)' % (OUT, os.path.getsize(OUT)))
    print('vocab groups: %s (共 %d 词)' % ([len(g['words']) for g in groups], len(d['vocab'])))
    print('text: 段落 %d · 可点词 %d' % (len(txt['paras']), len(txt['glossar'])))
    print('connect pairs: %s | 翻译卡 %d' % ([len(g['pairs']) for g in grids], len(cards)))
    print('grammar tables: %s' % [t['title'] for t in gram['tables']])


if __name__ == '__main__':
    main()
