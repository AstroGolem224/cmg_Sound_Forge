/* ── State ─────────────────────────────────────────────────────────────── */
const state = {
  sfxBlob:    null,
  sfxExt:     'mp3',
  ttsBlob:    null,
  ttsExt:     'mp3',
  sfxAudio:   null,
  ttsAudio:   null,
  voiceId:    null,
  voiceProvider: 'elevenlabs',
  orModels:   [],
};

/* ── Utils ─────────────────────────────────────────────────────────────── */
function $(id) { return document.getElementById(id); }

async function apiFetch(path, opts = {}) {
  const res = await fetch(path, opts);
  if (!res.ok) {
    const txt = await res.text().catch(() => res.statusText);
    let msg = txt;
    try { msg = JSON.parse(txt)?.detail ?? txt; } catch (_) {}
    throw new Error(msg);
  }
  return res;
}

function setStatus(elId, msg, isErr = false) {
  const el = $(elId);
  el.textContent = msg;
  el.style.color = isErr ? '#e05252' : '';
}

function setSpinner(id, visible) {
  $(id).classList.toggle('visible', visible);
}

function sliderSync(sliderId, valId, suffix = '') {
  const s = $(sliderId), v = $(valId);
  const update = () => { v.textContent = parseFloat(s.value).toFixed(2).replace(/\.?0+$/, '') + suffix; };
  update();
  s.addEventListener('input', update);
}

/* ── Tabs ──────────────────────────────────────────────────────────────── */
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    $('tab-' + btn.dataset.tab).classList.add('active');
  });
});

/* ── Sliders ───────────────────────────────────────────────────────────── */
sliderSync('sfx-duration',   'sfx-duration-val',   's');
sliderSync('tts-speed',      'tts-speed-val',       '×');
sliderSync('tts-stability',  'tts-stability-val',   '');
sliderSync('tts-similarity', 'tts-similarity-val',  '');
sliderSync('oai-speed',      'oai-speed-val',        '×');

/* ── SFX Provider toggle ───────────────────────────────────────────────── */
$('sfx-provider').addEventListener('change', function() {
  const isHF = this.value === 'huggingface';
  $('sfx-hf-model-wrap').style.display = isHF ? '' : 'none';
  $('sfx-duration-wrap').style.display = isHF ? 'none' : '';
});

/* ── Voice Provider toggle ─────────────────────────────────────────────── */
$('voice-provider').addEventListener('change', function() {
  state.voiceProvider = this.value;
  state.voiceId = null;
  const isOAI = this.value === 'openai';
  $('el-settings').style.display  = isOAI ? 'none' : '';
  $('oai-settings').style.display = isOAI ? '' : 'none';
  loadVoices(this.value);
});

/* ── Voice Search ──────────────────────────────────────────────────────── */
$('voice-search').addEventListener('input', function() {
  const q = this.value.toLowerCase();
  document.querySelectorAll('.voice-card').forEach(card => {
    card.style.display = card.dataset.name.includes(q) ? '' : 'none';
  });
});

/* ── Audio playback ────────────────────────────────────────────────────── */
function makePlayer(playBtnId, getBlob, getExt) {
  let audio = null;
  const btn = $(playBtnId);
  btn.addEventListener('click', () => {
    const blob = getBlob();
    if (!blob) return;
    if (audio && !audio.paused) {
      audio.pause();
      btn.textContent = '▶';
      return;
    }
    if (!audio || audio._blob !== blob) {
      URL.revokeObjectURL(audio?._url);
      const url = URL.createObjectURL(blob);
      audio = new Audio(url);
      audio._blob = blob;
      audio._url = url;
      audio.addEventListener('ended', () => { btn.textContent = '▶'; });
    }
    audio.play();
    btn.textContent = '⏸';
  });
  return { stop: () => { if (audio) { audio.pause(); audio.currentTime = 0; btn.textContent = '▶'; } } };
}

makePlayer('sfx-play-btn', () => state.sfxBlob, () => state.sfxExt);
makePlayer('tts-play-btn', () => state.ttsBlob, () => state.ttsExt);

