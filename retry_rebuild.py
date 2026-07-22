import subprocess
import time

max_retries = 10
for i in range(max_retries):
    print(f"Attempt {i+1}...")
    result = subprocess.run(['venv/bin/python', 'rebuild_properties.py'], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode == 0:
        print("Success!")
        break
    else:
        print(f"Failed with {result.returncode}. Output:\n{result.stderr[-500:]}")
        time.sleep(5)
