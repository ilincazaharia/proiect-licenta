import sqlite3
from typing import Optional, List
from repositories.db_connection import DBConnection
from domain.models import Referral

class ReferralRepository:
    def __init__(self):
        pass

    def _row_to_referral(self, row) -> Referral:
        return Referral(
            id=row[0],
            patient_id=row[1],
            triage_level=row[2],
            specialty=row[3],
            sender_id=row[4],
            receiver_id=row[5],
            status=row[6],
            observatii=row[7],
            response_notes=row[8],
            patient_name=row[9],
            patient_cnp=row[10],
            sender_name=row[11],
            receiver_name=row[12]
        )

    def create(self, referral: Referral) -> bool:
        """Creează o trimitere nouă în starea 'in_asteptare'."""
        try:
            conn = DBConnection.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO referrals (patient_id, triage_level, specialty, sender_id, status, observatii)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                referral.patient_id,
                referral.triage_level,
                referral.specialty,
                referral.sender_id,
                referral.status,
                referral.observatii
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Eroare în ReferralRepository.create: {e}")
            return False

    def get_by_sender_id(self, sender_id: int) -> List[Referral]:
        """Obține istoricul trimiterilor efectuate de un medic de urgențe (sender)."""
        conn = DBConnection.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.id, r.patient_id, r.triage_level, r.specialty, r.sender_id, r.receiver_id, r.status, r.observatii, r.response_notes,
                   (p.prenume || ' ' || p.nume) as patient_name, p.cnp as patient_cnp,
                   (u_send.prenume || ' ' || u_send.nume) as sender_name,
                   (u_rec.prenume || ' ' || u_rec.nume) as receiver_name
            FROM referrals r
            INNER JOIN patients p ON r.patient_id = p.id
            INNER JOIN users u_send ON r.sender_id = u_send.id
            LEFT JOIN users u_rec ON r.receiver_id = u_rec.id
            WHERE r.sender_id = ?
            ORDER BY r.id DESC
        """, (sender_id,))
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_referral(row) for row in rows]

    def get_pending_by_specialty(self, specialty: str) -> List[Referral]:
        """Obține trimiterile aflate în așteptare pentru o secție specializată."""
        conn = DBConnection.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.id, r.patient_id, r.triage_level, r.specialty, r.sender_id, r.receiver_id, r.status, r.observatii, r.response_notes,
                   (p.prenume || ' ' || p.nume) as patient_name, p.cnp as patient_cnp,
                   (u_send.prenume || ' ' || u_send.nume) as sender_name,
                   (u_rec.prenume || ' ' || u_rec.nume) as receiver_name
            FROM referrals r
            INNER JOIN patients p ON r.patient_id = p.id
            INNER JOIN users u_send ON r.sender_id = u_send.id
            LEFT JOIN users u_rec ON r.receiver_id = u_rec.id
            WHERE LOWER(r.specialty) = ? AND r.status = 'in_asteptare'
            ORDER BY r.id ASC
        """, (specialty.lower().strip(),))
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_referral(row) for row in rows]

    def get_accepted_by_specialty(self, specialty: str) -> List[Referral]:
        """Obține pacienții acceptați (internați în prezent) pe o secție specializată."""
        conn = DBConnection.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.id, r.patient_id, r.triage_level, r.specialty, r.sender_id, r.receiver_id, r.status, r.observatii, r.response_notes,
                   (p.prenume || ' ' || p.nume) as patient_name, p.cnp as patient_cnp,
                   (u_send.prenume || ' ' || u_send.nume) as sender_name,
                   (u_rec.prenume || ' ' || u_rec.nume) as receiver_name
            FROM referrals r
            INNER JOIN patients p ON r.patient_id = p.id
            INNER JOIN users u_send ON r.sender_id = u_send.id
            LEFT JOIN users u_rec ON r.receiver_id = u_rec.id
            WHERE LOWER(r.specialty) = ? AND r.status = 'acceptat'
            ORDER BY r.id DESC
        """, (specialty.lower().strip(),))
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_referral(row) for row in rows]

    def update_status(self, referral_id: int, receiver_id: int, status: str, response_notes: str) -> bool:
        """Actualizează starea unei trimiteri (Acceptat/Refuzat) cu note și ID medic primitor."""
        try:
            conn = DBConnection.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE referrals
                SET receiver_id = ?, status = ?, response_notes = ?
                WHERE id = ?
            """, (receiver_id, status, response_notes, referral_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Eroare în ReferralRepository.update_status: {e}")
            return False
