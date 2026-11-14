// state setup of the application
const state = {
  carts: [],
  selectedCart: null,
  stationCart: null,
  quantities: {},
  stationMode: false,
  toastTimeout: null,
};
// function to convert cents into dollars
const money = (cents) => `$${(cents / 100).toFixed(2)}`;
// function to keep text displayed as text
const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (character) => ({
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#39;",
})[character]);
// Helper function for api to return data else throw error
async function api(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Something went wrong. Please try again.");
  return data;
}
// show display toast then remove the message
function showToast(message) {
  const toast = document.querySelector("#toast");
  toast.textContent = message;
  toast.classList.add("visible");
  clearTimeout(state.toastTimeout);
  state.toastTimeout = setTimeout(() => toast.classList.remove("visible"), 3500);
}
// truck icon
function truckIllustration(cart) {
  const color = escapeHtml(cart.color);
  return `<svg class="truck-illustration" viewBox="0 0 360 150" aria-hidden="true" focusable="false">
    <ellipse cx="180" cy="125" rx="136" ry="10" fill="#000" opacity=".3"/>
    <rect x="44" y="27" width="272" height="92" rx="17" fill="${color}"/>
    <rect x="55" y="36" width="191" height="74" rx="10" fill="#f3eddf"/>
    <path d="M66 41h18v64H66zm35 0h18v64h-18zm35 0h18v64h-18zm35 0h18v64h-18zm35 0h17v64h-17z" fill="${color}" opacity=".9"/>
    <rect x="72" y="64" width="158" height="21" rx="5" fill="#fffaf0" stroke="#d7ccba" stroke-width="2"/>
    <circle cx="151" cy="74.5" r="18" fill="#fffaf0"/>
    <text x="151" y="81" text-anchor="middle" font-size="21">${escapeHtml(cart.icon)}</text>
    <rect x="253" y="43" width="44" height="59" rx="9" fill="#354039"/>
    <rect x="261" y="51" width="28" height="38" rx="5" fill="#b9d1cc"/>
    <path d="M49 42h7v16h-7zm0 43h7v16h-7zm255-39h6v12h-6zm0 39h6v12h-6z" fill="#ffe2a1"/>
  </svg>`;
}
// Create map button per each cart
function renderTruckMap() {
  document.querySelector("#truck-stalls").innerHTML = state.carts.map((cart, index) => `
    <button class="truck-stop stop-${index}" type="button"
      aria-pressed="${cart.id === state.selectedCart}"
      aria-label="Choose ${escapeHtml(cart.name)}, ${escapeHtml(cart.cuisine)}. Pickup in ${escapeHtml(cart.pickup_time)}."
      data-cart="${escapeHtml(cart.id)}"
      title="${escapeHtml(cart.name)}"
      style="--truck-color:${escapeHtml(cart.color)}">
      <span class="truck-stop-name">${escapeHtml(cart.name)}</span>
      <span class="truck-stop-roof">
        <span class="truck-stop-icon" aria-hidden="true">${escapeHtml(cart.icon)}</span>
      </span>
    </button>`).join("");
}

