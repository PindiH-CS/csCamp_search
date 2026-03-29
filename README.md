# Customizable Search Engine for CS camp 2026
## Features
- Lore-related results logged in `.md` format, and recorded in **sqlite3** database
- Customizable interface with **Jinja Templating**
- Real-life fallback with **SearXNG** open source browsing API

## Prerequisites
- **Python** >= 3.8
- **Docker** and **Docker build**

## Execution
### Deploy
clone this directory, then run
``` bash
docker compose up -d --build
```
### Edit Lore Contents
Place the relevant `.md` files in the directory `lore_contents`, and run `rebuild.py` to rebuild the `.db` file.

### Refresh
Run
``` bash
uvicorn main:app --reload --port 5000  
```
