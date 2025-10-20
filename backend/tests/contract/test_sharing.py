
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.utils.user import create_random_user
from tests.utils.document import create_random_document


@pytest.mark.asyncio
async def test_share_document(client: AsyncClient, db_session: AsyncSession) -> None:
    """
    Test sharing a document with another user.
    """
    # Create owner and a document
    owner, owner_headers = await create_random_user(db_session)
    document = await create_random_document(db_session, owner_id=owner.id)

    # Create a user to share with
    user_to_share_with, _ = await create_random_user(db_session, username="shareduser", email="shared@example.com")

    # Share the document
    response = await client.post(
        f"/documents/{document.id}/share",
        headers=owner_headers,
        json={"user_ids": [str(user_to_share_with.id)]},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] == str(document.id)
    assert len(data["shared_with"]) == 1
    assert data["shared_with"][0]["user_id"] == str(user_to_share_with.id)
    assert data["shared_with"][0]["access_type"] == "editor"


@pytest.mark.asyncio
async def test_share_document_not_owner(client: AsyncClient, db_session: AsyncSession) -> None:
    """
    Test that a non-owner cannot share a document.
    """
    # Create owner and a document
    owner, _ = await create_random_user(db_session)
    document = await create_random_document(db_session, owner_id=owner.id)

    # Create a non-owner user
    non_owner, non_owner_headers = await create_random_user(db_session, username="nonowner", email="nonowner@example.com")

    # Create a user to share with
    user_to_share_with, _ = await create_random_user(db_session, username="shareduser", email="shared@example.com")

    # Try to share the document as non-owner
    response = await client.post(
        f"/documents/{document.id}/share",
        headers=non_owner_headers,
        json={"user_ids": [str(user_to_share_with.id)]},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_share_document_not_found(client: AsyncClient, db_session: AsyncSession) -> None:
    """
    Test sharing a document that does not exist.
    """
    owner, owner_headers = await create_random_user(db_session)
    non_existent_uuid = "f47ac10b-58cc-4372-a567-0e02b2c3d479"

    response = await client.post(
        f"/documents/{non_existent_uuid}/share",
        headers=owner_headers,
        json={"user_ids": [str(owner.id)]},
    )

    assert response.status_code == 404

