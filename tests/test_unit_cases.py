import pytest
import pandas as pd
import os
from fastapi.testclient import TestClient
from api.main import app   # or your FastAPI entrypoint

client = TestClient(app)

# Test Case 1: Existing test for home endpoint
def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert "Document Portal" in response.text

# Test Case 2: Test analyze endpoint with a new document type (.xlsx)
def test_analyze_new_document_types(tmp_path):
    """
    Test the /analyze endpoint with an Excel file containing a table.
    """
    # Create a temporary Excel file with a sample table
    test_file = tmp_path / "test_document.xlsx"
    df = pd.DataFrame({
        "Name": ["Alice", "Bob"],
        "Age": [25, 30],
        "City": ["New York", "London"]
    })
    df.to_excel(test_file, index=False)

    # Open the file and send it to the /analyze endpoint
    with open(test_file, "rb") as f:
        response = client.post("/analyze", files={"file": ("test_document.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})

    # Clean up the temporary file
    os.remove(test_file)

    # Assert the response
    assert response.status_code == 200
    response_json = response.json()
    assert "Title" in response_json  # Based on Metadata model
    assert "Summary" in response_json
    assert isinstance(response_json["Summary"], list)
    assert "Table" in response_json["Summary"][0]  # Check for table inclusion in summary