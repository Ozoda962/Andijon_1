# # from django.core.management.base import BaseCommand
# # from django.utils.dateparse import parse_datetime

# # from app.management.commands.csv_reader import read_all_csv_from_folder
# # from app.models import Datchik, DatchikLog


# # def to_float(val):
# #     if val in (None, "", "N.C.", "  NAN"):
# #         return None
# #     try:
# #         return float(val)
# #     except ValueError:
# #         return None


# # def get_datchik_title(column_name):
# #     if "bosim" in column_name:
# #         return column_name.replace(" bosim", "").strip()
# #     if "temp" in column_name:
# #         return column_name.replace(" temp", "").strip()
# #     return None


# # def apply_formula(datchik, raw_value):
# #     if raw_value is None:
# #         return None

# #     if not hasattr(datchik, "formula"):
# #         return raw_value

# #     f = datchik.formula

# #     try:
# #         return eval(
# #             f.formula,
# #             {"__builtins__": {}},
# #             {
# #                 "x": raw_value,
# #                 "A": f.A,
# #                 "B": f.B,
# #                 "C": f.C,
# #                 "D": f.D
# #             }
# #         )
# #     except Exception:
# #         return raw_value


# # class Command(BaseCommand):
# #     help = "Import datchik logs from CSV"

# #     def handle(self, *args, **options):

# #         folder = "C:\\Users\\user\\Desktop\\ftp\\omnialog_885_shelemer"
# #         rows = read_all_csv_from_folder(folder)

# #         print(rows)

# #         header = None
# #         start_index = 0


# #         for i, row in enumerate(rows):
# #             print(row, row[0])
# #             if row and row[0] == "Date Time":
# #                 header = row
# #                 start_index = i + 1
# #                 break

# #         if not header:
# #             self.stdout.write(self.style.ERROR("Header topilmadi"))
# #             return

# #         datchik_map = {d.title: d for d in Datchik.objects.all()}

# #         logs = []

# #         for row in rows[start_index:]:
# #             if not row:
# #                 continue

# #             record = {}
# #             for i, col in enumerate(header):
# #                 record[col] = row[i] if i < len(row) else None

# #             record_date = parse_datetime(
# #                 record["Date Time"].replace("/", "-")
# #             )

# #             temp_buffer = {}

# #             for col, val in record.items():
# #                 datchik_title = get_datchik_title(col)
# #                 if not datchik_title:
# #                     continue

# #                 if datchik_title not in datchik_map:
# #                     continue

# #                 if datchik_title not in temp_buffer:
# #                     temp_buffer[datchik_title] = {
# #                         "pressure": None,
# #                         "temperature": None
# #                     }

# #                 if "bosim" in col:
# #                     temp_buffer[datchik_title]["pressure"] = to_float(val)

# #                 if "temp" in col:
# #                     temp_buffer[datchik_title]["temperature"] = to_float(val)

# #             for title, values in temp_buffer.items():
# #                 datchik = datchik_map[title]
# #                 pressure = apply_formula(datchik, values["pressure"])
# #                 temperature = apply_formula(datchik, values["temperature"])

# #                 logs.append(
# #                 DatchikLog(
# #                     datchik=datchik,
# #                     record_date=record_date,
# #                     pressure=pressure,
# #                     temperature=temperature,
# #                 )
# #             )

# #         DatchikLog.objects.bulk_create(logs)

# #         self.stdout.write(
# #             self.style.SUCCESS(f"{len(logs)} ta log saqlandi")
# #         )

# from django.core.management.base import BaseCommand
# from django.utils.dateparse import parse_datetime
# import re
# from app.management.commands.csv_reader import read_csv
# from app.models import Datchik, DatchikLog


# def to_float(val):
#     if val in (None, "", "N.C.", "  NAN", "NAN"):
#         return None
#     try:
#         return float(val)
#     except ValueError:
#         return None


