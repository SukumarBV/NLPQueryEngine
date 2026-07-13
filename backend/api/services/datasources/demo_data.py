"""
Builds a small, deterministic, realistic-looking demo database entirely
offline (no network calls, no external downloads). Used by DemoDataSource
so a recruiter can try the app with zero setup.
"""
import random
import sqlite3
from datetime import date, timedelta

FIRST_NAMES = [
    "Olivia", "Liam", "Emma", "Noah", "Ava", "Ethan", "Sophia", "Mason",
    "Isabella", "James", "Mia", "Benjamin", "Charlotte", "Lucas", "Amelia",
    "Henry", "Harper", "Alexander", "Evelyn", "Daniel", "Abigail", "Michael",
    "Ella", "Elijah", "Scarlett", "Jacob", "Grace", "William", "Chloe", "Owen",
]
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Clark", "Lewis", "Walker",
]
DEPARTMENTS = ["Engineering", "Sales", "Marketing", "Human Resources", "Finance"]
TITLES = {
    "Engineering": ["Software Engineer", "Senior Engineer", "Engineering Manager", "QA Engineer"],
    "Sales": ["Account Executive", "Sales Manager", "SDR", "Regional Sales Director"],
    "Marketing": ["Marketing Specialist", "Content Strategist", "Marketing Manager", "SEO Analyst"],
    "Human Resources": ["HR Generalist", "Recruiter", "HR Manager"],
    "Finance": ["Financial Analyst", "Accountant", "Finance Manager"],
}
REGIONS = ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East"]
PRODUCT_CATALOG = [
    ("Aurora Laptop 14", "Electronics", 1299.00),
    ("Aurora Laptop 16", "Electronics", 1599.00),
    ("Zenith Wireless Mouse", "Accessories", 39.99),
    ("Zenith Mechanical Keyboard", "Accessories", 89.99),
    ("Nimbus 27in Monitor", "Electronics", 349.00),
    ("Nimbus 4K Monitor", "Electronics", 549.00),
    ("Pulse Noise-Cancelling Headphones", "Audio", 199.00),
    ("Pulse Earbuds", "Audio", 129.00),
    ("Vertex Standing Desk", "Furniture", 429.00),
    ("Vertex Ergo Chair", "Furniture", 349.00),
    ("Cascade Webcam HD", "Accessories", 59.99),
    ("Cascade Ring Light", "Accessories", 34.99),
    ("Summit Portable SSD 1TB", "Storage", 119.00),
    ("Summit Portable SSD 2TB", "Storage", 199.00),
    ("Halo Smart Speaker", "Audio", 89.00),
    ("Halo Smart Display", "Audio", 149.00),
    ("Drift Backpack Pro", "Accessories", 79.00),
    ("Drift Laptop Sleeve", "Accessories", 24.99),
    ("Orbit Docking Station", "Accessories", 149.00),
    ("Orbit USB-C Hub", "Accessories", 44.99),
    ("Lumen Desk Lamp", "Furniture", 49.99),
    ("Lumen Monitor Light Bar", "Furniture", 59.99),
    ("Cove Router Mesh System", "Networking", 249.00),
    ("Cove Wifi Extender", "Networking", 69.00),
    ("Trail Fitness Tracker", "Wearables", 99.00),
]
ORDER_STATUSES = ["completed", "completed", "completed", "completed", "shipped", "processing", "cancelled"]

SEED = 42
START_DATE = date(2025, 1, 1)
END_DATE = date(2026, 6, 30)


def _random_date(rng: random.Random, start: date, end: date) -> date:
    delta_days = (end - start).days
    return start + timedelta(days=rng.randint(0, delta_days))


def build_demo_database(db_path: str) -> None:
    """Creates and populates the demo SQLite database at db_path. Idempotent-ish: overwrites any existing file."""
    rng = random.Random(SEED)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.executescript(
        """
        PRAGMA foreign_keys = ON;

        DROP TABLE IF EXISTS sales;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS employees;
        DROP TABLE IF EXISTS departments;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS customers;

        CREATE TABLE departments (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        );

        CREATE TABLE employees (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            title TEXT NOT NULL,
            department_id INTEGER NOT NULL,
            salary NUMERIC NOT NULL,
            hire_date TEXT NOT NULL,
            FOREIGN KEY (department_id) REFERENCES departments(id)
        );

        CREATE TABLE customers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            region TEXT NOT NULL,
            signup_date TEXT NOT NULL
        );

        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price NUMERIC NOT NULL
        );

        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            order_date TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        );

        CREATE TABLE sales (
            id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price NUMERIC NOT NULL,
            revenue NUMERIC NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );
        """
    )

    # Departments
    for i, dept in enumerate(DEPARTMENTS, start=1):
        cur.execute("INSERT INTO departments (id, name) VALUES (?, ?)", (i, dept))

    # Employees (~30)
    used_emails = set()

    def unique_email(first, last, domain="demo-corp.example"):
        base = f"{first}.{last}".lower()
        email = f"{base}@{domain}"
        n = 2
        while email in used_emails:
            email = f"{base}{n}@{domain}"
            n += 1
        used_emails.add(email)
        return email

    employee_id = 1
    for _ in range(30):
        first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
        dept_index = rng.randint(1, len(DEPARTMENTS))
        dept_name = DEPARTMENTS[dept_index - 1]
        title = rng.choice(TITLES[dept_name])
        salary = rng.randint(55, 165) * 1000
        hire_date = _random_date(rng, date(2019, 1, 1), date(2026, 3, 1))
        cur.execute(
            "INSERT INTO employees (id, name, email, title, department_id, salary, hire_date) VALUES (?,?,?,?,?,?,?)",
            (employee_id, f"{first} {last}", unique_email(first, last), title, dept_index, salary, hire_date.isoformat()),
        )
        employee_id += 1

    # Customers (~50)
    customer_id = 1
    for _ in range(50):
        first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
        region = rng.choice(REGIONS)
        signup_date = _random_date(rng, date(2023, 1, 1), date(2026, 5, 1))
        cur.execute(
            "INSERT INTO customers (id, name, email, region, signup_date) VALUES (?,?,?,?,?)",
            (customer_id, f"{first} {last}", unique_email(first, last, "customer.example"), region, signup_date.isoformat()),
        )
        customer_id += 1

    # Products
    for i, (name, category, price) in enumerate(PRODUCT_CATALOG, start=1):
        cur.execute("INSERT INTO products (id, name, category, price) VALUES (?,?,?,?)", (i, name, category, price))
    num_products = len(PRODUCT_CATALOG)

    # Orders (~120) + Sales line items (~250)
    sale_id = 1
    for order_id in range(1, 121):
        cust_id = rng.randint(1, customer_id - 1)
        order_date = _random_date(rng, START_DATE, END_DATE)
        status = rng.choice(ORDER_STATUSES)
        cur.execute(
            "INSERT INTO orders (id, customer_id, order_date, status) VALUES (?,?,?,?)",
            (order_id, cust_id, order_date.isoformat(), status),
        )

        for _ in range(rng.randint(1, 3)):
            product_id = rng.randint(1, num_products)
            unit_price = PRODUCT_CATALOG[product_id - 1][2]
            quantity = rng.randint(1, 4)
            revenue = round(unit_price * quantity, 2)
            cur.execute(
                "INSERT INTO sales (id, order_id, product_id, quantity, unit_price, revenue) VALUES (?,?,?,?,?,?)",
                (sale_id, order_id, product_id, quantity, unit_price, revenue),
            )
            sale_id += 1

    conn.commit()
    conn.close()
