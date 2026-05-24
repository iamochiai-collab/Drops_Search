let allCards = [];
let filteredCards = [];
let visibleCount = 0;
let activePreviewId = null;
let favoriteIds = new Set();
let selectedIds = new Set();
let showFavoritesOnly = false;
let showSelectedOnly = false;
const PAGE_SIZE = 96;
const FAVORITES_KEY = 'dropletFavorites';
const $ = (id) => document.getElementById(id);

const QUICK_TAG_CANDIDATES = [
  '学校', '先生', '友達', 'ありがとう', 'トイレ', '食べる', '飲む', 'ご飯',
  '家', 'お風呂', '寝る', '遊ぶ', '歩く', '走る', '病院', '保健室',
  '図書館', '公園', '車', '電車', 'バス', '車椅子', '痛い', '嬉しい'
];

function kanaToHira(str) {
  return String(str || '').replace(/[\u30a1-\u30f6]/g, ch => String.fromCharCode(ch.charCodeAt(0) - 0x60));
}

function normalizeText(str) {
  return kanaToHira(String(str || ''))
    .normalize('NFKC')
    .toLowerCase()
    .replace(/[\s　・･、。,.，．（）()［\]【】「」『』\-_/／]+/g, '')
    .trim();
}

function tokenizeQuery(query) {
  return String(query || '')
    .trim()
    .split(/[\s　]+/)
    .map(normalizeText)
    .filter(Boolean);
}

function unique(arr) {
  return [...new Set(arr)].filter(Boolean);
}

function makeSearchTerms(card) {
  return unique([card.title, card.category, card.subcategory, card.code, ...(card.tags || [])]);
}

function makeSearchText(card) {
  return makeSearchTerms(card).map(normalizeText).join(' ');
}

function levenshtein(a, b) {
  if (a === b) return 0;
  if (!a.length || !b.length) return Math.max(a.length, b.length);
  const dp = Array.from({ length: a.length + 1 }, (_, i) => Array(b.length + 1).fill(0));
  for (let i = 0; i <= a.length; i++) dp[i][0] = i;
  for (let j = 0; j <= b.length; j++) dp[0][j] = j;
  for (let i = 1; i <= a.length; i++) {
    for (let j = 1; j <= b.length; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      dp[i][j] = Math.min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost);
    }
  }
  return dp[a.length][b.length];
}

function scoreTokenAgainstCard(card, token) {
  const terms = card._searchTerms;
  const title = normalizeText(card.title);
  if (title === token) return 2000;
  if (terms.includes(token)) return 1800;
  if (title.startsWith(token)) return 1200;
  if (title.includes(token)) return 1000;
  if (card.searchText.includes(token)) return 800;

  let best = 0;
  for (const term of terms) {
    if (!term) continue;
    if (term.includes(token) || token.includes(term)) best = Math.max(best, 650);
    const limit = token.length <= 3 ? 1 : token.length <= 6 ? 2 : 3;
    const d = levenshtein(token, term);
    if (d <= limit) best = Math.max(best, 480 - d * 40);
  }
  return best;
}

function scoreCard(card, query) {
  const tokens = tokenizeQuery(query);
  if (!tokens.length) return 0;
  let total = 0;
  for (const token of tokens) {
    const s = scoreTokenAgainstCard(card, token);
    if (s <= 0) return 0;
    total += s;
  }
  return total;
}

function loadFavorites() {
  try {
    const saved = JSON.parse(localStorage.getItem(FAVORITES_KEY) || '[]');
    favoriteIds = new Set(Array.isArray(saved) ? saved : []);
  } catch {
    favoriteIds = new Set();
  }
}

function saveFavorites() {
  localStorage.setItem(FAVORITES_KEY, JSON.stringify([...favoriteIds]));
  updateCounters();
}

function updateCounters() {
  $('favoriteCount').textContent = favoriteIds.size;
  $('selectedCountInline').textContent = selectedIds.size;
  $('selectedCountBar').textContent = selectedIds.size;
  $('selectionBar').hidden = selectedIds.size === 0;
}

