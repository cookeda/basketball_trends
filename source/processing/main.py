import subprocess

subprocess.run(['python', 'basketball_trends/source/processing/agg_csv_files.py'])
# subprocess.run(['python', 'basketball_trends/source/processing/clean_data.py'])
subprocess.run(['python', 'basketball_trends/source/processing/game_preview_v2.py'])
subprocess.run(['python', 'basketball_trends/source/processing/combine_ranges.py']) #date needed
subprocess.run(['python', 'basketball_trends/source/processing/pre_process.py'])
subprocess.run(['python', 'basketball_trends/source/processing/final_preprocess.py']) #date needed
