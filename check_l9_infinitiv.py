#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_l9_infinitiv.py — 「Infinitiv ohne zu」节例句出处机械核验

核验规则（逐字，不做意译比对）：
  · 出处「教材 L9 课文」→ 去 %% 标记、去对话引号与说话人前缀后，必须能在 l9-data.json / example_lektion9.json 里找到原文
  · 出处「真题 YYYY · Ⅳ-NN」→ 必须等于该年 OCR 语料第 NN 行题干把空位替换成答案后的整句
  · 出处「真题 YYYY · Ⅲ 阅读原文」→ 必须作为子串出现在该年 OCR 语料里
  · 地图表 → 必须命中「教材」或「真题」其中之一
  · 出处「通用例句」→ 不核验（作者自撰），单列出来供人复核

用法: python3 check_l9_infinitiv.py [l9-infinitiv.json]
退出码: 0 = 全部通过；1 = 有未命中
"""
import json
import os
import re
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
PGG = os.path.join(DIR, 'pgg', 'full')

ANSWER = {          # 空位答案（逐题抄自各年分析表，用于把题干还原成整句）
    ('2023', '43'): 'um',
    ('2023', '50'): 'können',
    ('2024', '41'): 'die',
    ('2024', '49'): 'um',
    ('2025', '42'): 'Statt',
    ('2026', '45'): 'lassen',
    ('2026', '47'): 'kommenden',
}


def norm(s):
    s = s.replace('\u00a0', ' ')
    s = s.replace('\u201e', '"').replace('\u201c', '"')
    s = s.replace('\u00bb', '').replace('\u00ab', '')
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


def strip_mark(s):
    return norm(re.sub(r'%%(.+?)%%', r'\1', s))


def load_corpus():
    blob = []
    for fn in ('l9-data.json', 'example_lektion9.json'):
        with open(os.path.join(DIR, fn), encoding='utf-8') as f:
            d = json.load(f)

        def walk(o):
            if isinstance(o, str):
                blob.append(strip_mark(o))
            elif isinstance(o, dict):
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(d)
    big = norm(' ‖ '.join(blob))
    return re.sub(r'(Personalchefin|Max|Anna)\s*:\s*', '', big)


def load_pgg(y):
    with open(os.path.join(PGG, '%s_A_full.md' % y), encoding='utf-8') as f:
        return f.read()


def stem_of(raw, num):
    """取 OCR 语料里第 num 题的题干行（逐字，保留空位）"""
    for line in raw.split('\n'):
        if re.match(r'^\s*%s\.\s' % num, line):
            return norm(re.sub(r'^\s*%s\.\s*' % num, '', line))
    return None


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DIR, 'l9-infinitiv.json')
    with open(path, encoding='utf-8') as f:
        d = json.load(f)

    corpus = load_corpus()
    pgg = {y: (load_pgg(y), norm(load_pgg(y))) for y in ('2023', '2024', '2025', '2026')}

    items = [(r[4], '地图表') for r in d['map']['rows']]
    for c in d['cards']:
        for b in c['blocks']:
            if b[0] == 'tbl' and b[1][-1] == '出处':
                ci = 0 if b[1][0] == '例句' else 1        # 「例句/中文/出处」或「类型/例/出处」
                for r in b[2]:
                    items.append((r[ci], r[-1]))

    # 所有「题干 + 答案」还原句（地图表自动判定时用）
    restored_all = set()
    for (y, n), ans in ANSWER.items():
        st = stem_of(pgg[y][0], n)
        if st and '________' in st:
            restored_all.add(norm(st.replace('________', ans)))

    hit = miss = skip = 0
    for de, where in items:
        de = norm(de)
        if where == '地图表':
            if de in corpus or de in restored_all or any(de in pgg[y][1] for y in pgg):
                hit += 1
            else:
                miss += 1
                print('❌ 地图表例句三处都查不到：%s' % de)
        elif where.startswith('教材'):
            if de in corpus:
                hit += 1
            else:
                miss += 1
                print('❌ 教材句未命中：%s' % de)
        elif where.startswith('真题') and '阅读' in where:
            year = re.search(r'(\d{4})', where).group(1)
            if de in pgg[year][1]:
                hit += 1
            else:
                miss += 1
                print('❌ 真题阅读原句未命中（%s）：%s' % (year, de))
        elif where.startswith('真题'):
            year = re.search(r'(\d{4})', where).group(1)
            num = re.search(r'-\s*(\d+)', where).group(1)
            ans = ANSWER.get((year, num))
            stem = stem_of(pgg[year][0], num)
            if ans is None or stem is None or '________' not in stem:
                miss += 1
                print('❌ 语料/答案缺失：%s（题干=%r）' % (where, stem))
                continue
            restored = norm(stem.replace('________', ans))
            if restored == de:
                hit += 1
            else:
                miss += 1
                print('❌ 真题句不一致：\n   页：%s\n   源：%s\n   ← %s' % (de, restored, where))
        else:
            skip += 1
            print('·  通用例句（不核验）：%s' % de)

    print('\n核验结果：命中 %d / 未命中 %d / 跳过 %d（通用例句）' % (hit, miss, skip))
    return 1 if miss else 0


if __name__ == '__main__':
    sys.exit(main())
