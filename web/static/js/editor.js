(function () {
  "use strict";

  const T = window.CF_TEMPLATE;
  const NAME = window.CF_TEMPLATE_NAME;
  const URLS = window.CF_URLS;
  const DEMO_ROW = window.CF_DEMO_ROW;

  const canvas = document.getElementById("cardCanvas");
  const ctx = canvas.getContext("2d");

  const PX_PER_MM = canvas.width / T.card.width_mm;
  canvas.height = Math.round(T.card.height_mm * PX_PER_MM);

  let selectedId = null;
  let dragMode = null;      // 'move' | 'resize' | null
  let dragStart = null;     // {mx, my, x_mm, y_mm, w_mm, h_mm}

  const imageCache = {};    // url -> HTMLImageElement
  const loadedFonts = new Set();

  // ── Utilidades ────────────────────────────────────────────────────────────

  function mm(px) { return px / PX_PER_MM; }
  function px(mmVal) { return mmVal * PX_PER_MM; }

  function sortedLayers() {
    return [...T.layers].sort((a, b) => a.z_index - b.z_index);
  }

  function layerById(id) { return T.layers.find(l => l.id === id); }

  function getImage(url) {
    if (imageCache[url]) return imageCache[url];
    const img = new Image();
    img.src = url;
    img.onload = render;
    imageCache[url] = img;
    return img;
  }

  function ensureFont(family) {
    if (!family || loadedFonts.has(family)) return;
    loadedFonts.add(family);
    const url = `${URLS.font}${encodeURIComponent(family)}.ttf`;
    const face = new FontFace(family, `url(${url})`);
    face.load().then(loaded => {
      document.fonts.add(loaded);
      render();
    }).catch(() => { /* fonte indisponível — usa fallback do navegador */ });
  }

  // ── Render ────────────────────────────────────────────────────────────────

  function render() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#d8d8d8";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    for (const layer of sortedLayers()) {
      if (!layer.visible) continue;
      drawLayer(layer);
    }

    if (selectedId) drawSelection(layerById(selectedId));
  }

  function drawLayer(layer) {
    const x = px(layer.x_mm), y = px(layer.y_mm);
    const w = px(layer.width_mm), h = px(layer.height_mm);

    if (layer.type === "background") {
      if (layer.source_image) {
        const img = getImage(URLS.asset + encodeURIComponent(layer.source_image));
        if (img.complete && img.naturalWidth) {
          drawCover(img, x, y, w, h);
          return;
        }
      }
      const grad = ctx.createLinearGradient(0, y, 0, y + h);
      grad.addColorStop(0, "#8a8a8a");
      grad.addColorStop(1, "#5a5a5a");
      ctx.fillStyle = grad;
      ctx.fillRect(x, y, w, h);
      return;
    }

    if (layer.type === "image") {
      ctx.fillStyle = "rgba(78,124,140,0.12)";
      ctx.fillRect(x, y, w, h);
      ctx.strokeStyle = "rgba(78,124,140,0.55)";
      ctx.setLineDash([4, 3]);
      ctx.strokeRect(x + 0.5, y + 0.5, w - 1, h - 1);
      ctx.setLineDash([]);
      ctx.fillStyle = "#6b9cac";
      ctx.font = "11px sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(`🖼 ${layer.field || layer.label || "arte"}`, x + w / 2, y + h / 2);
      return;
    }

    if (layer.type === "text" || layer.type === "mana") {
      const s = layer.style || {};
      ensureFont(s.font_family);
      const text = layer.static_text || DEMO_ROW[layer.field] || `{${layer.field || layer.label}}`;
      const sizePx = (s.font_size_pt || 9) * (96 / 72) * (PX_PER_MM / (96 / 25.4));
      const weight = s.font_weight === "bold" ? "bold" : "normal";
      const style = s.font_style === "italic" ? "italic" : "normal";
      ctx.font = `${style} ${weight} ${sizePx}px "${s.font_family || "sans-serif"}", sans-serif`;
      ctx.fillStyle = s.color || "#111111";
      ctx.textBaseline = "top";
      const align = s.align || "left";
      ctx.textAlign = align === "center" ? "center" : (align === "right" ? "right" : "left");
      const tx = align === "center" ? x + w / 2 : (align === "right" ? x + w : x);

      const lh = (s.line_height_pt || (s.font_size_pt || 9) * 1.35) * (96 / 72) * (PX_PER_MM / (96 / 25.4));
      const lines = layer.multiline ? wrapText(String(text), w) : [String(text)];
      lines.forEach((line, i) => ctx.fillText(line, tx, y + i * lh));
      return;
    }
  }

  function wrapText(text, maxWidth) {
    const words = text.split(" ");
    const lines = [];
    let cur = "";
    for (const word of words) {
      const test = (cur + " " + word).trim();
      if (ctx.measureText(test).width <= maxWidth || !cur) {
        cur = test;
      } else {
        lines.push(cur);
        cur = word;
      }
    }
    if (cur) lines.push(cur);
    return lines;
  }

  function drawCover(img, x, y, w, h) {
    const ir = img.naturalWidth / img.naturalHeight;
    const dr = w / h;
    let sx, sy, sw, sh;
    if (ir > dr) {
      sh = img.naturalHeight; sw = sh * dr; sy = 0; sx = (img.naturalWidth - sw) / 2;
    } else {
      sw = img.naturalWidth; sh = sw / dr; sx = 0; sy = (img.naturalHeight - sh) / 2;
    }
    ctx.drawImage(img, sx, sy, sw, sh, x, y, w, h);
  }

  function drawSelection(layer) {
    if (!layer) return;
    const x = px(layer.x_mm), y = px(layer.y_mm), w = px(layer.width_mm), h = px(layer.height_mm);
    ctx.strokeStyle = "#DE6A30";
    ctx.lineWidth = 2;
    ctx.strokeRect(x, y, w, h);
    ctx.fillStyle = "#DE6A30";
    ctx.fillRect(x + w - 8, y + h - 8, 8, 8);
  }

  // ── Interação: arrastar / redimensionar ─────────────────────────────────

  function mousePos(evt) {
    const rect = canvas.getBoundingClientRect();
    return { mx: evt.clientX - rect.left, my: evt.clientY - rect.top };
  }

  function hitTest(mx, my) {
    const layers = sortedLayers().reverse();
    for (const layer of layers) {
      const x = px(layer.x_mm), y = px(layer.y_mm), w = px(layer.width_mm), h = px(layer.height_mm);
      if (mx >= x && mx <= x + w && my >= y && my <= y + h) return layer;
    }
    return null;
  }

  function nearHandle(layer, mx, my) {
    if (!layer) return false;
    const x = px(layer.x_mm) + px(layer.width_mm);
    const y = px(layer.y_mm) + px(layer.height_mm);
    return Math.abs(mx - x) <= 10 && Math.abs(my - y) <= 10;
  }

  canvas.addEventListener("mousedown", evt => {
    const { mx, my } = mousePos(evt);
    const selected = selectedId ? layerById(selectedId) : null;

    if (selected && nearHandle(selected, mx, my)) {
      dragMode = "resize";
      dragStart = { mx, my, w_mm: selected.width_mm, h_mm: selected.height_mm };
      return;
    }
    const hit = hitTest(mx, my);
    selectLayer(hit ? hit.id : null);
    if (hit) {
      dragMode = "move";
      dragStart = { mx, my, x_mm: hit.x_mm, y_mm: hit.y_mm };
    }
  });

  canvas.addEventListener("mousemove", evt => {
    if (!dragMode) return;
    const { mx, my } = mousePos(evt);
    const layer = layerById(selectedId);
    if (!layer) return;
    const dxmm = mm(mx - dragStart.mx), dymm = mm(my - dragStart.my);

    if (dragMode === "move") {
      layer.x_mm = Math.max(0, +(dragStart.x_mm + dxmm).toFixed(2));
      layer.y_mm = Math.max(0, +(dragStart.y_mm + dymm).toFixed(2));
    } else if (dragMode === "resize") {
      layer.width_mm = Math.max(2, +(dragStart.w_mm + dxmm).toFixed(2));
      layer.height_mm = Math.max(2, +(dragStart.h_mm + dymm).toFixed(2));
    }
    syncPropsFromLayer(layer);
    render();
  });

  window.addEventListener("mouseup", () => { dragMode = null; });

  // ── Lista de camadas ─────────────────────────────────────────────────────

  function renderLayerList() {
    const list = document.getElementById("layerList");
    list.innerHTML = "";
    for (const layer of sortedLayers().reverse()) {
      const item = document.createElement("div");
      item.className = "layer-item" + (layer.id === selectedId ? " selected" : "");
      item.innerHTML = `<span>${layer.label || layer.id}</span><span class="type-tag" title="z-index ${layer.z_index}">${layer.type} · ${layer.z_index}</span>`;
      item.onclick = () => selectLayer(layer.id);
      list.appendChild(item);
    }
  }

  function selectLayer(id) {
    selectedId = id;
    renderLayerList();
    const layer = id ? layerById(id) : null;
    document.getElementById("propsForm").style.display = layer ? "block" : "none";
    document.getElementById("propsEmpty").style.display = layer ? "none" : "block";
    if (layer) syncPropsFromLayer(layer);
    render();
  }

  // ── Painel de propriedades ───────────────────────────────────────────────

  const P = id => document.getElementById(id);

  function syncPropsFromLayer(layer) {
    P("p_label").value = layer.label || "";
    P("p_field").value = layer.field || "";
    P("p_static").value = layer.static_text || "";
    P("p_x").value = layer.x_mm;
    P("p_y").value = layer.y_mm;
    P("p_w").value = layer.width_mm;
    P("p_h").value = layer.height_mm;
    P("p_z").value = layer.z_index;
    P("p_fit").value = layer.fit || "cover";
    P("p_visible").checked = !!layer.visible;
    P("p_multiline").checked = !!layer.multiline;
    const s = layer.style || {};
    P("p_font").value = s.font_family || "";
    P("p_size").value = s.font_size_pt || 9;
    P("p_lh").value = s.line_height_pt || 0;
    P("p_weight").value = s.font_weight || "normal";
    P("p_style").value = s.font_style || "normal";
    P("p_align").value = s.align || "left";
    P("p_color").value = toHex(s.color || "#111111");

    // Imagem fixa: só faz sentido pra camadas de imagem/fundo
    const isImageLike = layer.type === "image" || layer.type === "background";
    P("p_fixedImageWrap").style.display = isImageLike ? "block" : "none";
    P("p_fixedImageName").textContent = layer.source_image
      ? `imagem atual: ${layer.source_image}`
      : "nenhuma imagem definida";
  }

  function toHex(c) {
    if (/^#[0-9a-f]{6}$/i.test(c)) return c;
    return "#111111";
  }

  function bindProp(id, apply) {
    P(id).addEventListener("input", () => {
      const layer = layerById(selectedId);
      if (!layer) return;
      apply(layer, P(id));
      renderLayerList();
      render();
    });
  }

  function populateFontSelect() {
    const sel = P("p_font");
    sel.innerHTML = "";
    for (const f of window.CF_FONTS) {
      const opt = document.createElement("option");
      opt.value = f; opt.textContent = f;
      sel.appendChild(opt);
    }
  }

  populateFontSelect();

  bindProp("p_label", (l, el) => l.label = el.value);
  bindProp("p_field", (l, el) => l.field = el.value);
  bindProp("p_static", (l, el) => l.static_text = el.value);
  bindProp("p_x", (l, el) => l.x_mm = parseFloat(el.value) || 0);
  bindProp("p_y", (l, el) => l.y_mm = parseFloat(el.value) || 0);
  bindProp("p_w", (l, el) => l.width_mm = parseFloat(el.value) || 1);
  bindProp("p_h", (l, el) => l.height_mm = parseFloat(el.value) || 1);
  bindProp("p_z", (l, el) => l.z_index = parseInt(el.value) || 0);
  bindProp("p_fit", (l, el) => l.fit = el.value);
  bindProp("p_visible", (l, el) => l.visible = el.checked);
  bindProp("p_multiline", (l, el) => l.multiline = el.checked);
  bindProp("p_font", (l, el) => { l.style = l.style || {}; l.style.font_family = el.value; loadedFonts.delete(el.value); ensureFont(el.value); });
  bindProp("p_size", (l, el) => { l.style = l.style || {}; l.style.font_size_pt = parseFloat(el.value) || 9; });
  bindProp("p_lh", (l, el) => { l.style = l.style || {}; l.style.line_height_pt = parseFloat(el.value) || 0; });
  bindProp("p_weight", (l, el) => { l.style = l.style || {}; l.style.font_weight = el.value; });
  bindProp("p_style", (l, el) => { l.style = l.style || {}; l.style.font_style = el.value; });
  bindProp("p_align", (l, el) => { l.style = l.style || {}; l.style.align = el.value; });
  bindProp("p_color", (l, el) => { l.style = l.style || {}; l.style.color = el.value; });

  // ── Alinhamento ───────────────────────────────────────────────────────────

  function alignLayer(mode) {
    const layer = layerById(selectedId);
    if (!layer) return;
    const cw = T.card.width_mm, ch = T.card.height_mm;
    if (mode === "left")       layer.x_mm = 0;
    if (mode === "center-h")   layer.x_mm = +(cw / 2 - layer.width_mm / 2).toFixed(2);
    if (mode === "right")      layer.x_mm = +(cw - layer.width_mm).toFixed(2);
    if (mode === "top")        layer.y_mm = 0;
    if (mode === "middle-v")   layer.y_mm = +(ch / 2 - layer.height_mm / 2).toFixed(2);
    if (mode === "bottom")     layer.y_mm = +(ch - layer.height_mm).toFixed(2);
    syncPropsFromLayer(layer);
    render();
  }
  P("alignLeft").addEventListener("click", () => alignLayer("left"));
  P("alignCenterH").addEventListener("click", () => alignLayer("center-h"));
  P("alignRight").addEventListener("click", () => alignLayer("right"));
  P("alignTop").addEventListener("click", () => alignLayer("top"));
  P("alignMiddleV").addEventListener("click", () => alignLayer("middle-v"));
  P("alignBottom").addEventListener("click", () => alignLayer("bottom"));

  // ── Ordem de empilhamento (z-index) ─────────────────────────────────────

  function orderLayer(mode) {
    const layer = layerById(selectedId);
    if (!layer) return;
    const zs = T.layers.map(l => l.z_index);
    const seq = sortedLayers(); // crescente por z_index
    const idx = seq.findIndex(l => l.id === layer.id);

    if (mode === "front") layer.z_index = Math.max(...zs) + 1;
    if (mode === "back")  layer.z_index = Math.min(...zs) - 1;
    if (mode === "up" && idx < seq.length - 1) {
      const next = seq[idx + 1];
      const tmp = layer.z_index; layer.z_index = next.z_index; next.z_index = tmp;
    }
    if (mode === "down" && idx > 0) {
      const prev = seq[idx - 1];
      const tmp = layer.z_index; layer.z_index = prev.z_index; prev.z_index = tmp;
    }
    syncPropsFromLayer(layer);
    renderLayerList();
    render();
  }
  P("orderFront").addEventListener("click", () => orderLayer("front"));
  P("orderBack").addEventListener("click", () => orderLayer("back"));
  P("orderUp").addEventListener("click", () => orderLayer("up"));
  P("orderDown").addEventListener("click", () => orderLayer("down"));

  // ── Imagem fixa (camadas de imagem/fundo sem campo do dataset) ──────────

  P("p_fixedImageUpload").addEventListener("change", async evt => {
    const file = evt.target.files[0];
    const layer = layerById(selectedId);
    if (!file || !layer) return;
    const fd = new FormData(); fd.append("file", file);
    const res = await fetch(URLS.layerImage, { method: "POST", body: fd });
    const data = await res.json();
    if (data.ok) {
      layer.source_image = data.filename;
      delete imageCache[URLS.asset + encodeURIComponent(data.filename)];
      syncPropsFromLayer(layer);
      render();
      await saveTemplate(true);
    } else {
      alert(data.error || "Falha no upload");
    }
  });

  P("btnDeleteLayer").addEventListener("click", () => {
    if (!selectedId) return;
    if (!confirm("Excluir esta camada?")) return;
    T.layers = T.layers.filter(l => l.id !== selectedId);
    selectLayer(null);
  });

  // ── Nova camada ───────────────────────────────────────────────────────────

  P("btnAddLayer").addEventListener("click", () => {
    const type = P("newLayerType").value;
    const n = T.layers.length + 1;
    const id = `${type}_${n}_${Date.now().toString(36).slice(-4)}`;
    const base = {
      id, type, label: `Nova ${type}`, field: type === "text" ? "" : "",
      static_text: type === "text" ? "Texto" : "", condition: "",
      x_mm: 5, y_mm: 5, width_mm: 30, height_mm: 8, z_index: T.layers.length,
      visible: true, multiline: false, fit: "cover",
      source_image: "", source_gradient: "",
      style: { font_family: window.CF_FONTS[0] || "Beleren-Bold", font_size_pt: 9,
               font_weight: "normal", font_style: "normal", color: "#111111",
               align: "left", line_height_pt: 0 },
    };
    T.layers.push(base);
    renderLayerList();
    selectLayer(id);
  });

  // ── Uploads ──────────────────────────────────────────────────────────────

  function findOrCreateBackgroundLayer() {
    let bg = T.layers.find(l => l.type === "background");
    if (!bg) {
      bg = { id: "background", type: "background", label: "Fundo", field: "", static_text: "",
             condition: "", x_mm: 0, y_mm: 0, width_mm: T.card.width_mm, height_mm: T.card.height_mm,
             z_index: -1, visible: true, multiline: false, fit: "cover", source_image: "",
             source_gradient: "", style: {} };
      T.layers.push(bg);
    }
    return bg;
  }

  P("bgUpload").addEventListener("change", async evt => {
    const file = evt.target.files[0];
    if (!file) return;
    const fd = new FormData(); fd.append("file", file);
    const res = await fetch(URLS.background, { method: "POST", body: fd });
    const data = await res.json();
    if (data.ok) {
      const bg = findOrCreateBackgroundLayer();
      bg.source_image = data.filename;
      delete imageCache[URLS.asset + encodeURIComponent(data.filename)];
      render();
      await saveTemplate(true);
    } else {
      alert(data.error || "Falha no upload");
    }
  });

  P("backUpload").addEventListener("change", async evt => {
    const file = evt.target.files[0];
    if (!file) return;
    const fd = new FormData(); fd.append("file", file);
    const res = await fetch(URLS.backImage, { method: "POST", body: fd });
    const data = await res.json();
    if (data.ok) {
      T.back_image = data.filename;
      alert("Imagem de verso definida.");
    } else {
      alert(data.error || "Falha no upload");
    }
  });

  P("fontUpload").addEventListener("change", async evt => {
    const file = evt.target.files[0];
    if (!file) return;
    const fd = new FormData(); fd.append("file", file);
    const res = await fetch(URLS.font_upload, { method: "POST", body: fd });
    const data = await res.json();
    if (data.ok) {
      window.CF_FONTS = data.fonts;
      populateFontSelect();
      document.getElementById("fontCount").textContent = data.fonts.length;
      alert(`Fonte “${data.family}” disponível. Selecione-a numa camada de texto.`);
    } else {
      alert(data.error || "Falha no upload");
    }
  });

  // ── Salvar ───────────────────────────────────────────────────────────────

  async function saveTemplate(silent) {
    const payload = {
      meta: { name: NAME, inherits: T.meta && T.meta.parent ? T.meta.parent : null },
      card: T.card,
      gradients: T.gradients,
      layers: T.layers,
      back_image: T.back_image || "",
    };
    const res = await fetch(URLS.save, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!silent) {
      if (data.ok) alert("Template salvo.");
      else alert(data.error || "Erro ao salvar");
    }
    return data.ok;
  }

  P("btnSave").addEventListener("click", () => saveTemplate(false));

  // ── Preview real (renderização PIL do servidor) ─────────────────────────

  P("btnRealPreview").addEventListener("click", async () => {
    const payload = {
      row: DEMO_ROW,
      template: {
        meta: { name: NAME, inherits: T.meta && T.meta.parent ? T.meta.parent : null },
        card: T.card, gradients: T.gradients, layers: T.layers, back_image: T.back_image || "",
      },
    };
    const res = await fetch(URLS.preview, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (data.ok) {
      document.getElementById("previewImg").src = data.image;
      document.getElementById("previewModal").classList.add("open");
    } else {
      alert(data.error || "Erro ao renderizar");
    }
  });

  // ── Boot ─────────────────────────────────────────────────────────────────

  renderLayerList();
  render();
})();
