import os
import subprocess
import sqlite3
import httpx
import random
from contextlib import asynccontextmanager  # <-- Fix 1: Added this missing import

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import specs

# --- 1. Environment Variables ---
SEARXNG_URL = os.getenv("SEARXNG_URL", "http://localhost:8080/search")
IS_DOCKER = os.getenv("SEARXNG_URL") is not None

# --- 2. Startup Logic ---
def start_searxng(searxng_dir: str = "./searxng"):
    """Spins up the SearXNG docker container in the background."""
    if not os.path.isdir(searxng_dir):
        print(f"Error: Could not find the SearXNG directory at '{searxng_dir}'")
        return False

    print("Booting up SearXNG via Docker Compose...")
    try:
        result = subprocess.run(
            ["docker", "compose", "up", "-d"],
            cwd=searxng_dir,
            check=True,
            capture_output=True, 
            text=True
        )
        print("SearXNG started successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to start SearXNG Docker container.")
        print(f"Error details:\n{e.stderr}")
        return False
    except FileNotFoundError:
        print("Docker doesn't seem to be installed or in your system's PATH.")
        return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not IS_DOCKER:
        start_searxng(searxng_dir="./searxng")  # Ensure this path matches your local setup
    yield
    print("Shutting down FastAPI server...")


# --- 3. App Initialization ---
# Fix 2: Attach the lifespan to the app when you create it!
app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")


# --- 4. Routes ---
# Homepage Formatting
@app.get("/", response_class=HTMLResponse)
async def serve_homepage(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="larp_home.html"
    )

# Result page Formatting
@app.get("/search", response_class=HTMLResponse)
async def serve_results_page(request: Request, q: str):
    return templates.TemplateResponse(
        request=request, 
        name="larp_results.html", 
        context={"q": q}
    )
    
@app.get("/api/search")
async def search(q: str):
    results = []
    
    # Custom Lore Results
    try:
        safe_q = q.replace('"', '') 
        conn = sqlite3.connect('larp_lore.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT title, url, content 
            FROM lore_search 
            WHERE lore_search MATCH ?
        """, (safe_q,))
        
        lore_rows = cursor.fetchall()
        for row in lore_rows:
            results.append({
                "title": row[0], "url": row[1], "content": row[2], "source": "lore"
            })
        conn.close()
    except sqlite3.Error as e:
        print(f"Database Query Error: {e}")
    except Exception as e:
        print(f"Unexpected DB Error: {e}")

    # Real Web searching with SearXNG
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(SEARXNG_URL, params={"q": q, "format": "json"})
            if response.status_code == 200:
                searxng_data = response.json()
                for item in searxng_data.get("results", []):
                    results.append({
                        "title": item.get("title"), "url": item.get("url"),
                        "content": item.get("content"), "source": "web"
                    })
    except Exception as e:
        print(f"SearXNG Error: {e}")
        
    if len(results) > 1:
        rand_pos = random.randint(min(specs.rand_min, len(results) - 1), min(specs.rand_max, len(results) - 1))
        results[0], results[rand_pos] = results[rand_pos], results[0]

    return {"query": q, "results": results}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)