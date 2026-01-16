# # # # from django.core.management.base import BaseCommand
# # # # from django.utils.dateparse import parse_datetime

# # # # from app.management.commands.csv_reader import read_all_csv_from_folder
# # # # from app.models import Datchik, DatchikLog


# # # # def to_float(val):
# # # #     if val in (None, "", "N.C.", "  NAN"):
# # # #         return None
# # # #     try:
# # # #         return float(val)
# # # #     except ValueError:
# # # #         return None


# # # # def get_datchik_title(column_name):
# # # #     if "bosim" in column_name:
# # # #         return column_name.replace(" bosim", "").strip()
# # # #     if "temp" in column_name:
# # # #         return column_name.replace(" temp", "").strip()
# # # #     return None


# # # # def apply_formula(datchik, raw_value):
# # # #     if raw_value is None:
# # # #         return None

# # # #     if not hasattr(datchik, "formula"):
# # # #         return raw_value

# # # #     f = datchik.formula

# # # #     try:
# # # #         return eval(
# # # #             f.formula,
# # # #             {"__builtins__": {}},
# # # #             {
# # # #                 "x": raw_value,
# # # #                 "A": f.A,
# # # #                 "B": f.B,
# # # #                 "C": f.C,
# # # #                 "D": f.D
# # # #             }
# # # #         )
# # # #     except Exception:
# # # #         return raw_value


# # # # class Command(BaseCommand):
# # # #     help = "Import datchik logs from CSV"

# # # #     def handle(self, *args, **options):

# # # #         folder = "C:\\Users\\user\\Desktop\\ftp\\omnialog_885_shelemer"
# # # #         rows = read_all_csv_from_folder(folder)

# # # #         print(rows)

# # # #         header = None
# # # #         start_index = 0


# # # #         for i, row in enumerate(rows):
# # # #             print(row, row[0])
# # # #             if row and row[0] == "Date Time":
# # # #                 header = row
# # # #                 start_index = i + 1
# # # #                 break

# # # #         if not header:
# # # #             self.stdout.write(self.style.ERROR("Header topilmadi"))
# # # #             return

# # # #         datchik_map = {d.title: d for d in Datchik.objects.all()}

# # # #         logs = []

# # # #         for row in rows[start_index:]:
# # # #             if not row:
# # # #                 continue

# # # #             record = {}
# # # #             for i, col in enumerate(header):
# # # #                 record[col] = row[i] if i < len(row) else None

# # # #             record_date = parse_datetime(
# # # #                 record["Date Time"].replace("/", "-")
# # # #             )

# # # #             temp_buffer = {}

# # # #             for col, val in record.items():
# # # #                 datchik_title = get_datchik_title(col)
# # # #                 if not datchik_title:
# # # #                     continue

# # # #                 if datchik_title not in datchik_map:
# # # #                     continue

# # # #                 if datchik_title not in temp_buffer:
# # # #                     temp_buffer[datchik_title] = {
# # # #                         "pressure": None,
# # # #                         "temperature": None
# # # #                     }

# # # #                 if "bosim" in col:
# # # #                     temp_buffer[datchik_title]["pressure"] = to_float(val)

# # # #                 if "temp" in col:
# # # #                     temp_buffer[datchik_title]["temperature"] = to_float(val)

# # # #             for title, values in temp_buffer.items():
# # # #                 datchik = datchik_map[title]
# # # #                 pressure = apply_formula(datchik, values["pressure"])
# # # #                 temperature = apply_formula(datchik, values["temperature"])

# # # #                 logs.append(
# # # #                 DatchikLog(
# # # #                     datchik=datchik,
# # # #                     record_date=record_date,
# # # #                     pressure=pressure,
# # # #                     temperature=temperature,
# # # #                 )
# # # #             )

# # # #         DatchikLog.objects.bulk_create(logs)

# # # #         self.stdout.write(
# # # #             self.style.SUCCESS(f"{len(logs)} ta log saqlandi")
# # # #         )

# # # from django.core.management.base import BaseCommand
# # # from django.utils.dateparse import parse_datetime
# # # import re
# # # from app.management.commands.csv_reader import read_csv
# # # from app.models import Datchik, DatchikLog, DatchikFormula