function selectCart(cartId) {
  if (cartId !== state.selectedCart) state.quantities = {};
  state.selectedCart = cartId;
  renderMenu();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function renderMenu() {
  const cart = state.carts.find((entry) => entry.id === state.selectedCart);
  const menuLayout = document.querySelector("#menu-layout");
  const pod = document.querySelector(".pod-map");
  const mapHeading = document.querySelector("#pod-map-title");
  if (!cart) {
    menuLayout.classList.add("hidden");
    pod.classList.remove("hidden");
    mapHeading.classList.remove("hidden");
    return;
  }
  pod.classList.add("hidden");
  mapHeading.classList.add("hidden");
  menuLayout.classList.remove("hidden");
  document.querySelector("#selected-cart-heading").innerHTML = `
    <div class="picked-cart"><span class="picked-cart-icon">${escapeHtml(cart.icon)}</span>
      <span><strong>${escapeHtml(cart.name)}</strong><small>${escapeHtml(cart.cuisine)} · ${escapeHtml(cart.pickup_time)} pickup</small></span></div>
    <button class="back-to-map" type="button" data-map-back>← &nbsp;All food carts</button>`;
  document.querySelector("#order-cart-label").textContent = `PICKING UP FROM ${cart.name.toUpperCase()} · SAMPLE MENU`;
  document.querySelector("#menu-grid").innerHTML = cart.items.map((item) => `
    <article class="menu-item">
      <div class="menu-item-top"><span class="menu-item-icon">${escapeHtml(item.icon)}</span>${item.badge ? `<span class="menu-badge">${escapeHtml(item.badge)}</span>` : ""}</div>
      <h3>${escapeHtml(item.name)}</h3><p>${escapeHtml(item.description)}</p>
      <div class="menu-item-bottom"><span class="menu-item-price">${money(item.price_cents)}</span>
      <button class="add-item" type="button" data-add="${escapeHtml(item.id)}" aria-label="Add ${escapeHtml(item.name)}">+</button></div>
    </article>`).join("");
  renderOrder();
}

function renderOrder() {
  const cart = state.carts.find((entry) => entry.id === state.selectedCart);
  if (!cart) return;
  const items = cart.items.filter((item) => state.quantities[item.id]);
  const count = items.reduce((total, item) => total + state.quantities[item.id], 0);
  const total = items.reduce((sum, item) => sum + item.price_cents * state.quantities[item.id], 0);
  document.querySelector("#cart-empty").classList.toggle("hidden", items.length > 0);
  document.querySelector("#cart-lines").innerHTML = items.map((item) => `
    <div class="cart-line">
      <div class="cart-line-main"><div class="cart-line-name">${escapeHtml(item.name)}</div>
        <div class="cart-line-price">${money(item.price_cents * state.quantities[item.id])}</div></div>
      <div class="quantity-control">
        <button type="button" data-change="${escapeHtml(item.id)}" data-delta="-1" aria-label="Remove one ${escapeHtml(item.name)}">−</button>
        <span>${state.quantities[item.id]}</span>
        <button type="button" data-change="${escapeHtml(item.id)}" data-delta="1" aria-label="Add one ${escapeHtml(item.name)}">+</button>
      </div>
    </div>`).join("");
  document.querySelector("#order-total").textContent = money(total);
  const nameEntered = document.querySelector("#customer-name").value.trim().length > 0;
  document.querySelector("#place-order").disabled = count === 0 || !nameEntered;
}

function renderStationTabs() {
  document.querySelector("#station-tabs").innerHTML = state.carts.map((cart) => `
    <button class="station-tab ${cart.id === state.stationCart ? "active" : ""}" type="button"
      role="tab" aria-selected="${cart.id === state.stationCart}" data-station="${escapeHtml(cart.id)}">
      ${escapeHtml(cart.icon)} &nbsp; ${escapeHtml(cart.name)}
    </button>`).join("");
}
// Display date
function displayTime(timestamp) {
  const date = new Date(`${timestamp.replace(" ", "T")}Z`);
  return new Intl.DateTimeFormat([], { hour: "numeric", minute: "2-digit" }).format(date);
}

function nextStatus(status) {
  return { received: "preparing", preparing: "ready", ready: "completed" }[status] || null;
}

function statusLabel(status) {
  return { received: "New order", preparing: "Preparing", ready: "Ready for pickup", completed: "Completed" }[status];
}

async function loadOrders() {
  const cartId = state.stationCart;
  if (!cartId) return;
  const data = await api(`/api/orders?cart_id=${encodeURIComponent(cartId)}`);
  if (!state.stationMode || cartId !== state.stationCart) return;
  const orders = data.orders;
  const active = orders.filter((order) => order.status !== "completed");
  const completed = orders.filter((order) => order.status === "completed");
  const incoming = orders.filter((order) => order.status === "received");
  document.querySelector("#station-stats").innerHTML = `
    <div class="stat-card"><span>ACTIVE ORDERS</span><strong>${active.length.toString().padStart(2, "0")}</strong></div>
    <div class="stat-card"><span>NEW TO PREPARE</span><strong>${incoming.length.toString().padStart(2, "0")}</strong></div>
    <div class="stat-card"><span>COMPLETED TODAY</span><strong>${completed.length.toString().padStart(2, "0")}</strong></div>`;
  document.querySelector("#queue-title").textContent = `${orders.length} ${orders.length === 1 ? "order" : "orders"} for this cart`;
  document.querySelector("#queue-updated").textContent = `Updated ${new Intl.DateTimeFormat([], { hour: "numeric", minute: "2-digit", second: "2-digit" }).format(new Date())}`;
  if (orders.length === 0) {
    document.querySelector("#order-queue").innerHTML = `<div class="queue-empty"><span>◷</span>No orders just yet. New orders will show up here.</div>`;
    return;
  }
  document.querySelector("#order-queue").innerHTML = orders.map((order) => {
    const next = nextStatus(order.status);
    const button = next ? `<button class="status-action" type="button" data-order="${order.id}" data-status="${next}">${{ preparing: "Start preparing", ready: "Mark ready", completed: "Complete order" }[next]} →</button>` : "";
    return `<article class="queue-order">
      <div class="queue-order-head">
        <div><div class="queue-customer">${escapeHtml(order.customer_name)}</div><span class="queue-code">PICKUP #${escapeHtml(order.pickup_code)} · ${displayTime(order.created_at)}</span></div>
        <span class="status-pill status-${escapeHtml(order.status)}">${statusLabel(order.status)}</span>
      </div>
      <div class="queue-order-items">${order.items.map((item) => `<div class="queue-order-item"><span>${item.quantity} × ${escapeHtml(item.name)}</span><span>${money(item.unit_price_cents * item.quantity)}</span></div>`).join("")}</div>
      <div class="queue-order-foot"><div class="queue-order-total">${money(order.total_cents)}<span class="queue-order-time">Pickup order · #${escapeHtml(order.pickup_code)}</span></div>${button}</div>
    </article>`;
  }).join("");
}

async function setStationMode(enabled) {
  state.stationMode = enabled;
  document.querySelector("#customer-view").classList.toggle("hidden", enabled);
  document.querySelector("#station-view").classList.toggle("hidden", !enabled);
  document.querySelector("#switch-label").textContent = enabled ? "Back to ordering" : "Food cart login";
  document.querySelector("#view-switch").setAttribute("aria-pressed", String(enabled));
  if (enabled) {
    renderStationTabs();
    await loadOrders();
  }
}

async function placeOrder() {
  const button = document.querySelector("#place-order");
  const cart = state.carts.find((entry) => entry.id === state.selectedCart);
  const items = cart.items
    .filter((item) => state.quantities[item.id])
    .map((item) => ({ menu_item_id: item.id, quantity: state.quantities[item.id] }));
  button.disabled = true;
  try {
    const result = await api("/api/orders", {
      method: "POST",
      body: JSON.stringify({
        customer_name: document.querySelector("#customer-name").value.trim(),
        cart_id: cart.id,
        items,
      }),
    });
    state.quantities = {};
    renderOrder();
    showToast(`Order #${result.pickup_code} sent to ${cart.name}. See you at pickup!`);
  } catch (error) {
    showToast(error.message);
    renderOrder();
  }
}

document.querySelector("#selected-cart-heading").addEventListener("click", (event) => {
  if (!event.target.closest("[data-map-back]")) return;
  state.selectedCart = null;
  state.quantities = {};
  renderTruckMap();
  renderMenu();
  window.scrollTo({ top: 0, behavior: "smooth" });
});

document.querySelector("#truck-stalls").addEventListener("click", (event) => {
  const truck = event.target.closest("[data-cart]");
  if (truck) selectCart(truck.dataset.cart);
});

document.querySelector("#menu-grid").addEventListener("click", (event) => {
  const button = event.target.closest("[data-add]");
  if (!button) return;
  const itemId = button.dataset.add;
  state.quantities[itemId] = (state.quantities[itemId] || 0) + 1;
  renderOrder();
});

document.querySelector("#cart-lines").addEventListener("click", (event) => {
  const button = event.target.closest("[data-change]");
  if (!button) return;
  const itemId = button.dataset.change;
  state.quantities[itemId] += Number(button.dataset.delta);
  if (!state.quantities[itemId]) delete state.quantities[itemId];
  renderOrder();
});

document.querySelector("#customer-name").addEventListener("input", renderOrder);
document.querySelector("#place-order").addEventListener("click", placeOrder);
document.querySelector("#view-switch").addEventListener("click", () => {
  setStationMode(!state.stationMode).catch((error) => showToast(error.message));
});

document.querySelector("#station-tabs").addEventListener("click", (event) => {
  const tab = event.target.closest("[data-station]");
  if (!tab) return;
  state.stationCart = tab.dataset.station;
  renderStationTabs();
  loadOrders().catch((error) => showToast(error.message));
});

document.querySelector("#refresh-orders").addEventListener("click", () => {
  loadOrders().catch((error) => showToast(error.message));
});

document.querySelector("#order-queue").addEventListener("click", async (event) => {
  const button = event.target.closest("[data-order]");
  if (!button) return;
  button.disabled = true;
  try {
    await api(`/api/orders/${button.dataset.order}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status: button.dataset.status }),
    });
    await loadOrders();
  } catch (error) {
    button.disabled = false;
    showToast(error.message);
  }
});

async function start() {
  try {
    const data = await api("/api/carts");
    state.carts = data.carts;
    state.selectedCart = null;
    state.stationCart = state.carts[0]?.id ?? null;
    renderTruckMap();
    renderMenu();
  } catch (error) {
    showToast(`Could not connect to the order database: ${error.message}`);
  }
}

setInterval(() => {
  if (state.stationMode) loadOrders().catch((error) => showToast(error.message));
}, 8000);

start();
