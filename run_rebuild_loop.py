import subprocess
import time

max_retries = 20
for i in range(max_retries):
    print(f"Attempt {i+1}...")
    result = subprocess.run(['venv/bin/python', 'rebuild_properties.py'], capture_output=True, text=True)
    if result.returncode == 0:
        print("Success!")
        break
    else:
        print(f"Failed. Retrying in 10s... {result.stderr[-300:]}")
        time.sleep(10)
