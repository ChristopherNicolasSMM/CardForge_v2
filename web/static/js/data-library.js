(function () {
  "use strict";

  const URLS = window.CF_URLS;
  let images = [];
  let replaceTarget = null;

  function encodedName(name) { return encodeURIComponent(name); }
  function escapeHtml(value) {
    return String(value).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  function activateTab(name) {
    document.querySelectorAll(".data-tab").forEach(button => {
      const active = button.dataset.tab === name;
      button.classList.toggle("active", active);
      button.setAttribute("aria-selected", String(active));
    });
    document.querySelectorAll(".data-tab-panel").forEach(panel => {
      const active = panel.id === `tab-${name}`;
      panel.classList.toggle("active", active);
      panel.hidden = !active;
    });
    history.replaceState(null, "", `#${name}`);
    if (name === "images") loadImages();
  }

  document.querySelectorAll(".data-tab").forEach(button => button.addEventListener("click", () => activateTab(button.dataset.tab)));
  const initialTab = ["dataset", "images", "simulate"].includes(location.hash.slice(1)) ? location.hash.slice(1) : "dataset";
  activateTab(initialTab);

  async function loadImages() {
    const response = await fetch(URLS.library);
    images = response.ok ? await response.json() : [];
    renderImages();
  }

  function renderImages() {
    const query = document.getElementById("imageSearch").value.trim().toLowerCase();
    const filtered = images.filter(item => item.filename.toLowerCase().includes(query));
    const grid = document.getElementById("imageLibraryGrid");
    document.getElementById("imageLibraryEmpty").hidden = filtered.length > 0;
    grid.innerHTML = filtered.map(item => `
      <article class="image-library-card">
        <button class="image-thumb" type="button" data-action="view" data-name="${escapeHtml(item.filename)}"><img src="${item.url}" alt="${escapeHtml(item.filename)}" loading="lazy"></button>
        <div class="image-card-body"><strong title="${escapeHtml(item.filename)}">${escapeHtml(item.filename)}</strong><span>${item.usage_count ? `${item.usage_count} card(s)` : "Não utilizada"}</span></div>
        <div class="image-card-actions">
          <button class="btn btn-sm" type="button" data-action="replace" data-name="${escapeHtml(item.filename)}">Substituir</button>
          <button class="btn btn-sm" type="button" data-action="rename" data-name="${escapeHtml(item.filename)}">Renomear</button>
          <button class="btn btn-sm btn-danger" type="button" data-action="delete" data-name="${escapeHtml(item.filename)}">Apagar</button>
        </div>
      </article>`).join("");
  }

  document.getElementById("imageLibraryGrid").addEventListener("click", async event => {
    const button = event.target.closest("button[data-action]");
    if (!button) return;
    const name = button.dataset.name;
    const item = images.find(image => image.filename === name);
    if (button.dataset.action === "view") {
      document.getElementById("imageViewTitle").textContent = name;
      document.getElementById("imageViewImg").src = item.url;
      document.getElementById("imageViewModal").classList.add("open");
    } else if (button.dataset.action === "replace") {
      replaceTarget = name;
      document.getElementById("imageReplaceInput").click();
    } else if (button.dataset.action === "rename") {
      await renameImage(name);
    } else if (button.dataset.action === "delete") {
      await deleteImage(name);
    }
  });

  document.getElementById("imageSearch").addEventListener("input", renderImages);
  document.getElementById("btnAddImages").addEventListener("click", () => document.getElementById("imageUploadInput").click());
  document.getElementById("imageUploadInput").addEventListener("change", async event => {
    const files = Array.from(event.target.files || []);
    if (!files.length) return;
    const body = new FormData();
    files.forEach(file => body.append("files", file));
    const response = await fetch(URLS.artUpload, { method: "POST", body });
    const result = await response.json();
    event.target.value = "";
    if (!response.ok || !result.ok) return alert(result.error || "Falha ao enviar as imagens.");
    await loadImages();
  });

  document.getElementById("imageReplaceInput").addEventListener("change", async event => {
    const file = event.target.files[0];
    if (!file || !replaceTarget) return;
    const body = new FormData(); body.append("file", file);
    const response = await fetch(`${URLS.library}/${encodedName(replaceTarget)}/replace`, { method: "POST", body });
    const result = await response.json();
    event.target.value = ""; replaceTarget = null;
    if (!response.ok || !result.ok) return alert(result.error || "Falha ao substituir a imagem.");
    await loadImages();
  });

  async function renameImage(name) {
    const nextName = prompt("Novo nome da imagem:", name);
    if (!nextName || nextName.trim() === name) return;
    const response = await fetch(`${URLS.library}/${encodedName(name)}/rename`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name: nextName.trim() })
    });
    const result = await response.json();
    if (!response.ok || !result.ok) return alert(result.error || "Falha ao renomear a imagem.");
    // Recarrega também a cópia do dataset mantida pela tabela, evitando que
    // um auto-save posterior restaure a referência antiga.
    location.hash = "images";
    location.reload();
  }

  async function deleteImage(name) {
    const usageResponse = await fetch(`${URLS.library}/${encodedName(name)}/usage`);
    const usage = await usageResponse.json();
    const message = usage.count
      ? `A imagem ${name} está sendo utilizada por ${usage.count} card(s). Deseja realmente apagá-la?`
      : `Deseja realmente apagar a imagem ${name}?`;
    if (!confirm(message)) return;
    const response = await fetch(`${URLS.library}/${encodedName(name)}/delete`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ confirmed: true })
    });
    const result = await response.json();
    if (!response.ok || !result.ok) return alert(result.error || "Falha ao apagar a imagem.");
    await loadImages();
  }

  document.getElementById("btnCloseLibModal").addEventListener("click", () => document.getElementById("libModal").classList.remove("open"));
  document.getElementById("btnCloseImageView").addEventListener("click", () => document.getElementById("imageViewModal").classList.remove("open"));
})();
