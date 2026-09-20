import json, re, sys
d = json.load(open('/home/gem/.openclaw/workspace/skyflyld/l9-data.json', encoding='utf-8'))
print('--- t1.paras[0] head:'); print(d['t1']['paras'][0][:260])
print('--- t1 glossar sample:'); print(json.dumps(d['t1']['glossar'][:2], ensure_ascii=False, indent=1))
print('--- t2 dialogue[0:4]'); print(json.dumps(d['t2']['dialogue'][:4], ensure_ascii=False, indent=1))
print('--- surface != key:')
n = 0
for t in ('t1', 't2'):
    for p in d[t]['paras']:
        for m in re.finditer(r'%%(.+?)%%', p):
            s, k = m.group(1).split('|')
            if s != k:
                print('   ', t, repr(s), '<=', k); n += 1
print('   count', n)
print('--- glossar 例句缺失:', [(t, e['w']) for t in ('t1','t2') for e in d[t]['glossar'] if not e.get('ex')])
print('--- t2 dialect who 种类:', sorted(set(x['who'] for x in d['t2']['dialogue'])))
print('--- t2 对话第一轮:', json.dumps(d['t2']['dialogue'][1], ensure_ascii=False)[:200])
print('--- luecken items[0]:', json.dumps(d['luecken']['items'][0], ensure_ascii=False))
print('--- grammar tables:', [t['title'] for t in d['grammar']['tables']])
print('--- translation cards:', len(d['translation']['cards']))
