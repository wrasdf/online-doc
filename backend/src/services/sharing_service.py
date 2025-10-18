
import uuid
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from src.models.document_access import DocumentAccess
from src.services.document_service import DocumentService
from src.services.user_service import UserService


class SharingService:
    @staticmethod
    async def share_document(
        db: AsyncSession,
        document_id: uuid.UUID,
        user_ids: List[uuid.UUID],
        owner_id: uuid.UUID,
    ) -> List[DocumentAccess]:
        """
        Share a document with a list of users.
        """
        # Check if the user sharing the document is the owner
        is_owner = await DocumentService.check_document_ownership(
            db, document_id=document_id, user_id=owner_id
        )
        if not is_owner:
            raise PermissionError("Only the document owner can share the document.")

        # Create DocumentAccess objects for each user
        accesses = []
        for user_id in user_ids:
            # Prevent sharing with the owner
            if user_id == owner_id:
                continue

            # Check if user exists
            user = await UserService.get_user_by_id(db, user_id=user_id)
            if not user:
                raise ValueError(f"User with id {user_id} not found.")

            # Check if access already exists
            existing_access = await db.execute(
                select(DocumentAccess).filter(
                    DocumentAccess.document_id == document_id,
                    DocumentAccess.user_id == user_id,
                )
            )
            if existing_access.scalars().first():
                continue

            access = DocumentAccess(
                document_id=document_id,
                user_id=user_id,
                granted_by=owner_id,
            )
            accesses.append(access)

        db.add_all(accesses)
        await db.commit()
        return accesses

    @staticmethod
    async def remove_access(
        db: AsyncSession,
        document_id: uuid.UUID,
        user_id: uuid.UUID,
        owner_id: uuid.UUID,
    ) -> None:
        """
        Remove a user's access to a document.
        """
        # Check if the user removing access is the owner
        is_owner = await DocumentService.check_document_ownership(
            db, document_id=document_id, user_id=owner_id
        )
        if not is_owner:
            raise PermissionError("Only the document owner can remove access.")

        # Find and delete the access
        result = await db.execute(
            select(DocumentAccess).filter(
                DocumentAccess.document_id == document_id,
                DocumentAccess.user_id == user_id,
            )
        )
        access = result.scalars().first()
        if not access:
            raise ValueError(f"Access for user {user_id} not found.")

        await db.delete(access)
        await db.commit()

    @staticmethod
    async def get_collaborators(
        db: AsyncSession,
        document_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> List[dict]:
        """
        Get all collaborators for a document (including the owner).
        User must have access to the document to view collaborators.
        """
        # Check if user has access to the document
        has_access = await DocumentService.check_document_access(
            db, document_id=document_id, user_id=user_id
        )
        if not has_access:
            raise PermissionError("You don't have access to this document.")

        # Get the document to find the owner
        document = await DocumentService.get_document(db, document_id=document_id, user_id=user_id)
        if not document:
            raise ValueError("Document not found.")

        # Get all document accesses
        result = await db.execute(
            select(DocumentAccess).filter(DocumentAccess.document_id == document_id)
        )
        accesses = result.scalars().all()

        # Build collaborator list
        collaborators = []

        # Add owner first
        owner = await UserService.get_user_by_id(db, user_id=document.owner_id)
        if owner:
            collaborators.append({
                "user_id": str(owner.id),
                "username": owner.username,
                "email": owner.email,
                "access_type": "owner",
                "granted_at": document.created_at,
            })

        # Add other collaborators
        for access in accesses:
            user = await UserService.get_user_by_id(db, user_id=access.user_id)
            if user:
                collaborators.append({
                    "user_id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "access_type": access.access_type,
                    "granted_at": access.granted_at,
                })

        return collaborators
