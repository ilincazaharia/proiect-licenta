import sqlite3
from typing import Optional, List
from repositories.db_connection import DBConnection
from domain.models import User

class UserRepository:
    def __init__(self):
        pass

    def _row_to_user(self, row) -> User:
        """Helper pentru conversia unui rând din baza de date în obiect User."""
        return User(
            id=row[0],
            nume=row[1],
            prenume=row[2],
            email=row[3],
            role=row[4],
            specialty=row[5]
        )

    def get_by_email(self, email: str) -> Optional[User]:
        """Caută un utilizator după email (cu JOIN pe tabela doctors pentru specializare)."""
        conn = DBConnection.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.nume, u.prenume, u.email, u.role, d.specialty
            FROM users u
            LEFT JOIN doctors d ON u.id = d.user_id
            WHERE LOWER(u.email) = ?
        """, (email.lower().strip(),))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_user(row)
        return None

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Caută un utilizator după ID."""
        conn = DBConnection.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.nume, u.prenume, u.email, u.role, d.specialty
            FROM users u
            LEFT JOIN doctors d ON u.id = d.user_id
            WHERE u.id = ?
        """, (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_user(row)
        return None

    def get_password_info_by_email(self, email: str) -> Optional[tuple]:
        """Returnează (password_hash, salt) pentru validarea parolei."""
        conn = DBConnection.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash, salt FROM users WHERE LOWER(email) = ?", (email.lower().strip(),))
        row = cursor.fetchone()
        conn.close()
        return row

    def create(self, user: User, password_hash: str, salt: str) -> bool:
        """Creează un utilizator nou și, dacă este medic, îi asociază specializarea în doctors."""
        try:
            conn = DBConnection.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (nume, prenume, email, password_hash, salt, role)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user.nume.strip(),
                user.prenume.strip(),
                user.email.lower().strip(),
                password_hash,
                salt,
                user.role
            ))
            
            user_id = cursor.lastrowid
            
            # Dacă rolul este de medic, inserăm și în tabela doctors
            if user.role in ('medic_urgente', 'medic_sectie') and user.specialty:
                cursor.execute("""
                    INSERT INTO doctors (user_id, specialty)
                    VALUES (?, ?)
                """, (user_id, user.specialty))
                
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Eroare în UserRepository.create: {e}")
            return False

    def get_all_doctors(self) -> List[User]:
        """Returnează toți medicii (cu specializarea extrasă din doctors)."""
        conn = DBConnection.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.nume, u.prenume, u.email, u.role, d.specialty
            FROM users u
            INNER JOIN doctors d ON u.id = d.user_id
            WHERE u.role IN ('medic_urgente', 'medic_sectie')
            ORDER BY u.id DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_user(row) for row in rows]

    def delete_doctor(self, doctor_id: int) -> bool:
        """Șterge un medic (cascade de pe users șterge și din doctors)."""
        try:
            conn = DBConnection.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ? AND role IN ('medic_urgente', 'medic_sectie')", (doctor_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Eroare în UserRepository.delete_doctor: {e}")
            return False
