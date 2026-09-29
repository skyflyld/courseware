#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_l9_lassen.py — 生成 l9-lassen.json（Lektion 9 课件「lassen 用法」节的唯一数据源）

来源（三份，均为已核验内容，不重打、不改写）：
  1) 「五种用法地图」表 —— Sky 2026-09-29 提供的表格图，逐字转录（两路 OCR 独立复核一致）
  2) 第一章正文 —— tools/lassen_lean_data.py 的 OVERVIEW（总览表已由①取代，故不重复收录）
  3) 第二章正文 —— tools/lassen_lean_data.py 的 USAGE_CHAPTER（五节精讲，逐行照搬）

输出: l9-lassen.json（块 DSL，与 build_l9_bewerbung.py 的 sec_lassen() 对齐）
纪律: 德文/中文一律取源值原样；不新增例句、不改写解释。
"""
import importlib.util
import json
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(DIR, 'l9-lassen.json')
LEAN = os.environ.get('LASSEN_LEAN', '/home/gem/.openclaw/workspace/tools/lassen_lean_data.py')


def load_lean(path):
    d = os.path.dirname(os.path.abspath(path))
    if d not in sys.path:
        sys.path.insert(0, d)          # lassen_lean_data 依赖同目录的 lassen_data
    spec = importlib.util.spec_from_file_location('lassen_lean_data', path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules['lassen_lean_data'] = mod
    spec.loader.exec_module(mod)
    return mod


# ── ① 五种用法地图（Sky 提供表格，逐字转录）────────────────────────
MAP = {
    'title': '一张表记全：五种用法地图',
    'no': '1.3',
    'headers': ['#', '结构', '一句话规则', '中文', '例句'],
    'rows': [
        ['①', 'lassen + 四格 + 不定式', '别人动手', '让...做',
         'Ich lasse mein Auto reparieren.'],
        ['②', 'lassen + 四格 + 不定式', '我不拦', '允许 / 听任',
         'Lass mich bitte ausreden!'],
        ['③', 'sich lassen + 不定式', '东西「可被」做', '能被...',
         'Das Problem lässt sich lösen.'],
        ['④', 'sich（四格）+ 不定式 + lassen', '别人对我做', '让...给我做',
         'Ich lasse mich untersuchen.'],
        ['⑤', 'lassen 作独立动词 / 固定搭配', '只是状态，没有动作', '留下 / 离开',
         'Er hat mich stehen lassen.'],
    ],
    'rule': [
        '一句话规则（考试用）：',
        '① 主语动不动手？　动手 → 不用 lassen；不动手 → 用 lassen。',
        '② 动作用在谁身上？　别人 → ①②④　东西 → ③　根本没有动作、只有状态 → ⑤。',
    ],
    'lead': [
        ['p', 'lassen 的核心只有一条：**主语不亲自动手**——动作由别人完成，或者根本不发生。'
              '中文的「让」把三件事混在一起（我让某人做、我不拦某人做、这事能被做），'
              '德语都用 lassen 覆盖，原因就在这里。'],
    ],
    'tail': [
        ['p', '① 与 ② 的结构完全相同，只能靠语义分辨——这是本考点最大的坑。'],
    ],
}


def main():
    lean = load_lean(LEAN)

    # 第二章正文按 h2 切卡；第一章正文进 map.lead / map.tail，第一章总览表由 MAP 取代
    cards = []
    cur = None
    for blk in lean.USAGE_CHAPTER:
        if blk[0] == 'h1':
            continue
        if blk[0] == 'h2':
            cur = {'title': blk[1], 'blocks': []}
            cards.append(cur)
            continue
        if cur is None:
            continue
        cur['blocks'].append(list(blk))

    data = {
        'title': 'lassen 用法',
        'nav': '🔧 lassen 用法',
        'icon': '🔧',
        'num': 6,
        'lead': 'lassen 的核心只有一条：主语不亲自动手——动作由别人完成，或者根本不发生。',
        'map': MAP,
        'cards': cards,
        'src': 'lassen 专四考点精讲 · 第一章 / 第二章',
    }

    n_tbl = sum(1 for c in cards for b in c['blocks'] if b[0] == 'tbl')
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('wrote %s (%d bytes)' % (OUT, os.path.getsize(OUT)))
    print('地图行=%d | 卡片=%d | 表=%d | 例句总数=%d'
          % (len(MAP['rows']), len(cards), n_tbl + 1,
             len(MAP['rows']) + sum(len(b[2]) for c in cards for b in c['blocks'] if b[0] == 'tbl')))
    print('卡片标题: %s' % [c['title'] for c in cards])


if __name__ == '__main__':
    main()
