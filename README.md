# Cartside

A neighborhood food-cart ordering app. Customers can browse vendors at Gresham Food Carts, build an order for one cart, and send it to that cart's local order queue. Food-cart staff can view their own queue, advance orders through preparation, and mark pickups complete.

Orders, menu items, and cart information are stored in a local SQLite database. The database is created automatically the first time the server starts.

## Run it

1. Open a terminal in this folder.
2. Run `python app.py`.
3. Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.
4. Select **Food cart login** to open the cart dashboard and choose a cart.

Python 3.9 or newer is required. The server uses only Python's standard library; no package installation is necessary. To stop the server, press **Ctrl+C** in the terminal.

The homepage shows an original, self-contained illustration of the food-cart pod rather than a full street map. It does not load external map tiles.

The active cart names are based on Google Maps listings at the supplied address checked on November 12, 2026: Shawarma Chef, E-San Thai Cuisine, Xanos Mexican Food, El Punto Venezolano, and Healthy Panda. Flatliners Grill was listed as temporarily closed and is not included. The menu items and prices in this prototype are examples, not verified current vendor menus.

The SQLite database is saved as `food_cart_orders.sqlite3` next to `app.py`. Keep this file to keep orders between restarts.
