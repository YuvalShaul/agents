from fastapi.testclient import TestClient

from main import app, books

client = TestClient(app)


def setup_function():
    books.clear()


def test_list_books_empty():
    response = client.get("/books")
    assert response.status_code == 200
    assert response.json() == []


def test_create_and_get_book():
    response = client.post(
        "/books", json={"title": "Dune", "author": "Frank Herbert", "year": 1965}
    )
    assert response.status_code == 201
    created = response.json()
    assert created["id"] == 1

    response = client.get(f"/books/{created['id']}")
    assert response.status_code == 200
    assert response.json()["title"] == "Dune"


def test_get_missing_book_returns_404():
    response = client.get("/books/999")
    assert response.status_code == 404


def test_update_book():
    created = client.post(
        "/books", json={"title": "Dune", "author": "Frank Herbert", "year": 1965}
    ).json()

    response = client.put(
        f"/books/{created['id']}",
        json={"title": "Dune Messiah", "author": "Frank Herbert", "year": 1969},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Dune Messiah"


def test_delete_book():
    created = client.post(
        "/books", json={"title": "Dune", "author": "Frank Herbert", "year": 1965}
    ).json()

    response = client.delete(f"/books/{created['id']}")
    assert response.status_code == 204

    response = client.get(f"/books/{created['id']}")
    assert response.status_code == 404
