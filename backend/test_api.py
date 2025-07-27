import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_user_workflow():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 1. Test user signup or login (adjust endpoint & payload as per your app)
        # For example, login endpoint:
        login_data = {"username": "testuser", "password": "testpassword"}
        response = await ac.post("/auth/login", json=login_data)
        assert response.status_code == 200
        tokens = response.json()
        assert "access_token" in tokens

        access_token = tokens["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # 2. Test get current user profile
        response = await ac.get("/users/me", headers=headers)
        assert response.status_code == 200
        user = response.json()
        assert user["username"] == "testuser"

        # 3. Test search users (adjust query params as needed)
        response = await ac.get("/users/search", params={"username": "test"}, headers=headers)
        # If no users found, your code raises 404 so you can assert that or handle accordingly
        assert response.status_code in [200, 404]

        # 4. Test friend request send (you need a second user created first)
        # Example friend request payload:
        friend_request = {"receiver_id": 2}  # Make sure user with ID 2 exists
        response = await ac.post("/friends/request", json=friend_request, headers=headers)
        # Status could be 201 or 400 if already friends
        assert response.status_code in [201, 400]

        # You can add more tests for respond, list, remove friends, etc.

# Add more test functions here for other routers / endpoints
