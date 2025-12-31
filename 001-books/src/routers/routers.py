import httpx
from fastapi import APIRouter, HTTPException
from typing import List
from ..schemas.schemas import Book, BaseBook
from pydantic import BaseModel

router = APIRouter(
    prefix = "/books"
)

@router.get("/search/title") 
async def search_books(query: str) -> list[BaseBook]:
    data = await fetch_books_from_api(query, isTitle= True,)

    if "items" not in data:
        return []

    books = []
    for item in data["items"]:
        info = item.get("volumeInfo", {})
        identifier = item.get("id")

        if info.get("authors") != None:
            authors = list(info.get("authors"))
        else:
            authors = None

        books.append(
            BaseBook(
                title=info.get("title"),
                author=authors,
                thumbnail=str(info.get("imageLinks", {}).get("thumbnail")),
                identifier = str(identifier)
                )
            )  
        
    return books

@router.get("/search/author") 
async def search_books(query: str) -> list[BaseBook]:
    data = await fetch_books_from_api(query, isAuthor=True)

    if "items" not in data:
        return []

    books = []
    for item in data["items"]:
        identifier = item.get("id")
        info = item.get("volumeInfo", {})

        if info.get("authors") != None:
            authors = list(info.get("authors"))
        else:
            authors = None

        books.append(
            BaseBook(
                title=info.get("title"),
                author=authors,
                thumbnail=str(info.get("imageLinks", {}).get("thumbnail")),
                identifier = str(identifier)
            )  
        )
    return books

@router.get("/{bookid}", response_model=Book)
async def book_info(bookid: str):
    book = await fetch_books_from_api(query=bookid, isInfo=True)
    print(book.get("imageLinks"))
    finalBook = Book(
        title = str(book.get("volumeInfo", {}).get("title")),
        author = list(book.get("volumeInfo", {}).get("authors", [])),
        thumbnail = str(book.get("volumeInfo", {}).get("imageLinks", {}).get("smallThumbnail")),
        identifier = str(book.get("id")),
        description = str(book.get("volumeInfo", {}).get("description")),
        published_year = str(book.get("volumeInfo", {}).get("publishedDate"))
    )
    return finalBook

async def fetch_books_from_api(query: str, isAuthor: bool = False, isTitle: bool = False, isInfo: bool = False):
    if isTitle:
        url = f"https://www.googleapis.com/books/v1/volumes?q={query}"
    elif isAuthor:
        url = f"https://www.googleapis.com/books/v1/volumes?q=+inauthor:{query}"
    elif isInfo:
        url = f"https://www.googleapis.com/books/v1/volumes/{query}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
    
    return response.json()