# # # def to_float(val):
# # #     if val in (None, "", "N.C.", "  NAN", "NAN"):
# # #         return None
# # #     try:
# # #         return float(val)
# # #     except ValueError:
# # #         return None


# # # def get_datchik_title(column_name):
# # #     if "bosimi" in column_name:
# # #         return column_name.replace(" bosimi", "_bosimi").strip()
# # #     if "temp" in column_name:
# # #         return column_name.replace(" temp", "_temp").strip()
# # #     return None


# # # def apply_formula(datchik, raw_value, formula_type='Bosim'):
# # #     if raw_value is None:
# # #         return None

# # #     if not hasattr(datchik, "formula") or not datchik.formula:
# # #         return raw_value

# # #     formula_obj = datchik.formula.last()

# # #     if formula_type == 'Bosim':
# # #         f = formula_obj.bosim_formula
# # #     elif formula_type == 'Bosim_m':
# # #         f = formula_obj.bosim_m_formula
# # #     elif formula_type == 'Bosim_sm':
# # #         f = formula_obj.bosim_sm_formula
# # #     elif formula_type == 'Bosim_mm':
# # #         f = formula_obj.bosim_mm_formula
# # #     elif formula_type == 'Suv_sathi':
# # #         f = formula_obj.suv_sathi_formula
# # #     elif formula_type == 'Temperatura':
# # #         f = formula_obj.temperatura_formula
# # #     elif formula_type == 'Suv_sarfi':
# # #         f = formula_obj.suv_sarfi_formula
# # #     elif formula_type == 'Loyqaligi':
# # #         f = formula_obj.loyqaligi_formula

# # #     try:
# # #         return eval(
# # #             f.formula,
# # #             {"__builtins__": {}},
# # #             {
# # #                 "x": raw_value,
# # #                 "A": Datchik.A,
# # #                 "B": Datchik.B,
# # #                 "C": Datchik.C,
# # #                 "D": Datchik.D
# # #             }
# # #         )

# # #     except Exception:
# # #         return raw_value


# # # class Command(BaseCommand):
# # #     help = "Import datchik logs from CSV"

# # #     def handle(self, *args, **options):
# # #         # folder = "C:\\Users\\user\\Desktop\\ftp\\omnialog_885_shelemer"
# # #         rows = read_csv("mLog_22_12_25__15_42_29.csv")
# # #         # print(rows) 

# # #         if not rows:
# # #             self.stdout.write(self.style.ERROR("CSV fayl topilmadi yoki bo'sh"))
# # #             return

# # #         header = None
# # #         start_index = 0


# # #         for i, row in enumerate(rows):
# # #             # print("nechta",row)
# # #             if row and row[0] == "Date Time":
# # #                 header = row
# # #                 # print(header)
# # #                 start_index = i + 1
# # #                 break

# # #         if not header:
# # #             self.stdout.write(self.style.ERROR("Header topilmadi"))
# # #             return


# # #         datchik_map = {(d.title): d for d in Datchik.objects.all()}
# # #         print(datchik_map)

# # #         logs = []

# # #         for row in rows[start_index:]:
# # #             if not row:
# # #                 continue


# # #             record = {header[i]: row[i] if i < len(row) else None for i in range(len(header))}

# # #             record_date = parse_datetime(record["Date Time"].replace("/", "-"))

# # #             temp_buffer = {}


# # #             for col, val in record.items():
# # #                 datchik_title = get_datchik_title(col)
# # #                 if not datchik_title:
# # #                     continue

# # #                 if datchik_title not in datchik_map:
# # #                     continue

# # #                 if datchik_title not in temp_buffer:
# # #                     temp_buffer[key] = {
# # #                         "pressure": None,
# # #                         "temperature": None
# # #                     }

# # #                 if "bosim" in col:
# # #                     temp_buffer[key]["bosim"] = to_float(val)

# # #                 if "temp" in col:
# # #                     temp_buffer[key]["temperatura"] = to_float(val)


# # #             for key, values in temp_buffer.items():
# # #                 datchik = datchik_map.get(key)
# # #                 if not datchik:
# # #                     continue