# def get_datchik_title(column_name):
#     if "bosim" in column_name:
#         return column_name.replace(" bosim", "").strip()
#     if "temp" in column_name:
#         return column_name.replace(" temp", "").strip()
#     return None


# # def normalize_name(name):
# #     if not name:
# #         return ""
# #     name = name.strip().upper()
    
# #     # 'SH/885/14 Z' → 'SH.D-014'
# #     # 1. 'SH/' → 'SH.'
# #     name = name.replace("SH/", "SH.")    
# #     # 2. Raqam qismini uch xonali formatga keltirish
# #     name = re.sub(r"(\d+)", lambda m: m.group(1).zfill(3), name)    
# #     # 3. Bo‘sh joy va / yoki boshqa belgilarni olib tashlash
# #     name = re.sub(r"[^A-Z0-9\.-]", "", name)    
# #     return name

# def csv_to_db_title(column_name):
#     # 'SH/885/14 Z' → '014'
#     match = re.search(r"/(\d+)", column_name)
#     if match:
#         num = match.group(1).zfill(3)
#         return f"SH.D-{num}"  # bazadagi title bilan to‘liq mos
#     return None

# def apply_formula(datchik, raw_value):
#     if raw_value is None:
#         return None

#     if not hasattr(datchik, "formula") or not datchik.formula:
#         return raw_value

#     f = datchik.formula
#     try:
#         return eval(
#             f.formula,
#             {"__builtins__": {}},
#             {
#                 "x": raw_value,
#                 "A": f.A,
#                 "B": f.B,
#                 "C": f.C,
#                 "D": f.D
#             }
#         )

#     except Exception:
#         return raw_value


# class Command(BaseCommand):
#     help = "Import datchik logs from CSV"

#     def handle(self, *args, **options):
#         # folder = "C:\\Users\\user\\Desktop\\ftp\\omnialog_885_shelemer"
#         rows = read_csv("mLog_22_12_25__15_51_55.csv")
#         print(rows) 

#         if not rows:
#             self.stdout.write(self.style.ERROR("CSV fayl topilmadi yoki bo‘sh"))
#             return

#         header = None
#         start_index = 0


#         for i, row in enumerate(rows):
#             if row and row[0] == "Date Time":
#                 header = row
#                 start_index = i + 1
#                 break

#         if not header:
#             self.stdout.write(self.style.ERROR("Header topilmadi"))
#             return


#         datchik_map = {(d.title): d for d in Datchik.objects.all()}

#         logs = []

#         for row in rows[start_index:]:
#             if not row:
#                 continue


#             record = {header[i]: row[i] if i < len(row) else None for i in range(len(header))}

#             record_date = parse_datetime(record["Date Time"].replace("/", "-"))

#             temp_buffer = {}


#             for col, val in record.items():
#                 datchik_title = get_datchik_title(col)
#                 if not datchik_title:
#                     continue

#                 key = normalize_name(datchik_title)

#                 if key not in datchik_map:
#                     continue

#                 if key not in temp_buffer:
#                     temp_buffer[key] = {
#                         "pressure": None,
#                         "temperature": None
#                     }

#                 if "bosim" in col:
#                     temp_buffer[key]["pressure"] = to_float(val)

#                 if "temp" in col:
#                     temp_buffer[key]["temperature"] = to_float(val)

#             for key, values in temp_buffer.items():
#                 datchik = datchik_map.get(key)
#                 if not datchik:
#                     continue

#                 pressure = apply_formula(datchik, values["pressure"])
#                 temperature = apply_formula(datchik, values["temperature"])

#                 logs.append(
#                     DatchikLog(
#                         datchik=datchik,
#                         record_date=record_date,
#                         pressure=pressure,
#                         temperature=temperature,
#                     )
#                 )

#         if logs:
#             DatchikLog.objects.bulk_create(logs)

#         self.stdout.write(self.style.SUCCESS(f"{len(logs)} ta log saqlandi"))

