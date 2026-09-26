#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""split_sent.py — 课文德文句子切分（供逐句点译数据层使用）

只做一件事：把 l9-data.json 的 T1 段落 / T2 对话切成句子列表（保留 %%…%% 标记）
判据：断点在 [.!?] (+可选收尾引号) 之后，且后续以空格 + 大写字母 / » 开头。
"""
import json
import os
import re
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
BOUND = re.compile(r'([.!?])([»«"„“”\']?)(\s+)')


def split_sentences(text):
    out, start = [], 0
    for m in BOUND.finditer(text):
        nxt = text[m.end():m.end() + 1]
        if nxt and (nxt.isupper() or nxt in '»«"ÄÖÜ'):
            out.append(text[start:m.end()])
            start = m.end()
    out.append(text[start:])
    return [s.strip() for s in out if s.strip()]


def plain(s):
    return re.sub(r'%%(.+?)%%', lambda m: m.group(1).split('|')[0], s)


def collect():
    d = json.load(open(os.path.join(DIR, 'l9-data.json'), encoding='utf-8'))
    res = {}
    for key in ('t1', 't2'):
        t = d[key]
        items = []
        if key == 't1':
            for p in t['paras']:
                items += split_sentences(p)
        else:
            for turn in t['dialogue']:
                items += split_sentences(turn['de'])
        res[key] = items
    return res


if __name__ == '__main__':
    r = collect()
    for k, v in r.items():
        print('==== %s: %d 句' % (k, len(v)))
        for i, s in enumerate(v):
            print('%s%d\t%s' % (k, i + 1, plain(s)))