# # #                 bosim = apply_formula(datchik, values["bosim"],)
# # #                 bosim_m = apply_formula(datchik, values["bosim"]*0.10119,)
# # #                 bosim_sm = apply_formula(datchik, values["bosim"]*0.10119*100,)
# # #                 bosim_mm = apply_formula(datchik, values["bosim"]*0.10119*100*10,)
# # #                 suv_sathi = apply_formula(datchik, values["bosim"]*0.10119*100,)
# # #                 temperatura = apply_formula(datchik, values["temperatura"],)
# # #                 suv_sarfi = apply_formula(datchik, values["bosim"]*0.10119*100,)
# # #                 # loyqaligi = models.FloatField(null=True, blank=True)


# # #                 logs.append(
# # #                     DatchikLog(
# # #                         datchik=datchik,
# # #                         sana=record_date,
# # #                         bosim=bosim,
# # #                         bosim_m=bosim_m,
# # #                         bosim_sm=bosim_sm,
# # #                         bosim_mm=bosim_mm,
# # #                         suv_sathi=suv_sathi,
# # #                         temperatura=temperatura,
# # #                         suv_sarfi=suv_sarfi,
                        
# # #                     )
# # #                 )

# # #         if logs:
# # #             DatchikLog.objects.bulk_create(logs)

# # #         self.stdout.write(self.style.SUCCESS(f"{len(logs)} ta log saqlandi"))

# # # from django.core.management.base import BaseCommand
# # # from django.utils.dateparse import parse_datetime
# # # import re
# # # from app.management.commands.csv_reader import read_all_csv_from_folder
# # # from app.models import Datchik, DatchikLog


# # # def to_float(val):
# # #     if val in (None, "", "N.C.", "  NAN", "NAN"):
# # #         return None
# # #     try:
# # #         return float(val)
# # #     except ValueError:
# # #         return None


# # # def apply_formula(datchik, raw_value):
# # #     if raw_value is None:
# # #         return None
# # #     if not hasattr(datchik, "formula") or not datchik.formula:
# # #         return raw_value
# # #     f = datchik.formula
# # #     try:
# # #         return eval(
# # #             f.formula,
# # #             {"__builtins__": {}},
# # #             {
# # #                 "x": raw_value,
# # #                 "A": f.A,
# # #                 "B": f.B,
# # #                 "C": f.C,
# # #                 "D": f.D
# # #             }
# # #         )
# # #     except Exception:
# # #         return raw_value


# # # class Command(BaseCommand):
# # #     help = "Import datchik logs from CSV and apply formulas"

# # #     def handle(self, *args, **options):
# # #         folder = "C:\\Users\\user\\Desktop\\ftp\\omnialog_885_shelemer"
# # #         rows = read_all_csv_from_folder(folder)

# # #         if not rows:
# # #             self.stdout.write(self.style.ERROR("CSV fayl topilmadi yoki bo'sh"))
# # #             return

# # #         # Header qatorini topamiz
# # #         header = None
# # #         start_index = 0
# # #         for i, row in enumerate(rows):
# # #             if row and row[0] == "Date Time":
# # #                 header = row
# # #                 start_index = i + 1
# # #                 break

# # #         if not header:
# # #             self.stdout.write(self.style.ERROR("Header topilmadi"))
# # #             return

# # #         # Barcha datchiklarni bazadan olamiz va nomini normalizatsiya qilamiz
# # #         datchik_map = {normalize_name(d.title): d for d in Datchik.objects.all()}

# # #         logs = []

# # #         # Har bir qatorni CSVdan o‘qib chiqamiz
# # #         for row in rows[start_index:]:
# # #             if not row:
# # #                 continue

# # #             record = {header[i]: row[i] if i < len(row) else None for i in range(len(header))}
# # #             record_date = parse_datetime(record["Date Time"].replace("/", "-"))
# # #             if not record_date:
# # #                 continue

# # #             temp_buffer = {}

# # #             for col, val in record.items():
# # #                 datchik_title = get_datchik_title(col)
# # #                 if not datchik_title:
# # #                     continue

# # #                 key = normalize_name(datchik_title)

# # #                 if key not in datchik_map:
# # #                     continue

