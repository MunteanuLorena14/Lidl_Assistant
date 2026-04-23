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
    print("Tabel creat cu succes!")

def seed_data():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM produse")
    count = cursor.fetchone()[0]
    
    if count > 0:
        print("Datele există deja!")
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
    print(f"Au fost adăugate {len(produse)} produse!")

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

if __name__ == "__main__":
    create_tables()
    seed_data()
    
    # Test search
    # print("\nTest căutare 'Lactate':")
    # rezultate = search_products("Lactate")
    # for produs in rezultate:
    #     print(f"  {produs['nume']} - {produs['pret']} RON - Stoc: {produs['stoc']}")