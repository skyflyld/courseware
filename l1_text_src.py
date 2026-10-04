# -*- coding: utf-8 -*-
"""l1_text_src.py — Lektion 1 课文原文（逐字）+ 段落结构

来源：archive/german-teaching/lektion1-texte/texte-verbatim.md
（Sky 2026-09-28 提供 5 张教材照片，T1 S.13–15 / T2 S.25–26，两次独立转录比对通过）
本文件只做搬运与分段，不改写任何一个字。
"""

T1_INTRO = [
    ("", "Emilie und ihre Oma erzählen über ihre eigene Kindheit."),
    ("Oma", "Meine Kindheit war von der Nachkriegszeit geprägt, nur Armut, Trümmer, "
            "Gewalterfahrung in Schule und Familie. Ja, wir waren froh, den Krieg überlebt zu haben. "
            "Aber das Wirtschaftswunder hielt nur langsam Einzug."),
    ("Emilie", "Ich heiße Emilie. Ich bin nach 1995 geboren und gehöre deshalb zur "
               "sogenannten Generation Z."),
]

T1_LANDESKUNDE = ("Die Generation Z, auch als „Digital Natives“ bekannt, bezeichnet junge Menschen, "
                  "die zwischen den Jahren 1995 und 2010 geboren sind. Sie folgt auf die Generation Y "
                  "(auch „Millennials“ genannt) und ist die erste Generation, "
                  "die mit dem Smartphone aufwächst.")

