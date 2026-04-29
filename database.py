import sqlite3

DATABASE_FILE = "inventar.db"

def get_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produse (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nume TEXT NOT NULL,
            categorie TEXT NOT NULL,
            pret REAL NOT NULL,
            stoc INTEGER NOT NULL
        )
    """)

    conn.commit()
    conn.close()
    print("Table created successfully!")

def seed_data():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM produse")
    count = cursor.fetchone()[0]

    if count > 0:
        print("Data already exists!")
        conn.close()
        return

    produse = [
        ("Lapte Zuzu 1L", "Lactate", 6.99, 150),
        ("Iaurt Danone 400g", "Lactate", 8.49, 80),
        ("Branza telemea 500g", "Lactate", 18.99, 45),
        ("Paine alba 500g", "Panificatie", 4.99, 200),
        ("Croissant cu ciocolata", "Panificatie", 3.49, 120),
        ("Piept de pui 1kg", "Carne", 24.99, 60),
        ("Muschi de porc 1kg", "Carne", 32.99, 40),
        ("Mere Golden 1kg", "Fructe", 7.99, 100),
        ("Banane 1kg", "Fructe", 8.99, 90),
        ("Rosii 1kg", "Legume", 9.99, 75),
        ("Cartofi 2kg", "Legume", 6.49, 110),
        ("Apa plata Borsec 2L", "Bauturi", 4.99, 300),
        ("Coca-Cola 2L", "Bauturi", 12.99, 150),
        ("Ulei Bunica 1L", "Conserve", 14.99, 85),
        ("Orez Panda 1kg", "Conserve", 8.99, 95),
        ("Detergent Ariel 2kg", "Curatenie", 49.99, 30),
        ("Sampon Head&Shoulders", "Ingrijire", 24.99, 50),
        ("Cafea Jacobs 250g", "Cafea", 29.99, 70),
        ("Ciocolata Milka 100g", "Dulciuri", 8.99, 200),
        ("Chips-uri Lays 150g", "Snacks", 9.99, 180),
    ]

    cursor.executemany("""
        INSERT INTO produse (nume, categorie, pret, stoc)
        VALUES (?, ?, ?, ?)
    """, produse)

    conn.commit()
    conn.close()
    print(f"{len(produse)} products added successfully!")

def search_products(query):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM produse
        WHERE nume LIKE ? OR categorie LIKE ?
    """, (f"%{query}%", f"%{query}%"))

    results = cursor.fetchall()
    conn.close()
    return results

def get_all_products():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM produse ORDER BY categorie, nume")
    results = cursor.fetchall()
    conn.close()
    return results

def get_database_schema():
    schema = """
    Table: produse
    Columns:
        - id (INTEGER, PRIMARY KEY, AUTOINCREMENT)
        - nume (TEXT) - product name
        - categorie (TEXT) - product category
        - pret (REAL) - price in RON
        - stoc (INTEGER) - current stock quantity
    """
    return schema.strip()

def get_inventory_stats():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total_products FROM produse")
    total = cursor.fetchone()["total_products"]

    cursor.execute("SELECT SUM(pret * stoc) as total_value FROM produse")
    total_value = cursor.fetchone()["total_value"]

    cursor.execute("SELECT categorie, COUNT(*) as count, SUM(stoc) as total_stoc FROM produse GROUP BY categorie")
    by_category = cursor.fetchall()

    cursor.execute("SELECT * FROM produse WHERE stoc < 50 ORDER BY stoc ASC")
    low_stock = cursor.fetchall()

    conn.close()
    return {
        "total_products": total,
        "total_inventory_value": round(total_value, 2),
        "by_category": [dict(row) for row in by_category],
        "low_stock_items": [dict(row) for row in low_stock]
    }

def execute_sql(sql, params=None):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)

        if sql.strip().upper().startswith("SELECT"):
            results = cursor.fetchall()
            conn.close()
            return [dict(row) for row in results]
        else:
            conn.commit()
            affected = cursor.rowcount
            conn.close()
            return {"affected_rows": affected}

    except Exception as e:
        conn.close()
        return {"error": str(e)}


def execute_sql_batch(statements):
    """
    Execute a list of SQL statements atomically (single transaction).

    Each statement must be a single SQL statement (no semicolon-separated scripts).
    Returns {"results": [...]} on success or {"error": "..."} on failure (rolled back).
    """
    conn = get_connection()
    cursor = conn.cursor()
    results = []

    try:
        conn.execute("BEGIN")

        for sql in statements:
            cursor.execute(sql)

            if sql.strip().upper().startswith("SELECT"):
                rows = cursor.fetchall()
                results.append([dict(row) for row in rows])
            else:
                results.append({"affected_rows": cursor.rowcount})

        conn.commit()
        conn.close()
        return {"results": results}

    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        conn.close()
        return {"error": str(e)}

if __name__ == "__main__":
    create_tables()
    seed_data()
