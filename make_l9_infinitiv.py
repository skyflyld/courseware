#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_l9_infinitiv.py — 生成 l9-infinitiv.json（Lektion 9 课件「Infinitiv ohne zu」节的唯一数据源）

标准与「lassen 用法」节一致：一张表记全（地图 + 规则框）+ 逐条精讲 + 不收练习。

例句出处三分（构建后有 check_l9_infinitiv.py 机械核验）：
  · 教材 L9 课文 —— 逐字取自 l9-data.json（去 %% 标记 / 去对话引号），核验对象
  · 真题 YYYY · 卷号-题号 —— 逐字取自 pgg/full/YYYY_A_full.md（空格补答案后比对），核验对象
  · 通用例句 —— 语法书通用短例，作者自撰，不含教材/真题归属

输出: l9-infinitiv.json
"""
import json
import os

DIR = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(DIR, 'l9-infinitiv.json')

T = '教材 L9 课文'
G = '通用例句'


def z(no, section):
    return '真题 %s · %s' % (no, section)


# ── 一张表记全 ────────────────────────────────────────────────────
MAP = {
    'title': '一张表记全：不带 zu 的六类动词',
    'headers': ['#', '动词组', '结构', '一句话规则', '例句'],
    'rows': [
        ['①', '情态动词',
         'können / müssen / dürfen / sollen / wollen / mögen + 不定式', '情态在前，动作在句末',
         'Ich kann gut zuhören und auch überzeugen.'],
        ['②', 'werden',
         'werden + 不定式', '将来／变化，不定式不带 zu', 'Sie werden bald von uns hören.'],
        ['③', 'lassen',
         'lassen + 四格 + 不定式', '别人动手，主语不出手',
         'Die Personalchefin lässt Max seine Qualifikationen vorstellen.'],
        ['④', '感知动词',
         'sehen / hören / fühlen + 四格 + 不定式', '看到／听到某人正在做',
         'Da sieht man verschiedene Abteilungen zusammenarbeiten.'],
        ['⑤', '位移动词',
         'gehen / fahren / kommen / schicken + 不定式', '主语动身去做某事',
         'Im Sommer kann man hier spazieren gehen und im Winter Ski laufen.'],
        ['⑥', '保持与学教',
         'bleiben / lernen / lehren + 不定式', '保持某状态／学着做',
         'Hier lernen Sie Tipps kennen, die Ihnen helfen, Ihre Lebensqualität zu steigern.'],
    ],
    'rule': [
        '一句话规则（考试用）：',
        '① 看句末那个不定式——它前面的动词是「情态类」吗？　是 → 不带 zu：情态动词 / werden / '
        'lassen / 感知动词 / 位移动词 / bleiben、lernen、lehren。',
        '② 不是 → 一律带 zu：versuchen、beginnen、vergessen、hoffen、bitten、brauchen、'
        'die Gelegenheit haben …',
        '③ 完成时另加一步：这些「情态类」动词用不定式代替过去分词 —— hat … bauen lassen'
        '（不是 gelassen）。',
    ],
}

# ── 逐条精讲 ──────────────────────────────────────────────────────
CARDS = [
    {
        'title': '2.1 情态动词 + 不定式',
        'blocks': [
            ['p', '结构：**主语 + 情态动词（变位）+ 其他成分 + 不定式（句末）**'],
            ['b', '只有情态动词变位；不定式**永远是原形、永远在句末、不带 zu**。'],
            ['b', '六个情态动词：können / müssen / dürfen / sollen / wollen / mögen'
                  '（möchten 是 mögen 的虚拟式）。'],
            ['b', '可分动词在句末**合写**：einkaufen、zuhören、mitkommen。'],
            ['tbl', ['例句', '中文', '出处'], [
                ['Während des Austauschstudiums kann sie ihre Kenntnisse der chinesischen Sprache '
                 'und Kultur verbessern und ihre interkulturellen Kompetenzen ausbauen.',
                 '在交换留学期间，她可以提高自己关于汉语语言与文化的知识，并拓展跨文化能力。', T],
                ['Ich kann gut zuhören und auch überzeugen.', '我善于倾听，也能说服别人。', T],
                ['Was möchten Sie denn verdienen, Herr Baumann?', '那您希望拿到多少薪水，鲍曼先生？', T],
                ['Ich möchte mich auch für die Einladung zu dem Vorstellungsgespräch bedanken.',
                 '我也想感谢您邀请我来参加这次面试。', T],
            ], [9.6, 5.4, 2.0], 9],
            ['b', '✗ Ich kann gut **zuzuhören**.　→　✓ Ich kann gut zuhören.（不带 zu 时前缀不合写）'],
        ],
    },
    {
        'title': '2.2 werden + 不定式',
        'blocks': [
            ['p', '结构：**主语 + werden（变位）+ 其他成分 + 不定式（句末）**'],
            ['b', '两个意思本课都出现：**将来**（Ich werde …）和**变化／成为**（Geschäftsmann werden）。'],
            ['b', 'werden 自己也可以是不定式，跟在情态动词后面 —— **will … werden**，两个动词都不带 zu。'],
            ['tbl', ['例句', '中文', '出处'], [
                ['Sie werden bald von uns hören.', '您很快会收到我们的消息。', T],
                ['Ich werde mich ja auch schnell einarbeiten.', '反正我也会很快上手熟悉工作。', T],
                ['Ich will schon immer Geschäftsmann werden.', '我一直想成为商务人士。', T],
            ], [9.6, 5.4, 2.0], 9],
            ['b', '✗ Sie werden bald von uns **zu hören**.'],
        ],
    },
    {
        'title': '2.3 lassen + 四格 + 不定式',
        'blocks': [
            ['p', '结构：**主语 + lassen（变位）+ 第四格宾语 + 不定式（句末）**'],
            ['b', '主语不出手，让别人做；第四格宾语是**被做的那一方**。（lassen 的另外四种用法见上一节）'],
            ['tbl', ['例句', '中文', '出处'], [
                ['Die Personalchefin lässt Max seine Qualifikationen vorstellen.',
                 '人事主管让马克斯介绍自己的资历。', T],
                ['Ja, wir lassen die Angestellten anfangs immer eine Zeit lang in verschiedenen '
                 'Projekten arbeiten.', '有的，我们一开始都会让员工在不同项目里工作一段时间。', T],
                ['König Ludwig II. von Bayern hat das Schloss Neuschwanstein bauen lassen.',
                 '巴伐利亚国王路德维希二世让人建造了新天鹅堡。', z('2026', 'Ⅳ-45')],
            ], [9.6, 5.4, 2.0], 9],
            ['b', '完成时用**不定式**代替过去分词：… hat das Schloss bauen **lassen**。'
                  '写成 gelassen 就是 2026 年第 45 题的错项 c。'],
            ['b', '✗ Ich lasse mein Auto repariert.（不定式不跟着变位）'],
        ],
    },
    {
        'title': '2.4 感知动词 sehen / hören / fühlen + 不定式',
        'blocks': [
            ['p', '结构：**主语 + sehen / hören / fühlen（变位）+ 第四格宾语 + 不定式（句末）**'],
            ['b', '表示**看到／听到／感觉到某人正在做某事**，不定式同样不带 zu。'],
            ['b', '完成时也用不定式：Ich habe sie singen **hören**（不是 gehört）。'],
            ['tbl', ['例句', '中文', '出处'], [
                ['Da sieht man verschiedene Abteilungen zusammenarbeiten.',
                 '这样就能看到不同部门如何协作。', T],
                ['Ich will Dinge immer schnell voranschreiten sehen.',
                 '我总希望事情能快点推进。', T],
            ], [9.6, 5.4, 2.0], 9],
            ['b', '这一句里有两个不定式：voranschreiten（跟着 sehen）+ sehen（跟着情态动词 will）——'
                  '两个都不带 zu。'],
            ['b', '✗ Ich habe sie singen **gehört**.　→　✓ Ich habe sie singen hören.'],
        ],
    },
    {
        'title': '2.5 位移动词 gehen / fahren / kommen / schicken + 不定式',
        'blocks': [
            ['p', '结构：**主语 + gehen / fahren / kommen / schicken（变位）+ 不定式（句末）**'],
            ['b', '「主语动身去做某事」，动作紧跟其后，**不加 zu**。'],
            ['tbl', ['例句', '中文', '出处'], [
                ['Im Sommer kann man hier spazieren gehen und im Winter Ski laufen.',
                 '夏天可以在这里散步，冬天可以滑雪。', z('2023', 'Ⅲ 阅读原文')],
                ['Ich gehe einkaufen.', '我去买东西。', G],
                ['Komm essen!', '来吃饭！', G],
                ['Ich schicke ihn einkaufen.', '我打发他去买东西。', G],
            ], [9.6, 5.4, 2.0], 9],
            ['b', '同一句里情态动词也连着用：kann man … spazieren gehen —— spazieren gehen 整体当作一个不定式。'],
            ['b', '✗ Ich gehe **zu** einkaufen.'],
        ],
    },
    {
        'title': '2.6 bleiben / lernen / lehren + 不定式',
        'blocks': [
            ['p', '结构：**主语 + bleiben / lernen / lehren（变位）+ 不定式（句末）**'],
            ['b', '**bleiben + 不定式** = 保持某种状态：Er bleibt sitzen.（他继续坐着）'],
            ['b', '**lernen + 不定式** = 学着做某事；**lehren + 不定式** = 教某人做某事。'],
            ['tbl', ['例句', '中文', '出处'], [
                ['Hier lernen Sie Tipps kennen, die Ihnen helfen, Ihre Lebensqualität zu steigern.',
                 '在这里您可以了解到一些建议，它们能帮您提高生活质量。', z('2024', 'Ⅳ-41')],
                ['Ich lerne schwimmen.', '我在学游泳。', G],
                ['Er bleibt sitzen.', '他继续坐着。', G],
            ], [9.6, 5.4, 2.0], 9],
            ['b', '第一句里正好一组对照：lernen 后**不带 zu**（Tipps kennen），'
                  'helfen 后**带 zu**（zu steigern）。'],
            ['b', '✗ Ich lerne **zu** schwimmen.　→　✓ Ich lerne schwimmen.'
                  '（对比：Ich beginne zu schwimmen. —— beginne 必须带 zu）'],
        ],
    },
    {
        'title': '2.7 形式与语序：四条硬规矩',
        'blocks': [
            ['p', '不带 zu 的不定式，形式上只有四条规矩，记住就不会写错。'],
            ['tbl', ['规矩', '说明', '例'], [
                ['位置', '不定式在**句末**，中间可以夹宾语和状语',
                 'Die Personalchefin lässt Max seine Qualifikationen vorstellen.'],
                ['合写', '可分动词在句末**合写**，前缀不拆',
                 'Ich gehe einkaufen.'],
                ['原形', '不变位、不变成过去分词',
                 '✗ Ich lasse mein Auto repariert.'],
                ['Ersatzinfinitiv', '情态动词、lassen、sehen / hören / fühlen 的完成时'
                                    '**用不定式代替过去分词**',
                 'Das hätte ich doch tun können.'],
            ], [3.0, 7.0, 7.0], 9],
            ['b', '两个不定式连用时，顺序是「动作 → 情态／lassen」：hat … bauen lassen、'
                  'hätte … tun können、habe sie singen hören。'],
            ['b', '真题锚：2026 · Ⅳ-45（bauen lassen）与 2023 · Ⅳ-50（tun können）'
                  '两题都只考这一步。'],
            ['b', '从句里助动词也不拆开：…, dass er das Schloss hat bauen lassen.'],
        ],
    },
    {
        'title': '2.8 对照：这些情况必须带 zu',
        'blocks': [
            ['p', '除了上面六类，谓语动词后面的不定式**一律带 zu**。考场上绝大多数「不定式」题考的是这一侧。'],
            ['tbl', ['类型', '例', '出处'], [
                ['实义动词作谓语（bitten 等）',
                 'Wir bitten Sie, die Rechnung innerhalb der kommenden zehn Tage zu bezahlen.',
                 z('2026', 'Ⅳ-47')],
                ['实义动词作谓语（versuchen）', 'Ich versuche, früher zu schlafen.', G],
                ['brauchen（nicht / nur）', 'Du brauchst nicht zu kommen.', G],
                ['固定结构：die Gelegenheit haben',
                 'Wäre es möglich, dass man als Marketingassistenz auch die Gelegenheit hat, '
                 'andere Abteilungen kennen zu lernen?', T],
                ['固定结构：es ist wichtig / schwer', 'Es ist wichtig, jeden Tag zu üben.', G],
                ['haben / sein + zu + 不定式（情态替代）',
                 'Ich habe noch viel zu tun. / Das ist leicht zu verstehen.', G],
                ['um … zu', 'Der Betrieb braucht dringend Geld, um moderne Maschinen zu kaufen.',
                 z('2023', 'Ⅳ-43')],
                ['statt … zu',
                 'Statt einen Managementvortrag zu halten, erzählte der Professor die ganze Zeit '
                 'von seinem Urlaub in Italien.', z('2025', 'Ⅳ-42')],
                ['um … zu（含情态动词）',
                 'Es war im Restaurant einfach zu laut, um sich unterhalten zu können.',
                 z('2024', 'Ⅳ-49')],
            ], [4.0, 11.0, 2.0], 8.5],
            ['b', '倒数第三条要留神：um … zu 里的情态动词**自己也要带 zu** —— '
                  'um sich unterhalten **zu können**。'],
            ['b', '教材里的同一句就是最好的对照：kennen zu lernen（带 zu，跟在 die Gelegenheit haben 后）'
                  '——而单独说「学做某事」时是 Ich lerne schwimmen（不带 zu）。'],
        ],
    },
]


def main():
    data = {
        'title': 'Infinitiv ohne zu',
        'sub': '不带 zu 的不定式',
        'nav': '📐 不定式 ohne zu',
        'icon': '📐',
        'num': 7,
        'lead': '德语里只有「情态类」动词后面的不定式不带 zu——其余一律带 zu。'
                '判断只走一步：看句末那个不定式前面是哪个动词。',
        'src': '教材 Lektion 9 课文 + PGG 2023–2026 A 卷真题',
        'map': MAP,
        'cards': CARDS,
    }
    n_tbl = sum(1 for c in CARDS for b in c['blocks'] if b[0] == 'tbl')
    n_ex = sum(len(b[2]) for c in CARDS for b in c['blocks'] if b[0] == 'tbl')
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('wrote %s (%d bytes)' % (OUT, os.path.getsize(OUT)))
    print('地图行=%d | 卡片=%d | 表=%d | 例句=%d'
          % (len(MAP['rows']), len(CARDS), n_tbl + 1, n_ex + len(MAP['rows'])))


if __name__ == '__main__':
    main()
