
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.utils.user import create_random_user
from tests.utils.document import create_random_document


@pytest.mark.asyncio
async def test_sharing_flow(client: AsyncClient, db_session: AsyncSession) -> None:
    """
    Test the complete document sharing flow.
    """
    # 1. Create two users
    owner, owner_headers = await create_random_user(db_session)
    shared_user, shared_user_headers = await create_random_user(db_session, username="shareduser", email="shared@example.com")

    # 2. The first user creates a document
    document = await create_random_document(db_session, owner_id=owner.id)

    # 3. The first user shares the document with the second user
    response = await client.post(
        f"/documents/{document.id}/share",
        headers=owner_headers,
        json={"user_ids": [str(shared_user.id)]},
    )
    assert response.status_code == 200

    # 4. The second user can access the document
    response = await client.get(f"/documents/{document.id}", headers=shared_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == document.title

    # 5. The second user can edit the document
    updated_title = "New Title by Shared User"
    response = await client.put(
        f"/documents/{document.id}",
        headers=shared_user_headers,
        json={"title": updated_title},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == updated_title