# # #                 if key not in temp_buffer
# # #                     temp_buffer[key] = {
# # #                         "pressure": None,
# # #                         "temperature": None
# # #                     }

# # #                 if "bosim" in col or "Z" in col or "X" in col or "Y" in col:  # bosim yoki boshqa param
# # #                     temp_buffer[key]["pressure"] = to_float(val)
# # #                 if "temp" in col or "T" in col:  # temp bilan tugagan ustunlar
# # #                     temp_buffer[key]["temperature"] = to_float(val)

# # #             # Loglarni yaratamiz
# # #             for key, values in temp_buffer.items():
# # #                 datchik = datchik_map.get(key)
# # #                 if not datchik:
# # #                     continue

# # #                 pressure = apply_formula(datchik, values["pressure"])
# # #                 temperature = apply_formula(datchik, values["temperature"])

# # #                 logs.append(
# # #                     DatchikLog(
# # #                         datchik=datchik,
# # #                         record_date=record_date,
# # #                         pressure=pressure,
# # #                         temperature=temperature,
# # #                     )
# # #                 )

# # #         # Bulk create bilan saqlaymiz
# # #         if logs:
# # #             DatchikLog.objects.bulk_create(logs)

# # #         self.stdout.write(self.style.SUCCESS(f"{len(logs)} ta log saqlandi"))

# # from django.core.management.base import BaseCommand
# # from django.utils.dateparse import parse_datetime
# # from app.management.commands.csv_reader import read_csv
# # from app.models import Datchik, DatchikLog, DatchikFormula


# # # ===================== YORDAMCHI =====================

# # def to_float(val):
# #     if val in (None, "", "N.C.", "NAN", "  NAN"):
# #         return None
# #     try:
# #         return float(val)
# #     except Exception:
# #         return None


# # def normalize(col):
# #     return col.lower().strip()


# # def get_datchik_title(column_name):
# #     """
# #     Column name'dan datchik title'ni ajratadi.
# #     Misol: 'PO-82 bosim' -> 'PO-82'
# #     """
# #     col = normalize(column_name)

# #     keywords = ["bosimi", "bosim", "temp", "loyqa"]

# #     for k in keywords:
# #         if k in col:  # oldida yoki orqasida bo‘lishi mumkin
# #             return column_name.lower().replace(k, "").strip()

# #     # Agar hech nima topilmasa, asl nomni qaytarish
# #     return column_name.strip()


# # def get_value_type(column_name):
# #     """
# #     Column name'dan qiymat turini aniqlaydi
# #     """
# #     col = normalize(column_name)

# #     if "bosimi" in col:
# #         return "bosimi"
# #     if "bosim" in col:
# #         return "bosim"
# #     if "temp" in col:
# #         return "temperatura"
# #     if "loyqa" in col:
# #         return "loyqa"

# #     return None

# # def apply_formula(datchik, raw_value, formula_type):
# #     if raw_value is None:
# #         return None

# #     if not hasattr(datchik, "formula") or not datchik.formula:
# #         return raw_value

# #     formula = datchik.formula

# #     f = {
# #         "bosim": formula.bosim_formula,
# #         "bosim_m": formula.bosim_m_formula,
# #         "bosim_sm": formula.bosim_sm_formula,
# #         "bosim_mm": formula.bosim_mm_formula,
# #         "suv_sathi": formula.suv_sathi_formula,
# #         "temperatura": formula.temperatura_formula,
# #         "suv_sarfi": formula.suv_sarfi_formula,
# #         "loyqa": formula.loyqaligi_formula,
# #     }.get(formula_type)

# #     if not f:
# #         return raw_value

# #     try:
# #         return eval(
# #             f,
# #             {"__builtins__": {}},
# #             {
# #                 "x": raw_value,
# #                 "A": datchik.A,
# #                 "B": datchik.B,
# #                 "C": datchik.C,
# #                 "D": datchik.D
# #             }
# #         )
# #     except Exception:
# #         return raw_value


# # # ===================== COMMAND =====================

# # class Command(BaseCommand):
# #     help = "Import datchik logs from CSV"

# #     def handle(self, *args, **options):
# #         rows = read_csv("mLog_22_12_25__15_42_29.csv")

# #         if not rows:
# #             self.stdout.write(self.style.ERROR("CSV bo'sh yoki topilmadi"))
# #             return

