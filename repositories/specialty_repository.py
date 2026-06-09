import sqlite3
from typing import Optional, List
from repositories.db_connection import DBConnection
from domain.models import Specialty

class SpecialtyRepository:
    def __init__(self):
        pass

    def get_all(self) -> List[Specialty]:
        """Returnează toate specializările din baza de date."""
        conn = DBConnection.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM specialties ORDER BY name ASC")
        rows = cursor.fetchall()
        conn.close()
        
        return [Specialty(id=row[0], name=row[1]) for row in rows]

    def get_by_id(self, specialty_id: int) -> Optional[Specialty]:
        """Returnează o specializare după ID."""
        conn = DBConnection.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM specialties WHERE id = ?", (specialty_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return Specialty(id=row[0], name=row[1])
        return None
