import subprocess

# Paths to your Python scripts
script1 = 'team_rankings.py'  # Replace with the actual path to your first script
script2 = 'dk.py'  # Replace with the actual path to your second script

# Run script1 three times
for _ in range(3):
    subprocess.run(['python', script1], check=True)

# Run script2 once
subprocess.run(['python', script2], check=True)
subprocess.run(['python', 'covers_results.py'], check=True)
# subprocess.run(['python', 'reuslts_process.py'], check=True)