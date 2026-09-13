// State Management
const state = {
  file: null,
  serverFilename: null,
  findings: [],
  originalDoc: null,
  protectedDoc: null,
  step2Page: 1,
  step3Page: 1,
  currentTab: 'protected'
};

// DOM Elements
const pdfFileInput = document.getElementById('pdfFileInput');
const dropzone = document.getElementById('dropzone');
const fileLoadedCard = document.getElementById('fileLoadedCard');
const selectedName = document.getElementById('selectedName');
const selectedSize = document.getElementById('selectedSize');
const btnClearFile = document.getElementById('btnClearFile');
const btnScanDoc = document.getElementById('btnScanDoc');

const panelStep1 = document.getElementById('panelStep1');
const panelStep2 = document.getElementById('panelStep2');
const panelStep3 = document.getElementById('panelStep3');

const stepBadge1 = document.getElementById('stepBadge1');
const stepBadge2 = document.getElementById('stepBadge2');
const stepBadge3 = document.getElementById('stepBadge3');

const entityListBox = document.getElementById('entityListBox');
const foundCountPill = document.getElementById('foundCountPill');
const btnBackToUpload = document.getElementById('btnBackToUpload');
const btnApplyRedaction = document.getElementById('btnApplyRedaction');

const canvasStep2 = document.getElementById('canvasStep2');
const ctxStep2 = canvasStep2 ? canvasStep2.getContext('2d') : null;
const step2Cur = document.getElementById('step2Cur');
const step2Total = document.getElementById('step2Total');
const step2Prev = document.getElementById('step2Prev');
const step2Next = document.getElementById('step2Next');

const canvasStep3 = document.getElementById('canvasStep3');
const ctxStep3 = canvasStep3 ? canvasStep3.getContext('2d') : null;
const step3Cur = document.getElementById('step3Cur');
const step3Total = document.getElementById('step3Total');
const step3Prev = document.getElementById('step3Prev');
const step3Next = document.getElementById('step3Next');

const tabViewProtected = document.getElementById('tabViewProtected');
const tabViewOriginal = document.getElementById('tabViewOriginal');
const btnDownloadFile = document.getElementById('btnDownloadFile');
const btnStartNew = document.getElementById('btnStartNew');

const globalLoader = document.getElementById('globalLoader');
const loaderTitle = document.getElementById('loaderTitle');
const loaderSubtitle = document.getElementById('loaderSubtitle');

// Helper: Show/Hide Loader
function showLoading(title, subtitle) {
  if (loaderTitle) loaderTitle.innerText = title || 'Processing';
  if (loaderSubtitle) loaderSubtitle.innerText = subtitle || 'Please wait...';
  if (globalLoader) globalLoader.style.display = 'flex';
}

function hideLoading() {
  if (globalLoader) globalLoader.style.display = 'none';
}

// Helper: Step Navigation
function goToStep(stepNum) {
  [panelStep1, panelStep2, panelStep3].forEach(p => p && p.classList.remove('active'));
  [stepBadge1, stepBadge2, stepBadge3].forEach(b => b && b.classList.remove('active'));

  if (stepNum === 1) {
    if (panelStep1) panelStep1.classList.add('active');
    if (stepBadge1) stepBadge1.classList.add('active');
  } else if (stepNum === 2) {
    if (panelStep2) panelStep2.classList.add('active');
    if (stepBadge2) stepBadge2.classList.add('active');
  } else if (stepNum === 3) {
    if (panelStep3) panelStep3.classList.add('active');
    if (stepBadge3) stepBadge3.classList.add('active');
  }
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Drag and Drop Listeners
if (dropzone && pdfFileInput) {
  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('hover');
  });

  dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('hover');
  });

  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('hover');
    if (e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  pdfFileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      handleFileSelected(e.target.files[0]);
    }
  });
}

function handleFileSelected(file) {
  state.file = file;
  if (selectedName) selectedName.innerText = file.name;
  if (selectedSize) selectedSize.innerText = `${(file.size / 1024).toFixed(1)} KB`;
  if (dropzone) dropzone.style.display = 'none';
  if (fileLoadedCard) fileLoadedCard.style.display = 'block';
}

if (btnClearFile) {
  btnClearFile.addEventListener('click', () => {
    state.file = null;
    if (pdfFileInput) pdfFileInput.value = '';
    if (dropzone) dropzone.style.display = 'block';
    if (fileLoadedCard) fileLoadedCard.style.display = 'none';
  });
}

