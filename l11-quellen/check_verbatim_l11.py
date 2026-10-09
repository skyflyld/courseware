#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L11 引文逐字门：数据里的德文句子必须能在「教材页 OCR + 教师 PPT」里逐字找到。

源：/tmp/l11/ocr/*.txt（教材 12 页）+ /tmp/l11/vok/*.txt（词表页）+ /tmp/l11/ppt_text.txt（教师课件）

判据（教材页大量带填空横线，故用「分段命中」口径）：
  1. 归一化整句命中源 → 过
  2. 把教材的空位（_ _ _ / . . .）视作通配，句子按「已知答案词」切成若干段，
     每段（≥ 12 字符）都能在源里逐字命中 → 过（打印放行理由 = 该句含教材空位）
  3. 都不中 → FAIL（该句疑似自造，必须回查教材原页）
"""
import glob
import json
import os
import re
import sys

WS = '/home/gem/.openclaw/workspace'
DATA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(WS, 'skyflyld/l11-data.json')


def dehyph(t):
    """OCR/PPT 行末断词：后行小写 → 软连字符（去杠）；后行大写 → 复合词连字符（留杠）"""
    t = re.sub(r'-\s*\n\s*(?=[a-zäöüß])', '', t)
    t = re.sub(r'-\s*\n\s*(?=[A-ZÄÖÜ])', '-', t)
    return t


def norm(s):
    s = s.replace('\u00ad', '').replace('\u00a0', ' ')
    for a, b in (('„', '"'), ('“', '"'), ('”', '"'), ('’', "'"), ('‚', "'"),
                 ('–', '-'), ('—', '-'), ('−', '-'), ('…', '...'), ('´', "'"), ('`', "'"),
                 ('（', '('), ('）', ')'), ('：', ':'), ('，', ','), ('；', ';'), ('、', ','),
                 ('。', '.'), ('？', '?'), ('！', '!')):
        s = s.replace(a, b)
    s = re.sub(r'\s+', ' ', s)
    return s.strip().strip('.').strip()


HERE = os.path.dirname(os.path.abspath(__file__))
src = []
for p in (sorted(glob.glob(os.path.join(HERE, 'ocr/*.txt')))
          + sorted(glob.glob(os.path.join(HERE, 'vok/*.txt')))
          + [os.path.join(HERE, 'lektion11-ppt-text.txt')]):
    src.append(dehyph(open(p, encoding='utf-8', errors='replace').read()))
SRC = norm(' '.join(src))
# 教材空位（下划线串 / 省略号串 / PPT 里的 tab 分隔空）→ 通配
SRC_RE = re.sub(r'(?:_{2,}|\.{3,}|\s\u00a0)+', '\x00', SRC)
SRC_RE_L = SRC_RE.lower()

d = json.load(open(DATA, encoding='utf-8'))

# ---- 收集已知答案词（只取词库/答案本身，**不取句子文本**，否则会把正常词也切碎） ----
ANS = set()
EXTRA_ANS = ['eingeworfen', 'eingeladen', 'abgeholt', 'abzuschalten', 'angeschaut',
             'ausgeschaltet', 'gesendet', 'geteilt', 'gepostet']


def harvest(seq):
    for x in seq:
        if isinstance(x, str):
            for w in re.split(r'[|,]+', x):
                w = w.strip()
                if len(w) > 2:
                    ANS.add(w)
        elif isinstance(x, (list, tuple)):
            harvest(x)


for k in ('t1', 't2'):
    harvest([b['ans'] for b in d[k]['cloze']])
    harvest(list((d[k].get('alt') or {}).values()))
for ex in ('t1ex', 't2ex'):
    for g in d[ex]['groups']:
        harvest(g.get('bank') or [])
        harvest((g.get('alt') or {}).values())
        if not g.get('ref'):
            for it in g.get('paras') or []:
                harvest(it[1] if len(it) > 1 else [])
ANS |= set(EXTRA_ANS)
ANS_RE = re.compile(r'\b(?:%s)\b' % '|'.join(sorted((re.escape(a) for a in ANS), key=len, reverse=True)),
                    re.I) if ANS else None

fails, passes, gapped = [], 0, []


def segs_hit(s):
    segs = [norm(x) for x in re.split(r'\[\[\d+\]\]|<\d+>|[\n•]', s)]
    if ANS_RE:
        out = []
        for x in segs:
            out.extend(ANS_RE.split(x))
        segs = out
    segs = [x for x in segs if len(x) >= 12]
    if not segs:
        return 0
    if all(x in SRC_RE for x in segs):
        return 2
    if all(x.lower() in SRC_RE_L for x in segs):
        return 1          # 句首大小写差异（教材原句小写开头）
    return 0


def check(tag, s, strict=False):
    global passes
    sn = norm(s)
    if len(sn) < 10:
        return
    if re.search(r'[\u4e00-\u9fff]', sn) and not strict:
        return                      # 中文标签/说明行，跳过
    if any(ch in sn for ch in ('+', '→', '％')):
        return                      # 语法公式 / 箭头推导 / 公式行，不是引文
    if len(sn.split()) < 4:
        return                      # 太短，不足以当引文
    if sn in SRC:
        passes += 1
        return
    if segs_hit(s):
        gapped.append((tag, sn[:64]))
        passes += 1
        return
    fails.append((tag, sn[:170]))


t1, t2 = d['t1'], d['t2']
for k, t in (('T1', t1), ('T2', t2)):
    for i, b in enumerate(t['cloze'], 1):
        check('%s 课文 段%d' % (k, i), b['p'])
    for q in t['quotes']:
        check('%s 原句卡' % k, q['de'])
    for e in t['glossar']:
        check('%s 词条例句' % k, e.get('ex', ''))
    check('%s 旁注框' % k, t.get('box', ''))

for tb in d['grammar']['tables']:
    for r in tb['rows']:
        for c in r:
            cells = str(c).split(' / ') if '%%' in str(c) else []
            for piece in cells:
                check('语法表·例句', piece.replace('%%', ''))

for cg in d['connectGrids']:
    for a, _b in cg['pairs']:
        if a.count(' ') >= 3:                      # 只查整句配对
            check('连线·句', a)

for c in d['translation']['cards']:
    check('翻译卡', c['de'])

for ex in ('t1ex', 't2ex'):
    for g in d[ex]['groups']:
        for it in g.get('paras') or []:
            check('%s %s' % (ex, g['title'][:14]), it[0])
        for it in g.get('rows') or []:
            for c in it:
                check('%s %s' % (ex, g['title'][:14]), c)
        if g.get('beispiel'):
            check('%s Beispiel' % ex, re.sub(r'（.*?）', '', g['beispiel']).strip())
        for a, _b in g.get('pairs') or []:
            check('%s pairs' % ex, a)
        if g['kind'] == 'trans':
            for it in g.get('items') or []:
                check('%s trans' % ex, it[0])

print('源长度 = %d 字符 | 已知答案词 %d 个' % (len(SRC), len(ANS)))
print('逐字命中 %d 句（其中带教材空位分段放行 %d 句）' % (passes, len(gapped)))
for tg, s in gapped[:5]:
    print('  ↳ 含空位放行：%s | %s…' % (tg, s))
if fails:
    print('\n❌ 逐字未命中 %d 句：' % len(fails))
    for tg, s in fails:
        print('  - [%s] %s' % (tg, s))
    sys.exit(1)
print('\n✅ 全部德文逐字命中取证源（教材 OCR + 教师 PPT）')