from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
import re
from app.management.commands.csv_reader import read_all_csv_from_folder
from app.models import Datchik, DatchikLog


def to_float(val):
    if val in (None, "", "N.C.", "  NAN", "NAN"):
        return None
    try:
        return float(val)
    except ValueError:
        return None


def get_datchik_title(column_name):
    """
    CSV ustun nomidan datchik nomini ajratadi.
    Masalan: 'SH/885/10 X' yoki 'SH/885/10 X temp'
    """
    # temp va bosim so'zlarini olib tashlaymiz
    return column_name.replace(" temp", "").replace(" bosim", "").strip()


def normalize_name(name):
    """
    Minimal normalizatsiya: bo'sh joylarni olib tashlash va katta harf
    """
    if not name:
        return ""
    return name.strip().upper()

def csv_to_db_title(column_name):

    match = re.search(r"/(\d+)", column_name)
    print(column_name)
    if match:
        num = match.group(1).zfill(3)
        return f"SH.D-{num}"  
    return None


def apply_formula(datchik, raw_value):
    if raw_value is None:
        return None
    if not hasattr(datchik, "formula") or not datchik.formula:
        return raw_value
    f = datchik.formula
    try:
        return eval(
            f.formula,
            {"__builtins__": {}},
            {
                "x": raw_value,
                "X": raw_value,
                "A": f.A,
                "B": f.B,
                "C": f.C,
                "D": f.D
            }
        )
    except Exception:
        return raw_value


class Command(BaseCommand):
    help = "Import datchik logs from CSV and apply formulas"

    def handle(self, *args, **options):
        folder = "C:\\Users\\user\\Desktop\\ftp\\omnialog_885_shelemer"
        rows = read_all_csv_from_folder(folder)

        if not rows:
            self.stdout.write(self.style.ERROR("CSV fayl topilmadi yoki bo‘sh"))
            return

        # Header qatorini topamiz
        header = None
        start_index = 0
        for i, row in enumerate(rows):
            if row and row[0] == "Date Time":
                header = row
                start_index = i + 1
                break

        if not header:
            self.stdout.write(self.style.ERROR("Header topilmadi"))
            return

        # Barcha datchiklarni bazadan olamiz va nomini normalizatsiya qilamiz
        datchik_map = {normalize_name(d.title): d for d in Datchik.objects.all()}

        logs = []

        # Har bir qatorni CSVdan o‘qib chiqamiz
        for row in rows[start_index:]:
            if not row:
                continue

            record = {header[i]: row[i] if i < len(row) else None for i in range(len(header))}
            record_date = parse_datetime(record["Date Time"].replace("/", "-"))
            if not record_date:
                continue

            temp_buffer = {}

            for col, val in record.items():
                datchik_title = get_datchik_title(col)
                if not datchik_title:
                    continue

                key = normalize_name(datchik_title)

                if key not in datchik_map:
                    continue

                if key not in temp_buffer
                    temp_buffer[key] = {
                        "pressure": None,
                        "temperature": None
                    }

                if "bosim" in col or "Z" in col or "X" in col or "Y" in col:  # bosim yoki boshqa param
                    temp_buffer[key]["pressure"] = to_float(val)
                if "temp" in col or "T" in col:  # temp bilan tugagan ustunlar
                    temp_buffer[key]["temperature"] = to_float(val)

            # Loglarni yaratamiz
            for key, values in temp_buffer.items():
                datchik = datchik_map.get(key)
                if not datchik:
                    continue

                pressure = apply_formula(datchik, values["pressure"])
                temperature = apply_formula(datchik, values["temperature"])

                logs.append(
                    DatchikLog(
                        datchik=datchik,
                        record_date=record_date,
                        pressure=pressure,
                        temperature=temperature,
                    )
                )

        # Bulk create bilan saqlaymiz
        if logs:
            DatchikLog.objects.bulk_create(logs)

        self.stdout.write(self.style.SUCCESS(f"{len(logs)} ta log saqlandi"))