function initFilters() {
  const categories = unique(allCards.map(c => c.category));
  $('categorySelect').innerHTML = `<option value="">すべての大カテゴリ</option>` + categories.map(c => `<option>${escapeHtml(c)}</option>`).join('');
  $('categoryButtons').innerHTML = [`<button class="chip active" data-cat="">全部</button>`, ...categories.map(c => `<button class="chip" data-cat="${escapeHtml(c)}">${escapeHtml(c)}</button>`)].join('');
  document.querySelectorAll('.chip').forEach(btn => {
    btn.addEventListener('click', () => {
      $('categorySelect').value = btn.dataset.cat;
      updateSubcategoryOptions();
      applySearch();
    });
  });
  updateSubcategoryOptions();
}

function updateSubcategoryOptions() {
  const cat = $('categorySelect').value;
  const subs = unique(allCards.filter(c => !cat || c.category === cat).map(c => c.subcategory));
  $('subcategorySelect').innerHTML = `<option value="">すべての小カテゴリ</option>` + subs.map(s => `<option>${escapeHtml(s)}</option>`).join('');
  document.querySelectorAll('.chip').forEach(btn => btn.classList.toggle('active', btn.dataset.cat === cat));
}

function buildQuickTags() {
  const available = new Set(allCards.flatMap(card => [card.title, ...(card.tags || [])]).map(normalizeText));
  const usable = QUICK_TAG_CANDIDATES.filter(tag => available.has(normalizeText(tag)));
  $('commonTags').innerHTML = usable.map(tag => `<button type="button" class="chip quick-tag" data-tag="${escapeHtml(tag)}">${escapeHtml(tag)}</button>`).join('');
  document.querySelectorAll('.quick-tag').forEach(btn => {
    btn.addEventListener('click', () => {
      const tag = btn.dataset.tag;
      const alreadyActive = btn.classList.contains('active');

      // よく使うタグは「1つだけ選択」方式。
      // 同じタグをもう一度押したら解除、別のタグを押したら前のタグ検索を消して置き換える。
      document.querySelectorAll('.quick-tag').forEach(b => b.classList.remove('active'));

      if (alreadyActive) {
        $('searchInput').value = '';
      } else {
        btn.classList.add('active');
        $('searchInput').value = tag;
      }

      applySearch();
      $('searchInput').focus();
    });
  });
}

function updateToggleButtons() {
  $('favoriteFilterButton').classList.toggle('active', showFavoritesOnly);
  $('favoriteFilterButton').setAttribute('aria-pressed', String(showFavoritesOnly));
  $('showSelectedButton').classList.toggle('active', showSelectedOnly);
  $('showSelectedButton').setAttribute('aria-pressed', String(showSelectedOnly));
}

function applySearch() {
  const query = $('searchInput').value;
  const hasQuery = tokenizeQuery(query).length > 0;
  const cat = $('categorySelect').value;
  const sub = $('subcategorySelect').value;
  const sort = $('sortSelect').value;

  filteredCards = allCards
    .map(card => ({ ...card, score: hasQuery ? scoreCard(card, query) : 0 }))
    .filter(card => {
      const okQuery = !hasQuery || card.score > 0;
      const okCat = !cat || card.category === cat;
      const okSub = !sub || card.subcategory === sub;
      const okFav = !showFavoritesOnly || favoriteIds.has(card.id);
      const okSelected = !showSelectedOnly || selectedIds.has(card.id);
      return okQuery && okCat && okSub && okFav && okSelected;
    });

  if (sort === 'favorite') {
    filteredCards.sort((a, b) => Number(favoriteIds.has(b.id)) - Number(favoriteIds.has(a.id)) || String(a.code).localeCompare(String(b.code), 'ja'));
  } else if (sort === 'score') {
    filteredCards.sort((a, b) => (b.score - a.score) || String(a.code).localeCompare(String(b.code), 'ja'));
  } else if (sort === 'title') {
    filteredCards.sort((a, b) => String(a.title).localeCompare(String(b.title), 'ja'));
  } else {
    filteredCards.sort((a, b) => String(a.code).localeCompare(String(b.code), 'ja'));
  }

  visibleCount = PAGE_SIZE;
  render();
  updateToggleButtons();
  updateCounters();
}