T1_BLOCKS = [
    {"no": "①", "page": "S.14", "topic": "家庭与工作",
     "oma": "Vor dem Krieg hatte mein Vater einen eigenen Handwerksbetrieb, aber nach dem Krieg hatte der Betrieb keinen Boden unter den Füßen. "
            "Wir hatten kein Geld mehr. Deshalb arbeitete meine Mutter neben der Versorgung meiner drei Geschwister auch halbtags, als ich in die Schule kam. "
            "Sie hatte alle Hände voll zu tun.",
     "emilie": "Mein Vater besuchte eine Realschule und arbeitete anfangs in einem Elektrogeschäft. Jetzt ist er Manager. Meine Mutter arbeitet in einer Zahnarztpraxis. "
               "Sie sind sehr beschäftigt. Neben der Arbeit kümmern sie sich sehr um meinen Bruder und mich, besonders um unsere Schulleistungen. "
               "Wir wohnen mit unserem Hund in einem selbstgebauten Haus. Am Wochenende besuchen wir unsere Großeltern oder machen Ausflüge, wandern usw. "
               "Ja, für uns ist eine Auslandsreise pro Jahr sehr wichtig, am liebsten ans Meer."},
    {"no": "②", "page": "S.14", "topic": "安全",
     "oma": "Die Sicherheit der Kinder wurde früher auf die leichte Schulter genommen. In den Autos gab es keine Sicherheitsgurte, "
            "die Kindersicherung in Steckdosen fehlte und Medikamentenpackungen ließen sich leicht öffnen. "
            "Kleine Kinder fuhren auf Fahrrädern durch die Straßen – doch wer trug schon einen Helm? "
            "Beliebte Fahrzeuge waren außerdem selbstgebaute Seifenkisten, die oftmals keine Bremse hatten.",
     "emilie": "Meine Sicherheit? Ich würde sagen, meine Eltern kümmern sich zu sehr um mich, manchmal habe ich gar keine Freiheit. "
               "Sie wollen immer wissen, was ich gerade mache. Mit dem Handy können sie immer feststellen, wo ich gerade bin. "
               "Sie bringen mich zur Kita, zur Grundschule, zu Kursen und zu Freunden und holen mich wieder ab. "
               "Sie haben immer Angst, dass mir etwas passiert. Wann kann ich endlich auf eigenen Beinen stehen?"},
    {"no": "③", "page": "S.14", "topic": "学校",
     "oma": "In der Schule mussten die Kinder still und schweigend sitzen, denn das Wort gehörte einzig und allein den Lehrern. "
            "Disziplin und Gehorsamkeit waren gefordert. Schläge und Ohrfeigen waren sowohl im Unterricht als auch innerhalb der Familie keine Seltenheit.",
     "emilie": "Heute ist im Unterricht eigenes Denken und Handeln gefragt: Die Schüler dürfen und sollen selbstständig nachdenken und lernen. "
               "Eigene Ideen sind zu entwickeln und zu überprüfen. Zum Glück habe ich eine nette junge Lehrerin, "
               "die sich durch Offenheit, Freundlichkeit, Aufgeschlossenheit usw. auszeichnet und immer bestrebt ist, uns den Spaß am Lernen zu vermitteln."},
    {"no": "④", "page": "S.15", "topic": "课余与朋友",
     "oma": "Unterricht nach der Schule? Nein. Wir verließen meist nach der Schule die Wohnung und verbrachten den ganzen Tag auf der Straße. "
            "Alltägliche Streitereien über Kleinigkeiten ließen sich untereinander klären, denn die Erwachsenen hielten sich aus diesen meistens heraus. "
            "Ebenso erfolgten Verabredungen nicht über die Eltern, sondern wurden untereinander in der Schule vereinbart oder man fand sich an bestimmten Treffpunkten.",
     "emilie": "Ich spiele natürlich viel mit den digitalen Medien, am Handy oder am Rechner. "
               "Es ist unvorstellbar, wie das Leben ohne solche digitalen Medien aussieht. "
               "Mit Puppen oder mit einfachen Bausteinen spiele ich auch gern, aber heute nicht mehr so häufig wie in meiner Kindheit. "
               "Meine Freunde und ich spielen lieber Brettspiele oder gehen ins Freie."},
    {"no": "⑤", "page": "S.15", "topic": "阅读",
     "oma": "Ach, ich wollte einfach alle Bücher lesen, die ich bekommen konnte. Damals hatten wir aber nur ganz wenige Bücher. "
            "Mein Schulfreund Hans hatte von seiner Tante immer die neuesten Micky-Maus-Hefte. Die waren super!",
     "emilie": "Ich lese in meiner Freizeit gerne Detektivgeschichten, Ponygeschichten und Harry-Potter-Geschichten über Magie. "
               "Ich träume oft von einem Leben in einer magischen Welt."},
    {"no": "⑥", "page": "S.15", "topic": "星期天与幸福",
     "oma": "Der Sonntag war der einzige freie Tag der Woche und meist mit meiner Familie zu verbringen. "
            "Ein gemeinsamer Spaziergang oder der Kirchenbesuch am Sonntag, das war für mich eine glückliche Zeit. "
            "Aber das größte Glück war damals für mich, eine sehr gute Freundin gehabt zu haben.",
     "emilie": "Was bedeutet Glück für mich? Ich denke, die Freiheit, selbständige Entscheidungen treffen zu können, trägt viel zu meinem Glück bei. "
               "Familienausflüge machen mich auch glücklich."},
]

# T2 = Entdecken 2, S.25–26，采访（练习 9 的课文正文；五个空用 [[n]] 占位，答案见 EX9）
T2_LEAD = ("Der Austauschstudent Lukas schreibt einen Artikel zum Thema „Glück“ für die Zeitschrift "
           "„Interkulturelle Kommunikation“. Dafür befragt er Frau Prof. Liu, eine chinesische Expertin "
           "auf dem Gebiet der Psychologie.")

