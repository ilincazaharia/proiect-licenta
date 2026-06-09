import sqlite3
import os

class DBConnection:
    DB_PATH = "users.db"

    @classmethod
    def get_connection(cls) -> sqlite3.Connection:
        """Returnează o conexiune la baza de date SQLite."""
        return sqlite3.connect(cls.DB_PATH)

    @classmethod
    def init_db(cls):
        """Inițializează tabelele și efectuează migrările dacă este necesar."""
        conn = cls.get_connection()
        cursor = conn.cursor()
        
        # Tabela specializari/sectii
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS specialties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)
        
        # Inserare specializari implicite
        default_specialties = ["Cardiologie", "Neurologie", "Pediatrie", "Chirurgie", "Terapie Intensivă", "Gastroenterologie"]
        for spec in default_specialties:
            cursor.execute("INSERT OR IGNORE INTO specialties (name) VALUES (?)", (spec,))

        # Tabela utilizatori
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nume TEXT NOT NULL,
                prenume TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                role TEXT DEFAULT 'manager',
                specialty_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (specialty_id) REFERENCES specialties(id) ON DELETE SET NULL
            )
        """)
        
        # Tabela rulari simulare
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS simulation_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                run_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                num_doctors INTEGER NOT NULL,
                num_nurses INTEGER NOT NULL,
                arrival_rate REAL NOT NULL,
                peak_multiplier REAL NOT NULL,
                peak_start_min REAL NOT NULL,
                peak_duration_min REAL NOT NULL,
                simulation_duration REAL NOT NULL,
                warmup_period REAL NOT NULL,
                num_replications INTEGER NOT NULL,
                random_seed INTEGER NOT NULL,
                triage_distribution TEXT NOT NULL,
                treatment_times TEXT NOT NULL,
                results_json TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Migrare pentru a adăuga coloanele role și specialty_id dacă nu există deja
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'manager'")
        except sqlite3.OperationalError:
            pass # coloana exista deja
            
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN specialty_id INTEGER")
        except sqlite3.OperationalError:
            pass # coloana exista deja

        conn.commit()
        conn.close()
