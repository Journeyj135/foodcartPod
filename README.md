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
