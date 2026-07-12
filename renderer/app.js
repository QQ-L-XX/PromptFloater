(function () {
  "use strict";

  const $ = (selector) => document.querySelector(selector);
  const state = { data: { schema_version: 1, categories: [] }, activeCategoryId: null, searchQuery: "", editingItemId: null, selectedItemId: null };
  let api = null;
  let toastTimer = null;

  const clone = (value) => JSON.parse(JSON.stringify(value));
  const makeId = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
  const activeCategory = (data = state.data) => data.categories.find((category) => category.id === state.activeCategoryId);

  function toast(icon, message) {
    const element = $("#toast");
    $("#toast-icon").textContent = icon;
    $("#toast-msg").textContent = message;
    element.classList.remove("hidden");
    element.style.animation = "none";
    void element.offsetHeight;
    element.style.animation = "";
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => element.classList.add("hidden"), 1800);
  }

  function filteredItems() {
    const category = activeCategory();
    if (!category) return [];
    const query = state.searchQuery.toLowerCase().trim();
    const items = query
      ? category.items.filter((item) => item.content.toLowerCase().includes(query))
      : category.items.slice();
    return items.sort((left, right) => Number(right.fav) - Number(left.fav));
  }

  function ensureSelection() {
    const items = filteredItems();
    if (!items.length) {
      state.selectedItemId = null;
      return null;
    }
    if (!items.some((item) => item.id === state.selectedItemId)) {
      state.selectedItemId = items[0].id;
    }
    return state.selectedItemId;
  }

  function selectedItem() {
    ensureSelection();
    return filteredItems().find((item) => item.id === state.selectedItemId) || null;
  }

  function selectItem(id, rerender = true) {
    if (!filteredItems().some((item) => item.id === id)) return;
    state.selectedItemId = id;
    if (rerender) renderItems();
    else {
      document.querySelectorAll(".prompt-item").forEach((row) => {
        row.classList.toggle("selected", row.dataset.iid === id);
      });
    }
  }

  function moveSelection(direction) {
    const items = filteredItems();
    if (!items.length) return;
    const current = Math.max(0, items.findIndex((item) => item.id === state.selectedItemId));
    const next = (current + direction + items.length) % items.length;
    selectItem(items[next].id);
  }

  function isCode(text) {
    return text.split("\n").length >= 4 && /[{}();=><]/.test(text);
  }

  function truncate(text, limit) {
    return text.length <= limit ? text : text.slice(0, limit).trimEnd() + "...";
  }

  function cleanCategoryName(name) {
    return name
      .replace(/\p{Extended_Pictographic}/gu, "")
      .replace(/[\uFE0F\u200D]/g, "")
      .replace(/\s+/g, " ")
      .trim();
  }

  function formatResetTime(epochSeconds) {
    if (!epochSeconds) return "--";
    return new Date(epochSeconds * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  function usageLabel(windowInfo) {
    if (!windowInfo) return "--";
    const remaining = Math.max(0, 100 - Number(windowInfo.used_percent || 0));
    const value = remaining.toFixed(Number.isInteger(remaining) ? 0 : 1);
    return `剩${value}% · ${formatResetTime(windowInfo.resets_at)}`;
  }

  function compactResetDate(epochSeconds) {
    if (!epochSeconds) return "--";
    const date = new Date(epochSeconds * 1000);
    const now = new Date();
    if (date.toDateString() === now.toDateString()) return formatResetTime(epochSeconds);
    return date.toLocaleDateString([], { month: "2-digit", day: "2-digit" });
  }

  function compactUsage(windowInfo) {
    if (!windowInfo) return "--";
    const remaining = Math.max(0, 100 - Number(windowInfo.used_percent || 0));
    const value = remaining.toFixed(Number.isInteger(remaining) ? 0 : 1);
    return `剩${value}%→${compactResetDate(windowInfo.resets_at)}`;
  }

  function compactRemaining(windowInfo) {
    if (!windowInfo) return "--";
    const remaining = Math.max(0, 100 - Number(windowInfo.used_percent || 0));
    const value = remaining.toFixed(Number.isInteger(remaining) ? 0 : 1);
    return `${value}%`;
  }

  function renderCodexUsage(snapshot) {
    const button = $("#codex-usage");
    const text = $("#codex-usage-text");
    button.classList.remove("warn", "hot");
    if (!snapshot?.available) {
      text.textContent = "未检测到";
      button.title = snapshot?.error || "未检测到 Codex 用量记录";
      return;
    }
    text.textContent = `5H剩${compactRemaining(snapshot.primary)}`;
    const primaryRemaining = Math.max(0, 100 - Number(snapshot.primary?.used_percent || 0));
    button.classList.toggle("warn", primaryRemaining <= 30 && primaryRemaining > 10);
    button.classList.toggle("hot", primaryRemaining <= 10);
    const snapCore = $("#snap-usage");
    if (snapCore) snapCore.textContent = `${Math.round(primaryRemaining)}%`;
    const snapIndicator = $("#snapped-indicator");
    if (snapIndicator) {
      snapIndicator.classList.toggle("warn", primaryRemaining <= 30 && primaryRemaining > 10);
      snapIndicator.classList.toggle("hot", primaryRemaining <= 10);
      snapIndicator.title = `Codex 5H 剩余 ${Math.round(primaryRemaining)}%，点击展开`;
    }
    const weekly = snapshot.secondary ? `7D ${usageLabel(snapshot.secondary)}` : "7D --";
    button.title = `Codex 5H ${usageLabel(snapshot.primary)} | ${weekly}\n恢复时间按本机时区显示\n记录时间 ${snapshot.captured_at || "--"}`;
  }

  async function refreshCodexUsage(showToast = false) {
    if (!api?.get_codex_usage) {
      renderCodexUsage({ available: false, error: "当前版本不支持读取 Codex 用量" });
      return;
    }
    try {
      const result = await api.get_codex_usage();
      if (!result.ok) {
        renderCodexUsage({ available: false, error: result.error });
        if (showToast) toast("!", result.error || "读取 Codex 用量失败");
        return;
      }
      renderCodexUsage(result.data);
      if (showToast) toast("ok", "Codex usage refreshed");
    } catch (_) {
      renderCodexUsage({ available: false, error: "读取 Codex 用量失败" });
      if (showToast) toast("!", "读取 Codex 用量失败");
    }
  }

  function svgIcon(name) {
    const paths = {
      fav: "M12 3.7l2.55 5.17 5.7.83-4.13 4.02.98 5.68L12 16.72 6.9 19.4l.98-5.68L3.75 9.7l5.7-.83L12 3.7z",
      "fav-filled": "M12 3.7l2.55 5.17 5.7.83-4.13 4.02.98 5.68L12 16.72 6.9 19.4l.98-5.68L3.75 9.7l5.7-.83L12 3.7z",
      edit: "M4 20h4l10.5-10.5a2.83 2.83 0 10-4-4L4 16v4zM13.5 6.5l4 4",
      delete: "M4 7h16M9 7V4h6v3m3 0-1 13H7L6 7m4 4v5m4-5v5",
    };
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("width", "14");
    svg.setAttribute("height", "14");
    svg.setAttribute("fill", name === "fav-filled" ? "currentColor" : "none");
    svg.setAttribute("stroke", "currentColor");
    svg.setAttribute("stroke-width", "1.8");
    svg.setAttribute("stroke-linecap", "round");
    svg.setAttribute("stroke-linejoin", "round");
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", paths[name]);
    svg.append(path);
    return svg;
  }

  function actionButton(action, itemId, label, extraClass) {
    const button = document.createElement("button");
    button.className = `item-action-btn ${extraClass}`;
    button.dataset.act = action;
    button.dataset.iid = itemId;
    button.title = label;
    button.setAttribute("aria-label", label);
    button.append(svgIcon(action));
    return button;
  }

  function renderCategories() {
    const nodes = state.data.categories.map((category, index) => {
      const button = document.createElement("button");
      button.className = "cat-tab" + (category.id === state.activeCategoryId ? " active" : "");
      button.dataset.cid = category.id;
      button.append(document.createTextNode(`${String(index + 1).padStart(2, "0")} ${cleanCategoryName(category.name).toUpperCase()}`));
      const badge = document.createElement("span");
      badge.className = "cat-badge";
      badge.textContent = String(category.items.length);
      button.append(badge);
      return button;
    });
    $("#category-nav").replaceChildren(...nodes);
  }

  function renderItems() {
    const container = $("#items-container");
    const items = filteredItems();
    $("#empty-state").classList.add("hidden");
    $("#no-results").classList.add("hidden");
    if (!activeCategory()) {
      container.replaceChildren();
      $("#result-count").textContent = "0 / 0";
      return;
    }
    if (items.length === 0) {
      container.replaceChildren();
      $(state.searchQuery ? "#no-results" : "#empty-state").classList.remove("hidden");
      $("#result-count").textContent = `0 / ${activeCategory().items.length}`;
      return;
    }

    ensureSelection();

    const nodes = items.map((item, index) => {
      const row = document.createElement("div");
      row.className = "prompt-item";
      row.classList.toggle("selected", item.id === state.selectedItemId);
      row.dataset.iid = item.id;
      if (item.desc) row.dataset.desc = item.desc;
      row.style.animationDelay = `${index * 0.03}s`;

      const number = document.createElement("span");
      number.className = "item-index";
      number.textContent = String(index + 1).padStart(2, "0");
      const title = document.createElement("span");
      title.className = "item-title";
      title.textContent = truncate(item.desc || item.content.split("\n")[0].trim(), 54);
      const summary = document.createElement("span");
      summary.className = "item-summary";
      summary.textContent = truncate(item.content.replace(/\s+/g, " ").trim(), 110);
      const actions = document.createElement("div");
      actions.className = "item-actions";
      const copyState = document.createElement("span");
      copyState.className = "item-copy-state";
      copyState.textContent = "COPIED ✓";
      const shortcut = document.createElement("span");
      shortcut.className = "item-shortcut";
      shortcut.textContent = index < 9 ? `[${index + 1}]` : "";
      const favorite = actionButton("fav", item.id, "收藏", "fav-btn" + (item.fav ? " fav-active" : ""));
      if (item.fav) favorite.replaceChildren(svgIcon("fav-filled"));
      actions.append(copyState, shortcut, favorite, actionButton("edit", item.id, "编辑", "edit-btn"), actionButton("delete", item.id, "删除", "delete-btn"));
      row.append(number, title, summary, actions);
      row.addEventListener("mouseenter", () => selectItem(item.id, false));
      return row;
    });
    container.replaceChildren(...nodes);
    $("#result-count").textContent = `${items.length} / ${activeCategory().items.length}`;
    const selected = Array.from(container.querySelectorAll(".prompt-item")).find((row) => row.dataset.iid === state.selectedItemId);
    if (selected) selected.scrollIntoView({ block: "nearest" });
  }

  function renderAll() {
    renderCategories();
    renderItems();
  }

  async function persist(nextData, successMessage) {
    if (!api) {
      toast("!", "应用服务未就绪");
      return false;
    }
    let result;
    try {
      result = await api.save_data(nextData);
    } catch (error) {
      toast("!", "保存服务暂时不可用");
      return false;
    }
    if (!result.ok) {
      toast("!", result.error || "保存失败");
      return false;
    }
    state.data = result.data;
    if (!state.data.categories.some((category) => category.id === state.activeCategoryId)) {
      state.activeCategoryId = state.data.categories[0]?.id || null;
    }
    renderAll();
    if (successMessage) toast("ok", successMessage);
    return true;
  }

  function textareaCopy(text, onSuccess) {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.style.cssText = "position:fixed;left:-9999px";
    document.body.append(textarea);
    textarea.select();
    const copied = document.execCommand("copy");
    textarea.remove();
    if (copied) onSuccess(); else toast("!", "复制失败，请手动复制");
  }

  function browserCopy(text, onSuccess) {
    if (navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(text).then(onSuccess).catch(() => textareaCopy(text, onSuccess));
    } else {
      textareaCopy(text, onSuccess);
    }
  }

  async function copyPrompt(id) {
    const item = activeCategory()?.items.find((candidate) => candidate.id === id);
    if (!item) return;
    const onSuccess = () => {
      const row = Array.from(document.querySelectorAll(".prompt-item")).find((node) => node.dataset.iid === id);
      if (row) {
        row.classList.add("copied");
        setTimeout(() => { row.classList.remove("copied"); }, 900);
      }
      toast("ok", "Copied");
    };
    if (api) {
      try {
        const result = await api.copy_to_clipboard(item.content);
        if (result.ok) return onSuccess();
      } catch (_) {}
    }
    browserCopy(item.content, onSuccess);
  }

  function closeItemModal() {
    $("#modal-item").classList.add("hidden");
    state.editingItemId = null;
  }

  function openItemModal(id) {
    state.editingItemId = id || null;
    const select = $("#modal-item-category");
    const options = state.data.categories.map((category) => {
      const option = document.createElement("option");
      option.value = category.id;
      option.textContent = category.name;
      return option;
    });
    select.replaceChildren(...options);
    select.value = state.activeCategoryId || "";
    $("#modal-item-title").textContent = id ? "Edit" : "New";
    $("#modal-item-delete").classList.toggle("hidden", !id);
    $("#modal-item-content").value = "";
    if (id) {
      for (const category of state.data.categories) {
        const item = category.items.find((candidate) => candidate.id === id);
        if (item) {
          select.value = category.id;
          $("#modal-item-content").value = item.content;
          break;
        }
      }
    }
    $("#modal-item").classList.remove("hidden");
    setTimeout(() => $("#modal-item-content").focus(), 100);
  }

  async function saveItem() {
    const categoryId = $("#modal-item-category").value;
    const content = $("#modal-item-content").value.trim();
    if (!content) return toast("!", "内容不能为空");
    const next = clone(state.data);
    const target = next.categories.find((category) => category.id === categoryId);
    if (!target) return toast("!", "分类不存在");
    if (state.editingItemId) {
      for (const category of next.categories) {
        const index = category.items.findIndex((item) => item.id === state.editingItemId);
        if (index !== -1) {
          const item = category.items.splice(index, 1)[0];
          item.content = content;
          target.items.push(item);
          break;
        }
      }
    } else {
      const desc = truncate(content.split("\n")[0].trim(), 40);
      target.items.push({ id: makeId(), content, desc, fav: false });
    }
    if (await persist(next, "Saved")) closeItemModal();
  }

  async function deleteItem(id) {
    const next = clone(state.data);
    next.categories.forEach((category) => {
      category.items = category.items.filter((item) => item.id !== id);
    });
    if (await persist(next)) closeItemModal();
  }

  async function toggleFavorite(id) {
    const next = clone(state.data);
    for (const category of next.categories) {
      const item = category.items.find((candidate) => candidate.id === id);
      if (item) item.fav = !item.fav;
    }
    await persist(next);
  }

  function closeManageModal() {
    $("#modal-manage").classList.add("hidden");
  }

  function renderCategoryManager() {
    const rows = state.data.categories.map((category, index) => {
      const row = document.createElement("div");
      row.className = "cat-list-item";
      const number = document.createElement("span");
      number.style.cssText = "font-size:10px;color:var(--t3);min-width:16px";
      number.textContent = `${index + 1}.`;
      const input = document.createElement("input");
      input.className = "cat-name-input";
      input.value = category.name;
      input.dataset.cid = category.id;
      input.addEventListener("change", async () => {
        const name = input.value.trim();
        if (!name) return (input.value = category.name);
        const next = clone(state.data);
        next.categories.find((candidate) => candidate.id === category.id).name = name;
        if (await persist(next)) renderCategoryManager(); else input.value = category.name;
      });
      const remove = document.createElement("button");
      remove.className = "cat-del-btn";
      remove.textContent = "×";
      remove.title = "删除分类";
      remove.disabled = state.data.categories.length <= 1;
      remove.style.opacity = remove.disabled ? "0.15" : "";
      remove.addEventListener("click", async () => {
        const next = clone(state.data);
        next.categories = next.categories.filter((candidate) => candidate.id !== category.id);
        if (await persist(next)) renderCategoryManager();
      });
      row.append(number, input, remove);
      return row;
    });
    $("#category-list-body").replaceChildren(...rows);
  }

  function openManageModal() {
    renderCategoryManager();
    $("#modal-manage").classList.remove("hidden");
  }

  async function addCategory() {
    const next = clone(state.data);
    const category = { id: makeId(), name: "New", items: [] };
    next.categories.push(category);
    if (await persist(next)) {
      state.activeCategoryId = category.id;
      renderAll();
      renderCategoryManager();
    }
  }

  async function importData(file) {
    let parsed;
    try {
      parsed = JSON.parse(await file.text());
    } catch (_) {
      return toast("!", "JSON 解析失败");
    }
    const checked = await api.validate_import(parsed);
    if (!checked.ok) return toast("!", checked.error || "导入格式错误");
    if (!window.confirm("导入将替换当前提示词，是否继续？")) return;
    if (await persist(checked.data, "Imported")) {
      state.activeCategoryId = state.data.categories[0]?.id || null;
      renderAll();
    }
  }

  function exportData() {
    const blob = new Blob([JSON.stringify(state.data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "pf-backup.json";
    anchor.click();
    URL.revokeObjectURL(url);
    toast("ok", "Exported");
  }

  function isTypingTarget(target) {
    if (!target) return false;
    return ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName) || target.isContentEditable;
  }

  function toggleToolsMenu(force) {
    const menu = $("#tools-menu");
    const shouldOpen = typeof force === "boolean" ? force : menu.classList.contains("hidden");
    menu.classList.toggle("hidden", !shouldOpen);
    $("#btn-tools").classList.toggle("active", shouldOpen);
  }

  function closeTransientUi() {
    if (!$("#modal-item").classList.contains("hidden")) return closeItemModal(), true;
    if (!$("#modal-manage").classList.contains("hidden")) return closeManageModal(), true;
    if (!$("#quit-modal").classList.contains("hidden")) return $("#quit-modal").classList.add("hidden"), true;
    if (!$("#tools-menu").classList.contains("hidden")) return toggleToolsMenu(false), true;
    if (state.searchQuery) {
      state.searchQuery = "";
      state.selectedItemId = null;
      $("#search-input").value = "";
      $("#search-clear").classList.add("hidden");
      renderItems();
      return true;
    }
    return false;
  }

  function handleGlobalKey(event) {
    if (event.key === "Escape") {
      if (closeTransientUi()) event.preventDefault();
      else if (isTypingTarget(event.target)) event.target.blur();
      return;
    }
    if (isTypingTarget(event.target)) return;
    if (event.ctrlKey || event.metaKey || event.altKey) return;

    switch (event.key) {
      case "ArrowUp":
        event.preventDefault();
        moveSelection(-1);
        return;
      case "ArrowDown":
        event.preventDefault();
        moveSelection(1);
        return;
      case "Enter": {
        event.preventDefault();
        const item = selectedItem();
        if (item) copyPrompt(item.id);
        return;
      }
      case "/":
        event.preventDefault();
        $("#search-input").focus();
        return;
    }

    if (/^[1-9]$/.test(event.key)) {
      const item = filteredItems()[Number(event.key) - 1];
      if (item) copyPrompt(item.id);
      return;
    }

    switch (event.key.toLowerCase()) {
      case "n":
        event.preventDefault();
        openItemModal();
        return;
      case "e": {
        event.preventDefault();
        const item = selectedItem();
        if (item) openItemModal(item.id);
        return;
      }
      case "f": {
        event.preventDefault();
        const item = selectedItem();
        if (item) toggleFavorite(item.id);
        return;
      }
    }
  }

  function bindWindowControls() {
    const shell = $("#app-shell");
    const titlebar = document.querySelector(".titlebar");
    let dragging = false, startX = 0, startY = 0;
    titlebar.addEventListener("mousedown", (event) => {
      if (event.target.closest("button")) return;
      dragging = true; startX = event.screenX; startY = event.screenY; event.preventDefault();
    });
    window.addEventListener("mousemove", (event) => {
      if (!dragging) return;
      api.move_window(event.screenX - startX, event.screenY - startY);
      startX = event.screenX; startY = event.screenY;
    });
    window.addEventListener("mouseup", () => { dragging = false; });

    let resizing = false, resizeX = 0, resizeY = 0, resizeW = 0, resizeH = 0;
    $("#resize-handle").addEventListener("mousedown", (event) => {
      resizing = true; resizeX = event.screenX; resizeY = event.screenY;
      resizeW = window.innerWidth; resizeH = window.innerHeight; event.preventDefault();
    });
    window.addEventListener("mousemove", (event) => {
      if (!resizing) return;
      api.resize_window(Math.max(280, Math.min(700, resizeW + event.screenX - resizeX)), Math.max(200, Math.min(900, resizeH + event.screenY - resizeY)));
    });
    window.addEventListener("mouseup", () => { resizing = false; });

    let snapped = false, pinned = false, blurTimer = null, hoverTimer = null;
    const setSnapped = (value) => { snapped = value; shell.classList.toggle("snapped", value); $("#btn-snap").classList.toggle("pinned", value); };
    const snap = async () => { if (!snapped && await api.snap_to_edge()) setSnapped(true); };
    const unsnap = async () => { if (snapped && await api.unsnap_from_edge()) setSnapped(false); };
    $("#btn-snap").addEventListener("click", () => snapped ? unsnap() : snap());
    $("#snapped-indicator").addEventListener("click", (event) => { event.stopPropagation(); unsnap(); });
    $("#btn-pin").addEventListener("click", () => {
      pinned = !pinned;
      $("#btn-pin").classList.toggle("pinned", pinned);
    });
    window.addEventListener("blur", () => { if (!pinned && !snapped) blurTimer = setTimeout(snap, 500); });
    window.addEventListener("focus", () => { clearTimeout(blurTimer); });
    document.addEventListener("mouseenter", () => { clearTimeout(hoverTimer); if (snapped && !pinned) unsnap(); });
    document.addEventListener("mouseleave", () => { if (!snapped && !pinned) hoverTimer = setTimeout(snap, 1500); });
    document.addEventListener("keydown", (event) => {
      if (event.ctrlKey && event.shiftKey && event.key === "P") { event.preventDefault(); snapped ? unsnap() : snap(); }
    });
    setTimeout(() => { if (!pinned && !snapped) snap(); }, 2000);
    setInterval(async () => {
      const geometry = await api.get_geometry();
      if (!snapped && geometry.w > 200) api.save_geometry(geometry.w, geometry.h, geometry.x, geometry.y);
    }, 5000);
  }

  function bindEvents() {
    $("#search-input").addEventListener("input", (event) => {
      state.searchQuery = event.target.value;
      state.selectedItemId = null;
      $("#search-clear").classList.toggle("hidden", !state.searchQuery);
      renderItems();
    });
    $("#search-clear").addEventListener("click", () => {
      state.searchQuery = ""; state.selectedItemId = null; $("#search-input").value = ""; $("#search-clear").classList.add("hidden"); renderItems();
    });
    $("#category-nav").addEventListener("click", (event) => {
      const tab = event.target.closest(".cat-tab");
      if (!tab) return;
      state.activeCategoryId = tab.dataset.cid; state.searchQuery = ""; state.selectedItemId = null; $("#search-input").value = ""; $("#search-clear").classList.add("hidden"); renderAll();
    });
    $("#items-container").addEventListener("click", (event) => {
      const action = event.target.closest("[data-act]");
      const row = event.target.closest(".prompt-item");
      if (row) state.selectedItemId = row.dataset.iid;
      if (action) {
        event.stopPropagation();
        if (action.dataset.act === "edit") openItemModal(action.dataset.iid);
        if (action.dataset.act === "delete") deleteItem(action.dataset.iid);
        if (action.dataset.act === "fav") toggleFavorite(action.dataset.iid);
      } else if (row) copyPrompt(row.dataset.iid);
    });
    $("#items-container").addEventListener("dblclick", (event) => {
      const row = event.target.closest(".prompt-item");
      if (row && !event.target.closest("[data-act]")) openItemModal(row.dataset.iid);
    });
    $("#btn-add-item").addEventListener("click", () => openItemModal());
    $("#codex-usage").addEventListener("click", () => refreshCodexUsage(true));
    $("#btn-codex-usage").addEventListener("click", () => refreshCodexUsage(true));
    $("#btn-manage").addEventListener("click", openManageModal);
    $("#btn-export").addEventListener("click", exportData);
    $("#btn-tools").addEventListener("click", (event) => { event.stopPropagation(); toggleToolsMenu(); });
    $("#btn-import").addEventListener("click", () => {
      const input = document.createElement("input");
      input.type = "file"; input.accept = ".json";
      input.addEventListener("change", () => input.files[0] && importData(input.files[0]));
      input.click();
    });
    $("#modal-item-save").addEventListener("click", saveItem);
    $("#modal-item-cancel").addEventListener("click", closeItemModal);
    $("#modal-item-close").addEventListener("click", closeItemModal);
    $("#modal-item-delete").addEventListener("click", () => deleteItem(state.editingItemId));
    $("#btn-add-category").addEventListener("click", addCategory);
    $("#modal-manage-done").addEventListener("click", closeManageModal);
    $("#modal-manage-close").addEventListener("click", closeManageModal);
    $("#modal-item-content").addEventListener("keydown", (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key === "Enter") saveItem();
    });
    $("#btn-quit").addEventListener("click", () => $("#quit-modal").classList.remove("hidden"));
    $("#quit-no").addEventListener("click", () => $("#quit-modal").classList.add("hidden"));
    $("#quit-yes").addEventListener("click", () => api.quit_app());
    document.addEventListener("keydown", handleGlobalKey);
    document.addEventListener("click", (event) => {
      if (!event.target.closest("#tools-menu") && !event.target.closest("#btn-tools")) toggleToolsMenu(false);
    });
    const tooltip = $("#tt-desc");
    document.addEventListener("mousemove", (event) => {
      const row = document.elementFromPoint(event.clientX, event.clientY)?.closest(".prompt-item");
      if (!row?.dataset.desc) return tooltip.classList.remove("on");
      tooltip.textContent = row.dataset.desc; tooltip.classList.add("on");
      tooltip.style.left = `${Math.max(4, Math.min(event.clientX + 16, window.innerWidth - 234))}px`;
      tooltip.style.top = `${Math.max(6, event.clientY - 14)}px`;
    });
  }

  async function start() {
    api = window.pywebview?.api;
    if (!api) return;
    bindEvents();
    bindWindowControls();
    api.hide_taskbar_icon().catch(() => {});
    const result = await api.get_data();
    if (!result.ok) return toast("!", result.error || "读取失败");
    state.data = result.data;
    state.activeCategoryId = state.data.categories[0]?.id || null;
    renderAll();
    refreshCodexUsage();
    setInterval(refreshCodexUsage, 60000);
  }

  if (window.pywebview?.api) start();
  else window.addEventListener("pywebviewready", start, { once: true });
})();
