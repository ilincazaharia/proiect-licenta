import sqlite3
from typing import Optional, List
from repositories.db_connection import DBConnection
from domain.models import PatientEntity

class PatientRepository:
    def __init__(self):
        pass

    def _row_to_patient(self, row) -> PatientEntity:
        return PatientEntity(
            id=row[0],
            cnp=row[1],
            nume=row[2],
            prenume=row[3]
        )

    def create(self, patient: PatientEntity) -> bool:
        """Adaugă un pacient nou în baza de date."""
        try:
            conn = DBConnection.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO patients (cnp, nume, prenume)
                VALUES (?, ?, ?)
            """, (patient.cnp.strip(), patient.nume.strip(), patient.prenume.strip()))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Eroare în PatientRepository.create: {e}")
            return False

    def get_by_cnp(self, cnp: str) -> Optional[PatientEntity]:
        """Caută un pacient după CNP."""
        conn = DBConnection.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, cnp, nume, prenume FROM patients WHERE cnp = ?", (cnp.strip(),))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_patient(row)
        return None

    def get_by_id(self, patient_id: int) -> Optional[PatientEntity]:
        """Caută un pacient după ID."""
        conn = DBConnection.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, cnp, nume, prenume FROM patients WHERE id = ?", (patient_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_patient(row)
        return None

    def get_all(self) -> List[PatientEntity]:
        """Obține toți pacienții."""
        conn = DBConnection.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, cnp, nume, prenume FROM patients ORDER BY nume ASC, prenume ASC")
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_patient(row) for row in rows]
