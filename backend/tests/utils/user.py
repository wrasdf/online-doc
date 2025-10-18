
import random
import string
from typing import Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.schemas.user import UserCreate
from src.services.user_service import UserService
from src.services.auth_service import AuthService


def random_lower_string(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=length))


def random_email() -> str:
    return f"{random_lower_string()}@{random_lower_string()}.com"


def random_password() -> str:
    return random_lower_string(12)


async def create_random_user(db_session: AsyncSession, username: str = None, email: str = None) -> Tuple[User, dict]:
    """
    Create a random user and return the user object and auth headers.
    """ 
    if email is None:
        email = random_email()
    if username is None:
        username = random_lower_string(12)
    password = random_password()
    user_in = UserCreate(username=username, email=email, password=password)
    user = await UserService.create_user(db_session, user_in)
    token = AuthService.create_access_token(data={"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}
    return user, headers
