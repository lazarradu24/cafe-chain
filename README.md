# Cafe Chain Management System

A Flask + SQLite web application for managing a multi-location cafe chain. Admins (managers) get a full dashboard with stock alerts, revenue tracking, and menu management per location. Employees can log in to create orders and view their cafe's menu and stock.

---

## Default Accounts

| Username | Password | Role | Location |
|---|---|---|---|
| admin | admin | Admin | — |
| alice | alice123 | Employee | Cafe Central |
| bob | bob123 | Employee | Cafe Central |
| clara | clara123 | Employee | Cafe Riviera |
| david | david123 | Employee | Cafe Bohemia |
| eva | eva123 | Employee | Cafe Bohemia |

---

## Running Locally

**Requirements:** Python 3.8+, pip

```bash
# Install dependencies
pip install flask

# Start the server
python app.py
```

Open http://127.0.0.1:5000 in your browser. The database is created and seeded with sample data automatically on first run. Delete `cafe_chain.db` and restart to reset everything.

---

## Deploying to Heroku

Heroku is a cloud platform that runs your app on a remote server and gives it a public URL. The deployment works through Git — you push your code and Heroku builds and runs it automatically.

### What you need

- A free [Heroku account](https://signup.heroku.com)
- [Git](https://git-scm.com/downloads) installed
- [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) installed

### Step-by-step

**1. Install the Heroku CLI**

Download and run the installer from https://devcenter.heroku.com/articles/heroku-cli, then verify it works:

```bash
heroku --version
```

**2. Log in to Heroku**

```bash
heroku login
```

This opens a browser window. Sign in there and come back to the terminal.

**3. Set up Git in your project folder**

Open a terminal inside your `cafe_v2_new` folder and run:

```bash
git init
git add .
git commit -m "initial commit"
```

**4. Create a Heroku app**

```bash
heroku create cafe-chain-yourname
```

Replace `yourname` with something unique — Heroku app names must be globally unique. This gives you a URL like `https://cafe-chain-yourname.herokuapp.com`.

**5. Deploy**

```bash
git push heroku main
```

Heroku detects it's a Python app, installs the dependencies from `requirements.txt`, and starts the server using the `Procfile`.

**6. Open the app**

```bash
heroku open
```

Or just visit the URL directly in your browser.

### Important note about the database

Heroku's file system is ephemeral — any file written while the app is running (including `cafe_chain.db`) is lost when the server restarts, which happens at least once a day. This means:

- The database is recreated with sample data every time the server restarts.
- Any data entered through the app will be lost on restart.

For a student project and demo purposes this is completely fine — the app will always start up with working data. If you ever need persistent storage, Heroku offers a PostgreSQL add-on, but that requires changing the database connection code.

### Files required for Heroku (already included)

| File | Purpose |
|---|---|
| `Procfile` | Tells Heroku how to start the app (`gunicorn app:app`) |
| `requirements.txt` | Lists Python packages to install (`flask`, `gunicorn`) |
| `runtime.txt` | Specifies the Python version (`python-3.11.9`) |

---

## File Structure

```
cafe_v2_new/
  app.py                     — Flask application and all route handlers
  cafe_chain.db              — SQLite database (created on first run, not committed to Git)
  Procfile                   — Heroku process declaration
  requirements.txt           — Python dependencies
  runtime.txt                — Python version for Heroku
  templates/
    base.html                — Shared layout and navigation
    login.html               — Login page
    dashboard_admin.html     — Admin overview: stats, low-stock alerts, revenue
    dashboard_employee.html  — Employee view: cafe info, orders, menu, colleagues
    cafe_menu.html           — Per-cafe menu and stock management
    cafes.html / cafe_form.html
    employees.html / employee_form.html
    products.html / product_form.html
    orders.html / order_form.html
  ADBS2_Project_Documentation.docx
  README.md
```

---

## Database Schema

```
Cafe          (id, name, address, seat_number)
Employee      (id, name, date_of_birth, position, salary, cafe_id → Cafe)
Product       (id, name, price, category)
Cafe_Product  (cafe_id → Cafe, product_id → Product, stock)
Orders        (id, date, state, total, cafe_id → Cafe, employee_id → Employee)
Order_Product (order_id → Orders, product_id → Product, quantity, unit_price)
users         (id, username, password, role, employee_id → Employee)
```

Foreign keys are enforced on every connection with `PRAGMA foreign_keys = ON`.

---

## Key Behaviours

- **Per-cafe stock:** each cafe holds its own inventory count. Placing an order deducts from that cafe's stock only. Deleting an order restores the stock.
- **Cascade deletes:** deleting a cafe removes its employees, orders, and stock entries. Deleting an employee removes their orders and account. Deleting a product removes it from all cafe menus and order records.
- **Low-stock alerts:** any product with fewer than 20 units triggers a warning on the admin dashboard, with a one-click Refill button that adds 100 units.
- **Role separation:** access control is enforced at the route level in Python, not just in the UI.
- **Passwords:** stored as SHA-256 hashes.