function render() {
  const shown = filteredCards.slice(0, visibleCount);
  $('resultCount').textContent = `${filteredCards.length}件ヒット`;
  $('grid').innerHTML = shown.map(card => {
    const isFavorite = favoriteIds.has(card.id);
    const isSelected = selectedIds.has(card.id);
    return `
      <article class="card ${isFavorite ? 'is-favorite' : ''} ${isSelected ? 'is-selected' : ''}" tabindex="0" data-id="${card.id}">
        <div class="card-top-actions">
          <button class="icon-action favorite ${isFavorite ? 'active' : ''}" type="button" data-action="favorite" data-id="${card.id}" title="お気に入り">${isFavorite ? '★' : '☆'}<span>お気に入り</span></button>
          <button class="icon-action select ${isSelected ? 'active' : ''}" type="button" data-action="select" data-id="${card.id}" title="選択">${isSelected ? '☑' : '☐'}<span>選択</span></button>
        </div>
        <div class="thumb-wrap">
          <img class="thumb" src="${card.image}" alt="${escapeHtml(card.title)}" loading="lazy">
        </div>
        <div>
          <div class="title">${escapeHtml(card.title)}</div>
          <div class="meta">${escapeHtml(card.subcategory)} / ${escapeHtml(card.code)}</div>
        </div>
        <div class="card-actions">
          <button class="icon-action" type="button" data-action="copy" data-id="${card.id}" title="画像をコピー"><span>📋</span><span>コピー</span></button>
          <button class="icon-action" type="button" data-action="download" data-id="${card.id}" title="ダウンロード"><span>⬇</span><span>保存</span></button>
        </div>
      </article>
    `;
  }).join('');

  document.querySelectorAll('.card').forEach(el => {
    el.addEventListener('click', (e) => {
      if (e.target.closest('.icon-action')) return;
      openPreview(el.dataset.id);
    });
    el.addEventListener('keydown', (e) => { if (e.key === 'Enter') openPreview(el.dataset.id); });
  });

  document.querySelectorAll('.icon-action').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const card = allCards.find(c => c.id === btn.dataset.id);
      if (!card) return;
      const action = btn.dataset.action;
      if (action === 'copy') await copyImage(card);
      if (action === 'download') downloadImage(card);
      if (action === 'favorite') toggleFavorite(card.id);
      if (action === 'select') toggleSelect(card.id);
    });
  });

  $('moreButton').style.display = visibleCount < filteredCards.length ? 'block' : 'none';
}

function toggleFavorite(id) {
  if (favoriteIds.has(id)) favoriteIds.delete(id);
  else favoriteIds.add(id);
  saveFavorites();
  render();
  refreshPreviewButtons();
}

function toggleSelect(id) {
  if (selectedIds.has(id)) selectedIds.delete(id);
  else selectedIds.add(id);
  updateCounters();
  render();
  refreshPreviewButtons();
}

function refreshPreviewButtons() {
  if (!activePreviewId) return;
  const isFavorite = favoriteIds.has(activePreviewId);
  const isSelected = selectedIds.has(activePreviewId);
  $('previewFavorite').textContent = isFavorite ? '★ お気に入り解除' : '☆ お気に入りに追加';
  $('previewFavorite').classList.toggle('active', isFavorite);
  $('previewSelect').textContent = isSelected ? '☑ 選択を解除' : '☐ この画像を選択';
  $('previewSelect').classList.toggle('active', isSelected);
}

function openPreview(id) {
  const card = allCards.find(c => c.id === id);
  if (!card) return;
  activePreviewId = id;
  $('previewImage').src = card.image;
  $('previewImage').alt = card.title;
  $('previewTitle').textContent = card.title;
  $('previewMeta').textContent = `${card.category} ＞ ${card.subcategory} / 番号：${card.code}`;
  $('previewOriginal').textContent = `元ファイル：${card.originalFile}`;
  $('previewTags').textContent = `検索ワード：${(card.tags || []).slice(0, 80).join('、')}`;
  refreshPreviewButtons();
  $('previewDialog').showModal();
}

function makeDownloadName(card) {
  const ext = (card.image.split('.').pop() || 'png').toLowerCase();
  const title = String(card.title || 'droplet').replace(/[\\/:*?"<>|]/g, '_');
  return `${title}.${ext}`;
}

async function fetchImageBlob(card) {
  const res = await fetch(card.image);
  if (!res.ok) throw new Error('画像取得に失敗しました');
  return await res.blob();
}

function loadImageForCanvas(src) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.decoding = 'async';
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = src;
  });
}

