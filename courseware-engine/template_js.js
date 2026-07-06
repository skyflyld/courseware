// ===== TTS (Text-to-Speech) =====
  function speakWord(word) {
    if (!window.speechSynthesis) return;
    speechSynthesis.cancel();
    var u = new SpeechSynthesisUtterance(word);
    u.lang = 'de-DE';
    u.rate = 0.85;
    speechSynthesis.speak(u);
  }

  // ===== SRS (Spaced Repetition System) =====
  function srsLoad() {
    try {
      var key = 'srs_' + (document.body.getAttribute('data-lektion') || 'unknown');
      return JSON.parse(localStorage.getItem(key) || '{}');
    } catch(e) { return {}; }
  }
  function srsSave(data) {
    try {
      var key = 'srs_' + (document.body.getAttribute('data-lektion') || 'unknown');
      localStorage.setItem(key, JSON.stringify(data));
    } catch(e) {}
  }
  function srsRecord(wordKey, correct) {
    if (!wordKey) return;
    var data = srsLoad();
    if (!data[wordKey]) data[wordKey] = { a:0, c:0, t:0 };
    data[wordKey].a++;
    if (correct) data[wordKey].c++;
    data[wordKey].t = Date.now();
    srsSave(data);
  }
  function srsGetState(wordKey) {
    var data = srsLoad();
    var e = data[wordKey];
    if (!e || e.a === 0) return 'new';
    var rate = e.c / e.a;
    if (e.a >= 3 && rate >= 0.8) return 'mastered';
    return 'learning';
  }

  // ===== Section Switching =====
  function switchSection(id) {
    document.querySelectorAll('section').forEach(s => s.classList.remove('active'));
    document.getElementById(id).classList.add('active');
    document.querySelectorAll('.nav-links button').forEach(b => b.classList.remove('active'));

    const labels = { home:0, text:1, vocab:2, grammar:3, exercise:4 };
    const btns = document.querySelectorAll('.nav-links button');
    if (btns[labels[id]]) btns[labels[id]].classList.add('active');

    // Close mobile nav
    document.querySelector('.nav-links').classList.remove('show');

    // Scroll to top of content (below nav bar)
    window.scrollTo({ top: 0, behavior: 'smooth' });

    // Init vocab if needed
    if (id === 'vocab') initVocab();
  }

  // ===== Person Tabs =====
  function switchPerson(id) {
    document.querySelectorAll('.person-content').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.person-tabs button').forEach(b => b.classList.remove('active'));
    var content = document.getElementById('vocab-' + id);
    if (content) content.classList.add('active');
    // Activate the clicked button
    document.querySelectorAll('.person-tabs button').forEach(function(b) {
      if (b.getAttribute('onclick') && b.getAttribute('onclick').includes("switchPerson('" + id + "')")) {
        b.classList.add('active');
      }
    });
  }

  // ===== Quiz =====
  function checkQuiz(btn, qId, index) {
    const card = document.getElementById(qId);
    const options = card.querySelectorAll('.options button');
    const correct = parseInt(card.querySelector('.options').dataset.correct);
    const feedback = card.querySelector('.feedback');

    options.forEach(b => b.disabled = true);

    if (index === correct) {
      btn.classList.add('correct');
      feedback.classList.add('show', 'correct');
    } else {
      btn.classList.add('wrong');
      options[correct].classList.add('correct');
      feedback.classList.add('show', 'wrong');
      // Override text for wrong
      const texts = {
        'q1': '❌ 不对。正确答案是 <strong>zu machen</strong>。Möglichkeit 后接带zu不定式。',
        'q2': '❌ 不对。正确答案是 <strong>warmzulaufen</strong>(注意 warmlaufen 是可分动词)。',
        'q3': '❌ 不对。正确答案是 B:我很高兴能更经常见到父亲。',
        'q4': '❌ 不对。完成时 zu 不定式要用 <strong>teilgenommen zu haben</strong>。',
        'q5': '❌ 不对。不同Berufsfelder给不同毕业证书,所以这个说法是错误的。',
        'q6': '❌ 不对。planen + zu + Infinitiv:<strong>zu schicken</strong>。',
      };
      if (texts[qId]) feedback.innerHTML = texts[qId];
    }
  }

  // ===== Show Answers =====
  document.querySelector('.show-zu-answers')?.addEventListener('click', function() {
    const ans = document.querySelector('.zu-answers');
    ans.style.display = ans.style.display === 'none' ? 'block' : 'none';
    this.textContent = ans.style.display === 'block' ? '隐藏答案' : '显示答案';
  });

  function showFillAnswers() {
    const el = document.getElementById('fill-answers');
    el.style.display = el.style.display === 'none' ? 'block' : 'none';
  }

  function showRewriteAnswers() {
    const el = document.getElementById('rewrite-answers');
    el.style.display = el.style.display === 'none' ? 'block' : 'none';
  }


  // ===== Vocab Panel (show/hide) =====
  function showVocab(word, zh, example) {
    document.getElementById('vpWord').textContent = word;
    document.getElementById('vpZh').textContent = zh;
    document.getElementById('vpEx').textContent = example;
    document.getElementById('vocabPanel').classList.add('show');
  }
  function closeVocabPanel() {
    document.getElementById('vocabPanel').classList.remove('show');
  }
  // Close on Escape key
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeVocabPanel();
  });

  // ===== Vocabulary Cards =====
  let vocabInitialized = false;

  function initVocab() {
    if (vocabInitialized) return;
    vocabInitialized = true;

    // Add SRS state coloring and speak buttons to existing static cards
    document.querySelectorAll('.vocab-card').forEach(function(card) {
      var frontEl = card.querySelector('.front');
      var word = frontEl ? frontEl.textContent.trim() : '';
      if (!word) return;

      // SRS state: add class and icon
      var state = srsGetState(word);
      if (state === 'mastered') card.classList.add('srs-mastered');
      else if (state === 'learning') card.classList.add('srs-learning');

      // Add speak button to front
      if (frontEl) {
        var sb = document.createElement('button');
        sb.className = 'speak-btn';
        sb.innerHTML = '\ud83d\udd0a';
        sb.title = '\u542c\u53d1\u97f3';
        var safeWord = word.replace(/'/g, "\\'");
        sb.onclick = function(e) { e.stopPropagation(); speakWord(safeWord); };
        frontEl.appendChild(sb);
      }
    });
  }

  // Init vocab on load if home visible, otherwise on demand
  // Preload answers toggle
  document.querySelector('.show-zu-answers')?.addEventListener('click', function() {
    const ans = document.querySelector('.zu-answers');
    ans.style.display = ans.style.display === 'none' ? 'block' : 'none';
    this.textContent = ans.style.display === 'block' ? '隐藏答案' : '显示答案';
  });
// ===== Hamburger Menu Toggle =====
function toggleNav() {
  document.getElementById('navLinks').classList.toggle('show');
}

// ===== Matching Game =====
let matchSelected = null;

function matchClick(el) {
  if (el.classList.contains("matched")) return;
  if (matchSelected === null) {
    matchSelected = el;
    el.classList.add("selected");
  } else if (matchSelected === el) {
    matchSelected.classList.remove("selected");
    matchSelected = null;
  } else {
    var d = matchSelected.classList.contains("de");
    var e = el.classList.contains("de");
    if (d === e) {
      matchSelected.classList.remove("selected");
      matchSelected = el;
      el.classList.add("selected");
    } else if (matchSelected.dataset.pair === el.dataset.pair) {
      matchSelected.classList.remove("selected");
      matchSelected.classList.add("matched");
      el.classList.add("matched");
      // SRS: record correct match
      var deCard = matchSelected.classList.contains("de") ? matchSelected : el;
      srsRecord(deCard.textContent.trim(), true);
      matchSelected = null;
      var r = document.querySelectorAll(".match-card:not(.matched)").length;
      if (r === 0) { setTimeout(function(){alert("Alles richtig!");},200); }
    } else {
      matchSelected.classList.remove("selected");
      var o = matchSelected;
      matchSelected = null;
      // SRS: record wrong match
      var deCard2 = o.classList.contains("de") ? o : el;
      var otherCard = o.classList.contains("de") ? el : o;
      srsRecord(deCard2.classList.contains("de") ? deCard2.textContent.trim() : otherCard.textContent.trim(), false);
      o.style.borderColor = "#e74c3c";
      el.style.borderColor = "#e74c3c";
      setTimeout(function(){o.style.borderColor = "";el.style.borderColor = "";},400);
    }
  }
}
