(function () {
  "use strict";

  let columns = window.CF_COLUMNS.slice();
  let rows = window.CF_ROWS.map(r => ({ ...r }));
  const LABELS = window.CF_COLUMN_LABELS || {};
  const URLS = window.CF_URLS;

  let artTargetRow = null; // índice da linha sendo editada pelo picker de imagem

  function label(col) {
    if (col === TEMPLATE_FIELD) return LABELS[col] || "Template";
    return LABELS[col] || col;
  }

  // ── Coluna reservada _template ──────────────────────────────────────────
  // Marca de qual template (da coleção ativa) aquela linha é dona — usado
  // por Gerar/Proxy pra filtrar o lote quando a coleção mistura mais de um
  // template no mesmo dataset. Ver web/services/template_assignment.py.
  const TEMPLATE_FIELD = "_template";
  let templateOptions = [];

  async function loadTemplateOptions() {
    try {
      const res = await fetch(URLS.templatesList);
      templateOptions = await res.json();
      const previewSelect = document.getElementById("previewTemplate");
      if (previewSelect) {
        previewSelect.innerHTML = templateOptions.map(t => `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`).join("")
          || '<option value="">— nenhum template —</option>';
      }
    } catch (e) {
      templateOptions = [];
    }
  }

  // ── Filtro + paginação (client-side, a tabela inteira já está em memória) ──
  // Os índices que a página realmente desenha (pageIndices) são sempre um
  // subconjunto dos índices ORIGINAIS de `rows` — data-row="${i}" nas células
  // guarda esse índice original, nunca a posição na página, pra edição e
  // auto-save continuarem batendo com a linha certa independente do filtro
  // ou de qual página está sendo exibida.
  let filterText = "";
  let pageSize = 20;
  let currentPage = 1;

  function filteredIndices() {
    if (!filterText) return rows.map((_, i) => i);
    const q = filterText.toLowerCase();
    const out = [];
    for (let i = 0; i < rows.length; i++) {
      const row = rows[i];
      for (const c of columns) {
        if (String(row[c] || "").toLowerCase().includes(q)) { out.push(i); break; }
      }
    }
    return out;
  }

  // ── Auto-save ────────────────────────────────────────────────────────────

  const AUTO_SAVE_DELAY_MS = 1000;
  let isDirty = false;
  let autoSaveTimer = null;
  const saveStatusEl = document.getElementById("saveStatus");

  function setSaveStatus(state) {
    if (!saveStatusEl) return;
    saveStatusEl.classList.remove("dirty", "saving", "saved");
    if (state === "dirty") {
      saveStatusEl.textContent = "Alterações não salvas…";
      saveStatusEl.classList.add("dirty");
    } else if (state === "saving") {
      saveStatusEl.textContent = "Salvando…";
      saveStatusEl.classList.add("saving");
    } else if (state === "saved") {
      const t = new Date();
      const hh = String(t.getHours()).padStart(2, "0"), mm = String(t.getMinutes()).padStart(2, "0");
      saveStatusEl.textContent = `Salvo às ${hh}:${mm}`;
      saveStatusEl.classList.add("saved");
    } else {
      saveStatusEl.textContent = "";
    }
  }

  function scheduleAutoSave() {
    isDirty = true;
    setSaveStatus("dirty");
    if (autoSaveTimer) clearTimeout(autoSaveTimer);
    autoSaveTimer = setTimeout(() => { saveData(true); }, AUTO_SAVE_DELAY_MS);
  }

  window.addEventListener("beforeunload", evt => {
    if (!isDirty) return;
    evt.preventDefault();
    evt.returnValue = "";
  });

  async function saveData(silent) {
    if (autoSaveTimer) { clearTimeout(autoSaveTimer); autoSaveTimer = null; }
    setSaveStatus("saving");
    let data;
    try {
      const res = await fetch(URLS.save, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ columns, rows }),
      });
      data = await res.json();
    } catch (e) {
      data = { ok: false };
    }
    if (data.ok) {
      isDirty = false;
      setSaveStatus("saved");
    } else {
      setSaveStatus("dirty");
      if (!silent) alert("Erro ao salvar.");
    }
    return data.ok;
  }

  // ── Tabela ───────────────────────────────────────────────────────────────

  function renderTable() {
    const table = document.getElementById("dataTable");
    const allIndices = filteredIndices();
    const totalPages = pageSize === "all" ? 1 : Math.max(1, Math.ceil(allIndices.length / pageSize));
    if (currentPage > totalPages) currentPage = totalPages;
    if (currentPage < 1) currentPage = 1;
    const pageIndices = pageSize === "all" ? allIndices
      : allIndices.slice((currentPage - 1) * pageSize, currentPage * pageSize);

    const thead = `<thead><tr>${columns.map(c => `<th>
        <span class="col-label">${label(c)}</span>
        <span class="col-action" title="Renomear campo" onclick="CF_renameColumn('${c}')">✎</span>
        <span class="col-action" title="Remover campo" onclick="CF_removeColumn('${c}')">✕</span>
      </th>`).join("")}<th></th></tr></thead>`;
    const tbody = "<tbody>" + pageIndices.map(i => {
      const row = rows[i];
      const cells = columns.map(col => {
        if (col === "art") {
          const val = row.art || "";
          const normalized = String(val).replace(/\\/g, "/");
          const encodedPath = normalized.split("/").map(encodeURIComponent).join("/");
          const thumbUrl = val ? (val.startsWith("http") ? val : `/data/library/${encodedPath}`) : "";
          return `<td>
            <div class="art-cell">
              ${thumbUrl ? `<img src="${thumbUrl}" alt="">` : ""}
              <button type="button" class="btn btn-sm" onclick="CF_pickArt(${i})">${val ? "Trocar" : "Escolher"}</button>
            </div>
          </td>`;
        }
        if (col === TEMPLATE_FIELD) {
          const val = row[col] || "";
          const isEmpty = val === "";
          const isInvalid = !isEmpty && !templateOptions.includes(val);
          let opts = `<option value="">— nenhum —</option>` +
            templateOptions.map(t => `<option value="${escapeHtml(t)}" ${t === val ? "selected" : ""}>${escapeHtml(t)}</option>`).join("");
          if (isInvalid) {
            opts += `<option value="${escapeHtml(val)}" selected>⚠ ${escapeHtml(val)} (não existe)</option>`;
          }
          const border = isInvalid ? "border-color:#d4520e" : (isEmpty ? "border-color:#8a7a4a" : "");
          return `<td><select data-row="${i}" data-col="${col}" style="width:100%; ${border}">${opts}</select></td>`;
        }
        return `<td contenteditable="true" data-row="${i}" data-col="${col}">${escapeHtml(row[col] || "")}</td>`;
      }).join("");
      return `<tr>${cells}<td><span class="row-remove" onclick="CF_removeRow(${i})" title="Remover">✕</span></td></tr>`;
    }).join("") + "</tbody>";
    table.innerHTML = thead + tbody;

    table.querySelectorAll("td[contenteditable]").forEach(td => {
      td.addEventListener("input", () => {
        const r = +td.dataset.row, c = td.dataset.col;
        rows[r][c] = td.textContent.trim();
        scheduleAutoSave();
      });
    });

    table.querySelectorAll(`select[data-col="${TEMPLATE_FIELD}"]`).forEach(sel => {
      sel.addEventListener("change", () => {
        const r = +sel.dataset.row, c = sel.dataset.col;
        rows[r][c] = sel.value;
        scheduleAutoSave();
        renderTable(); // recalcula estilo de aviso (vazio/inválido) da célula
      });
    });

    renderPagination(allIndices.length, totalPages);
    const countLabel = document.getElementById("rowCountLabel");
    if (countLabel) {
      countLabel.textContent = filterText
        ? `${allIndices.length} de ${rows.length} linha(s) (filtrado)`
        : `${rows.length} linha(s)`;
    }
    populateRowSelect();
  }

  function renderPagination(filteredCount, totalPages) {
    const box = document.getElementById("tablePagination");
    if (!box) return;
    if (filteredCount === 0) {
      box.innerHTML = filteredCount === 0
        ? `<span>Nenhuma linha bate com o filtro.</span>`
        : "";
      return;
    }
    const start = (currentPage - 1) * pageSize + 1;
    const end = Math.min(filteredCount, currentPage * pageSize);
    box.innerHTML = `
      <button type="button" ${currentPage <= 1 ? "disabled" : ""} id="pgFirst">« Primeira</button>
      <button type="button" ${currentPage <= 1 ? "disabled" : ""} id="pgPrev">‹ Anterior</button>
      <span>Página ${currentPage} de ${totalPages} — linhas ${start}–${end} de ${filteredCount}</span>
      <button type="button" ${currentPage >= totalPages ? "disabled" : ""} id="pgNext">Próxima ›</button>
      <button type="button" ${currentPage >= totalPages ? "disabled" : ""} id="pgLast">Última »</button>
    `;
    const go = (p) => { currentPage = p; renderTable(); };
    const first = document.getElementById("pgFirst"); if (first) first.onclick = () => go(1);
    const prev = document.getElementById("pgPrev"); if (prev) prev.onclick = () => go(currentPage - 1);
    const next = document.getElementById("pgNext"); if (next) next.onclick = () => go(currentPage + 1);
    const last = document.getElementById("pgLast"); if (last) last.onclick = () => go(totalPages);
  }

  const filterInput = document.getElementById("dataFilterInput");
  if (filterInput) {
    let filterDebounce = null;
    filterInput.addEventListener("input", () => {
      clearTimeout(filterDebounce);
      filterDebounce = setTimeout(() => {
        filterText = filterInput.value.trim();
        currentPage = 1;
        renderTable();
      }, 200);
    });
  }

  const pageSizeSelect = document.getElementById("pageSizeSelect");
  if (pageSizeSelect) {
    pageSizeSelect.addEventListener("change", () => {
      pageSize = pageSizeSelect.value === "all" ? "all" : parseInt(pageSizeSelect.value, 10);
      currentPage = 1;
      renderTable();
    });
  }

  function escapeHtml(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  window.CF_removeRow = function (i) {
    rows.splice(i, 1);
    renderTable();
    scheduleAutoSave();
  };

  window.CF_removeColumn = function (col) {
    if (!confirm(`Remover o campo "${label(col)}" de todos os cards? Os valores desse campo serão perdidos.`)) return;
    columns = columns.filter(c => c !== col);
    rows.forEach(r => { delete r[col]; });
    renderTable();
    scheduleAutoSave();
  };

  window.CF_renameColumn = function (col) {
    const input = prompt(`Novo nome do campo (sem espaços, ex: ataque):`, col);
    if (!input) return;
    const key = input.trim().toLowerCase().replace(/\s+/g, "_").replace(/[^\w\-]/g, "");
    if (!key || key === col) return;
    if (columns.includes(key)) { alert("Já existe um campo com esse nome."); return; }
    columns = columns.map(c => c === col ? key : c);
    rows.forEach(r => {
      if (col in r) { r[key] = r[col]; delete r[col]; }
    });
    renderTable();
    scheduleAutoSave();
  };

  document.getElementById("btnAddRow").addEventListener("click", () => {
    const empty = {};
    columns.forEach(c => empty[c] = "");
    rows.push(empty);
    renderTable();
    scheduleAutoSave();
  });

  document.getElementById("btnAddCol").addEventListener("click", () => {
    const input = document.getElementById("newColName");
    const name = input.value.trim().toLowerCase().replace(/\s+/g, "_");
    if (!name) return;
    if (columns.includes(name)) { alert("Essa coluna já existe."); return; }
    columns.push(name);
    rows.forEach(r => r[name] = "");
    input.value = "";
    renderTable();
    scheduleAutoSave();
  });

  const btnAddTemplateCol = document.getElementById("btnAddTemplateCol");
  if (btnAddTemplateCol) {
    btnAddTemplateCol.addEventListener("click", () => {
      if (columns.includes(TEMPLATE_FIELD)) { alert("A coluna _template já existe nesta coleção."); return; }
      columns.push(TEMPLATE_FIELD);
      rows.forEach(r => r[TEMPLATE_FIELD] = "");
      renderTable();
      scheduleAutoSave();
    });
  }

  document.getElementById("btnSaveData").addEventListener("click", () => saveData(false));

  // ── Paleta de símbolos (helper de notação {X}) ──────────────────────────
  // Célula contenteditable não é um <input>/<textarea> normal — não dá pra
  // simplesmente ler/escrever selectionStart. Guardamos a célula com foco e
  // o Range do cursor nela; ao clicar num ícone da paleta (o que tira o
  // foco da célula), restauramos esse Range antes de inserir o texto.
  let lastEditableCell = null;
  let lastCaretRange = null;

  document.addEventListener("focusin", evt => {
    if (evt.target.matches && evt.target.matches("td[contenteditable]")) {
      lastEditableCell = evt.target;
    }
  });
  document.addEventListener("selectionchange", () => {
    if (!lastEditableCell || document.activeElement !== lastEditableCell) return;
    const sel = window.getSelection();
    if (sel && sel.rangeCount > 0 && lastEditableCell.contains(sel.anchorNode)) {
      lastCaretRange = sel.getRangeAt(0).cloneRange();
    }
  });

  const btnInsertSymbol = document.getElementById("btnInsertSymbol");
  if (btnInsertSymbol) {
    btnInsertSymbol.addEventListener("click", () => {
      if (!lastEditableCell) {
        alert("Clique num campo de texto da tabela primeiro (ex: rules_text), pra eu saber onde inserir o símbolo.");
        return;
      }
      window.CF_openSymbolPicker(btnInsertSymbol, notation => {
        const cell = lastEditableCell;
        cell.focus();
        const sel = window.getSelection();
        sel.removeAllRanges();
        if (lastCaretRange && cell.contains(lastCaretRange.startContainer)) {
          sel.addRange(lastCaretRange);
        } else {
          // sem posição salva (ex: célula nunca teve o cursor ainda) —
          // insere no fim do conteúdo, nunca no meio às cegas.
          const r = document.createRange();
          r.selectNodeContents(cell);
          r.collapse(false);
          sel.addRange(r);
        }
        document.execCommand("insertText", false, `{${notation}}`);
        // Reaproveita o listener de "input" já existente pra sincronizar
        // rows[][] e disparar o auto-save — sem duplicar essa lógica aqui.
        cell.dispatchEvent(new Event("input", { bubbles: true }));
      });
    });
  }

  // ── Picker de imagens (biblioteca de assets) ────────────────────────────

  window.CF_pickArt = function (rowIndex) {
    artTargetRow = rowIndex;
    document.getElementById("libModal").classList.add("open");
    loadLibrary();
  };

  async function loadLibrary() {
    const res = await fetch(URLS.library);
    const files = await res.json();
    const grid = document.getElementById("libGrid");
    grid.innerHTML = files.map(f =>
      `<img src="${f.url}" title="${f.filename}" onclick="CF_applyArt('${f.filename}')">`
    ).join("") || "<p style='grid-column:1/-1'>Nenhuma imagem na biblioteca ainda.</p>";
  }

  window.CF_applyArt = function (filename) {
    if (artTargetRow === null) return;
    rows[artTargetRow].art = filename;
    document.getElementById("libModal").classList.remove("open");
    renderTable();
    scheduleAutoSave();
  };

  document.getElementById("libUploadInput").addEventListener("change", async evt => {
    const file = evt.target.files[0];
    if (!file) return;
    const fd = new FormData(); fd.append("file", file);
    const res = await fetch(URLS.artUpload, { method: "POST", body: fd });
    const data = await res.json();
    if (data.ok) {
      if (artTargetRow !== null) {
        rows[artTargetRow].art = data.filename;
        renderTable();
        scheduleAutoSave();
      }
      document.getElementById("libModal").classList.remove("open");
    } else {
      alert(data.error || "Falha no upload");
    }
  });

  // ── Preview ao vivo ──────────────────────────────────────────────────────

  function populateRowSelect() {
    const sel = document.getElementById("previewRow");
    const current = sel.value;
    sel.innerHTML = rows.map((r, i) => `<option value="${i}">${escapeHtml(r.name || `card ${i + 1}`)}</option>`).join("")
      || "<option value=''>— nenhum card —</option>";
    if (current) sel.value = current;
  }

  document.getElementById("btnPreviewRow").addEventListener("click", async () => {
    const tpl = document.getElementById("previewTemplate").value;
    const idx = document.getElementById("previewRow").value;
    if (!tpl || idx === "") { alert("Escolha um template e um card."); return; }
    const row = rows[+idx];
    const templatePath = tpl.split("/").map(encodeURIComponent).join("/");
    const res = await fetch(`/templates/${templatePath}/preview`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ row }),
    });
    const data = await res.json();
    if (data.ok) {
      const img = document.getElementById("previewRowImg");
      img.src = data.image;
      img.hidden = false;
      const placeholder = document.getElementById("previewPlaceholder");
      if (placeholder) placeholder.hidden = true;
    } else {
      alert(data.error || "Erro ao renderizar");
    }
  });

  loadTemplateOptions().then(renderTable);
})();
