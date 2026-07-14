# FastAPI Tutorial Notes & Complete Guide

## Table of Contents
1. [Introduction & Key Features](#introduction--key-features)
2. [Installation & Setup](#installation--setup)
3. [Creating a Basic FastAPI Application](#creating-a-basic-fastapi-application)
4. [Routing & Decorators](#routing--decorators)
5. [Request/Response Handling](#requestresponse-handling)
6. [Automatic API Documentation](#automatic-api-documentation)
7. [HTML vs JSON Responses](#html-vs-json-responses)
8. [Advanced Routing Concepts](#advanced-routing-concepts)
9. [Development vs Production](#development-vs-production)
10. [Best Practices & Patterns](#best-practices--patterns)

---

## Introduction & Key Features

### What is FastAPI?

FastAPI is a modern, fast web framework for building APIs and web applications in Python. It's built on top of Starlette (async web framework) and Pydantic (data validation).

**Key Advantages:**

- **Speed**: One of the fastest Python frameworks (benchmarks show speeds comparable to Node.js and Go)
- **Automatic Validation**: Built-in request/response validation using Pydantic models
- **Automatic Documentation**: Auto-generates interactive API docs (Swagger UI and ReDoc)
- **Type Hints**: Leverages Python type hints for better code quality and IDE support
- **Async/Await Support**: Native support for asynchronous programming
- **Dependency Injection**: Built-in system for managing dependencies
- **Security**: Includes utilities for OAuth2, JWT, and other security patterns
- **Production Ready**: Designed with production requirements in mind

### Project Overview

The tutorial builds a complete blog/social media application featuring:

- User registration and authentication (with JWT tokens and password hashing)
- Post creation, reading, updating, and deletion (CRUD operations)
- User profiles with image uploads
- Password reset with email notifications (using background tasks)
- Pagination for loading posts
- Authorization checks (users can only edit/delete their own posts)
- Dark mode toggle on frontend
- Both JSON API endpoints and HTML pages

---

## Installation & Setup

### Option 1: Using pip (Traditional)

```bash
pip install "fastapi[standard]"
```

The `[standard]` extras include:
- **FastAPI framework** - Core framework
- **Uvicorn** - ASGI server (runs your application)
- **FastAPI CLI** - Command-line tool for running your app

### Option 2: Using UV (Recommended Modern Approach)

UV is a faster, more efficient package manager written in Rust:

```bash
# Create a new project with UV
uv init fastapi_blog
cd fastapi_blog

# Add FastAPI with standard extras
uv add "fastapi[standard]"
```

If using UV, run commands with:
```bash
uv run fastapi dev main.py
```

### Project Structure

```
fastapi_blog/
├── main.py
├── .python-version
└── pyproject.toml (if using UV)
```

**Initial main.py:**
```python
from fastapi import FastAPI

app = FastAPI()
```

That's literally all you need to start!

---

## Creating a Basic FastAPI Application

### Step 1: Import and Initialize

```python
from fastapi import FastAPI

# Create application instance
app = FastAPI()
```

The `app` object is your central hub for defining routes and configuring your application.

### Step 2: Create Your First Route

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Hello World"}
```

**Breaking it down:**

- `@app.get("/")` - Decorator for GET requests to the root path
- `def home()` - Function name (can be anything; used for documentation)
- `return {"message": "Hello World"}` - FastAPI automatically converts to JSON

### HTTP Method Decorators

FastAPI provides decorators for all HTTP methods:

```python
@app.get("/posts")          # GET request
@app.post("/posts")         # POST request
@app.put("/posts/{id}")     # PUT request
@app.delete("/posts/{id}")  # DELETE request
@app.patch("/posts/{id}")   # PATCH request
@app.options("/path")       # OPTIONS request
@app.head("/path")          # HEAD request
```

### Synchronous vs Asynchronous

**Synchronous (Blocking) - Use for simple operations:**

```python
@app.get("/users")
def get_users():
    # Database call, file read, etc.
    return {"users": []}
```

**Asynchronous (Non-blocking) - Use for I/O operations:**

```python
@app.get("/async-users")
async def get_async_users():
    # Handles multiple concurrent requests
    # Use for API calls, database queries, file I/O
    return {"users": []}
```

**When to use each:**
- **Sync**: Simple returns, CPU-bound operations, existing sync libraries
- **Async**: Multiple I/O operations, calling other APIs, high concurrency needs

FastAPI handles both perfectly fine; the framework manages execution intelligently.

---

## Routing & Decorators

### Route Paths

```python
# Root path
@app.get("/")
def root():
    return {"msg": "root"}

# Nested paths
@app.get("/api/posts")
def get_posts():
    return []

# Path parameters (variables in URL)
@app.get("/posts/{post_id}")
def get_post(post_id: int):
    return {"post_id": post_id}
```

### Path Parameters with Type Hints

FastAPI uses Python type hints for automatic validation and conversion:

```python
@app.get("/posts/{post_id}")
def get_post(post_id: int):
    # post_id is automatically converted to int
    # If not an integer, FastAPI returns 422 validation error
    return {"post_id": post_id, "type": type(post_id).__name__}
```

### Query Parameters

```python
@app.get("/posts")
def get_posts(skip: int = 0, limit: int = 10):
    # ?skip=20&limit=5 in URL
    return {"skip": skip, "limit": limit}

# Optional parameters
@app.get("/search")
def search(q: str = None):
    if q:
        return {"query": q}
    return {"query": "empty"}
```

### Combining Path and Query Parameters

```python
@app.get("/users/{user_id}/posts")
def get_user_posts(user_id: int, skip: int = 0, limit: int = 10):
    # user_id is path parameter
    # skip and limit are query parameters
    return {"user_id": user_id, "skip": skip, "limit": limit}
```

### Stacking Multiple Decorators

Make the same function handle multiple paths:

```python
@app.get("/")
@app.get("/posts")
def get_homepage():
    return {"page": "home"}

# Accessible from both / and /posts
# Both URLs return identical content
```

**Use case:** When you want the same content at multiple URLs (e.g., homepage at both `/` and `/posts`)

### Multiple Decorators on Same Path

```python
@app.get("/items")
@app.post("/items")
def handle_items():
    # Handles both GET and POST
    # Generally not recommended; be explicit
    pass
```

---

## Request/Response Handling

### Returning JSON (Default)

```python
@app.get("/posts")
def get_posts():
    # FastAPI automatically serializes to JSON
    return [
        {"id": 1, "title": "First Post"},
        {"id": 2, "title": "Second Post"}
    ]
```

**Response automatically includes proper headers:**
- `Content-Type: application/json`
- Proper JSON serialization

### Custom Response Classes

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

app = FastAPI()

# HTML Response
@app.get("/page", response_class=HTMLResponse)
def get_page():
    return """
    <html>
        <body>
            <h1>Hello World</h1>
        </body>
    </html>
    """

# Plain Text Response
@app.get("/text", response_class=PlainTextResponse)
def get_text():
    return "This is plain text"

# Explicit JSON (same as default)
@app.get("/json", response_class=JSONResponse)
def get_json():
    return {"message": "json"}
```

### Using F-Strings for Dynamic HTML

```python
@app.get("/", response_class=HTMLResponse)
def home():
    posts = [
        {"id": 1, "title": "Post One"},
        {"id": 2, "title": "Post Two"}
    ]
    
    # Create HTML with dynamic data
    post_html = "".join([
        f"<li>{post['title']}</li>" for post in posts
    ])
    
    return f"""
    <html>
        <body>
            <h1>My Blog</h1>
            <ul>{post_html}</ul>
        </body>
    </html>
    """
```

**Note:** This is a basic approach. For production, use templating (Jinja2, which is next in the series).

---

## Automatic API Documentation

### Swagger UI (OpenAPI Interactive Docs)

Access at: `http://localhost:8000/docs`

Features:
- Interactive API explorer
- Try out endpoints directly in browser
- See request/response examples
- View curl commands
- Automatic parameter suggestions

```python
@app.get("/items/{item_id}")
def get_item(item_id: int, q: str = None):
    """
    Get an item by ID.
    
    - **item_id**: The ID of the item
    - **q**: Optional query string
    """
    return {"item_id": item_id, "q": q}
```

The docstring automatically appears in the docs!

### ReDoc (Alternative Documentation)

Access at: `http://localhost:8000/redoc`

- Modern, cleaner interface
- Better for reading/reference
- Same information as Swagger UI
- Better for printing/sharing

### Customizing Documentation

```python
from fastapi import FastAPI

app = FastAPI(
    title="Blog API",
    description="A simple blog API with posts and users",
    version="1.0.0",
    docs_url="/docs",           # Custom docs URL
    redoc_url="/redoc",         # Custom ReDoc URL
    openapi_url="/openapi.json" # Custom OpenAPI schema URL
)
```

### Hiding Routes from Documentation

```python
@app.get("/internal")
def internal_route(include_in_schema=False):
    # This route still works but won't appear in /docs
    return {"internal": True}

# Better syntax:
@app.get("/internal", include_in_schema=False)
def internal_route():
    return {"internal": True}
```

**Use cases:**
- HTML pages served to browsers (not API consumers)
- Internal endpoints
- Temporary debugging routes
- Deprecated endpoints

---

## HTML vs JSON Responses

### Design Pattern: Separation of Concerns

Modern FastAPI applications typically separate API routes from HTML rendering:

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI()

# Dummy data
posts = [
    {"id": 1, "author": "Alice", "title": "First Post", "content": "...", "date": "2024-01-01"},
    {"id": 2, "author": "Bob", "title": "Second Post", "content": "...", "date": "2024-01-02"},
]

# === API ROUTES (JSON) ===
@app.get("/api/posts")
def get_posts_api():
    """For programmatic access (JavaScript, mobile apps, other services)"""
    return posts

@app.get("/api/posts/{post_id}")
def get_post_api(post_id: int):
    """Get a specific post as JSON"""
    post = next((p for p in posts if p["id"] == post_id), None)
    return post if post else {"error": "Not found"}

# === HTML ROUTES (For Browsers) ===
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def get_homepage():
    """Render HTML for humans"""
    html = "<h1>Welcome to My Blog</h1>"
    for post in posts:
        html += f"<h2>{post['title']}</h2><p>{post['content']}</p>"
    return html

@app.get("/posts", response_class=HTMLResponse, include_in_schema=False)
def get_posts_html():
    """Same content as homepage, different URL"""
    # Reuse the same content
    return get_homepage()
```

### Why Separate API and HTML Routes?

1. **Different consumers**: JSON for applications, HTML for browsers
2. **Cleaner documentation**: API docs only show API endpoints
3. **Performance**: APIs can be optimized separately
4. **Flexibility**: Easier to add features to one without affecting the other
5. **Security**: Can apply different auth/validation rules

---

## Advanced Routing Concepts

### Path Parameters with Multiple Types

```python
@app.get("/posts/{post_id}")
def get_post(post_id: int):
    return {"post_id": post_id}

@app.get("/posts/{slug}")  # Slug as string
def get_post_by_slug(slug: str):
    return {"slug": slug}

# FastAPI is smart about routing - more specific routes first!
```

### Enums for Path Parameters

```python
from enum import Enum

class PostStatus(str, Enum):
    active = "active"
    draft = "draft"
    archived = "archived"

@app.get("/posts/status/{status}")
def get_posts_by_status(status: PostStatus):
    # Only accepts valid enum values
    return {"status": status}
    # /posts/status/active ✓
    # /posts/status/invalid ✗ (422 error)
```

### Request Body (for POST/PUT)

```python
from pydantic import BaseModel

class Post(BaseModel):
    title: str
    content: str
    author: str

@app.post("/posts")
def create_post(post: Post):
    # FastAPI automatically validates the request body
    # Must be valid JSON matching Post model
    return {"created": post}
```

### Optional Path Configuration

```python
from fastapi import APIRouter

# Create a router for organizing routes
router = APIRouter(prefix="/api", tags=["posts"])

@router.get("/posts")
def get_posts():
    return []

@router.get("/posts/{post_id}")
def get_post(post_id: int):
    return {"id": post_id}

app.include_router(router)
# Routes now: /api/posts, /api/posts/{post_id}
```

---

## Development vs Production

### Running the Application

**Development Mode (with auto-reload):**
```bash
# Using fastapi dev
fastapi dev main.py

# Using UV
uv run fastapi dev main.py
```

**Features:**
- Auto-restarts on file changes
- Better error messages
- Debugging output
- Great for development

**Production Mode (optimized):**
```bash
fastapi run main.py
```

**Features:**
- No auto-reload
- Optimized for performance
- Minimal debug info
- Can add Gunicorn for multi-worker setup

### Full Production Setup

```bash
# Install Gunicorn
pip install gunicorn

# Run with multiple workers
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

### Environment Configuration

```python
from fastapi import FastAPI
import os

# Read from environment variables
DEBUG = os.getenv("DEBUG", "False") == "True"
ENVIRONMENT = os.getenv("ENV", "development")

app = FastAPI(
    title="My API",
    debug=DEBUG
)

@app.get("/config")
def get_config():
    return {
        "environment": ENVIRONMENT,
        "debug": DEBUG
    }
```

---

## Best Practices & Patterns

### 1. Structure Your Application

```
blog/
├── main.py
├── app.py              # Application factory
├── models.py           # Pydantic models
├── database.py         # Database configuration
├── routers/
│   ├── posts.py
│   ├── users.py
│   └── auth.py
├── crud.py             # Database operations
├── schemas.py          # Pydantic schemas
├── dependencies.py     # Dependency injection
└── utils.py            # Helper functions
```

### 2. Use Pydantic Models for Validation

```python
from pydantic import BaseModel, EmailStr, Field

class PostCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=10)
    author: str

class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    author: str
    
    class Config:
        from_attributes = True  # For ORM models
```

### 3. Use Routers for Organization

```python
from fastapi import APIRouter

post_router = APIRouter(
    prefix="/api/posts",
    tags=["posts"],
    responses={404: {"description": "Not found"}}
)

@post_router.get("/")
def list_posts():
    return []

@post_router.post("/")
def create_post(post_data: dict):
    return {"created": post_data}

app.include_router(post_router)
```

### 4. Proper Status Codes

```python
from fastapi import status

@app.post("/items", status_code=status.HTTP_201_CREATED)
def create_item(item: dict):
    return {"created": item}

@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int):
    return None
```

### 5. Error Handling

```python
from fastapi import HTTPException

@app.get("/posts/{post_id}")
def get_post(post_id: int):
    post = find_post(post_id)
    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )
    return post

@app.get("/admin")
def admin_only(user_role: str):
    if user_role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Not authorized"
        )
    return {"admin": True}
```

### 6. Dependency Injection

```python
from fastapi import Depends

def get_current_user(token: str = Depends(get_token)):
    # Validate token and return user
    return {"user_id": 1, "role": "admin"}

@app.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return current_user
```

### 7. Middleware and Exception Handlers

```python
from fastapi.middleware.cors import CORSMiddleware

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception handler
from fastapi import Request

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return {"error": str(exc)}
```

### 8. Testing

```python
from fastapi.testclient import TestClient

client = TestClient(app)

def test_get_posts():
    response = client.get("/api/posts")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_post():
    response = client.post("/api/posts", json={
        "title": "Test",
        "content": "Test content",
        "author": "Test Author"
    })
    assert response.status_code == 201
```

### 9. Use Type Hints Everywhere

```python
from typing import List, Optional

@app.get("/posts")
def get_posts(skip: int = 0, limit: int = 10) -> List[dict]:
    return []

@app.get("/posts/{post_id}")
def get_post(post_id: int) -> Optional[dict]:
    return None
```

### 10. Document Your API

```python
@app.get("/posts", tags=["posts"], summary="List Posts")
def list_posts(skip: int = 0, limit: int = 10):
    """
    Get a list of posts with pagination.
    
    - **skip**: Number of posts to skip (default: 0)
    - **limit**: Maximum posts to return (default: 10)
    
    Returns a list of posts sorted by date.
    """
    return []
```

---

## What Comes Next in the Series

Based on the tutorial outline, expect to learn:

1. **Jinja2 Templates** - Proper HTML templating (instead of raw strings)
2. **Database Integration** - SQLAlchemy with SQLite → PostgreSQL
3. **Pydantic Models** - Advanced data validation and serialization
4. **Complete CRUD** - Create, Read, Update, Delete operations
5. **User Authentication** - JWT tokens, password hashing, secure login
6. **File Uploads** - Handling image and file uploads
7. **Background Tasks** - Async email sending, scheduled jobs
8. **Security** - OAuth2, password hashing, JWT implementation
9. **Testing** - Unit and integration tests
10. **Deployment** - Production setup and deployment strategies

---

## Key Takeaways

✅ FastAPI provides automatic validation and documentation  
✅ Use decorators to define routes (`@app.get()`, `@app.post()`, etc.)  
✅ Python type hints are essential for data validation  
✅ Separate API routes (JSON) from HTML routes  
✅ Use `include_in_schema=False` to hide routes from docs  
✅ FastAPI handles both sync and async functions  
✅ Pydantic models provide built-in validation  
✅ The framework automatically generates OpenAPI/Swagger docs  
✅ Use routers and dependency injection for better code organization  
✅ Always use proper HTTP status codes  

---

## Useful Resources

- **Official Docs**: https://fastapi.tiangolo.com/
- **Starlette Docs**: https://www.starlette.io/
- **Pydantic Docs**: https://docs.pydantic.dev/
- **Uvicorn Docs**: https://www.uvicorn.org/
- **OpenAPI Spec**: https://swagger.io/specification/