async function makePngBlobForClipboard(card) {
  // Clipboard APIはGIFのままでは失敗するブラウザが多いので、
  // コピー時だけPNGに変換してからクリップボードへ入れる。
  const img = await loadImageForCanvas(card.image);
  const canvas = document.createElement('canvas');
  canvas.width = img.naturalWidth || img.width;
  canvas.height = img.naturalHeight || img.height;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(img, 0, 0);
  return await new Promise((resolve, reject) => {
    canvas.toBlob(blob => {
      if (blob) resolve(blob);
      else reject(new Error('PNG変換に失敗しました'));
    }, 'image/png');
  });
}

async function copyImage(card) {
  try {
    if (!navigator.clipboard || !window.ClipboardItem) throw new Error('copy-unsupported');
    const pngBlob = await makePngBlobForClipboard(card);
    await navigator.clipboard.write([new ClipboardItem({ 'image/png': pngBlob })]);
    showToast('画像をコピーしたよ');
  } catch (err) {
    console.error(err);
    // ブラウザが画像コピーに未対応の場合でも、URLだけはコピーを試す。
    try {
      const url = new URL(card.image, location.href).href;
      await navigator.clipboard.writeText(url);
      showToast('画像コピーは不可。画像URLをコピーしたよ');
    } catch {
      showToast('コピーできなかったので、画像だけ開いて長押し保存してね');
    }
    openPreview(card.id);
  }
}

function downloadImage(card) {
  const a = document.createElement('a');
  a.href = card.image;
  a.download = makeDownloadName(card);
  document.body.appendChild(a);
  a.click();
  a.remove();
}

async function bulkDownloadSelected() {
  const cards = allCards.filter(card => selectedIds.has(card.id));
  if (!cards.length) {
    showToast('先に画像を選択してね');
    return;
  }
  showToast(`${cards.length}枚のダウンロードを順番に始めるよ`);
  for (const [i, card] of cards.entries()) {
    downloadImage(card);
    await new Promise(resolve => setTimeout(resolve, i === 0 ? 100 : 180));
  }
}

async function bulkCopySelectedAsImage() {
  const cards = allCards.filter(card => selectedIds.has(card.id));
  if (!cards.length) {
    showToast('先に画像を選択してね');
    return;
  }

  if (!navigator.clipboard || !window.ClipboardItem) {
    showToast('このブラウザでは画像コピーに対応していないかも');
    return;
  }

  try {
    showToast(`${cards.length}枚を1枚の画像にまとめてコピー中...`);

    // 選択画像を1枚のシート画像にしてコピーする。
    // 複数の画像を別々に一括コピーするのはブラウザ対応が不安定なため、この方式にしている。
    const cellSize = 180;
    const gap = 18;
    const labelHeight = 34;
    const padding = 24;
    const maxColumns = 5;
    const columns = Math.min(maxColumns, Math.max(1, Math.ceil(Math.sqrt(cards.length))));
    const rows = Math.ceil(cards.length / columns);

    const canvas = document.createElement('canvas');
    canvas.width = padding * 2 + columns * cellSize + (columns - 1) * gap;
    canvas.height = padding * 2 + rows * (cellSize + labelHeight) + (rows - 1) * gap;

    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.font = '16px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
    ctx.fillStyle = '#1e293b';

    for (const [index, card] of cards.entries()) {
      const img = await loadImageForCanvas(card.image);
      const col = index % columns;
      const row = Math.floor(index / columns);
      const x = padding + col * (cellSize + gap);
      const y = padding + row * (cellSize + labelHeight + gap);

      ctx.fillStyle = '#f8fafc';
      roundRect(ctx, x, y, cellSize, cellSize, 18);
      ctx.fill();

      const scale = Math.min(cellSize * 0.86 / img.width, cellSize * 0.86 / img.height);
      const drawW = img.width * scale;
      const drawH = img.height * scale;
      const drawX = x + (cellSize - drawW) / 2;
      const drawY = y + (cellSize - drawH) / 2;
      ctx.drawImage(img, drawX, drawY, drawW, drawH);

      ctx.fillStyle = '#1e293b';
      const title = card.title.length > 12 ? `${card.title.slice(0, 12)}…` : card.title;
      ctx.fillText(title, x + cellSize / 2, y + cellSize + labelHeight / 2);
    }

    const pngBlob = await new Promise((resolve, reject) => {
      canvas.toBlob(blob => {
        if (blob) resolve(blob);
        else reject(new Error('まとめ画像の作成に失敗しました'));
      }, 'image/png');
    });

    await navigator.clipboard.write([new ClipboardItem({ 'image/png': pngBlob })]);
    showToast(`${cards.length}枚をまとめ画像としてコピーしたよ`);
  } catch (err) {
    console.error(err);
    showToast('一括コピーできなかった。枚数を減らすか、ダウンロードを使ってね');
  }
}

