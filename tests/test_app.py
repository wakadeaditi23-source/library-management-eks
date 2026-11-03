import os
import sys
from datetime import date, timedelta

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402


@pytest.fixture
def client(tmp_path):
    app = create_app(db_path=str(tmp_path / "test.db"))
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client, app


def test_health(client):
    c, _ = client
    res = c.get("/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"


def test_add_and_list_book(client):
    c, _ = client
    c.post("/books", data={"title": "Clean Code", "author": "Robert Martin"}, follow_redirects=True)
    res = c.get("/")
    assert b"Clean Code" in res.data


def test_add_book_requires_fields(client):
    c, _ = client
    res = c.post("/books", data={"title": "", "author": ""}, follow_redirects=True)
    assert b"Title and author are required" in res.data


def test_search(client):
    c, _ = client
    c.post("/books", data={"title": "Python Basics", "author": "Alice"}, follow_redirects=True)
    c.post("/books", data={"title": "Java Guide", "author": "Bob"}, follow_redirects=True)
    res = c.get("/?q=python")
    assert b"Python Basics" in res.data
    assert b"Java Guide" not in res.data


def test_issue_and_return(client):
    c, _ = client
    c.post("/books", data={"title": "DBMS", "author": "Navathe"}, follow_redirects=True)
    res = c.post("/books/1/issue", data={"borrower": "Sahil"}, follow_redirects=True)
    assert b"Issued to Sahil" in res.data
    res = c.post("/books/1/issue", data={"borrower": "Someone"}, follow_redirects=True)
    assert b"already issued" in res.data
    res = c.post("/books/1/return", follow_redirects=True)
    assert b"Available" in res.data


def test_overdue(client):
    c, app = client
    c.post("/books", data={"title": "Old Book", "author": "X"}, follow_redirects=True)
    import sqlite3

    past = (date.today() - timedelta(days=3)).isoformat()
    db = sqlite3.connect(app.config["DB_PATH"])
    db.execute("UPDATE books SET issued_to='Sahil', issue_date=?, due_date=? WHERE id=1", (past, past))
    db.commit()
    db.close()
    res = c.get("/overdue")
    assert b"Old Book" in res.data


def test_delete(client):
    c, _ = client
    c.post("/books", data={"title": "Temp", "author": "Y"}, follow_redirects=True)
    c.post("/books/1/delete", follow_redirects=True)
    res = c.get("/")
    assert b"Temp" not in res.data
