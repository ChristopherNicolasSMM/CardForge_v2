(function () {
  "use strict";

  let columns = window.CF_COLUMNS.slice();
  let rows = window.CF_ROWS.map(r => ({ ...r }));
  const LABELS = window.CF_COLUMN_LABELS || {};
  const URLS = window.CF_URLS;

  let artTargetRow = null; // índice da linha sendo editada pelo picker de imagem

  function label(col) { return LABELS[col] || col; }

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
  };

  window.CF_removeColumn = function (col) {
    if (!confirm(`Remover o campo "${label(col)}" de todos os cards? Os valores desse campo serão perdidos.`)) return;
    columns = columns.filter(c => c !== col);
    rows.forEach(r => { delete r[col]; });
    renderTable();
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
  };

  document.getElementById("btnAddRow").addEventListener("click", () => {
    const empty = {};
    columns.forEach(c => empty[c] = "");
    rows.push(empty);
    renderTable();
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
  });

  document.getElementById("btnSaveData").addEventListener("click", async () => {
    const res = await fetch(URLS.save, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ columns, rows }),
    });
    const data = await res.json();
    if (data.ok) alert(`${data.count} card(s) salvos.`);
    else alert("Erro ao salvar.");
  });

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
