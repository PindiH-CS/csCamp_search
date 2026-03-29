from pathlib import Path
import sqlite3

import specs

def parse_md(lore_md: Path):
    if not lore_md.exists():
        return None

    with open(lore_md, 'r', encoding='utf-8') as f:
        content = f.read()

    parts = content.split("---", 2)
    
    if len(parts) < 3:
        return None

    meta = {}
    head = parts[1].strip()
    body = parts[2].strip()

    for line in head.split('\n'):
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip()

    # if "keywords" in meta:
    #     meta["keywords"] = [k.strip() for k in meta["keywords"].split(",")]

    return meta, body


def rebuild_database():
    # Connect to the database
    conn = sqlite3.connect(specs.DB_PATH)
    cursor = conn.cursor()
    
    lore_dir = Path(specs.lore_dirname)
    
    # Make sure the table "lore_search" exists
    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS lore_search USING fts5(
            title, url, content, keywords
        )
    ''')
    
    # Wipe old table
    cursor.execute('DELETE FROM lore_search')
    
    files_processed = 0
    
    # iterate throug the markdown files
    if lore_dir.exists() and lore_dir.is_dir():
        for file in lore_dir.glob("*.md"):
            result = parse_md(file)
            if result:
                meta, body = result
                
                cursor.execute('''
                    INSERT INTO lore_search (title, url, content, keywords)
                    VALUES (?, ?, ?, ?)
                ''', (
                    meta.get('title', 'UNTITLED FILE'), 
                    meta.get('url', 'http://unknown.node'), 
                    body, 
                    meta.get('keywords', '')
                ))
            
                files_processed += 1
                print(f"\x1b[32m[+]\x1b[0m Loaded: {meta.get('title')}")
            else:
                print(f"\x1b[31m[-]\x1b[0m Skipped {file.name}: Invalid formatting.")
    conn.commit()
    conn.close()
    
    print(f"Process Done, processed {files_processed} files.")
                
if __name__ == "__main__":
    rebuild_database()