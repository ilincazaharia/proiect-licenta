import hashlib
import os
import re
from typing import Optional, Tuple
from repositories.user_repository import UserRepository
from domain.models import User

class AuthService:
    def __init__(self, user_repository: Optional[UserRepository] = None):
        self.user_repo = user_repository or UserRepository()

    def generate_salt(self) -> str:
        """Generează un salt unic"""
        return os.urandom(16).hex()

    def hash_password(self, password: str, salt: str) -> str:
        """Criptează parola folosind SHA-256 și salt."""
        return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

    def is_valid_email(self, email: str) -> bool:
        """Validează formatul adresei de e-mail."""
        pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        return bool(re.match(pattern, email))

    def register_user(self, last_name: str, first_name: str, email: str, password: str, role: str = 'manager', specialty_id: Optional[int] = None) -> Tuple[bool, str]:
        """
        Înregistrează un utilizator nou cu validările necesare.
        Returnează (succes, mesaj).
        """
        last_name = last_name.strip()
        first_name = first_name.strip()
        email = email.lower().strip()

        if not last_name or not first_name:
            return False, "Numele și prenumele sunt obligatorii."
        
        if not self.is_valid_email(email):
            return False, "Formatul adresei de e-mail nu este valid."
        
        if len(password) < 6:
            return False, "Parola trebuie să aibă cel puțin 6 caractere."
        
        # Verificare existență utilizator
        existing_user = self.user_repo.get_by_email(email)
        if existing_user is not None:
            return False, "Această adresă de e-mail este deja înregistrată."

        salt = self.generate_salt()
        pwd_hash = self.hash_password(password, salt)

        new_user = User(
            id=None,
            last_name=last_name,
            first_name=first_name,
            email=email,
            role=role,
            specialty_id=specialty_id
        )

        success = self.user_repo.create(new_user, pwd_hash, salt)
        if success:
            return True, "Înregistrarea a fost efectuată cu succes."
        return False, "Eroare internă la salvarea utilizatorului."

    def verify_user(self, email: str, password: str) -> Tuple[bool, Optional[User]]:
        """Verifică datele de autentificare."""
        email = email.lower().strip()
        pwd_info = self.user_repo.get_password_info_by_email(email)
        
        if not pwd_info:
            return False, None

        pwd_hash, salt = pwd_info
        calculated_hash = self.hash_password(password, salt)

        if calculated_hash == pwd_hash:
            user = self.user_repo.get_by_email(email)
            return True, user
        
        return False, None
