from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import httpx
import random
import specs
import subprocess
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")
SEARXNG_URL = "http://localhost:8080/search"

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

# Homepage Formatting
@app.get("/", response_class=HTMLResponse)
async def serve_homepage(request: Request):
    # Pass request and name explicitly as keyword arguments
    return templates.TemplateResponse(
        request=request, 
        name="larp_home.html"
    )

# Result page Formatting
@app.get("/search", response_class=HTMLResponse)
async def serve_results_page(request: Request, q: str):
    # The variables you want to send to the HTML go inside a 'context' dict
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
            response = await client.get(f"{SEARXNG_URL}?q={q}&format=json")
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
        rand_pos = random.randint(0, min(specs.rand_range, len(results) - 1))
        results[0], results[rand_pos] = results[rand_pos], results[0]

    return {"query": q, "results": results}

def start():
    import uvicorn
    start_searxng()
    uvicorn.run(app, host="0.0.0.0", port=5000)