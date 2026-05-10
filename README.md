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

## Deploying to Railway

Railway is a cloud platform that runs your app on a remote server and gives it a public URL. Deployment works by connecting a GitHub repository — no CLI tools required.

### What you need

- A free [GitHub account](https://github.com)
- A free [Railway account](https://railway.app) (sign in with GitHub)

### Step-by-step

**1. Create a GitHub repository**

Go to github.com, create a new repository named `cafe-chain`, and upload all project files except `cafe_chain.db` (the database is created automatically on first run). Commit the files.

**2. Connect Railway to GitHub**

Go to [railway.app](https://railway.app), sign in with GitHub, then click:

```
New Project → Deploy from GitHub repo → select cafe-chain → Deploy
```

Railway reads the `Procfile`, installs dependencies from `requirements.txt`, and starts the server automatically.

**3. Open the app**

Go to your project in Railway → **Settings → Domains → Generate Domain**. Railway gives you a public URL following the pattern:

```
https://cafe-chain-yourname.up.railway.app
```

### Important note about the database

Railway's file system is ephemeral — any file written while the app is running is lost when the container restarts. This means the SQLite database is recreated with sample data on each restart. The `init_db()` function is called at module level so the database is always initialised when the server starts.

For a student project and demo this is completely fine — the app always starts in a working state. If persistent storage is needed, Railway offers a PostgreSQL plugin, but that would require updating the database connection code.

### Files required for Railway (already included)

| File | Purpose |
|---|---|
| `Procfile` | Tells Railway how to start the app (`gunicorn app:app`) |
| `requirements.txt` | Lists Python packages to install (`flask`, `gunicorn`) |
| `runtime.txt` | Specifies the Python version (`python-3.11.9`) |

---

## File Structure

```
cafe_v4/
  app.py                     — Flask application and all route handlers
  cafe_chain.db              — SQLite database (created on first run, not committed to Git)
  Procfile                   — Railway process declaration
  requirements.txt           — Python dependencies
  runtime.txt                — Python version for Railway
  templates/
    base.html                — Shared layout and navigation
    login.html               — Login page
    dashboard_admin.html     — Admin overview: stats, low-stock alerts, revenue
    dashboard_employee.html  — Employee view: cafe info, orders, personal stats
    cafe_menu.html           — Per-cafe menu and stock management
    cafes.html / cafe_form.html
    employees.html / employee_form.html
    products.html / product_form.html
    orders.html / order_form.html
    create_account.html      — Admin creates account for an employee
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
- **Role separation:** admins have full CRUD on all entities; employees can only see and manage their own orders and their cafe's menu. Access control is enforced at the route level in Python, not just in the UI.
- **Account management:** only admins can create employee accounts, via the Create Account button on the Employees page.
- **Low-stock alerts:** any product with fewer than 20 units triggers a warning on the admin dashboard.
- **Passwords:** stored as SHA-256 hashes.
