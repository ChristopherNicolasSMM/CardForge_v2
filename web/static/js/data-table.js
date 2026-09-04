(function () {
  "use strict";

  let columns = window.CF_COLUMNS.slice();
  let rows = window.CF_ROWS.map(r => ({ ...r }));
  const LABELS = window.CF_COLUMN_LABELS || {};
  const URLS = window.CF_URLS;

  let artTargetRow = null; // índice da linha sendo editada pelo picker de imagem

  function label(col) { return LABELS[col] || col; }

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
    const thead = `<thead><tr>${columns.map(c => `<th>
        <span class="col-label">${label(c)}</span>
        <span class="col-action" title="Renomear campo" onclick="CF_renameColumn('${c}')">✎</span>
        <span class="col-action" title="Remover campo" onclick="CF_removeColumn('${c}')">✕</span>
      </th>`).join("")}<th></th></tr></thead>`;
    const tbody = "<tbody>" + rows.map((row, i) => {
      const cells = columns.map(col => {
        if (col === "art") {
          const val = row.art || "";
          const thumbUrl = val ? (val.startsWith("http") ? val : `/data/library/${encodeURIComponent(val)}`) : "";
          return `<td>
            <div class="art-cell">
              ${thumbUrl ? `<img src="${thumbUrl}" alt="">` : ""}
              <button type="button" class="btn btn-sm" onclick="CF_pickArt(${i})">${val ? "Trocar" : "Escolher"}</button>
            </div>
          </td>`;
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

    populateRowSelect();
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
    const res = await fetch(`/templates/${encodeURIComponent(tpl)}/preview`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ row }),
    });
    const data = await res.json();
    if (data.ok) {
      const img = document.getElementById("previewRowImg");
      img.src = data.image;
      img.style.display = "block";
    } else {
      alert(data.error || "Erro ao renderizar");
    }
  });

  renderTable();
})();
