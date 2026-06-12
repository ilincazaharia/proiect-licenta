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
        """Inițializează tabelele."""
        conn = cls.get_connection()
        cursor = conn.cursor()
        
        # Tabela utilizatori
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                last_name TEXT NOT NULL,
                first_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                role TEXT DEFAULT 'manager'
            )
        """)

        # Tabela specializări
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS specialties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)

        # Tabela medici
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS doctors (
                user_id INTEGER PRIMARY KEY,
                specialty_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (specialty_id) REFERENCES specialties(id)
            )
        """)

        # Tabela pacienți
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cnp TEXT UNIQUE NOT NULL,
                last_name TEXT NOT NULL,
                first_name TEXT NOT NULL
            )
        """)

        # Tabela trimiteri 
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                triage_level TEXT NOT NULL,
                specialty_id INTEGER NOT NULL,
                sender_id INTEGER NOT NULL,
                receiver_id INTEGER,
                status TEXT DEFAULT 'in_asteptare',
                observations TEXT,
                response_notes TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
                FOREIGN KEY (specialty_id) REFERENCES specialties(id),
                FOREIGN KEY (sender_id) REFERENCES users(id),
                FOREIGN KEY (receiver_id) REFERENCES users(id)
            )
        """)

        # Tabela loguri pacienți
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patient_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
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

        # Populează specializările dacă nu există
        cursor.execute("SELECT COUNT(*) FROM specialties")
        if cursor.fetchone()[0] == 0:
            default_specs = [
                "Urgențe",
                "Cardiologie",
                "Neurologie",
                "Pediatrie",
                "Chirurgie",
                "Terapie Intensivă",
                "Gastroenterologie"
            ]
            for spec in default_specs:
                cursor.execute("INSERT INTO specialties (name) VALUES (?)", (spec,))

        conn.commit()
        conn.close()