// Render PDF Page onto Canvas with Dynamic Mobile Scale Fitting
async function renderCanvasPage(pdfDoc, pageNum, canvas, ctx, curSpan, prevBtn, nextBtn, totalPages) {
  if (!pdfDoc || !canvas || !ctx) return;

  const page = await pdfDoc.getPage(pageNum);
  const unscaledViewport = page.getViewport({ scale: 1.0 });

  // Calculate fitting ratio according to container width on small screens
  const containerWidth = canvas.parentElement ? canvas.parentElement.clientWidth - 24 : 600;
  const isMobile = window.innerWidth <= 960;
  
  let scale = 1.5;
  if (isMobile && containerWidth > 50) {
    scale = Math.min(1.5, Math.max(0.7, containerWidth / unscaledViewport.width));
  }

  const viewport = page.getViewport({ scale: scale });

  canvas.width = viewport.width;
  canvas.height = viewport.height;

  const renderContext = {
    canvasContext: ctx,
    viewport: viewport
  };

  await page.render(renderContext).promise;

  if (curSpan) curSpan.innerText = pageNum;
  if (prevBtn) prevBtn.disabled = pageNum <= 1;
  if (nextBtn) nextBtn.disabled = pageNum >= totalPages;
}

// Handle window resize dynamically to adjust PDF scale
window.addEventListener('resize', () => {
  if (panelStep2 && panelStep2.classList.contains('active') && state.originalDoc) {
    renderCanvasPage(state.originalDoc, state.step2Page, canvasStep2, ctxStep2, step2Cur, step2Prev, step2Next, state.originalDoc.numPages);
  } else if (panelStep3 && panelStep3.classList.contains('active')) {
    const doc = state.currentTab === 'protected' ? state.protectedDoc : state.originalDoc;
    if (doc) {
      renderCanvasPage(doc, state.step3Page, canvasStep3, ctxStep3, step3Cur, step3Prev, step3Next, doc.numPages);
    }
  }
});

// Render Entities in Step 2: Uniform red tag styling
function renderEntityItems() {
  if (!entityListBox) return;
  entityListBox.innerHTML = '';

  const findings = state.findings || [];
  if (foundCountPill) {
    foundCountPill.innerText = `${findings.length} found`;
  }

  if (findings.length === 0) {
    entityListBox.innerHTML = `<div class="no-entities" style="padding: 16px; color: #94a3b8; font-size: 0.85rem;">No sensitive PII detected.</div>`;
    return;
  }

  findings.forEach((item, index) => {
    const row = document.createElement('div');
    row.className = 'entity-item-row';

    row.innerHTML = `
      <div class="entity-item-info">
        <span class="entity-tag tag-red">${item.label}</span>
        <div class="entity-text-group">
          <span class="entity-val">${item.value}</span>
          <span class="entity-meta">Page ${item.page || 1} &bull; ${item.source || 'scanner'}</span>
        </div>
      </div>
      <label class="custom-checkbox">
        <input type="checkbox" data-index="${index}" checked />
        <span class="checkmark"></span>
      </label>
    `;

    const checkbox = row.querySelector('input[type="checkbox"]');
    checkbox.addEventListener('change', (e) => {
      state.findings[index].excluded = !e.target.checked;
    });

    entityListBox.appendChild(row);
  });
}

// Step 1 -> Step 2: Upload and Analyze
if (btnScanDoc) {
  btnScanDoc.addEventListener('click', async () => {
    if (!state.file) return;

    showLoading('Analyzing Document', 'Extracting high-sensitivity identifiers...');

    try {
      const formData = new FormData();
      formData.append('document', state.file);

      const res = await fetch('/scan', { method: 'POST', body: formData });
      if (!res.ok) throw new Error('Document scan failed.');
      const data = await res.json();

      state.serverFilename = data.filename;
      state.findings = data.detections || [];
      renderEntityItems();

      const pdfBytes = await fetch(`/uploads/${state.serverFilename}`).then(r => r.arrayBuffer());
      state.originalDoc = await pdfjsLib.getDocument({ data: pdfBytes }).promise;

      state.step2Page = 1;
      if (step2Total) step2Total.innerText = state.originalDoc.numPages;

      goToStep(2);
      setTimeout(async () => {
        await renderCanvasPage(state.originalDoc, 1, canvasStep2, ctxStep2, step2Cur, step2Prev, step2Next, state.originalDoc.numPages);
      }, 50);

    } catch (err) {
      alert('Scan error: ' + err.message);
    } finally {
      hideLoading();
    }
  });
}

// Step 2 Pagination
if (step2Prev) {
  step2Prev.addEventListener('click', async () => {
    if (state.step2Page > 1) {
      state.step2Page--;
      await renderCanvasPage(state.originalDoc, state.step2Page, canvasStep2, ctxStep2, step2Cur, step2Prev, step2Next, state.originalDoc.numPages);
    }
  });
}

