const state = {
    contacts: [],
    filterMode: "all", // "all" | "bookmarked"
    category: "ALL",
    search: "",
    viewMode: "cards", // "cards" | "table"
};

const METHOD_META = {
    phone: { icon: "📞", name: "电话号码", defaultLabel: "手机", placeholder: "例如：138-0000-0000" },
    email: { icon: "✉️", name: "电子邮箱", defaultLabel: "工作邮箱", placeholder: "例如：name@example.com" },
    social: { icon: "💬", name: "社交账号", defaultLabel: "微信", placeholder: "例如：wx_id 或 github.com/user" },
    address: { icon: "📍", name: "联系地址", defaultLabel: "办公地址", placeholder: "例如：福州市闽侯县学园路2号" },
};

document.addEventListener("DOMContentLoaded", () => {
    bindEvents();
    loadContacts();
});

function bindEvents() {
    document.getElementById("tabAll").addEventListener("click", () => setFilterMode("all"));
    document.getElementById("tabBookmarked").addEventListener("click", () => setFilterMode("bookmarked"));
    document.getElementById("statCardAll").addEventListener("click", () => {
        state.category = "ALL";
        document.getElementById("categoryFilter").value = "ALL";
        setFilterMode("all");
    });
    document.getElementById("statCardBookmarked").addEventListener("click", () => setFilterMode("bookmarked"));
    const statCardCategories = document.getElementById("statCardCategories");
    if (statCardCategories) {
        statCardCategories.addEventListener("click", toggleCategoryChipsPanel);
    }

    const searchInput = document.getElementById("searchInput");
    let debounceTimer = null;
    searchInput.addEventListener("input", (e) => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            state.search = e.target.value.trim();
            loadContacts();
        }, 200);
    });

    document.getElementById("categoryFilter").addEventListener("change", (e) => {
        state.category = e.target.value;
        loadContacts();
    });

    document.getElementById("btnViewCards").addEventListener("click", () => setViewMode("cards"));
    document.getElementById("btnViewTable").addEventListener("click", () => setViewMode("table"));

    document.getElementById("btnAddContact").addEventListener("click", () => openModal());
    document.getElementById("btnCloseModal").addEventListener("click", closeModal);
    document.getElementById("btnCancelModal").addEventListener("click", closeModal);

    document.querySelectorAll("[data-add-type]").forEach((btn) => {
        btn.addEventListener("click", () => {
            addMethodRow({ method_type: btn.getAttribute("data-add-type"), label: "", value: "" });
        });
    });

    document.getElementById("contactForm").addEventListener("submit", handleSaveContact);

    // Base UI initialized
    document.getElementById("btnExportExcel").addEventListener("click", handleExportExcel);
    const fileInput = document.getElementById("excelFileInput");
    document.getElementById("btnImportExcel").addEventListener("click", () => fileInput.click());
    fileInput.addEventListener("change", handleImportExcel);
}

function setFilterMode(mode) {
    state.filterMode = mode;
    document.getElementById("tabAll").classList.toggle("active", mode === "all");
    document.getElementById("tabBookmarked").classList.toggle("active", mode === "bookmarked");
    loadContacts();
}

function setViewMode(mode) {
    state.viewMode = mode;
    document.getElementById("btnViewCards").classList.toggle("active", mode === "cards");
    document.getElementById("btnViewTable").classList.toggle("active", mode === "table");
    renderContacts();
}

async function loadContacts() {
    const params = new URLSearchParams();
    if (state.search) params.set("search", state.search);
    if (state.category && state.category !== "ALL") params.set("category", state.category);
    if (state.filterMode === "bookmarked") params.set("bookmarked", "1");

    try {
        const res = await fetch(`/api/contacts?${params.toString()}`);
        const data = await res.json();
        state.contacts = data.contacts || [];
        updateStatsAndCategories(data.stats || {});
        renderContacts();
    } catch (err) {
        showToast("加载联系人失败，请检查网络连接", "error");
    }
}

function toggleCategoryChipsPanel() {
    const panel = document.getElementById("categoryChipsPanel");
    const card = document.getElementById("statCardCategories");
    if (!panel) return;
    const isHidden = panel.classList.toggle("hidden");
    if (card) {
        card.classList.toggle("active-card", !isHidden);
    }
}

function selectCategoryChip(categoryVal) {
    state.category = categoryVal;
    const select = document.getElementById("categoryFilter");
    if (select) select.value = categoryVal;
    loadContacts();
}

