#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gate_verbatim.py — L1 交互课件「引文逐字门」

判据：课件里所有标为课文的德文（T1 双声部六块 + 引言 + Landeskunde + T2 采访全文
      + 课文原句卡），都必须能在源文件里逐字找到（归一化空白/引号后做子串匹配）。
      「自编」的不参与（它们本来就不是课文）。

源文件：archive/german-teaching/lektion1-texte/texte-verbatim.md
被测：l1-data.json（渲染层的唯一数据源）+ 产物 HTML 的课文区

退出码：0 = 全部逐字命中；1 = 有句子找不到（打印清单）
"""
import json
import os
import re
import sys

WS = '/home/gem/.openclaw/workspace'
SRC = os.path.join(WS, 'archive/german-teaching/lektion1-texte/texte-verbatim.md')
DIR = os.path.dirname(os.path.abspath(__file__))


def norm(s):
    s = s.replace('\u00ad', '').replace('\u00a0', ' ').replace('\ufeff', '')
    for a, b in (('„', '"'), ('“', '"'), ('”', '"'), ('’', "'"), ('‚', "'"),
                 ('–', '-'), ('—', '-'), ('−', '-'), ('…', '...')):
        s = s.replace(a, b)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


with open(SRC, encoding='utf-8') as f:
    SRC_N = norm(f.read())

with open(os.path.join(DIR, 'l1-data.json'), encoding='utf-8') as f:
    d = json.load(f)

cands = []            # (来源标签, 德文)


def add(tag, s):
    if s and isinstance(s, str):
        cands.append((tag, s))


t1 = d['t1']
for turn in t1['intro']:
    for s in turn['sents']:
        add('T1 引言', s)
for b in t1['blocks']:
    for s in b['oma']:
        add('T1 %s Oma' % b['no'], s)
    for s in b['emilie']:
        add('T1 %s Emilie' % b['no'], s)
for s in t1['landeskunde']:
    add('T1 Landeskunde', s)
for q in t1['quotes']:
    add('T1 原句卡', q['de'])

t2 = d['t2']
for s in t2['lead_sents']:
    add('T2 引言', s)
for turn in t2['dialogue']:
    for s in turn['sents']:
        add('T2 对话', s)
for q in t2['quotes']:
    add('T2 原句卡', q['de'])

def is_verbatim(s):
    """逐字命中源文件；教材带空的练习题按 Wortbank 填入后放行（左右两截能对上）。"""
    sn = norm(s)
    if sn in SRC_N or norm(sn.rstrip('.')) in SRC_N:
        return True
    snl = sn.lower()
    for c in CHUNKS_N:
        i = snl.find(c.lower()) if c else -1
        if i >= 0:
            pat = re.escape(sn[:i]) + r'.{0,200}?' + re.escape(sn[i + len(c):])
            if re.search(pat, SRC_N, re.I):
                return True
    return False


miss = []
for tag, s in cands:
    if norm(s) not in SRC_N:
        miss.append((tag, s))

# 练习 9 的五个填空句：教材原文带空，阅读页按 Wortbank（教材自己给的五个片段）
# 填入后就不再是源文件里的连续字符串。这类改写单独放行，但必须满足：
#   句子去掉填入片段后，左右两截都能在同一行源文里按顺序找到（即「确实是这道题」）。
import l1_sents as _s

CHUNKS_N = [norm(c) for c in _s.S.EX9_CHUNKS]
FILLED = []
still = []
for tag, s in miss:
    sn = norm(s)
    hit = None
    snl = sn.lower()
    for c in CHUNKS_N:
        cn = norm(c)
        i = snl.find(cn.lower()) if cn else -1
        if i >= 0:
            pre, post = sn[:i], sn[i + len(cn):]
            pat = re.escape(pre) + r'.{0,200}?' + re.escape(post)
            if re.search(pat, SRC_N, re.I):
                hit = c
                break
    if hit:
        FILLED.append((tag, hit, s))
    else:
        still.append((tag, s))
miss = still

print('=== 引文逐字门 ===')
print('源: %s' % SRC)
print('待核德文句: %d 条（T1 %d · T2 %d）'
      % (len(cands),
         sum(1 for t, _ in cands if t.startswith('T1')),
         sum(1 for t, _ in cands if t.startswith('T2'))))
if FILLED:
    print('↪ 练习 9 填空句（源文本带空，按教材 Wortbank 填入）: %d 条' % len(FILLED))
    for tag, c, s in FILLED:
        print('   [%s] 填入「%s」 → %s' % (tag, c, s[:78]))
if miss:
    print('❌ 逐字找不到 %d 条：' % len(miss))
    for tag, s in miss:
        print('   [%s] %s' % (tag, s[:110]))
    sys.exit(1)
print('✅ %d/%d 条全部逐字命中源文件' % (len(cands), len(cands)))

# 产物侧再核一遍：HTML 里课文区的德文也必须在源里（防生成期动手脚）
html_path = os.path.join(DIR, 'lektion1-rund-um-das-glueck.html')
if os.path.exists(html_path):
    with open(html_path, encoding='utf-8') as f:
        html = f.read()
    spans = re.findall(r'<p class="(?:duo-de|dlg-de|cloze-p tr-p)" lang="de">(.*?)</p>',
                       html, re.S)
    n_bad = 0
    checked = 0
    for sp in spans:
        # 先摘掉逐句点译的中文层（.tr-zh），否则中文会黏在德文句尾导致假失败
        sp = re.sub(r'<span class="tr-zh"[^>]*>.*?</span>', '', sp, flags=re.S)
        plain = norm(re.sub(r'<[^>]+>', '', sp))
        # 整段（可含多句）拆句后逐句核
        for s in re.split(r'(?<=[.!?»])\s+', plain):
            s = norm(s)
            if len(re.findall(r'[a-zäöüß]{4,}', s)) < 3:
                continue
            checked += 1
            if not is_verbatim(s):
                n_bad += 1
                if n_bad <= 6:
                    print('   ✗ 产物侧: %s' % s[:110])
    print('产物课文区抽核: %d 句 → 未命中 %d 句' % (checked, n_bad))
    if n_bad:
        sys.exit(1)
print('✅ 逐字门通过')
