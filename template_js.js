// ===== Section Navigation =====
function switchSection(id) {
  document.querySelectorAll('section').forEach(s => s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  document.querySelectorAll('.nav-links button').forEach(b => b.classList.remove('active'));

  const map = { home:0, text:1, vocab:2, grammar:3, exercise:4, translation:5 };
  const btns = document.querySelectorAll('.nav-links button');
  if (btns[map[id]]) btns[map[id]].classList.add('active');

  document.querySelector('.nav-links').classList.remove('show');
  window.scrollTo({ top: 0, behavior: 'smooth' });
  updateProgress(id);
}

function updateProgress(id) {
  const map = { home:0, text:20, vocab:40, grammar:60, exercise:80, translation:100 };
  const bar = document.getElementById('progressFill');
  if (bar) bar.style.width = (map[id] || 0) + '%';
}

// ===== Mobile Nav Toggle =====
function toggleNav() {
  document.getElementById('navLinks').classList.toggle('show');
}

// ===== Text Pagination =====
function prevPage(id) {
  var container = document.getElementById('tp-' + id);
  if (!container) return;
  var pages = container.querySelectorAll('.text-page');
  var current = 0;
  pages.forEach(function(p, i) {
    if (p.style.display !== 'none') current = i;
    p.style.display = 'none';
  });
  if (current > 0) {
    pages[current - 1].style.display = 'block';
    updatePager(id, pages.length, current - 1);
  } else {
    pages[0].style.display = 'block';
  }
}

function nextPage(id) {
  var container = document.getElementById('tp-' + id);
  if (!container) return;
  var pages = container.querySelectorAll('.text-page');
  var current = 0;
  pages.forEach(function(p, i) {
    if (p.style.display !== 'none') current = i;
    p.style.display = 'none';
  });
  if (current < pages.length - 1) {
    pages[current + 1].style.display = 'block';
    updatePager(id, pages.length, current + 1);
  } else {
    pages[pages.length - 1].style.display = 'block';
  }
}

function updatePager(id, total, current) {
  var prevBtn = document.getElementById('tp-prev-' + id);
  var nextBtn = document.getElementById('tp-next-' + id);
  var info = document.getElementById('tp-info-' + id);
  if (prevBtn) prevBtn.disabled = current === 0;
  if (nextBtn) nextBtn.disabled = current >= total - 1;
  if (info) info.textContent = (current + 1) + ' / ' + total;
}

// ===== Vocab Flip Cards =====
function flipCard(el) {
  el.classList.toggle('flipped');
}

// ===== Translation Flip Cards =====
function flipTrans(el) {
  el.classList.toggle('flipped');
}

// ===== Vocab Panel =====
function showVocab(word, zh, ex, phrase, example) {
  document.getElementById('vpWord').textContent = word || '';
  document.getElementById('vpZh').textContent = zh || '';
  document.getElementById('vpPhrase').innerHTML = phrase ? '📎 ' + phrase : '';
  document.getElementById('vpExample').innerHTML = example ? '💬 ' + example : '';
  document.getElementById('vpEx').textContent = ex || '';
  document.getElementById('vocabPanel').classList.add('show');
  document.getElementById('vocabOverlay').classList.add('show');
}

function hideVocab() {
  document.getElementById('vocabPanel').classList.remove('show');
  document.getElementById('vocabOverlay').classList.remove('show');
}

document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') hideVocab();
});

// ===== Vocab Tabs =====
function switchVocabTab(id) {
  document.querySelectorAll('.person-content').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.person-tabs button').forEach(b => b.classList.remove('active'));
  var content = document.getElementById('vc-' + id);
  if (content) content.classList.add('active');
  document.querySelectorAll('.person-tabs button').forEach(function(b) {
    if (b.getAttribute('onclick') && b.getAttribute('onclick').includes("switchVocabTab('" + id + "')")) {
      b.classList.add('active');
    }
  });
}

// ===== Quiz =====
function checkQuiz(el, qId, optIdx) {
  var card = el.closest('.quiz-card');
  var answerDiv = card.querySelector('.q-answer');
  var answer = answerDiv ? answerDiv.textContent.replace('答案：','').trim() : '';
  var correctLetter = answer.charCodeAt(0) - 65;
  var options = card.querySelectorAll('.opt');
  options.forEach(function(o) { o.style.pointerEvents = 'none'; });
  if (optIdx === correctLetter) {
    el.classList.add('correct');
  } else {
    el.classList.add('wrong');
    options[correctLetter].classList.add('correct');
  }
}