function updateStatsAndCategories(stats) {
    const total = stats.total ?? 0;
    const bookmarked = stats.bookmarked ?? 0;
    const categories = stats.categories || [];

    document.getElementById("statTotalCount").textContent = total;
    document.getElementById("statBookmarkedCount").textContent = bookmarked;
    document.getElementById("statCategoryCount").textContent = categories.length;
    document.getElementById("badgeAll").textContent = total;
    document.getElementById("badgeBookmarked").textContent = bookmarked;

    const select = document.getElementById("categoryFilter");
    const currentVal = state.category;
    select.innerHTML = `<option value="ALL">全部分组 (All Groups)</option>`;
    categories.forEach((cat) => {
        const opt = document.createElement("option");
        opt.value = cat;
        opt.textContent = cat;
        if (cat === currentVal) opt.selected = true;
        select.appendChild(opt);
    });

    const chipsList = document.getElementById("categoryChipsList");
    if (chipsList) {
        const allItems = ["ALL", ...categories];
        chipsList.innerHTML = allItems
            .map((cat) => {
                const isAct = currentVal === cat ? "active" : "";
                const label = cat === "ALL" ? "全部分组" : escapeHTML(cat);
                const arg = escapeHTML(cat).replace(/'/g, "\\'");
                return `<button type="button" class="category-chip-btn ${isAct}" onclick="selectCategoryChip('${arg}')">${label}</button>`;
            })
            .join("");
    }
}

function renderContacts() {
    const grid = document.getElementById("contactsGrid");
    const tableWrapper = document.getElementById("contactsTableWrapper");
    const tableBody = document.getElementById("contactsTableBody");
    const emptyState = document.getElementById("emptyState");

    if (!state.contacts.length) {
        grid.classList.add("hidden");
        tableWrapper.classList.add("hidden");
        emptyState.classList.remove("hidden");
        return;
    }

    emptyState.classList.add("hidden");

    if (state.viewMode === "cards") {
        tableWrapper.classList.add("hidden");
        grid.classList.remove("hidden");
        grid.innerHTML = state.contacts.map(renderCardHTML).join("");
    } else {
        grid.classList.add("hidden");
        tableWrapper.classList.remove("hidden");
        tableBody.innerHTML = state.contacts.map(renderTableRowHTML).join("");
    }
}

function renderCardHTML(contact) {
    const initial = (contact.name || "?").trim().charAt(0).toUpperCase();
    const bmClass = contact.bookmarked ? "is-bookmarked" : "";
    const starActive = contact.bookmarked ? "active" : "";
    const starIcon = contact.bookmarked ? "★" : "☆";
    const metaParts = [contact.company, contact.title].filter(Boolean);
    const metaText = metaParts.length ? metaParts.join(" · ") : "未填写单位/职位";

    const methods = contact.methods || [];
    const methodsHTML = methods.length
        ? methods
              .map((m) => {
                  const meta = METHOD_META[m.method_type] || METHOD_META.phone;
                  const labelText = escapeHTML(m.label || meta.defaultLabel);
                  return `
                    <div class="method-item">
                        <span class="method-icon">${meta.icon}</span>
                        <span class="method-label">${labelText}</span>
                        <span class="method-value">${escapeHTML(m.value)}</span>
                    </div>
                  `;
              })
              .join("")
        : `<div class="method-item"><span class="method-value" style="color:#94a3b8;">暂无联系方式</span></div>`;

    const notesHTML = contact.notes
        ? `<div class="card-notes">📝 ${escapeHTML(contact.notes)}</div>`
        : "";

    return `
        <article class="contact-card ${bmClass}">
            <div class="card-top">
                <div class="avatar-group">
                    <div class="avatar">${escapeHTML(initial)}</div>
                    <div>
                        <div class="contact-name-row">
                            <span class="contact-name">${escapeHTML(contact.name)}</span>
                            <span class="category-pill">${escapeHTML(contact.category || "未分类")}</span>
                        </div>
                        <div class="contact-meta">${escapeHTML(metaText)}</div>
                    </div>
                </div>
                <button
                    type="button"
                    class="bookmark-btn ${starActive}"
                    onclick="toggleBookmark(${contact.id})"
                    title="${contact.bookmarked ? "取消星标收藏" : "设为星标收藏"}"
                >${starIcon}</button>
            </div>
            <div class="card-methods">${methodsHTML}</div>
            ${notesHTML}
            <div class="card-footer">
                <button type="button" class="btn-sm" onclick="editContact(${contact.id})">✏️ 编辑</button>
                <button type="button" class="btn-sm btn-sm-danger" onclick="deleteContact(${contact.id})">🗑️ 删除</button>
            </div>
        </article>
    `;
}

function renderTableRowHTML(contact) {
    const bmClass = contact.bookmarked ? "is-bookmarked" : "";
    const starActive = contact.bookmarked ? "active" : "";
    const starIcon = contact.bookmarked ? "★" : "☆";
    const methods = contact.methods || [];

    const renderTypeTags = (type) => {
        const items = methods.filter((m) => m.method_type === type);
        if (!items.length) return `<span style="color:#cbd5e1;">—</span>`;
        return items
            .map(
                (m) =>
                    `<span class="table-method-tag"><strong>${escapeHTML(
                        m.label || METHOD_META[type].defaultLabel
                    )}:</strong> ${escapeHTML(m.value)}</span>`
            )
            .join("");
    };

    return `
        <tr class="${bmClass}">
            <td>
                <button
                    type="button"
                    class="bookmark-btn ${starActive}"
                    onclick="toggleBookmark(${contact.id})"
                >${starIcon}</button>
            </td>
            <td>
                <strong>${escapeHTML(contact.name)}</strong>
                <div style="font-size:12px;color:#64748b;">${escapeHTML(
                    [contact.company, contact.title].filter(Boolean).join(" · ")
                )}</div>
            </td>
            <td><span class="category-pill">${escapeHTML(contact.category || "未分类")}</span></td>
            <td>${renderTypeTags("phone")}</td>
            <td>${renderTypeTags("email")}</td>
            <td>${renderTypeTags("social")}</td>
            <td>${renderTypeTags("address")}</td>
            <td>
                <button type="button" class="btn-sm" onclick="editContact(${contact.id})">编辑</button>
                <button type="button" class="btn-sm btn-sm-danger" onclick="deleteContact(${contact.id})">删除</button>
            </td>
        </tr>
    `;
}

async function toggleBookmark(contactId) {
    try {
        const res = await fetch(`/api/contacts/${contactId}/bookmark`, { method: "PATCH" });
        if (!res.ok) throw new Error("操作失败");
        const updated = await res.json();
        showToast(
            updated.bookmarked
                ? `⭐ 已将「${updated.name}」加入星标收藏`
                : `已取消「${updated.name}」的星标收藏`
        );
        loadContacts();
    } catch (err) {
        showToast("更新收藏状态失败", "error");
    }
}

function openModal(contact = null) {
    const modal = document.getElementById("contactModal");
    const title = document.getElementById("modalTitle");
    const container = document.getElementById("methodsContainer");
    container.innerHTML = "";

    if (contact) {
        title.textContent = "编辑联系人";
        document.getElementById("contactId").value = contact.id;
        document.getElementById("inputName").value = contact.name || "";
        document.getElementById("inputCategory").value = contact.category || "";
        document.getElementById("inputCompany").value = contact.company || "";
        document.getElementById("inputTitle").value = contact.title || "";
        document.getElementById("inputNotes").value = contact.notes || "";
        document.getElementById("inputBookmarked").checked = Boolean(contact.bookmarked);

        const methods = contact.methods || [];
        if (methods.length) {
            methods.forEach((m) => addMethodRow(m));
        } else {
            addMethodRow({ method_type: "phone", label: "手机", value: "" });
        }
    } else {
        title.textContent = "新建联系人";
        document.getElementById("contactForm").reset();
        document.getElementById("contactId").value = "";
        addMethodRow({ method_type: "phone", label: "手机", value: "" });
        addMethodRow({ method_type: "email", label: "邮箱", value: "" });
    }

    modal.classList.remove("hidden");
}

function closeModal() {
    document.getElementById("contactModal").classList.add("hidden");
}

function addMethodRow(method = { method_type: "phone", label: "", value: "" }) {
    const container = document.getElementById("methodsContainer");
    const type = method.method_type || "phone";
    const meta = METHOD_META[type] || METHOD_META.phone;
    const labelVal = method.label !== undefined && method.label !== "" ? method.label : meta.defaultLabel;

    const row = document.createElement("div");
    row.className = "method-row";
    row.innerHTML = `
        <select class="method-type-select" aria-label="联系方式类型">
            <option value="phone" ${type === "phone" ? "selected" : ""}>📞 电话号码</option>
            <option value="email" ${type === "email" ? "selected" : ""}>✉️ 电子邮箱</option>
            <option value="social" ${type === "social" ? "selected" : ""}>💬 社交账号</option>
            <option value="address" ${type === "address" ? "selected" : ""}>📍 联系地址</option>
        </select>
        <input type="text" class="method-label-input" placeholder="标签 (如: 手机)" value="${escapeHTML(labelVal)}" />
        <input type="text" class="method-value-input" placeholder="${meta.placeholder}" value="${escapeHTML(method.value || "")}" />
        <button type="button" class="btn-remove-method" title="移除此项">×</button>
    `;

    const selectEl = row.querySelector(".method-type-select");
    const labelEl = row.querySelector(".method-label-input");
    const valueEl = row.querySelector(".method-value-input");

    selectEl.addEventListener("change", (e) => {
        const newMeta = METHOD_META[e.target.value] || METHOD_META.phone;
        labelEl.value = newMeta.defaultLabel;
        valueEl.placeholder = newMeta.placeholder;
    });

    row.querySelector(".btn-remove-method").addEventListener("click", () => {
        row.remove();
    });

    container.appendChild(row);
}

async function editContact(contactId) {
    const contact = state.contacts.find((c) => c.id === contactId);
    if (contact) {
        openModal(contact);
    }
}

async function handleSaveContact(e) {
    e.preventDefault();
    const id = document.getElementById("contactId").value;
    const methods = [];
    document.querySelectorAll("#methodsContainer .method-row").forEach((row) => {
        const method_type = row.querySelector(".method-type-select").value;
        const label = row.querySelector(".method-label-input").value.trim();
        const value = row.querySelector(".method-value-input").value.trim();
        if (value) {
            methods.push({ method_type, label, value });
        }
    });

    const payload = {
        name: document.getElementById("inputName").value.trim(),
        category: document.getElementById("inputCategory").value.trim() || "未分类",
        company: document.getElementById("inputCompany").value.trim(),
        title: document.getElementById("inputTitle").value.trim(),
        notes: document.getElementById("inputNotes").value.trim(),
        bookmarked: document.getElementById("inputBookmarked").checked,
        methods,
    };

    try {
        const url = id ? `/api/contacts/${id}` : "/api/contacts";
        const method = id ? "PUT" : "POST";
        const res = await fetch(url, {
            method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!res.ok) {
            showToast(data.error || "保存失败", "error");
            return;
        }
        closeModal();
        showToast(id ? `已更新联系人「${data.name}」` : `已新建联系人「${data.name}」`);
        loadContacts();
    } catch (err) {
        showToast("保存请求异常", "error");
    }
}

async function deleteContact(contactId) {
    const target = state.contacts.find((c) => c.id === contactId);
    const name = target ? target.name : `#${contactId}`;
    if (!confirm(`确定要删除联系人「${name}」吗？此操作不可撤销。`)) return;

    try {
        const res = await fetch(`/api/contacts/${contactId}`, { method: "DELETE" });
        if (!res.ok) throw new Error("删除失败");
        showToast(`已删除联系人「${name}」`);
        loadContacts();
    } catch (err) {
        showToast("删除联系人失败", "error");
    }
}

function handleExportExcel() {
    const params = new URLSearchParams();
    if (state.search) params.set("search", state.search);
    if (state.category && state.category !== "ALL") params.set("category", state.category);
    if (state.filterMode === "bookmarked") params.set("bookmarked", "1");
    window.location.href = `/api/contacts/export?${params.toString()}`;
    showToast("📤 正在生成并下载 Excel 文件...");
}

async function handleImportExcel(e) {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
        const res = await fetch("/api/contacts/import", {
            method: "POST",
            body: formData,
        });
        const data = await res.json();
        if (!res.ok) {
            showToast(data.error || "Excel 导入失败", "error");
        } else {
            showToast(`📥 ${data.message}`);
            loadContacts();
        }
    } catch (err) {
        showToast("上传 Excel 文件失败", "error");
    } finally {
        e.target.value = "";
    }
}

function showToast(message, type = "success") {
    const container = document.getElementById("toastContainer");
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.remove();
    }, 3200);
}

function escapeHTML(str) {
    return String(str ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}
