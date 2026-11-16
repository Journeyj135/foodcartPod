# Cartside

A neighborhood food-cart ordering app. Customers can browse vendors at Food Carts, build an order for one cart, and send it to that cart's local order queue. Food-cart staff can view their own queue, advance orders through preparation, and mark pickups complete.

Orders, menu items, and cart information are stored in a local SQLite database. The database is created automatically the first time the server starts.

## Run it

1. Open a terminal in this folder.
   cd pods/foodcartPod/foodcartPod
2. Run `python app.py`.
3. Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.
4. Select **Food cart login** to open the cart dashboard and choose a cart.

Python 3.9 or newer is required. The server uses only Python's standard library; no package installation is necessary. To stop the server, press **Ctrl+C** in the terminal.

The homepage shows six clickable food carts surrounding a central Gresham Food Carts building. Each cart opens its own sample menu; the illustration is self-contained and does not load external map tiles.

The seeded carts are Shawarma Chef, E-San Thai Cuisine, Gothic Bites, El Punto Venezolano, Xanos Mexican Food, and Wingz N Thingz. All menu items and prices are examples, not verified current vendor menus.

The SQLite database is saved as `food_cart_orders.sqlite3` next to `app.py`. Keep this file to keep orders between restarts.

# Functions

#### Updates the page to show the food cart map or the selected carts menu.

```js
function renderMenu() {
  const cart = state.carts.find((entry) => entry.id === state.selectedCart);
  const menuLayout = document.querySelector("#menu-layout");
  const pod = document.querySelector(".pod-map");
  if (!cart) {
    menuLayout.classList.add("hidden");
    pod.classList.remove("hidden");
    return;
  }
  pod.classList.add("hidden");
  menuLayout.classList.remove("hidden");
  document.querySelector("#selected-cart-heading").innerHTML = `
    <div class="picked-cart"><span class="picked-cart-icon">${escapeHtml(cart.icon)}</span>
      <span><strong>${escapeHtml(cart.name)}</strong><small>${escapeHtml(cart.cuisine)} · ${escapeHtml(cart.pickup_time)} pickup</small></span></div>
    <button class="back-to-map" type="button" data-map-back>← &nbsp;All food carts</button>`;
  document.querySelector("#order-cart-label").textContent =
    `PICKING UP FROM ${cart.name.toUpperCase()} · SAMPLE MENU`;
  document.querySelector("#menu-grid").innerHTML = cart.items
    .map(
      (item) => `
    <article class="menu-item">
      <div class="menu-item-top"><span class="menu-item-icon">${escapeHtml(item.icon)}</span>${item.badge ? `<span class="menu-badge">${escapeHtml(item.badge)}</span>` : ""}</div>
      <h3>${escapeHtml(item.name)}</h3><p>${escapeHtml(item.description)}</p>
      <div class="menu-item-bottom"><span class="menu-item-price">${money(item.price_cents)}</span>
      <button class="add-item" type="button" data-add="${escapeHtml(item.id)}" aria-label="Add ${escapeHtml(item.name)}">+</button></div>
    </article>`,
    )
    .join("");
  renderOrder();
}
```

#### Calculates the order summary for the current selected food cart when quantity and name are enabled

```js
function renderOrder() {
  const cart = state.carts.find((entry) => entry.id === state.selectedCart);
  if (!cart) return;
  const items = cart.items.filter((item) => state.quantities[item.id]);
  const count = items.reduce(
    (total, item) => total + state.quantities[item.id],
    0,
  );
  const total = items.reduce(
    (sum, item) => sum + item.price_cents * state.quantities[item.id],
    0,
  );
  document
    .querySelector("#cart-empty")
    .classList.toggle("hidden", items.length > 0);
  document.querySelector("#cart-lines").innerHTML = items
    .map(
      (item) => `
    <div class="cart-line">
      <div class="cart-line-main"><div class="cart-line-name">${escapeHtml(item.name)}</div>
        <div class="cart-line-price">${money(item.price_cents * state.quantities[item.id])}</div></div>
      <div class="quantity-control">
        <button type="button" data-change="${escapeHtml(item.id)}" data-delta="-1" aria-label="Remove one ${escapeHtml(item.name)}">−</button>
        <span>${state.quantities[item.id]}</span>
        <button type="button" data-change="${escapeHtml(item.id)}" data-delta="1" aria-label="Add one ${escapeHtml(item.name)}">+</button>
      </div>
    </div>`,
    )
    .join("");
  document.querySelector("#order-total").textContent = money(total);
  const nameEntered =
    document.querySelector("#customer-name").value.trim().length > 0;
  document.querySelector("#place-order").disabled = count === 0 || !nameEntered;
}
```

#### Displays the carts icon and name as Active or inactive

```js
function renderStationTabs() {
  document.querySelector("#station-tabs").innerHTML = state.carts
    .map(
      (cart) => `
    <button class="station-tab ${cart.id === state.stationCart ? "active" : ""}" type="button"
      role="tab" aria-selected="${cart.id === state.stationCart}" data-station="${escapeHtml(cart.id)}">
      ${escapeHtml(cart.icon)} &nbsp; ${escapeHtml(cart.name)}
    </button>`,
    )
    .join("");
}
```

#### Gets the Orders from the selected food cart and shows on screen

```js
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
  document.querySelector("#queue-title").textContent =
    `${orders.length} ${orders.length === 1 ? "order" : "orders"} for this cart`;
  document.querySelector("#queue-updated").textContent =
    `Updated ${new Intl.DateTimeFormat([], { hour: "numeric", minute: "2-digit", second: "2-digit" }).format(new Date())}`;
  if (orders.length === 0) {
    document.querySelector("#order-queue").innerHTML =
      `<div class="queue-empty"><span>◷</span>No orders just yet. New orders will show up here.</div>`;
    return;
  }
  document.querySelector("#order-queue").innerHTML = orders
    .map((order) => {
      const next = nextStatus(order.status);
      const button = next
        ? `<button class="status-action" type="button" data-order="${order.id}" data-status="${next}">${{ preparing: "Start preparing", ready: "Mark ready", completed: "Complete order" }[next]} →</button>`
        : "";
      return `<article class="queue-order">
      <div class="queue-order-head">
        <div><div class="queue-customer">${escapeHtml(order.customer_name)}</div><span class="queue-code">PICKUP #${escapeHtml(order.pickup_code)} · ${displayTime(order.created_at)}</span></div>
        <span class="status-pill status-${escapeHtml(order.status)}">${statusLabel(order.status)}</span>
      </div>
      <div class="queue-order-items">${order.items.map((item) => `<div class="queue-order-item"><span>${item.quantity} × ${escapeHtml(item.name)}</span><span>${money(item.unit_price_cents * item.quantity)}</span></div>`).join("")}</div>
      <div class="queue-order-foot"><div class="queue-order-total">${money(order.total_cents)}<span class="queue-order-time">Pickup order · #${escapeHtml(order.pickup_code)}</span></div>${button}</div>
    </article>`;
    })
    .join("");
}
```
