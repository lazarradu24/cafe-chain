from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3, hashlib
from functools import wraps
from datetime import date

app = Flask(__name__)
app.secret_key = "cafechain_secret_2024"
DB = "cafe_chain.db"

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS Cafe (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
            address TEXT NOT NULL, seat_number INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS Employee (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
            date_of_birth TEXT NOT NULL, position TEXT NOT NULL,
            salary REAL NOT NULL, cafe_id INTEGER NOT NULL,
            FOREIGN KEY (cafe_id) REFERENCES Cafe(id));
        CREATE TABLE IF NOT EXISTS Product (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
            price REAL NOT NULL, category TEXT NOT NULL DEFAULT 'Other');
        CREATE TABLE IF NOT EXISTS Cafe_Product (
            cafe_id INTEGER NOT NULL, product_id INTEGER NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (cafe_id, product_id),
            FOREIGN KEY (cafe_id) REFERENCES Cafe(id),
            FOREIGN KEY (product_id) REFERENCES Product(id));
        CREATE TABLE IF NOT EXISTS Orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT NOT NULL,
            state TEXT NOT NULL DEFAULT 'pending'
                CHECK(state IN ('pending','in-progress','completed','cancelled')),
            total REAL NOT NULL DEFAULT 0,
            cafe_id INTEGER NOT NULL, employee_id INTEGER NOT NULL,
            FOREIGN KEY (cafe_id) REFERENCES Cafe(id),
            FOREIGN KEY (employee_id) REFERENCES Employee(id));
        CREATE TABLE IF NOT EXISTS Order_Product (
            order_id INTEGER NOT NULL, product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1, unit_price REAL NOT NULL DEFAULT 0,
            PRIMARY KEY (order_id, product_id),
            FOREIGN KEY (order_id) REFERENCES Orders(id),
            FOREIGN KEY (product_id) REFERENCES Product(id));
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'employee'
                CHECK(role IN ('admin','employee')),
            employee_id INTEGER UNIQUE,
            FOREIGN KEY (employee_id) REFERENCES Employee(id));
        """)
        db.execute("INSERT OR IGNORE INTO users (username,password,role) VALUES (?,?,?)",
                   ("admin", hash_pw("admin"), "admin"))
        if db.execute("SELECT COUNT(*) FROM Cafe").fetchone()[0] == 0:
            db.executescript("""
            INSERT INTO Cafe (name, address, seat_number) VALUES
                ('Cafe Central',  '12 Main Street, Prague',     40),
                ('Cafe Riviera',  '5 Harbour Road, Brno',       25),
                ('Cafe Bohemia',  '88 Old Town Square, Ostrava', 60);
            INSERT INTO Employee (name, date_of_birth, position, salary, cafe_id) VALUES
                ('Alice Novak', '1990-03-15','Manager',2800.00,1),
                ('Bob Krejci',  '1995-07-22','Barista',1600.00,1),
                ('Clara Mares', '1988-11-01','Manager',2900.00,2),
                ('David Horak', '1997-05-30','Barista',1500.00,3),
                ('Eva Blaha',   '1993-09-14','Waiter', 1400.00,3);
            INSERT INTO Product (name, price, category) VALUES
                ('Espresso',     2.50,'Drinks'),('Cappuccino',3.20,'Drinks'),
                ('Latte',        3.50,'Drinks'),('Hot Chocolate',3.80,'Drinks'),
                ('Croissant',    2.00,'Food'),  ('Cheesecake',4.50,'Food'),
                ('Sandwich',     5.00,'Food'),  ('Muffin',2.80,'Food');
            INSERT INTO Cafe_Product (cafe_id, product_id, stock) VALUES
                (1,1,200),(1,2,8),(1,3,120),(1,5,5),(1,6,40),
                (2,1,100),(2,2,90),(2,4,12),(2,6,3),(2,7,50),
                (3,1,180),(3,2,130),(3,3,7),(3,5,75),(3,7,55),(3,8,4);
            """)
            for uname, pw, eid in [("alice","alice123",1),("bob","bob123",2),
                                    ("clara","clara123",3),("david","david123",4),("eva","eva123",5)]:
                db.execute("INSERT OR IGNORE INTO users (username,password,role,employee_id) VALUES (?,?,?,?)",
                           (uname, hash_pw(pw), "employee", eid))
            db.execute("INSERT INTO Orders (date,state,total,cafe_id,employee_id) VALUES ('2024-05-01','completed',12.20,1,1)")
            db.execute("INSERT INTO Orders (date,state,total,cafe_id,employee_id) VALUES ('2024-05-02','completed',8.50,1,2)")
            db.execute("INSERT INTO Orders (date,state,total,cafe_id,employee_id) VALUES ('2024-05-03','completed',15.70,2,3)")
            db.execute("INSERT INTO Orders (date,state,total,cafe_id,employee_id) VALUES ('2024-05-04','in-progress',6.00,3,4)")
            db.execute("INSERT INTO Orders (date,state,total,cafe_id,employee_id) VALUES ('2024-05-05','pending',0.00,3,5)")
            db.execute("INSERT INTO Order_Product VALUES (1,1,2,2.50)")
            db.execute("INSERT INTO Order_Product VALUES (1,5,1,2.00)")
            db.execute("INSERT INTO Order_Product VALUES (1,6,1,4.50)")
            db.execute("INSERT INTO Order_Product VALUES (2,2,1,3.20)")
            db.execute("INSERT INTO Order_Product VALUES (2,5,2,2.00)")
            db.execute("INSERT INTO Order_Product VALUES (3,3,2,3.50)")
            db.execute("INSERT INTO Order_Product VALUES (3,6,2,4.50)")
            db.execute("INSERT INTO Order_Product VALUES (3,7,1,5.00)")
            db.execute("INSERT INTO Order_Product VALUES (4,1,1,2.50)")
            db.execute("INSERT INTO Order_Product VALUES (4,2,1,3.50)")
            db.execute("INSERT INTO Order_Product VALUES (5,4,1,0.00)")

def login_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if "user_id" not in session: return redirect(url_for("login"))
        return f(*a, **kw)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if "user_id" not in session: return redirect(url_for("login"))
        if session.get("role") != "admin":
            flash("Access denied.", "danger")
            return redirect(url_for("dashboard"))
        return f(*a, **kw)
    return wrapper

def current_user():
    return {"id":session.get("user_id"),"username":session.get("username"),
            "role":session.get("role"),"employee_id":session.get("employee_id"),
            "cafe_id":session.get("cafe_id")}

@app.route("/", methods=["GET","POST"])
def login():
    if "user_id" in session: return redirect(url_for("dashboard"))
    if request.method == "POST":
        u, p = request.form["username"].strip(), request.form["password"]
        row = get_db().execute(
            "SELECT u.*, e.cafe_id FROM users u LEFT JOIN Employee e ON e.id=u.employee_id "
            "WHERE u.username=? AND u.password=?", (u, hash_pw(p))).fetchone()
        if row:
            session.update({"user_id":row["id"],"username":row["username"],
                            "role":row["role"],"employee_id":row["employee_id"],"cafe_id":row["cafe_id"]})
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("login"))

@app.route("/employees/create-account/<int:employee_id>", methods=["GET","POST"])
@admin_required
def create_account(employee_id):
    db  = get_db()
    emp = db.execute("SELECT e.*, c.name AS cafe_name FROM Employee e JOIN Cafe c ON c.id=e.cafe_id WHERE e.id=?", (employee_id,)).fetchone()
    if not emp: flash("Employee not found.", "danger"); return redirect(url_for("employees"))
    if db.execute("SELECT id FROM users WHERE employee_id=?", (employee_id,)).fetchone():
        flash(f"{emp['name']} already has an account.", "warning"); return redirect(url_for("employees"))
    if request.method == "POST":
        u, p, p2 = request.form["username"].strip(), request.form["password"], request.form["password2"]
        if not u or not p: flash("All fields are required.", "danger")
        elif p != p2: flash("Passwords do not match.", "danger")
        else:
            try:
                with db: db.execute("INSERT INTO users (username,password,role,employee_id) VALUES (?,?,?,?)", (u, hash_pw(p), "employee", employee_id))
                flash(f"Account created for {emp['name']}.", "success"); return redirect(url_for("employees"))
            except: flash("Username already taken.", "danger")
    return render_template("create_account.html", emp=emp, u=current_user())

@app.route("/dashboard")
@login_required
def dashboard():
    u, db = current_user(), get_db()
    if u["role"] == "admin":
        stats = {
            "cafes":     db.execute("SELECT COUNT(*) FROM Cafe").fetchone()[0],
            "employees": db.execute("SELECT COUNT(*) FROM Employee").fetchone()[0],
            "products":  db.execute("SELECT COUNT(*) FROM Product").fetchone()[0],
            "orders":    db.execute("SELECT COUNT(*) FROM Orders").fetchone()[0],
            "revenue":   db.execute("SELECT COALESCE(SUM(total),0) FROM Orders WHERE state='completed'").fetchone()[0],
            "pending":   db.execute("SELECT COUNT(*) FROM Orders WHERE state IN ('pending','in-progress')").fetchone()[0],
            "low_stock": db.execute("SELECT COUNT(*) FROM Cafe_Product WHERE stock < 20").fetchone()[0],
        }
        return render_template("dashboard_admin.html", stats=stats,
            revenue_by_cafe=db.execute("SELECT c.name, COALESCE(SUM(o.total),0) AS rev FROM Cafe c LEFT JOIN Orders o ON o.cafe_id=c.id AND o.state='completed' GROUP BY c.id ORDER BY rev DESC").fetchall(),
            recent_orders=db.execute("SELECT o.id,o.date,o.state,o.total,c.name AS cafe,e.name AS emp FROM Orders o JOIN Cafe c ON c.id=o.cafe_id JOIN Employee e ON e.id=o.employee_id ORDER BY o.date DESC LIMIT 8").fetchall(),
            low_stock=db.execute("SELECT p.id AS product_id,cp.cafe_id,p.name,c.name AS cafe_name,cp.stock FROM Cafe_Product cp JOIN Product p ON p.id=cp.product_id JOIN Cafe c ON c.id=cp.cafe_id WHERE cp.stock<20 ORDER BY cp.stock").fetchall(),
            cafe_stock_summary=db.execute("SELECT c.id,c.name,COUNT(cp.product_id) AS product_count,COALESCE(SUM(cp.stock),0) AS total_stock,SUM(CASE WHEN cp.stock<20 THEN 1 ELSE 0 END) AS low_items FROM Cafe c LEFT JOIN Cafe_Product cp ON cp.cafe_id=c.id GROUP BY c.id ORDER BY c.name").fetchall(),
            u=u)
    else:
        emp = db.execute("SELECT e.*,c.name AS cafe_name,c.address AS cafe_address,c.seat_number FROM Employee e JOIN Cafe c ON c.id=e.cafe_id WHERE e.id=?", (u["employee_id"],)).fetchone()
        return render_template("dashboard_employee.html", emp=emp,
            emp_orders=db.execute("SELECT o.id,o.date,o.state,o.total,COUNT(op.product_id) AS items FROM Orders o LEFT JOIN Order_Product op ON op.order_id=o.id WHERE o.employee_id=? GROUP BY o.id ORDER BY o.date DESC LIMIT 10", (u["employee_id"],)).fetchall(),
            my_stats={"my_orders":db.execute("SELECT COUNT(*) FROM Orders WHERE employee_id=?",(u["employee_id"],)).fetchone()[0],
                      "my_revenue":db.execute("SELECT COALESCE(SUM(total),0) FROM Orders WHERE employee_id=? AND state='completed'",(u["employee_id"],)).fetchone()[0],
                      "open_orders":db.execute("SELECT COUNT(*) FROM Orders WHERE employee_id=? AND state IN ('pending','in-progress')",(u["employee_id"],)).fetchone()[0]},
            cafe_menu=db.execute("SELECT p.name,p.category,p.price,cp.stock FROM Cafe_Product cp JOIN Product p ON p.id=cp.product_id WHERE cp.cafe_id=? ORDER BY p.category,p.name",(u["cafe_id"],)).fetchall(),
            colleagues=db.execute("SELECT name,position FROM Employee WHERE cafe_id=? AND id!=? ORDER BY name",(u["cafe_id"],u["employee_id"])).fetchall(),
            u=u)

@app.route("/cafes")
@admin_required
def cafes():
    return render_template("cafes.html", u=current_user(), cafes=get_db().execute(
        "SELECT c.*,COUNT(DISTINCT e.id) AS emp_count,COALESCE(SUM(CASE WHEN o.state='completed' THEN o.total ELSE 0 END),0) AS revenue FROM Cafe c LEFT JOIN Employee e ON e.cafe_id=c.id LEFT JOIN Orders o ON o.cafe_id=c.id GROUP BY c.id").fetchall())

@app.route("/cafes/add", methods=["GET","POST"])
@admin_required
def add_cafe():
    if request.method == "POST":
        with get_db() as db:
            db.execute("INSERT INTO Cafe (name,address,seat_number) VALUES (?,?,?)",
                       (request.form["name"],request.form["address"],request.form["seat_number"]))
        flash("Cafe added.", "success"); return redirect(url_for("cafes"))
    return render_template("cafe_form.html", cafe=None, u=current_user())

@app.route("/cafes/edit/<int:id>", methods=["GET","POST"])
@admin_required
def edit_cafe(id):
    db = get_db()
    if request.method == "POST":
        with db: db.execute("UPDATE Cafe SET name=?,address=?,seat_number=? WHERE id=?",
                            (request.form["name"],request.form["address"],request.form["seat_number"],id))
        flash("Cafe updated.", "success"); return redirect(url_for("cafes"))
    return render_template("cafe_form.html", cafe=db.execute("SELECT * FROM Cafe WHERE id=?",(id,)).fetchone(), u=current_user())

@app.route("/cafes/delete/<int:id>")
@admin_required
def delete_cafe(id):
    db = get_db()
    with db:
        for oid, in db.execute("SELECT id FROM Orders WHERE cafe_id=?", (id,)).fetchall():
            db.execute("DELETE FROM Order_Product WHERE order_id=?", (oid,))
        db.execute("DELETE FROM Orders WHERE cafe_id=?", (id,))
        db.execute("DELETE FROM Cafe_Product WHERE cafe_id=?", (id,))
        for eid, in db.execute("SELECT id FROM Employee WHERE cafe_id=?", (id,)).fetchall():
            db.execute("DELETE FROM users WHERE employee_id=?", (eid,))
        db.execute("DELETE FROM Employee WHERE cafe_id=?", (id,))
        db.execute("DELETE FROM Cafe WHERE id=?", (id,))
    flash("Cafe and all related records deleted.", "warning"); return redirect(url_for("cafes"))

@app.route("/cafes/<int:cafe_id>/menu", methods=["GET","POST"])
@admin_required
def cafe_menu(cafe_id):
    db   = get_db()
    cafe = db.execute("SELECT * FROM Cafe WHERE id=?", (cafe_id,)).fetchone()
    if not cafe: flash("Cafe not found.", "danger"); return redirect(url_for("cafes"))
    if request.method == "POST":
        action = request.form.get("action")
        if action == "update_stock":
            with db: db.execute("UPDATE Cafe_Product SET stock=? WHERE cafe_id=? AND product_id=?",
                                (int(request.form["stock"]),cafe_id,int(request.form["product_id"])))
            flash("Stock updated.", "success")
        elif action == "refill":
            with db: db.execute("UPDATE Cafe_Product SET stock=stock+100 WHERE cafe_id=? AND product_id=?",
                                (cafe_id,int(request.form["product_id"])))
            flash("Stock refilled by 100 units.", "success")
        elif action == "add_product":
            try:
                with db: db.execute("INSERT INTO Cafe_Product (cafe_id,product_id,stock) VALUES (?,?,?)",
                                    (cafe_id,int(request.form["product_id"]),int(request.form.get("stock",0))))
                flash("Product added to menu.", "success")
            except: flash("Product is already on this cafe's menu.", "warning")
        elif action == "remove_product":
            with db: db.execute("DELETE FROM Cafe_Product WHERE cafe_id=? AND product_id=?",
                                (cafe_id,int(request.form["product_id"])))
            flash("Product removed from menu.", "warning")
        return redirect(url_for("cafe_menu", cafe_id=cafe_id))
    return render_template("cafe_menu.html", cafe=cafe, u=current_user(),
        menu=db.execute("SELECT p.id,p.name,p.category,p.price,cp.stock FROM Cafe_Product cp JOIN Product p ON p.id=cp.product_id WHERE cp.cafe_id=? ORDER BY p.category,p.name",(cafe_id,)).fetchall(),
        available=db.execute("SELECT p.id,p.name,p.category,p.price FROM Product p WHERE p.id NOT IN (SELECT product_id FROM Cafe_Product WHERE cafe_id=?) ORDER BY p.category,p.name",(cafe_id,)).fetchall())

@app.route("/stock/refill", methods=["POST"])
@admin_required
def refill_stock():
    with get_db() as db:
        db.execute("UPDATE Cafe_Product SET stock=stock+100 WHERE cafe_id=? AND product_id=?",
                   (int(request.form["cafe_id"]),int(request.form["product_id"])))
    flash("Stock refilled by 100 units.", "success"); return redirect(url_for("dashboard"))

@app.route("/employees")
@admin_required
def employees():
    return render_template("employees.html", u=current_user(), employees=get_db().execute(
        "SELECT e.*,c.name AS cafe_name,CASE WHEN u.id IS NOT NULL THEN 1 ELSE 0 END AS has_account FROM Employee e JOIN Cafe c ON c.id=e.cafe_id LEFT JOIN users u ON u.employee_id=e.id ORDER BY c.name,e.name").fetchall())

@app.route("/employees/add", methods=["GET","POST"])
@admin_required
def add_employee():
    db = get_db()
    if request.method == "POST":
        with db: db.execute("INSERT INTO Employee (name,date_of_birth,position,salary,cafe_id) VALUES (?,?,?,?,?)",
                            (request.form["name"],request.form["dob"],request.form["position"],request.form["salary"],request.form["cafe_id"]))
        flash("Employee added.", "success"); return redirect(url_for("employees"))
    return render_template("employee_form.html", emp=None, cafes=db.execute("SELECT id,name FROM Cafe").fetchall(), u=current_user())

@app.route("/employees/edit/<int:id>", methods=["GET","POST"])
@admin_required
def edit_employee(id):
    db = get_db()
    if request.method == "POST":
        with db: db.execute("UPDATE Employee SET name=?,date_of_birth=?,position=?,salary=?,cafe_id=? WHERE id=?",
                            (request.form["name"],request.form["dob"],request.form["position"],request.form["salary"],request.form["cafe_id"],id))
        flash("Employee updated.", "success"); return redirect(url_for("employees"))
    return render_template("employee_form.html", emp=db.execute("SELECT * FROM Employee WHERE id=?",(id,)).fetchone(),
                           cafes=db.execute("SELECT id,name FROM Cafe").fetchall(), u=current_user())

@app.route("/employees/delete/<int:id>")
@admin_required
def delete_employee(id):
    db = get_db()
    with db:
        for oid, in db.execute("SELECT id FROM Orders WHERE employee_id=?", (id,)).fetchall():
            db.execute("DELETE FROM Order_Product WHERE order_id=?", (oid,))
        db.execute("DELETE FROM Orders WHERE employee_id=?", (id,))
        db.execute("DELETE FROM users WHERE employee_id=?", (id,))
        db.execute("DELETE FROM Employee WHERE id=?", (id,))
    flash("Employee deleted.", "warning"); return redirect(url_for("employees"))

@app.route("/products")
@login_required
def products():
    u, db = current_user(), get_db()
    rows = db.execute("SELECT p.*,COUNT(cp.cafe_id) AS cafe_count FROM Product p LEFT JOIN Cafe_Product cp ON cp.product_id=p.id GROUP BY p.id ORDER BY p.category,p.name").fetchall() if u["role"]=="admin" else \
           db.execute("SELECT p.*,cp.stock FROM Product p JOIN Cafe_Product cp ON cp.product_id=p.id WHERE cp.cafe_id=? ORDER BY p.category,p.name",(u["cafe_id"],)).fetchall()
    return render_template("products.html", products=rows, u=u)

@app.route("/products/add", methods=["GET","POST"])
@admin_required
def add_product():
    if request.method == "POST":
        with get_db() as db: db.execute("INSERT INTO Product (name,price,category) VALUES (?,?,?)",
                                        (request.form["name"],request.form["price"],request.form["category"]))
        flash("Product added.", "success"); return redirect(url_for("products"))
    return render_template("product_form.html", product=None, u=current_user())

@app.route("/products/edit/<int:id>", methods=["GET","POST"])
@admin_required
def edit_product(id):
    db = get_db()
    if request.method == "POST":
        with db: db.execute("UPDATE Product SET name=?,price=?,category=? WHERE id=?",
                            (request.form["name"],request.form["price"],request.form["category"],id))
        flash("Product updated.", "success"); return redirect(url_for("products"))
    return render_template("product_form.html", product=db.execute("SELECT * FROM Product WHERE id=?",(id,)).fetchone(), u=current_user())

@app.route("/products/delete/<int:id>")
@admin_required
def delete_product(id):
    db = get_db()
    with db:
        db.execute("DELETE FROM Order_Product WHERE product_id=?", (id,))
        db.execute("DELETE FROM Cafe_Product WHERE product_id=?", (id,))
        db.execute("DELETE FROM Product WHERE id=?", (id,))
    flash("Product deleted.", "warning"); return redirect(url_for("products"))

@app.route("/orders")
@login_required
def orders():
    u, db = current_user(), get_db()
    q = "SELECT o.*,c.name AS cafe_name,e.name AS emp_name,COUNT(op.product_id) AS item_count FROM Orders o JOIN Cafe c ON c.id=o.cafe_id JOIN Employee e ON e.id=o.employee_id LEFT JOIN Order_Product op ON op.order_id=o.id"
    rows = db.execute(q+" GROUP BY o.id ORDER BY o.date DESC").fetchall() if u["role"]=="admin" else \
           db.execute(q+" WHERE o.employee_id=? GROUP BY o.id ORDER BY o.date DESC",(u["employee_id"],)).fetchall()
    return render_template("orders.html", orders=rows, u=u)

@app.route("/orders/add", methods=["GET","POST"])
@login_required
def add_order():
    u, db = current_user(), get_db()
    cafes     = db.execute("SELECT id,name FROM Cafe").fetchall() if u["role"]=="admin" else db.execute("SELECT id,name FROM Cafe WHERE id=?",(u["cafe_id"],)).fetchall()
    employees = db.execute("SELECT id,name,cafe_id FROM Employee").fetchall() if u["role"]=="admin" else db.execute("SELECT id,name,cafe_id FROM Employee WHERE id=?",(u["employee_id"],)).fetchall()
    products  = db.execute("SELECT id,name,price,category FROM Product ORDER BY category,name").fetchall() if u["role"]=="admin" else \
                db.execute("SELECT p.id,p.name,p.price,p.category,cp.stock FROM Product p JOIN Cafe_Product cp ON cp.product_id=p.id WHERE cp.cafe_id=? ORDER BY p.category,p.name",(u["cafe_id"],)).fetchall()
    if request.method == "POST":
        pids,qtys = request.form.getlist("product_ids"),request.form.getlist("quantities")
        cafe_id   = request.form.get("cafe_id") or u["cafe_id"]
        emp_id    = request.form.get("employee_id") or u["employee_id"]
        with db:
            cur   = db.execute("INSERT INTO Orders (date,state,total,cafe_id,employee_id) VALUES (?,?,0,?,?)",
                               (request.form["date"],request.form["state"],cafe_id,emp_id))
            oid   = cur.lastrowid; total = 0.0
            for pid,qty in zip(pids,qtys):
                if pid and int(qty)>0:
                    price = db.execute("SELECT price FROM Product WHERE id=?",(pid,)).fetchone()["price"]
                    db.execute("INSERT OR IGNORE INTO Order_Product VALUES (?,?,?,?)",(oid,pid,qty,price))
                    total += price*int(qty)
                    db.execute("UPDATE Cafe_Product SET stock=stock-? WHERE cafe_id=? AND product_id=?",(qty,cafe_id,pid))
            db.execute("UPDATE Orders SET total=? WHERE id=?",(total,oid))
        flash(f"Order #{oid} created. Total: {total:.2f} EUR","success"); return redirect(url_for("orders"))
    return render_template("order_form.html",order=None,cafes=cafes,employees=employees,products=products,order_products=[],u=u,today=date.today().isoformat())

@app.route("/orders/edit/<int:id>", methods=["GET","POST"])
@login_required
def edit_order(id):
    u, db = current_user(), get_db()
    order = db.execute("SELECT * FROM Orders WHERE id=?",(id,)).fetchone()
    if u["role"]=="employee" and order["employee_id"]!=u["employee_id"]:
        flash("You can only edit your own orders.","danger"); return redirect(url_for("orders"))
    cafes     = db.execute("SELECT id,name FROM Cafe").fetchall() if u["role"]=="admin" else db.execute("SELECT id,name FROM Cafe WHERE id=?",(u["cafe_id"],)).fetchall()
    employees = db.execute("SELECT id,name,cafe_id FROM Employee").fetchall() if u["role"]=="admin" else db.execute("SELECT id,name,cafe_id FROM Employee WHERE id=?",(u["employee_id"],)).fetchall()
    products  = db.execute("SELECT id,name,price,category FROM Product ORDER BY category,name").fetchall() if u["role"]=="admin" else \
                db.execute("SELECT p.id,p.name,p.price,p.category,cp.stock FROM Product p JOIN Cafe_Product cp ON cp.product_id=p.id WHERE cp.cafe_id=? ORDER BY p.category,p.name",(u["cafe_id"],)).fetchall()
    if request.method == "POST":
        pids,qtys = request.form.getlist("product_ids"),request.form.getlist("quantities")
        cafe_id   = request.form.get("cafe_id") or u["cafe_id"]
        emp_id    = request.form.get("employee_id") or u["employee_id"]
        old_items = db.execute("SELECT product_id,quantity FROM Order_Product WHERE order_id=?",(id,)).fetchall()
        with db:
            for item in old_items:
                db.execute("UPDATE Cafe_Product SET stock=stock+? WHERE cafe_id=? AND product_id=?",(item["quantity"],order["cafe_id"],item["product_id"]))
            db.execute("DELETE FROM Order_Product WHERE order_id=?",(id,))
            total=0.0
            for pid,qty in zip(pids,qtys):
                if pid and int(qty)>0:
                    price=db.execute("SELECT price FROM Product WHERE id=?",(pid,)).fetchone()["price"]
                    db.execute("INSERT INTO Order_Product VALUES (?,?,?,?)",(id,pid,qty,price))
                    total+=price*int(qty)
                    db.execute("UPDATE Cafe_Product SET stock=stock-? WHERE cafe_id=? AND product_id=?",(qty,cafe_id,pid))
            db.execute("UPDATE Orders SET date=?,state=?,total=?,cafe_id=?,employee_id=? WHERE id=?",
                       (request.form["date"],request.form["state"],total,cafe_id,emp_id,id))
        flash("Order updated.","success"); return redirect(url_for("orders"))
    return render_template("order_form.html",order=order,cafes=cafes,employees=employees,products=products,
                           order_products=db.execute("SELECT product_id,quantity FROM Order_Product WHERE order_id=?",(id,)).fetchall(),
                           u=u,today=date.today().isoformat())

@app.route("/orders/delete/<int:id>")
@login_required
def delete_order(id):
    u, db = current_user(), get_db()
    order = db.execute("SELECT * FROM Orders WHERE id=?",(id,)).fetchone()
    if u["role"]=="employee" and order["employee_id"]!=u["employee_id"]:
        flash("You can only delete your own orders.","danger"); return redirect(url_for("orders"))
    with db:
        for item in db.execute("SELECT product_id,quantity FROM Order_Product WHERE order_id=?",(id,)).fetchall():
            db.execute("UPDATE Cafe_Product SET stock=stock+? WHERE cafe_id=? AND product_id=?",(item["quantity"],order["cafe_id"],item["product_id"]))
        db.execute("DELETE FROM Order_Product WHERE order_id=?",(id,))
        db.execute("DELETE FROM Orders WHERE id=?",(id,))
    flash("Order deleted.","warning"); return redirect(url_for("orders"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
