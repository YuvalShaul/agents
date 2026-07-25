from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Books API")


class BookCreate(BaseModel):
    title: str
    author: str
    year: int


class Book(BookCreate):
    id: int


books: dict[int, Book] = {}
next_id = 1


@app.get("/books", response_model=list[Book])
def list_books():
    return list(books.values())


@app.get("/books/{book_id}", response_model=Book)
def get_book(book_id: int):
    book = books.get(book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@app.post("/books", response_model=Book, status_code=201)
def create_book(book: BookCreate):
    global next_id
    new_book = Book(id=next_id, **book.model_dump())
    books[next_id] = new_book
    next_id += 1
    return new_book


@app.put("/books/{book_id}", response_model=Book)
def update_book(book_id: int, book: BookCreate):
    if book_id not in books:
        raise HTTPException(status_code=404, detail="Book not found")
    updated_book = Book(id=book_id, **book.model_dump())
    books[book_id] = updated_book
    return updated_book


@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int):
    if book_id not in books:
        raise HTTPException(status_code=404, detail="Book not found")
    del books[book_id]
