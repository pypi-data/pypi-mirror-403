import os
import sys
import time
import subprocess

WATCH_DIR = "."

def get_mtime():
    times = []
    for root, _, files in os.walk(WATCH_DIR):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                times.append(os.path.getmtime(path))
    return max(times)

def run():
    last_mtime = get_mtime()
    proc = subprocess.Popen([sys.executable, "application.py"])
    while True:
        time.sleep(1)
        new_mtime = get_mtime()
        if new_mtime != last_mtime:
            print("Reloading server...")
            proc.kill()
            proc = subprocess.Popen([sys.executable, "application.py"])
            last_mtime = new_mtime
            print(last_mtime)


if __name__ == "__main__":
    print("Starting server with auto-reload...")
    print("Server is running at http://127.0.0.1:8000")
    print("Press Ctrl+C to stop.")
    run()
