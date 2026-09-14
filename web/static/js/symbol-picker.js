/**
 * Paleta de símbolos de mana (notação {X}).
 *
 * Widget genérico: mostra um popover com os ícones disponíveis
 * (buscados de /symbols/manifest, servidos globalmente — não depende de
 * template nem de coleção) e devolve a notação escolhida via callback.
 * A lógica de "onde e como inserir o texto" fica por conta de quem chama
 * — cada campo (input comum, contenteditable etc.) insere de um jeito.
 *
 * Uso:
 *   CF_openSymbolPicker(anchorEl, (notation) => {
 *     // notation ex: "W", "2/R", "W/B/P" — inserir como "{" + notation + "}"
 *   });
 *
 * Ver docs/09-simbolos-mana.md pra notação completa.
 */
(function () {
  "use strict";

  let manifestPromise = null;
  function loadManifest() {
    if (!manifestPromise) {
      manifestPromise = fetch("/symbols/manifest").then(r => r.json());
    }
    return manifestPromise;
  }

  let popoverEl = null;
  let currentOnPick = null;

  function buildPopoverHtml(items) {
    const byCategory = {};
    items.forEach(it => {
      (byCategory[it.category] = byCategory[it.category] || []).push(it);
    });
    return Object.keys(byCategory).map(cat => `
      <div class="symbol-picker-group">
        <div class="symbol-picker-group-title">${cat}</div>
        <div class="symbol-picker-grid">
          ${byCategory[cat].map(it => `
            <button type="button" class="symbol-picker-item"
                    data-notation="${it.notation}"
                    title="{${it.notation}} — ${it.label}">
              <img src="/symbols/icon/${it.file}" alt="${it.label}" loading="lazy">
            </button>
          `).join("")}
        </div>
      </div>
    `).join("");
  }

  function ensurePopover() {
    if (popoverEl) return popoverEl;
    popoverEl = document.createElement("div");
    popoverEl.className = "symbol-picker-popover";
    popoverEl.style.display = "none";
    document.body.appendChild(popoverEl);

    popoverEl.addEventListener("click", evt => {
      const btn = evt.target.closest(".symbol-picker-item");
      if (!btn) return;
      const notation = btn.dataset.notation;
      const cb = currentOnPick;
      closePopover();
      if (cb) cb(notation);
    });

    document.addEventListener("click", evt => {
      if (popoverEl.style.display === "none") return;
      if (popoverEl.contains(evt.target)) return;
      if (evt.target.closest(".symbol-picker-trigger")) return;
      closePopover();
    });
    document.addEventListener("keydown", evt => {
      if (evt.key === "Escape") closePopover();
    });

    return popoverEl;
  }

  function closePopover() {
    if (popoverEl) popoverEl.style.display = "none";
    currentOnPick = null;
  }

  window.CF_openSymbolPicker = function (anchorEl, onPick) {
    const pop = ensurePopover();
    if (pop.style.display !== "none") { closePopover(); return; }
    currentOnPick = onPick;
    pop.innerHTML = "<div class='symbol-picker-group-title'>carregando…</div>";
    pop.style.display = "block";
    const rect = anchorEl.getBoundingClientRect();
    pop.style.top = `${window.scrollY + rect.bottom + 4}px`;
    pop.style.left = `${window.scrollX + rect.left}px`;
    loadManifest().then(items => { pop.innerHTML = buildPopoverHtml(items); });
  };

  window.CF_closeSymbolPicker = closePopover;
})();
