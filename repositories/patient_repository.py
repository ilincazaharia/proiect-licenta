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
            last_name=row[2],
            first_name=row[3]
        )

    def create(self, patient: PatientEntity) -> bool:
        """Adaugă un pacient nou în baza de date."""
        try:
            conn = DBConnection.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO patients (cnp, last_name, first_name)
                VALUES (?, ?, ?)
            """, (patient.cnp.strip(), patient.last_name.strip(), patient.first_name.strip()))
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
        cursor.execute("SELECT id, cnp, last_name, first_name FROM patients WHERE cnp = ?", (cnp.strip(),))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_patient(row)
        return None

    def get_by_id(self, patient_id: int) -> Optional[PatientEntity]:
        """Caută un pacient după ID."""
        conn = DBConnection.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, cnp, last_name, first_name FROM patients WHERE id = ?", (patient_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_patient(row)
        return None

    def get_all(self) -> List[PatientEntity]:
        """Obține toți pacienții."""
        conn = DBConnection.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, cnp, last_name, first_name FROM patients ORDER BY last_name ASC, first_name ASC")
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_patient(row) for row in rows]

    def add_log(self, patient_id: int, event_type: str, details: str) -> bool:
        """Adaugă o înregistrare în logul pacientului."""
        try:
            conn = DBConnection.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO patient_logs (patient_id, event_type, details)
                VALUES (?, ?, ?)
            """, (patient_id, event_type, details))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Eroare în PatientRepository.add_log: {e}")
            return False

    def get_logs(self, patient_id: int) -> List[dict]:
        """Obține toate logurile pentru un pacient, sortate descrescător după timestamp (cele mai recente primele)."""
        try:
            conn = DBConnection.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, patient_id, event_type, details, datetime(timestamp, 'localtime') as local_ts
                FROM patient_logs
                WHERE patient_id = ?
                ORDER BY timestamp DESC, id DESC
            """, (patient_id,))
            rows = cursor.fetchall()
            conn.close()
            return [
                {
                    "id": r[0],
                    "patient_id": r[1],
                    "event_type": r[2],
                    "details": r[3],
                    "timestamp": r[4]
                }
                for r in rows
            ]
        except Exception as e:
            print(f"Eroare în PatientRepository.get_logs: {e}")
            return []

    def get_current_status(self, patient_id: int) -> str:
        """Determină starea curentă a pacientului pe baza ultimului log înregistrat."""
        try:
            conn = DBConnection.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT event_type FROM patient_logs
                WHERE patient_id = ?
                ORDER BY timestamp DESC, id DESC
                LIMIT 1
            """, (patient_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return row[0]
            return "externat"
        except Exception as e:
            print(f"Eroare în PatientRepository.get_current_status: {e}")
            return "externat"