function roundRect(ctx, x, y, width, height, radius) {
  const r = Math.min(radius, width / 2, height / 2);
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + width, y, x + width, y + height, r);
  ctx.arcTo(x + width, y + height, x, y + height, r);
  ctx.arcTo(x, y + height, x, y, r);
  ctx.arcTo(x, y, x + width, y, r);
  ctx.closePath();
}

function selectVisible() {
  filteredCards.slice(0, visibleCount).forEach(card => selectedIds.add(card.id));
  updateCounters();
  render();
  refreshPreviewButtons();
  showToast('表示中の画像を選択したよ');
}

function clearSelection() {
  selectedIds.clear();
  updateCounters();
  render();
  refreshPreviewButtons();
}

function showToast(message) {
  const el = $('toast');
  el.textContent = message;
  el.hidden = false;
  clearTimeout(showToast._timer);
  showToast._timer = setTimeout(() => { el.hidden = true; }, 2200);
}

function escapeHtml(str) {
  return String(str || '').replace(/[&<>"']/g, s => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[s]));
}

async function start() {
  loadFavorites();
  const res = await fetch('data/cards.json');
  allCards = await res.json();
  allCards = allCards.map(card => ({
    ...card,
    _searchTerms: makeSearchTerms(card).map(normalizeText),
    searchText: makeSearchText(card),
  }));

  $('totalCount').textContent = `${allCards.length}`;
  initFilters();
  buildQuickTags();
  updateCounters();
  applySearch();

  $('searchInput').addEventListener('input', () => {
    const value = $('searchInput').value.trim();
    document.querySelectorAll('.quick-tag.active').forEach(btn => {
      if (btn.dataset.tag !== value) btn.classList.remove('active');
    });
    applySearch();
  });
  $('categorySelect').addEventListener('change', () => { updateSubcategoryOptions(); applySearch(); });
  $('subcategorySelect').addEventListener('change', applySearch);
  $('sortSelect').addEventListener('change', applySearch);

  $('clearButton').addEventListener('click', () => {
    $('searchInput').value = '';
    document.querySelectorAll('.quick-tag').forEach(b => b.classList.remove('active'));
    $('categorySelect').value = '';
    updateSubcategoryOptions();
    $('subcategorySelect').value = '';
    $('sortSelect').value = 'score';
    showFavoritesOnly = false;
    showSelectedOnly = false;
    applySearch();
    $('searchInput').focus();
  });

  $('favoriteFilterButton').addEventListener('click', () => {
    showFavoritesOnly = !showFavoritesOnly;
    applySearch();
  });

  $('showSelectedButton').addEventListener('click', () => {
    showSelectedOnly = !showSelectedOnly;
    applySearch();
  });

  $('moreButton').addEventListener('click', () => { visibleCount += PAGE_SIZE; render(); });
  $('selectVisibleButton').addEventListener('click', selectVisible);
  $('clearSelectionButton').addEventListener('click', clearSelection);
  $('bulkCopyButton').addEventListener('click', bulkCopySelectedAsImage);
  $('bulkDownloadButton').addEventListener('click', bulkDownloadSelected);

  $('closeDialog').addEventListener('click', () => $('previewDialog').close());
  $('previewFavorite').addEventListener('click', () => {
    if (activePreviewId) toggleFavorite(activePreviewId);
  });
  $('previewSelect').addEventListener('click', () => {
    if (activePreviewId) toggleSelect(activePreviewId);
  });
  $('previewCopy').addEventListener('click', async () => {
    const card = allCards.find(c => c.id === activePreviewId);
    if (card) await copyImage(card);
  });
  $('previewDownload').addEventListener('click', () => {
    const card = allCards.find(c => c.id === activePreviewId);
    if (card) {
      downloadImage(card);
      showToast('ダウンロードを開始したよ');
    }
  });
  $('previewOpen').addEventListener('click', () => {
    const card = allCards.find(c => c.id === activePreviewId);
    if (card) window.open(card.image, '_blank');
  });
}

start().catch(err => {
  console.error(err);
  $('grid').innerHTML = '<p>データの読み込みに失敗しました。GitHub Pagesなどのサーバー上で開いてください。</p>';
});
