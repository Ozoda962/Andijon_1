# import csv
# import os
# def read_csv(path: str) -> list[list[str]]:
#     with open(path, newline='') as f:
#         reader = csv.reader(f)
#         return list(reader)

import csv
import os

def read_all_csv_from_folder(folder_path: str) -> list[list[str]]:
    all_rows = []

    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            if filename.endswith(".csv"):
                file_path = os.path.join(root, filename)
                with open(file_path, newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    all_rows.extend(list(reader))  
    
    return all_rows