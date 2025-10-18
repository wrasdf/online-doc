from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.models.user import User
from src.schemas.user import UserCreate
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    @staticmethod
    def verify_password(plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password):
        return pwd_context.hash(password)

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str):
        result = await db.execute(select(User).filter(User.email == email))
        return result.scalars().first()

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int):
        result = await db.execute(select(User).filter(User.id == user_id))
        return result.scalars().first()

    @staticmethod
    async def create_user(db: AsyncSession, user: UserCreate):
        hashed_password = UserService.get_password_hash(user.password)
        db_user = User(email=user.email, username=user.username, password_hash=hashed_password)
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user
