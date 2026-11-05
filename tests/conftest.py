# conftest.py -> pytest ki khaas file. Yahan jo "fixture" banate hain wo saare tests mein
# naam likhte hi mil jaata hai (import karne ki zaroorat nahi).

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    # TestClient = nakli browser jo bina server chalaye app ko request bhej sakta hai.
    return TestClient(app)