# #         header = None
# #         start_index = 0

# #         for i, row in enumerate(rows):
# #             if row and row[0] == "Date Time":
# #                 header = row
# #                 start_index = i + 1
# #                 break

# #         if not header:
# #             self.stdout.write(self.style.ERROR("Header topilmadi"))
# #             return

# #         datchik_map = {d.title: d for d in Datchik.objects.select_related("formula")}
# #         logs = []

# #         for row in rows[start_index:]:
# #             if not row:
# #                 continue

# #             record = {header[i]: row[i] if i < len(row) else None for i in range(len(header))}
# #             record_date = parse_datetime(record["Date Time"].replace("/", "-"))

# #             temp_buffer = {}

# #             for col, val in record.items():
# #                 datchik_title = get_datchik_title(col)
# #                 value_type = get_value_type(col)

# #                 if not datchik_title or not value_type:
# #                     continue

# #                 if datchik_title not in datchik_map:
# #                     continue

# #                 if datchik_title not in temp_buffer:
# #                     temp_buffer[datchik_title] = {
# #                         "bosim": None,
# #                         "temperatura": None,
# #                         "loyqa": None
# #                     }

# #                 temp_buffer[datchik_title][value_type] = to_float(val)

# #             for key, values in temp_buffer.items():
# #                 datchik = datchik_map.get(key)
# #                 if not datchik:
# #                     continue

# #                 bosim_raw = None
# #                 for key in values:
# #                     if "bosim" in key.lower():  # "bosim", "bosimi", "bosim_1" ham ishlaydi
# #                         bosim_raw = values[key]
# #                         break

# #                 try:
# #                     formula_obj = datchik.formula
# #                 except Datchik.formula.RelatedObjectDoesNotExist:
# #                     formula_obj = None

# #                 logs.append(
# #                     DatchikLog(
# #                         formula=formula_obj,   # ✅ endi crash bo‘lmaydi
# #                         sana=record_date,

# #                         bosim=apply_formula(datchik, bosim_raw, "bosim"),
# #                         bosim_m=apply_formula(datchik, bosim_raw if bosim_raw else None, "bosim_m"),
# #                         bosim_sm=apply_formula(datchik, bosim_raw if bosim_raw else None, "bosim"),
# #                         bosim_mm=apply_formula(datchik, bosim_raw if bosim_raw else None, "bosim"),

# #                         suv_sathi=apply_formula(datchik, bosim_raw if bosim_raw else None, "suv_sathi"),
# #                         temperatura=apply_formula(datchik, values["temp"], "temperatura"),
# #                         suv_sarfi=apply_formula(datchik, bosim_raw if bosim_raw else None, "suv_sarfi"),
# #                         loyqaligi=apply_formula(datchik, values["loyqa"], "loyqa"),
# #             )
# #         )


# #         if logs:
# #             DatchikLog.objects.bulk_create(logs)

# #         self.stdout.write(self.style.SUCCESS(f"{len(logs)} ta log saqlandi"))


from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from app.management.commands.csv_reader import read_csv
from app.models import Datchik, DatchikLog, DatchikFormula

def to_float(val):
    """Qiymatni float ga aylantirish, bo'sh yoki N.C. bo'lsa None"""
    if val in (None, "", "N.C.", "NAN", "  NAN"):
        return None
    try:
        return float(val)
    except Exception:
        return None


def normalize(col):
    return col.lower().strip()


def get_datchik_title(column_name):
    """
    Column name'dan datchik title'ni ajratadi.
    Misol: 'PO-82 bosim' -> 'PO-82'
    """
    col = normalize(column_name)
    keywords = ["bosimi", "bosim", "temp", "loyqa"]

    for k in keywords:
        if k in col: 
            return column_name.lower().replace(k, "").strip()

    return column_name.strip()


def get_value_type(column_name):
    """
    Column name'dan qiymat turini aniqlaydi
    """
    col = normalize(column_name)
    if "bosimi" in col:
        return "bosimi"
    if "bosim" in col:
        return "bosim"
    if "temp" in col:
        return "temperatura"
    if "loyqa" in col:
        return "loyqa"
    return None