/* ── Save audio ────────────────────────────────────────────────────────── */
function saveAudio(blob, ext, prefix) {
  if (!blob) return;
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${prefix}_${Date.now()}.${ext}`;
  a.click();
  URL.revokeObjectURL(url);
}

$('sfx-save').addEventListener('click', () => saveAudio(state.sfxBlob, state.sfxExt, 'sfx'));
$('tts-save').addEventListener('click', () => saveAudio(state.ttsBlob, state.ttsExt, 'voice'));

/* ── SFX Generate ──────────────────────────────────────────────────────── */
$('sfx-generate').addEventListener('click', async () => {
  const prompt = $('sfx-prompt').value.trim();
  if (!prompt) { setStatus('sfx-status', 'Bitte Prompt eingeben', true); return; }

  setSpinner('sfx-spinner', true);
  setStatus('sfx-status', 'Generiere...');
  $('sfx-generate').disabled = true;
  $('sfx-player').classList.remove('visible');

  try {
    const body = {
      prompt,
      provider: $('sfx-provider').value,
      duration: parseFloat($('sfx-duration').value),
      hf_model: $('sfx-hf-model').value,
    };
    const res = await apiFetch('/api/sfx/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const ext = res.headers.get('X-Audio-Ext') || 'mp3';
    state.sfxBlob = await res.blob();
    state.sfxExt  = ext;
    $('sfx-audio-name').textContent = prompt.slice(0, 50);
    $('sfx-player').classList.add('visible');
    $('sfx-play-btn').textContent = '▶';
    setStatus('sfx-status', 'Fertig.');
  } catch (e) {
    setStatus('sfx-status', e.message, true);
  } finally {
    setSpinner('sfx-spinner', false);
    $('sfx-generate').disabled = false;
  }
});

/* ── TTS Generate ──────────────────────────────────────────────────────── */
$('tts-generate').addEventListener('click', async () => {
  const text = $('tts-text').value.trim();
  if (!text) { setStatus('tts-status', 'Bitte Text eingeben', true); return; }
  if (!state.voiceId) { setStatus('tts-status', 'Bitte Stimme auswählen', true); return; }

  setSpinner('tts-spinner', true);
  setStatus('tts-status', 'Generiere...');
  $('tts-generate').disabled = true;
  $('tts-player').classList.remove('visible');

  try {
    const provider = state.voiceProvider;
    const body = {
      text,
      provider,
      voice_id:   state.voiceId,
      model_id:   provider === 'openai' ? $('oai-model').value : $('tts-model').value,
      stability:  parseFloat($('tts-stability').value),
      similarity: parseFloat($('tts-similarity').value),
      style:      0.1,
      speed:      parseFloat(provider === 'openai' ? $('oai-speed').value : $('tts-speed').value),
    };
    const res = await apiFetch('/api/voice/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const ext = res.headers.get('X-Audio-Ext') || 'mp3';
    state.ttsBlob = await res.blob();
    state.ttsExt  = ext;
    $('tts-audio-name').textContent = text.slice(0, 50);
    $('tts-player').classList.add('visible');
    $('tts-play-btn').textContent = '▶';
    setStatus('tts-status', 'Fertig.');
  } catch (e) {
    setStatus('tts-status', e.message, true);
  } finally {
    setSpinner('tts-spinner', false);
    $('tts-generate').disabled = false;
  }
});

/* ── Voice Browser ─────────────────────────────────────────────────────── */
async function loadVoices(provider) {
  const grid = $('voice-grid');
  grid.innerHTML = '<div class="voice-loading">Lade Stimmen...</div>';
  state.voiceId = null;

  try {
    const res = await apiFetch(`/api/voices/${provider}`);
    const voices = await res.json();
    renderVoices(voices, provider);
  } catch (e) {
    grid.innerHTML = `<div class="voice-loading" style="color:#e05252">${e.message}</div>`;
  }
}

function renderVoices(voices, provider) {
  const grid = $('voice-grid');
  if (!voices.length) {
    grid.innerHTML = '<div class="voice-loading">Keine Stimmen gefunden</div>';
    return;
  }
  grid.innerHTML = '';

  voices.forEach(v => {
    const id    = v.voice_id ?? v.id ?? v;
    const name  = v.name ?? id;
    const desc  = v.desc ?? v.labels?.accent ?? v.category ?? '';
    const previewUrl = v.preview_url ?? null;

    const card = document.createElement('div');
    card.className = 'voice-card';
    card.dataset.name = name.toLowerCase();
    card.dataset.id   = id;
    card.innerHTML = `
      <div class="voice-card-name">${name}</div>
      ${desc ? `<div class="voice-card-meta">${desc}</div>` : ''}
      ${previewUrl ? `<button class="voice-card-preview" title="Vorschau">▶</button>` : ''}
    `;

    card.addEventListener('click', (e) => {
      if (e.target.classList.contains('voice-card-preview')) return;
      document.querySelectorAll('.voice-card').forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
      state.voiceId = id;
    });

    const previewBtn = card.querySelector('.voice-card-preview');
    if (previewBtn) {
      previewBtn.addEventListener('click', async (e) => {
        e.stopPropagation();
        try {
          const res = await apiFetch(`/api/voice/preview?url=${encodeURIComponent(previewUrl)}`);
          const blob = await res.blob();
          const url = URL.createObjectURL(blob);
          const a = new Audio(url);
          a.play();
          previewBtn.textContent = '⏸';
          a.addEventListener('ended', () => { previewBtn.textContent = '▶'; URL.revokeObjectURL(url); });
        } catch (_) {}
      });
    }

    grid.appendChild(card);
  });
}

/* ── OpenRouter Models ─────────────────────────────────────────────────── */
async function loadORModels() {
  try {
    const res = await apiFetch('/api/openrouter/models');
    state.orModels = await res.json();
    updateModelSelects();
  } catch (_) {
    state.orModels = [];
  }
}

function updateModelSelects() {
  ['sfx-refine-model', 'tts-refine-model'].forEach(id => {
    const sel = $(id);
    sel.innerHTML = '';
    if (!state.orModels.length) {
      sel.innerHTML = '<option value="">Kein OpenRouter-Key gesetzt</option>';
      return;
    }
    state.orModels.forEach(m => {
      const opt = document.createElement('option');
      opt.value = m.id;
      const tag = m.is_free ? '[free] ' : '';
      opt.textContent = tag + (m.name ?? m.id);
      sel.appendChild(opt);
    });
  });
}

/* ── Refine Panel ──────────────────────────────────────────────────────── */
function setupRefine(toggleId, panelId, modelId, runId, resultId, actionsId, discardId, applyId, textareaId, type) {
  $(toggleId).addEventListener('click', () => {
    $(panelId).classList.toggle('visible');
  });

  $(runId).addEventListener('click', async () => {
    const prompt = $(textareaId).value.trim();
    if (!prompt) return;
    const model = $(modelId).value;
    if (!model) return;

    $(runId).disabled = true;
    $(resultId).textContent = 'Verfeinere...';
    $(resultId).classList.add('visible');
    $(actionsId).style.display = 'none';

    try {
      const res = await apiFetch('/api/prompt/refine', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, type, model }),
      });
      const data = await res.json();
      $(resultId).textContent = data.refined;
      $(actionsId).style.display = 'flex';
    } catch (e) {
      $(resultId).textContent = 'Fehler: ' + e.message;
    } finally {
      $(runId).disabled = false;
    }
  });

  $(discardId).addEventListener('click', () => {
    $(resultId).textContent = '';
    $(resultId).classList.remove('visible');
    $(actionsId).style.display = 'none';
  });

  $(applyId).addEventListener('click', () => {
    const refined = $(resultId).textContent;
    if (refined) $(textareaId).value = refined;
    $(panelId).classList.remove('visible');
    $(resultId).classList.remove('visible');
    $(actionsId).style.display = 'none';
  });
}

setupRefine('sfx-refine-toggle', 'sfx-refine-panel', 'sfx-refine-model', 'sfx-refine-run',
  'sfx-refine-result', 'sfx-refine-actions', 'sfx-refine-discard', 'sfx-refine-apply', 'sfx-prompt', 'sfx');

setupRefine('tts-refine-toggle', 'tts-refine-panel', 'tts-refine-model', 'tts-refine-run',
  'tts-refine-result', 'tts-refine-actions', 'tts-refine-discard', 'tts-refine-apply', 'tts-text', 'tts');

/* ── Settings ──────────────────────────────────────────────────────────── */
async function loadConfig() {
  try {
    const res = await apiFetch('/api/config');
    const cfg = await res.json();
    $('output-format').value = cfg.default_format ?? 'mp3';
    // Show placeholder if key is set
    Object.entries(cfg.keys_set ?? {}).forEach(([provider, set]) => {
      const el = $('key-' + provider);
      if (el && set) el.placeholder = '••••••••  (gesetzt)';
    });
  } catch (_) {}
}

document.querySelectorAll('[data-test]').forEach(btn => {
  btn.addEventListener('click', async () => {
    const provider = btn.dataset.test;
    const keyEl = $('key-' + provider);
    const key = keyEl.value.trim();
    const statusEl = $('status-' + provider);
    if (!key) { statusEl.textContent = 'Key eingeben'; statusEl.className = 'key-status error'; return; }

    btn.disabled = true;
    statusEl.textContent = 'Teste...';
    statusEl.className = 'key-status';
    try {
      const res = await apiFetch('/api/test-key', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider, key }),
      });
      const data = await res.json();
      const ok = data.result?.startsWith('OK');
      statusEl.textContent = data.result;
      statusEl.className = 'key-status ' + (ok ? 'ok' : 'error');
      if (ok && provider === 'openrouter') loadORModels();
    } catch (e) {
      statusEl.textContent = e.message;
      statusEl.className = 'key-status error';
    } finally {
      btn.disabled = false;
    }
  });
});

$('settings-save').addEventListener('click', async () => {
  const keys = {};
  ['elevenlabs', 'openai', 'huggingface', 'openrouter'].forEach(p => {
    const v = $('key-' + p).value.trim();
    if (v) keys[p] = v;
  });

  try {
    await apiFetch('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_keys: keys, default_format: $('output-format').value }),
    });
    setStatus('settings-status', 'Gespeichert.');
    if (keys.openrouter) loadORModels();
    setTimeout(() => setStatus('settings-status', ''), 3000);
  } catch (e) {
    setStatus('settings-status', e.message, true);
  }
});

/* ── Init ──────────────────────────────────────────────────────────────── */
(async function init() {
  await loadConfig();
  await loadVoices('elevenlabs');
  await loadORModels();
})();