if (step2Next) {
  step2Next.addEventListener('click', async () => {
    if (state.step2Page < state.originalDoc.numPages) {
      state.step2Page++;
      await renderCanvasPage(state.originalDoc, state.step2Page, canvasStep2, ctxStep2, step2Cur, step2Prev, step2Next, state.originalDoc.numPages);
    }
  });
}

if (btnBackToUpload) {
  btnBackToUpload.addEventListener('click', () => {
    goToStep(1);
  });
}

// Step 2 -> Step 3: Apply Redactions
if (btnApplyRedaction) {
  btnApplyRedaction.addEventListener('click', async () => {
    const selectedMode = document.querySelector('input[name="maskMode"]:checked')?.value || 'partial';
    const activeDetections = (state.findings || []).filter(item => !item.excluded);

    showLoading('Redacting Document', 'Sanitizing pixels and purging vector metadata...');

    try {
      const res = await fetch('/protect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename: state.serverFilename,
          mode: selectedMode,
          detections: activeDetections
        })
      });

      if (!res.ok) throw new Error('Redaction failed.');
      const data = await res.json();

      state.protectedFilename = data.protected_filename;
      state.protectedUrl = data.protected_url;

      const protBytes = await fetch(state.protectedUrl).then(r => r.arrayBuffer());
      state.protectedDoc = await pdfjsLib.getDocument({ data: protBytes }).promise;

      state.step3Page = 1;
      state.currentTab = 'protected';
      if (tabViewProtected) tabViewProtected.classList.add('active');
      if (tabViewOriginal) tabViewOriginal.classList.remove('active');
      if (step3Total) step3Total.innerText = state.protectedDoc.numPages;

      goToStep(3);
      setTimeout(async () => {
        await renderCanvasPage(state.protectedDoc, 1, canvasStep3, ctxStep3, step3Cur, step3Prev, step3Next, state.protectedDoc.numPages);
      }, 50);

    } catch (err) {
      alert('Protection error: ' + err.message);
    } finally {
      hideLoading();
    }
  });
}

// Step 3 Tab Switching & Pagination
if (tabViewProtected) {
  tabViewProtected.addEventListener('click', async () => {
    state.currentTab = 'protected';
    tabViewProtected.classList.add('active');
    if (tabViewOriginal) tabViewOriginal.classList.remove('active');
    await renderCanvasPage(state.protectedDoc, state.step3Page, canvasStep3, ctxStep3, step3Cur, step3Prev, step3Next, state.protectedDoc.numPages);
  });
}

if (tabViewOriginal) {
  tabViewOriginal.addEventListener('click', async () => {
    state.currentTab = 'original';
    tabViewOriginal.classList.add('active');
    if (tabViewProtected) tabViewProtected.classList.remove('active');
    await renderCanvasPage(state.originalDoc, state.step3Page, canvasStep3, ctxStep3, step3Cur, step3Prev, step3Next, state.originalDoc.numPages);
  });
}

if (step3Prev) {
  step3Prev.addEventListener('click', async () => {
    const doc = state.currentTab === 'protected' ? state.protectedDoc : state.originalDoc;
    if (state.step3Page > 1) {
      state.step3Page--;
      await renderCanvasPage(doc, state.step3Page, canvasStep3, ctxStep3, step3Cur, step3Prev, step3Next, doc.numPages);
    }
  });
}

if (step3Next) {
  step3Next.addEventListener('click', async () => {
    const doc = state.currentTab === 'protected' ? state.protectedDoc : state.originalDoc;
    if (state.step3Page < doc.numPages) {
      state.step3Page++;
      await renderCanvasPage(doc, state.step3Page, canvasStep3, ctxStep3, step3Cur, step3Prev, step3Next, doc.numPages);
    }
  });
}

if (btnDownloadFile) {
  btnDownloadFile.addEventListener('click', () => {
    if (state.protectedUrl) {
      const a = document.createElement('a');
      a.href = state.protectedUrl;
      a.download = state.protectedFilename || 'protected_document.pdf';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }
  });
}

if (btnStartNew) {
  btnStartNew.addEventListener('click', () => {
    state.file = null;
    state.serverFilename = null;
    state.findings = [];
    state.originalDoc = null;
    state.protectedDoc = null;
    if (pdfFileInput) pdfFileInput.value = '';
    if (dropzone) dropzone.style.display = 'block';
    if (fileLoadedCard) fileLoadedCard.style.display = 'none';
    goToStep(1);
  });
}