def apply_formula(datchik, raw_value, formula_type):
    """
    Raw value ga datchik formulasini qo'llash.
    Agar formula bo'lmasa → None qaytariladi (raw value tushmaydi)
    """
    if raw_value is None:
        return None

    formula = getattr(datchik, "formula", None)
    if not formula:
        return None

    f = {
        "bosim": formula.bosim_formula,
        "bosim_m": formula.bosim_m_formula,
        "bosim_sm": formula.bosim_sm_formula,
        "bosim_mm": formula.bosim_mm_formula,
        "suv_sathi": formula.suv_sathi_formula,
        "temperatura": formula.temperatura_formula,
        "suv_sarfi": formula.suv_sarfi_formula,
        "loyqa": formula.loyqaligi_formula,
    }.get(formula_type)

    if not f:
        return None

    try:
        return eval(
            f,
            {"__builtins__": {}},
            {
                "x": raw_value,
                "A": getattr(datchik, "A", 0),
                "B": getattr(datchik, "B", 0),
                "C": getattr(datchik, "C", 0),
                "D": getattr(datchik, "D", 0),
            }
        )
    except Exception:
        return None 



class Command(BaseCommand):

    def handle(self, *args, **options):
        rows = read_csv("mLog_22_12_25__18_18_52.csv")

        if not rows:
            self.stdout.write(self.style.ERROR("CSV bo'sh yoki topilmadi"))
            return

        header = None
        start_index = 0
        for i, row in enumerate(rows):
            if row and row[0].lower().strip() in ("date time", "datetime"):
                header = row
                start_index = i + 1
                break

        if not header:
            self.stdout.write(self.style.ERROR("Header topilmadi"))
            return

        # Datchiklarni bazadan olish
        datchik_map = {d.title.lower(): d for d in Datchik.objects.select_related("formula")}
        logs = []

        for row in rows[start_index:]:
            if not row:
                continue

            record = {header[i]: row[i] if i < len(row) else None for i in range(len(header))}
            record_date_raw = record.get("Date Time") or record.get("datetime")
            if not record_date_raw:
                continue

            record_date = parse_datetime(record_date_raw.replace("/", "-"))
            if not record_date:
                continue

            temp_buffer = {}

            # Har bir ustunni ajratish
            for col, val in record.items():
                datchik_title = get_datchik_title(col)
                value_type = get_value_type(col)

                if not datchik_title or not value_type:
                    continue

                datchik_key = datchik_title.lower()
                if datchik_key not in datchik_map:
                    continue

                if datchik_key not in temp_buffer:
                    temp_buffer[datchik_key] = {
                        "bosim": None,
                        "temperatura": None,
                        "loyqa": None
                    }

                temp_buffer[datchik_key][value_type] = to_float(val)

            # Log obyektlarini yaratish
            for key, values in temp_buffer.items():
                datchik = datchik_map.get(key)
                if not datchik:
                    continue

                # Bosim_raw topish (bosim yoki bosimi)
                bosim_raw = None
                for k in values:
                    if "bosim" in k.lower():
                        bosim_raw = values[k]
                        break
                temperatura_raw = values.get("temperatura")
                loyqa_raw = values.get("loyqa")

                logs.append(
                    DatchikLog(
                        formula=getattr(datchik, "formula", None),
                        sana=record_date,
                        bosim=apply_formula(datchik, bosim_raw, "bosim"),
                        bosim_m=apply_formula(datchik, bosim_raw, "bosim_m"),
                        bosim_sm=apply_formula(datchik, bosim_raw, "bosim_sm"),
                        bosim_mm=apply_formula(datchik, bosim_raw, "bosim_mm"),
                        suv_sathi=apply_formula(datchik, bosim_raw, "suv_sathi"),
                        temperatura=apply_formula(datchik, temperatura_raw, "temperatura"),
                        suv_sarfi=apply_formula(datchik, bosim_raw, "suv_sarfi"),
                        loyqaligi=apply_formula(datchik, loyqa_raw, "loyqa"),
                    )
                )

        if logs:
            DatchikLog.objects.bulk_create(logs)

        self.stdout.write(self.style.SUCCESS(f"{len(logs)} ta log saqlandi"))

