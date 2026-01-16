import csv
import os
def read_csv(path: str) -> list[list[str]]:
    with open(path, newline='') as f:
        reader = csv.reader(f)
        return list(reader)


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

import csv
import os


def read_csv_file(path: str) -> list[list[str]]:
    """
    CSV faylni to'liq o'qib, qatorlar ro'yxatini qaytaradi.
    Har bir qator -> list[str]

    Qo'llab-quvvatlaydi:
    - UTF-8 / UTF-8-BOM
    - simli va simsiz logger CSV
    - metadata + data bir faylda
    """

    if not os.path.isfile(path):
        return []

    rows: list[list[str]] = []

    with open(path, mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)

        for row in reader:

            if not row:
                continue

            if all((c is None or str(c).strip() == "") for c in row):
                continue

            clean_row = [c.strip() if isinstance(c, str) else c for c in row]
            rows.append(clean_row)

    return rows
