import sqlite3
import hashlib
import os
import re

DB_PATH = "users.db"

import json

def init_db():
    """Inițializează baza de date SQLite și creează tabelele necesare."""
    conn = sqlite3.connect(DB_PATH)
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

def generate_salt():
    """Generează un salt unic pentru hash-ul parolei."""
    return os.urandom(16).hex()

def hash_password(password, salt):
    """Criptează parola folosind SHA-256 și salt."""
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

def is_valid_email(email):
    """Validează formatul adresei de e-mail."""
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return bool(re.match(pattern, email))

def user_exists(email):
    """Verifică dacă un e-mail este deja înregistrat."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email.lower().strip(),))
    user = cursor.fetchone()
    conn.close()
    return user is not None

def register_user(nume, prenume, email, password, role='manager', specialty_id=None):
    """
    Înregistrează un utilizator nou cu rol și specializare opțională.
    Returnează (succes: bool, mesaj: str).
    """
    nume = nume.strip()
    prenume = prenume.strip()
    email = email.lower().strip()

    if not nume or not prenume:
        return False, "Numele și prenumele sunt obligatorii."
    
    if not is_valid_email(email):
        return False, "Formatul adresei de e-mail nu este valid."
    
    if len(password) < 6:
        return False, "Parola trebuie să aibă cel puțin 6 caractere."
    
    if user_exists(email):
        return False, "Această adresă de e-mail este deja înregistrată."

    try:
        salt = generate_salt()
        pwd_hash = hash_password(password, salt)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (nume, prenume, email, password_hash, salt, role, specialty_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (nume, prenume, email, pwd_hash, salt, role, specialty_id)
        )
        conn.commit()
        conn.close()
        return True, "Înregistrarea a fost efectuată cu succes."
    except Exception as e:
        return False, f"Eroare la înregistrare: {str(e)}"

def verify_user(email, password):
    """
    Verifică datele de autentificare ale utilizatorului.
    Returnează (succes: bool, date_utilizator: dict sau None).
    """
    email = email.lower().strip()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.nume, u.prenume, u.password_hash, u.salt, u.role, s.name as specialty 
        FROM users u
        LEFT JOIN specialties s ON u.specialty_id = s.id
        WHERE u.email = ?
    """, (email,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return False, None

    user_id, nume, prenume, pwd_hash, salt, role, specialty = row
    calculated_hash = hash_password(password, salt)

    if calculated_hash == pwd_hash:
        return True, {
            "id": user_id,
            "email": email,
            "nume": nume,
            "prenume": prenume,
            "role": role,
            "specialty": specialty
        }
    
    return False, None

def get_all_specialties():
    """Returnează toate specializările din baza de date."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM specialties ORDER BY name ASC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"Eroare la citirea specializărilor: {e}")
        return []

def get_all_doctors():
    """Returnează toți medicii înregistrați în baza de date (cu specializarea lor)."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.nume, u.prenume, u.email, u.role, s.name as specialty, u.created_at
            FROM users u
            LEFT JOIN specialties s ON u.specialty_id = s.id
            WHERE u.role IN ('medic_urgente', 'medic_sectie')
            ORDER BY u.created_at DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"Eroare la citirea medicilor din baza de date: {e}")
        return []

def delete_doctor(doctor_id):
    """Șterge un cont de medic din baza de date."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ? AND role IN ('medic_urgente', 'medic_sectie')", (doctor_id,))
        conn.commit()
        conn.close()
        return True, "Contul de medic a fost șters cu succes."
    except Exception as e:
        return False, f"Eroare la ștergerea contului de medic: {str(e)}"

def save_simulation_run(user_id, run_name, config_data, results_data):
    """
    Salvează o rulare de simulare (configurație + rezultate) în baza de date.
    Returnează (succes: bool, mesaj: str).
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO simulation_runs (
                user_id, run_name, num_doctors, num_nurses, arrival_rate, 
                peak_multiplier, peak_start_min, peak_duration_min, 
                simulation_duration, warmup_period, num_replications, random_seed, 
                triage_distribution, treatment_times, results_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            run_name,
            config_data.num_doctors,
            config_data.num_nurses,
            config_data.arrival_rate,
            config_data.peak_multiplier,
            config_data.peak_start_min,
            config_data.peak_duration_min,
            config_data.simulation_duration,
            config_data.warmup_period,
            config_data.num_replications,
            config_data.random_seed,
            json.dumps(config_data.triage_distribution),
            json.dumps(config_data.treatment_times),
            json.dumps(results_data)
        ))
        conn.commit()
        conn.close()
        return True, "Simularea a fost salvată în baza de date cu succes."
    except Exception as e:
        return False, f"Eroare la salvarea simulării: {str(e)}"

def get_user_simulation_runs(user_id):
    """
    Returnează toate simulările salvate pentru un utilizator dat.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, run_name, created_at, num_doctors, num_nurses, arrival_rate, 
                   peak_multiplier, peak_start_min, peak_duration_min, 
                   simulation_duration, warmup_period, num_replications, random_seed, 
                   triage_distribution, treatment_times, results_json
            FROM simulation_runs
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user_id,))
        rows = cursor.fetchall()
        
        runs = []
        for r in rows:
            run = dict(r)
            
            # Deserializare cu restaurarea tipurilor de chei potrivite (int)
            triage_dist = json.loads(run['triage_distribution'])
            run['triage_distribution'] = {int(k): float(v) for k, v in triage_dist.items()}
            
            treatment_t = json.loads(run['treatment_times'])
            run['treatment_times'] = {int(k): tuple(map(int, v)) for k, v in treatment_t.items()}
            
            run['results_json'] = json.loads(run['results_json'])
            runs.append(run)
            
        conn.close()
        return runs
    except Exception as e:
        print(f"Eroare la citirea simulărilor din baza de date: {e}")
        return []

def delete_simulation_run(run_id, user_id):
    """
    Șterge o rulare de simulare din baza de date.
    Returnează (succes: bool, mesaj: str).
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM simulation_runs WHERE id = ? AND user_id = ?", (run_id, user_id))
        conn.commit()
        conn.close()
        return True, "Simularea a fost ștearsă cu succes."
    except Exception as e:
        return False, f"Eroare la ștergerea simulării: {str(e)}"

# Inițializare automată la import
init_db()
