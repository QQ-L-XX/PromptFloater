(function () {
  "use strict";

  const $ = (selector) => document.querySelector(selector);
  const state = { data: { schema_version: 1, categories: [] }, activeCategoryId: null, searchQuery: "", editingItemId: null };
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

  function isCode(text) {
    return text.split("\n").length >= 4 && /[{}();=><]/.test(text);
  }

  function truncate(text, limit) {
    return text.length <= limit ? text : text.slice(0, limit).trimEnd() + "...";
  }

  function actionButton(action, itemId, label, extraClass) {
    const button = document.createElement("button");
    button.className = `item-action-btn ${extraClass}`;
    button.dataset.act = action;
    button.dataset.iid = itemId;
    button.title = label;
    button.setAttribute("aria-label", label);
    button.textContent = action === "fav" ? "☆" : action === "edit" ? "✎" : "×";
    return button;
  }

  function renderCategories() {
    const nodes = state.data.categories.map((category) => {
      const button = document.createElement("button");
      button.className = "cat-tab" + (category.id === state.activeCategoryId ? " active" : "");
      button.dataset.cid = category.id;
      button.append(document.createTextNode(category.name));
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
      return;
    }
    if (items.length === 0) {
      container.replaceChildren();
      $(state.searchQuery ? "#no-results" : "#empty-state").classList.remove("hidden");
      return;
    }

    const nodes = items.map((item, index) => {
      const row = document.createElement("div");
      row.className = "prompt-item";
      row.dataset.iid = item.id;
      if (item.desc) row.dataset.desc = item.desc;
      row.style.animationDelay = `${index * 0.03}s`;

      const number = document.createElement("span");
      number.className = "item-index";
      number.textContent = String(index + 1);
      const content = document.createElement("span");
      content.className = "item-content" + (isCode(item.content) ? " is-code" : "");
      content.textContent = truncate(item.content, 300);
      const actions = document.createElement("div");
      actions.className = "item-actions";
      const favorite = actionButton("fav", item.id, "收藏", "fav-btn" + (item.fav ? " fav-active" : ""));
      favorite.textContent = item.fav ? "★" : "☆";
      actions.append(favorite, actionButton("edit", item.id, "编辑", "edit-btn"), actionButton("delete", item.id, "删除", "delete-btn"));
      row.append(number, content, actions);
      return row;
    });
    container.replaceChildren(...nodes);
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
        setTimeout(() => row.classList.remove("copied"), 600);
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
      $("#search-clear").classList.toggle("hidden", !state.searchQuery);
      renderItems();
    });
    $("#search-clear").addEventListener("click", () => {
      state.searchQuery = ""; $("#search-input").value = ""; $("#search-clear").classList.add("hidden"); renderItems();
    });
    $("#category-nav").addEventListener("click", (event) => {
      const tab = event.target.closest(".cat-tab");
      if (!tab) return;
      state.activeCategoryId = tab.dataset.cid; state.searchQuery = ""; $("#search-input").value = ""; renderAll();
    });
    $("#items-container").addEventListener("click", (event) => {
      const action = event.target.closest("[data-act]");
      const row = event.target.closest(".prompt-item");
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
    $("#btn-manage").addEventListener("click", openManageModal);
    $("#btn-export").addEventListener("click", exportData);
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
    document.addEventListener("keydown", (event) => {
      if (event.key === "/" && document.activeElement === document.body) { event.preventDefault(); $("#search-input").focus(); }
      if (event.key === "Escape") { closeItemModal(); closeManageModal(); }
      if (document.activeElement === document.body && /^[1-9]$/.test(event.key)) {
        const item = filteredItems()[Number(event.key) - 1]; if (item) copyPrompt(item.id);
      }
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
  }

  if (window.pywebview?.api) start();
  else window.addEventListener("pywebviewready", start, { once: true });
})();
