#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""l1_sents.py — L1 课文句子切分（供逐句点译）

在 split_sent.py 的判据上加两条 L1 实测所需的处理：
  ① 缩写保护：Prof. / usw. / z. B. / Dr. / Nr. / Mio. 里的句点不当作句末
  ② 显式断点：源文本里的 ¦ 强制切句（教材里以句点收尾、但下一句以小写起头的那一处）
"""
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import l1_text_src as S

ABBR = ['Prof.', 'z. B.', 'bzw.', 'Dr.', 'Nr.', 'Mio.']
BOUND = re.compile(r'([.!?])([»«"„“”\']?)(\s+)')
_PH = '\u0007'


def split_sents(text):
    for i, a in enumerate(ABBR):
        text = text.replace(a, a[:-1] + _PH)          # 'Prof.' -> 'Prof\u0007'
    out = []
    for piece in text.split('¦'):
        start = 0
        for m in BOUND.finditer(piece):
            nxt = piece[m.end():m.end() + 1]
            if nxt and (nxt.isupper() or nxt in '»«"ÄÖÜ'):
                out.append(piece[start:m.end()])
                start = m.end()
        out.append(piece[start:])
    res = [s.replace(_PH, '.').strip() for s in out]
    return [s for s in res if s]


# 词库原样（正文里按句内位置调整首字母大小写）
CHUNK = {1: S.EX9_CHUNKS[2], 2: S.EX9_CHUNKS[1], 3: S.EX9_CHUNKS[0],
         4: S.EX9_CHUNKS[4], 5: S.EX9_CHUNKS[3]}
# 正文（阅读页）里的写法：句首大写；跟在「Das,」后面的用小写
CHUNK_INLINE = {1: 'was die Menschen in einem Land glücklich macht',
                2: 'Was sie früher glücklich machte',
                3: 'Wer genug zu essen und ein sicheres Zuhause hatte',
                4: 'Was das Glücksgefühl auslöst',
                5: 'Wer in solch einem Land lebt'}


def fill_chunks(t, table=None):
    table = table or CHUNK_INLINE
    return re.sub(r'\[\[(\d+)\]\]', lambda m: table[int(m.group(1))], t)


def t1_sources():
    """T1 的说话人轮次：[(who, 段落字符串), …]（who='' 为叙述行）"""
    out = list(S.T1_INTRO)
    for b in S.T1_BLOCKS:
        out.append(('Oma', b['oma']))
        out.append(('Emilie', b['emilie']))
    return out


def t2_sources():
    return [(who, fill_chunks(t)) for who, t in S.T2_DIALOGUE]


def all_sentences():
    res = {'t1': [], 't2': []}
    for who, t in t1_sources():
        res['t1'] += split_sents(t)
    res['t1'] += split_sents(S.T1_LANDESKUNDE)
    for who, t in t2_sources():
        res['t2'] += split_sents(t)
    res['t2'] += split_sents(S.T2_LEAD)
    return res


if __name__ == '__main__':
    s = all_sentences()
    with open('/tmp/l1build/sentences.txt', 'w', encoding='utf-8') as f:
        for k in ('t1', 't2'):
            f.write('=' * 30 + ' %s %d\n' % (k, len(s[k])))
            for i, x in enumerate(s[k], 1):
                f.write('%3d| %s\n' % (i, x))
    print('t1=%d t2=%d' % (len(s['t1']), len(s['t2'])))