T2_DIALOGUE = [
    ("Lukas", "Frau Prof. Liu, vielen Dank für Ihre Zeit. Ich möchte gleich mit der zentralen Frage beginnen: "
              "Was macht einen Menschen glücklich?"),
    ("Frau Prof. Liu", "Das ist eine umfassende Frage. Das, [[1]], ist für die Menschen natürlich "
                       "unterschiedlich, je nachdem, wer darüber spricht, in welcher Zeit und in welchem Land man lebt."),
    ("Lukas", "Könnten Sie das vielleicht etwas näher erläutern, Frau Prof. Liu?"),
    ("Frau Prof. Liu", "Für unsere Eltern und Großeltern ist das Glücksempfinden anders als für uns. [[2]], "
                       "war ein einfaches Leben. [[3]], empfand schon Glück. Doch heutzutage benötigen wir "
                       "offensichtlich immer mehr, um glücklich zu sein. Es scheint für den modernen Menschen "
                       "schwerer zu sein, Glück zu empfinden, ständig sind wir auf der Suche nach Glück."),
    ("Lukas", "Diesen Eindruck habe ich auch. Je mehr wir haben, desto mehr wollen wir. Sie sagten gerade, "
              "dass es eine Rolle spielt, in welchem Land man lebt. Könnten Sie zu diesem Punkt vielleicht "
              "noch etwas sagen?"),
    ("Frau Prof. Liu", "Ja, gerne. Die Ursachen für Glücksgefühle können sich von Kultur zu Kultur "
                       "unterscheiden.¦ [[4]], kann in einem anderen Land ganz anders sein. Eine Forschungsgruppe "
                       "hat eine Studie in 63 Ländern durchgeführt. Es wurde gezeigt, dass in vielen westlichen "
                       "Ländern die Einstellung herrscht, dass Glücksgefühle mehr mit persönlichem Erfolg "
                       "zusammenhängen. Für Menschen aus anderen Kulturkreisen muss das keineswegs so gelten. "
                       "In einem ostasiatischen Land wie Japan beispielsweise gilt Harmonie mit anderen und sich "
                       "selbst als Quelle des Glücks."),
    ("Lukas", "Wie Sie wissen, komme ich aus einem westlichen Land. Für mich kommt es wohl auch auf die "
              "persönliche Entwicklung, auf Karriere und Selbstverwirklichung an. Was verstehen Sie übrigens "
              "unter „Harmonie mit anderen“?"),
    ("Frau Prof. Liu", "Für mich bedeutet Harmonie, starke und positive Beziehungen zu anderen Menschen zu "
                       "haben, die die Gefühle von Verbundenheit und Zugehörigkeit vermitteln. Damit sind nicht "
                       "nur Paarbeziehungen, sondern auch gute Beziehungen zu Familienmitgliedern wie Eltern und "
                       "Kindern, zu Freunden, Kollegen oder Nachbarn gemeint. Sogar Zufallsbegegnungen können sich "
                       "günstig auf unser Glücksempfinden auswirken. Sehr interessant ist übrigens, dass die "
                       "Pflege menschlicher Beziehungen in manchen europäischen Ländern wie der Schweiz und "
                       "Island, aber auch in Lateinamerika ebenso wichtig ist wie in Japan."),
    ("Lukas", "Und wie ist es in China?"),
    ("Frau Prof. Liu", "Wir streben in China ebenfalls nach Harmonie. Harmonie in der Familie, in den "
                       "Beziehungen zu Freunden, Kollegen und Nachbarn. Aber noch wichtiger ist, dass unser "
                       "Glück mit der Gewissheit verbunden ist, dass man in einem sicheren und prosperierenden "
                       "Land lebt. [[5]], kann sich frei und selbständig entfalten und seinen eigenen Traum "
                       "verwirklichen."),
    ("Lukas", "Ja, jetzt verstehe ich, inwiefern das Glücksempfinden kulturabhängig ist. Nun interessiert "
              "mich noch, wie man in China persönliches Glück finden kann?"),
    ("Frau Prof. Liu", "Glück zu finden ist nicht schwer. Musik hören, Sport treiben und gute soziale "
                       "Beziehungen zu haben – all dies können Wege zum Glück sein. Doch können diese Faktoren "
                       "nur vorübergehend Glück bringen. Wie ich zuvor erwähnt habe, ist unser persönliches "
                       "Glück in China eng mit dem Schicksal unseres Landes verknüpft. Wenn man sieht, dass es "
                       "dem eigenen Land gut geht und die Mitbürger in Frieden und Sicherheit leben, kann diese "
                       "Wahrnehmung das individuelle Glück positiv beeinflussen."),
    ("Lukas", "Was kann man denn als einzelne Person tun, um glücklich zu sein und gleichzeitig sein Land zu "
              "unterstützen?"),
]

EX9_CHUNKS = [
    "Wer genug zu essen und ein sicheres Zuhause hatte",
    "Was sie früher glücklich machte",
    "Was die Menschen in einem Land glücklich macht",
    "Wer in solch einem Land lebt",
    "was das Glücksgefühl auslöst",
]