// ===== Connect Grid =====
var cSelected = null;

function cClick(el) {
  if (el.classList.contains('matched')) return;
  if (cSelected === null) {
    cSelected = el;
    el.classList.add('selected');
  } else if (cSelected === el) {
    cSelected.classList.remove('selected');
    cSelected = null;
  } else {
    var isDe1 = cSelected.classList.contains('de');
    var isDe2 = el.classList.contains('de');
    if (isDe1 === isDe2) {
      cSelected.classList.remove('selected');
      cSelected = el;
      el.classList.add('selected');
    } else if (cSelected.dataset.pair === el.dataset.pair) {
      cSelected.classList.remove('selected');
      cSelected.classList.add('matched');
      el.classList.add('matched');
      cSelected = null;
      var gid = el.dataset.gid;
      var total = document.querySelectorAll('#cg-de-' + gid + ' .c-item').length;
      var done = document.querySelectorAll('#cg-de-' + gid + ' .c-item.matched').length;
      document.getElementById('cg-cnt-' + gid).textContent = done;
      if (done >= total) {
        setTimeout(function(){ alert('Alle richtig!'); }, 200);
      }
    } else {
      cSelected.classList.remove('selected');
      var old = cSelected;
      cSelected = null;
      old.style.borderColor = '#e74c3c';
      el.style.borderColor = '#e74c3c';
      setTimeout(function() {
        old.style.borderColor = '';
        el.style.borderColor = '';
      }, 300);
    }
  }
}

// ===== Fill-gap =====
function checkFill(gid, idx) {
  var input = document.getElementById('fg-' + gid + '-' + idx);
  var result = document.getElementById('fg-res-' + gid + '-' + idx);
  var answer = input.dataset.answer;
  var val = input.value.trim().toLowerCase();
  if (val === answer.toLowerCase()) {
    input.style.borderColor = '#27ae60';
    input.style.background = '#e8f8e8';
    result.textContent = '\u2713';
    result.className = 'fill-result correct';
  } else {
    input.style.borderColor = '#e74c3c';
    input.style.background = '#fdecea';
    result.textContent = '\u2717';
    result.className = 'fill-result wrong';
  }
}

// Support Enter key in fill-gap
document.addEventListener('keydown', function(e) {
  if (e.key === 'Enter') {
    var input = e.target.closest('.fill-input');
    if (input) {
      var parts = input.id.split('-');
      checkFill(parseInt(parts[1]), parseInt(parts[2]));
    }
  }
});

// ===== Matching Game =====
var matchSelected = null;
function matchClick(el) {
  if (el.classList.contains('matched')) return;
  if (matchSelected === null) {
    matchSelected = el;
    el.classList.add('selected');
  } else if (matchSelected === el) {
    matchSelected.classList.remove('selected');
    matchSelected = null;
  } else {
    var d = matchSelected.classList.contains('de');
    var e = el.classList.contains('de');
    if (d === e) {
      matchSelected.classList.remove('selected');
      matchSelected = el;
      el.classList.add('selected');
    } else if (matchSelected.dataset.pair === el.dataset.pair) {
      matchSelected.classList.remove('selected');
      matchSelected.classList.add('matched');
      el.classList.add('matched');
      matchSelected = null;
      var remaining = document.querySelectorAll('.match-card:not(.matched)').length;
      if (remaining === 0) { setTimeout(function(){ alert('Alles richtig!'); }, 200); }
    } else {
      matchSelected.classList.remove('selected');
      var old = matchSelected;
      matchSelected = null;
      old.style.borderColor = '#e74c3c';
      el.style.borderColor = '#e74c3c';
      setTimeout(function(){old.style.borderColor = ''; el.style.borderColor = '';}, 300);
    }
  }
}

// ===== Keyboard shortcuts =====
document.addEventListener('keydown', function(e) {
  if (e.key === '1') switchSection('home');
  if (e.key === '2') switchSection('text');
  if (e.key === '3') switchSection('vocab');
  if (e.key === '4') switchSection('grammar');
  if (e.key === '5') switchSection('exercise');
  if (e.key === '6') switchSection('translation');
});
