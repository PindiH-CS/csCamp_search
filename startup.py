import subprocess
import os

def start_searxng(searxng_dir: str = "./searxng"):
    """Spins up the SearXNG docker container in the background."""
    
    # Verify the directory actually exists before trying
    if not os.path.isdir(searxng_dir):
        print(f"Error: Could not find the SearXNG directory at '{searxng_dir}'")
        return False

    print("Booting up SearXNG via Docker Compose...")
    
    try:
        # cwd=searxng_dir runs the command inside that specific folder
        # check=True forces Python to throw an error if Docker fails
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