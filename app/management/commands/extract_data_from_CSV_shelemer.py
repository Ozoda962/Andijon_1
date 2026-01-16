# # from django.core.management.base import BaseCommand
# # from datetime import datetime
# # from app.management.commands.csv_reader import read_csv
# # from app.models import Datchik, DatchikLog
# # import re

# # # ===================== YORDAMCHI FUNKSIYALAR =====================

# # def to_float(val):
# #     """String yoki boshqa turdagi qiymatni float ga aylantiradi"""
# #     if val in (None, "", "-", "N.C.", "NAN", "  NAN"):
# #         return None
# #     try:
# #         return float(str(val).strip())
# #     except Exception:
# #         return None

# # def normalize(text):
# #     return text.lower().strip() if text else ""

# # def parse_sh_column(column_name):
# #     """
# #     SH/<lokatsiya>/<sensor> <suffix> formatidagi stringni tahlil qiladi
# #     va key_name bilan birga qaytaradi:
# #       X,Y,Z -> bosim
# #       XT,YT,ZT -> temperatura
# #     """
# #     if not isinstance(column_name, str):
# #         return None

# #     column_name = column_name.strip()
# #     if not column_name.startswith("SH/"):
# #         return None

# #     pattern = r"^SH\/(\d+)\/(\d+)\s*(Z|ZT|X|XT|Y|YT)\s*$"
# #     match = re.match(pattern, column_name, re.IGNORECASE)
# #     if not match:
# #         return None

# #     location = match.group(1)
# #     sensor_number = int(match.group(2))
# #     suffix = match.group(3).upper()

# #     if suffix in ["X", "Y", "Z"]:
# #         value_type = "bosim"
# #         key_name = suffix.lower()  # x, y, z
# #     else:
# #         value_type = "temperatura"
# #         key_name = suffix.lower().replace("t", "_temp")  # x_temp, y_temp, z_temp

# #     return location, sensor_number, value_type, key_name

# # def apply_formula(datchik, raw_value, formula_type):
# #     if raw_value is None:
# #         return None
# #     formula = getattr(datchik, "formula", None)
# #     if not formula:
# #         return raw_value  # agar formula bo'lmasa, raw_value qaytarilsin

# #     formula_map = {
# #         "bosim": formula.bosim_formula,
# #         "bosim_m": formula.bosim_m_formula,
# #         "bosim_sm": formula.bosim_sm_formula,
# #         "bosim_mm": formula.bosim_mm_formula,
# #         "suv_sathi": formula.suv_sathi_formula,
# #         "suv_sarfi": formula.suv_sarfi_formula,
# #         "temperatura": formula.temperatura_formula,
# #         "loyqa": formula.loyqaligi_formula,
# #         "x": formula.bosim_x_formula,
# #         "y": formula.bosim_y_formula,
# #         "z": formula.bosim_z_formula,
# #         "x_temp": formula.temperatura_x_formula,
# #         "y_temp": formula.temperatura_y_formula,
# #         "z_temp": formula.temperatura_z_formula,
# #     }
# #     f = formula_map.get(formula_type)
# #     if not f:
# #         return raw_value  # agar formula yo'q bo'lsa, raw_value qaytarilsin

# #     try:
# #         return eval(f, {"__builtins__": {}}, {
# #             "x": raw_value,
# #             "X": raw_value,
# #             "A": getattr(datchik, "A", 0),
# #             "B": getattr(datchik, "B", 0),
# #             "C": getattr(datchik, "C", 0),
# #             "D": getattr(datchik, "D", 0),
# #         })
# #     except Exception:
# #         return raw_value  # xatolik bo'lsa raw_value qaytarilsin

# # # ===================== COMMAND =====================

# # class Command(BaseCommand):
# #     help = "Import datchik logs from CSV"

# #     def handle(self, *args, **options):
# #         rows = read_csv("mLog_22_12_25__18_18_52.csv")
# #         if not rows:
# #             self.stdout.write(self.style.ERROR("CSV topilmadi yoki bo'sh"))
# #             return

# #         # Header topish
# #         header, start_index = None, 0
# #         for i, row in enumerate(rows):
# #             if row and normalize(row[0]) in ("date time", "datetime"):
# #                 header, start_index = row, i + 1
# #                 break
# #         if not header:
# #             self.stdout.write(self.style.ERROR("Header topilmadi"))
# #             return

# #         # Datchiklarni map qilish: key = "location_id:sensor_number"
# #         datchik_map = {}
# #         for d in Datchik.objects.select_related("formula", "location"):
# #             if not d.location:
# #                 continue
# #             try:
# #                 sensor_number = int(d.title)  # title = sensor_number bo'lishi kerak
# #             except ValueError:
# #                 continue
# #             key = f"{d.location.id}:{sensor_number}"
# #             datchik_map[key] = d

# #         logs = []

# #         for row in rows[start_index:]:
# #             if not row:
# #                 continue
# #             record = {header[i]: row[i] if i < len(row) else None for i in range(len(header))}
# #             raw_date = record.get("Date Time") or record.get("datetime")
# #             if not raw_date:
# #                 continue
# #             try:
# #                 record_date = datetime.strptime(raw_date.strip(), "%Y/%m/%d %H:%M:%S")
# #             except Exception:
# #                 continue

# #             temp_buffer = {}

# #             for col, val in record.items():
# #                 parsed = parse_sh_column(col)
# #                 if parsed:
# #                     location, sensor_number, value_type, key_name = parsed
# #                     key = f"{int(location)}:{sensor_number}"
# #                     datchik = datchik_map.get(key)
# #                     if not datchik:
# #                         continue
# #                     if key not in temp_buffer:
# #                         temp_buffer[key] = {
# #                             "bosim": None, "temperatura": None,
# #                             "x": None, "y": None, "z": None,
# #                             "x_temp": None, "y_temp": None, "z_temp": None,
# #                             "loyqa": None
# #                         }
# #                     temp_buffer[key][key_name] = to_float(val)

# #                 # Loyqa ustunlarini alohida olish
# #                 elif "loyqa" in col.lower():
# #                     m = re.search(r"V\/S\s*(\d+)", col, re.IGNORECASE)
# #                     if not m:
# #                         continue
# #                     sensor_number = int(m.group(1))
# #                     # Lokatsiya id ni avtomatik topish (agar Datchik mavjud bo'lsa)
# #                     # default: birinchi location.id bilan bog'lanadi
# #                     loc_candidates = [d.location.id for d in Datchik.objects.filter(title=str(sensor_number))]
# #                     if not loc_candidates:
# #                         continue
# #                     loc_id = loc_candidates[0]
# #                     key = f"{loc_id}:{sensor_number}"
# #                     datchik = datchik_map.get(key)
# #                     if not datchik:
# #                         continue
# #                     if key not in temp_buffer:
# #                         temp_buffer[key] = {
# #                             "bosim": None, "temperatura": None,
# #                             "x": None, "y": None, "z": None,
# #                             "x_temp": None, "y_temp": None, "z_temp": None,
# #                             "loyqa": None
# #                         }
# #                     temp_buffer[key]["loyqa"] = to_float(val)

# #             # Loglarni yaratish
# #             for key, values in temp_buffer.items():
# #                 datchik = datchik_map.get(key)
# #                 if not datchik:
# #                     continue

# #                 logs.append(DatchikLog(
# #                     formula=getattr(datchik, "formula", None),
# #                     sana=record_date,
# #                     bosim=apply_formula(datchik, values.get("bosim"), "bosim"),
# #                     bosim_m=apply_formula(datchik, values.get("bosim"), "bosim_m"),
# #                     bosim_sm=apply_formula(datchik, values.get("bosim"), "bosim_sm"),
# #                     bosim_mm=apply_formula(datchik, values.get("bosim"), "bosim_mm"),
# #                     suv_sathi=apply_formula(datchik, values.get("bosim"), "suv_sathi"),
# #                     temperatura=apply_formula(datchik, values.get("temperatura"), "temperatura"),
# #                     suv_sarfi=apply_formula(datchik, values.get("bosim"), "suv_sarfi"),
# #                     loyqaligi=apply_formula(datchik, values.get("loyqa"), "loyqa"),
# #                     bosim_x=apply_formula(datchik, values.get("x"), "x"),
# #                     bosim_y=apply_formula(datchik, values.get("y"), "y"),
# #                     bosim_z=apply_formula(datchik, values.get("z"), "z"),
# #                     temperatura_x=apply_formula(datchik, values.get("x_temp"), "x_temp"),
# #                     temperatura_y=apply_formula(datchik, values.get("y_temp"), "y_temp"),
# #                     temperatura_z=apply_formula(datchik, values.get("z_temp"), "z_temp"),
# #                 ))

# #         if logs:
# #             DatchikLog.objects.bulk_create(logs)
# #             self.stdout.write(self.style.SUCCESS(f"{len(logs)} ta log saqlandi"))
# #         else:
# #             self.stdout.write(self.style.WARNING("Hech qanday log saqlanmadi"))

# # # # # from django.core.management.base import BaseCommand
# # # # # from django.utils.dateparse import parse_datetime

# # # # # from app.management.commands.csv_reader import read_all_csv_from_folder
# # # # # from app.models import Datchik, DatchikLog


# # # # # def to_float(val):
# # # # #     if val in (None, "", "N.C.", "  NAN"):
# # # # #         return None
# # # # #     try:
# # # # #         return float(val)
# # # # #     except ValueError:
# # # # #         return None


# # # # # def get_datchik_title(column_name):
# # # # #     if "bosim" in column_name:
# # # # #         return column_name.replace(" bosim", "").strip()
# # # # #     if "temp" in column_name:
# # # # #         return column_name.replace(" temp", "").strip()
# # # # #     return None


# # # # # def apply_formula(datchik, raw_value):
# # # # #     if raw_value is None:
# # # # #         return None

# # # # #     if not hasattr(datchik, "formula"):
# # # # #         return raw_value

# # # # #     f = datchik.formula

# # # # #     try:
# # # # #         return eval(
# # # # #             f.formula,
# # # # #             {"__builtins__": {}},
# # # # #             {
# # # # #                 "x": raw_value,
# # # # #                 "A": f.A,
# # # # #                 "B": f.B,
# # # # #                 "C": f.C,
# # # # #                 "D": f.D
# # # # #             }
# # # # #         )
# # # # #     except Exception:
# # # # #         return raw_value


# # # # # class Command(BaseCommand):
# # # # #     help = "Import datchik logs from CSV"

# # # # #     def handle(self, *args, **options):

# # # # #         folder = "C:\\Users\\user\\Desktop\\ftp\\omnialog_885_shelemer"
# # # # #         rows = read_all_csv_from_folder(folder)

# # # # #         print(rows)

# # # # #         header = None
# # # # #         start_index = 0


# # # # #         for i, row in enumerate(rows):
# # # # #             print(row, row[0])
# # # # #             if row and row[0] == "Date Time":
# # # # #                 header = row
# # # # #                 start_index = i + 1
# # # # #                 break

# # # # #         if not header:
# # # # #             self.stdout.write(self.style.ERROR("Header topilmadi"))
# # # # #             return

# # # # #         datchik_map = {d.title: d for d in Datchik.objects.all()}

# # # # #         logs = []

# # # # #         for row in rows[start_index:]:
# # # # #             if not row:
# # # # #                 continue

# # # # #             record = {}
# # # # #             for i, col in enumerate(header):
# # # # #                 record[col] = row[i] if i < len(row) else None

# # # # #             record_date = parse_datetime(
# # # # #                 record["Date Time"].replace("/", "-")
# # # # #             )

# # # # #             temp_buffer = {}

# # # # #             for col, val in record.items():
# # # # #                 datchik_title = get_datchik_title(col)
# # # # #                 if not datchik_title:
# # # # #                     continue

# # # # #                 if datchik_title not in datchik_map:
# # # # #                     continue

# # # # #                 if datchik_title not in temp_buffer:
# # # # #                     temp_buffer[datchik_title] = {
# # # # #                         "pressure": None,
# # # # #                         "temperature": None
# # # # #                     }

# # # # #                 if "bosim" in col:
# # # # #                     temp_buffer[datchik_title]["pressure"] = to_float(val)

# # # # #                 if "temp" in col:
# # # # #                     temp_buffer[datchik_title]["temperature"] = to_float(val)

# # # # #             for title, values in temp_buffer.items():
# # # # #                 datchik = datchik_map[title]
# # # # #                 pressure = apply_formula(datchik, values["pressure"])
# # # # #                 temperature = apply_formula(datchik, values["temperature"])

# # # # #                 logs.append(
# # # # #                 DatchikLog(
# # # # #                     datchik=datchik,
# # # # #                     record_date=record_date,
# # # # #                     pressure=pressure,
# # # # #                     temperature=temperature,
# # # # #                 )
# # # # #             )

# # # # #         DatchikLog.objects.bulk_create(logs)

# # # # #         self.stdout.write(
# # # # #             self.style.SUCCESS(f"{len(logs)} ta log saqlandi")
# # # # #         )

# # # # from django.core.management.base import BaseCommand
# # # # from django.utils.dateparse import parse_datetime
# # # # import re
# # # # from app.management.commands.csv_reader import read_csv
# # # # from app.models import Datchik, DatchikLog, DatchikFormula

# # # # def to_float(val):
# # # #     if val in (None, "", "N.C.", "  NAN", "NAN"):
# # # #         return None
# # # #     try:
# # # #         return float(val)
# # # #     except ValueError:
# # # #         return None


# # # # def get_datchik_title(column_name):
# # # #     if "bosimi" in column_name:
# # # #         return column_name.replace(" bosimi", "_bosimi").strip()
# # # #     if "temp" in column_name:
# # # #         return column_name.replace(" temp", "_temp").strip()
# # # #     return None


# # # # def apply_formula(datchik, raw_value, formula_type='Bosim'):
# # # #     if raw_value is None:
# # # #         return None

# # # #     if not hasattr(datchik, "formula") or not datchik.formula:
# # # #         return raw_value

# # # #     formula_obj = datchik.formula.last()

# # # #     if formula_type == 'Bosim':
# # # #         f = formula_obj.bosim_formula
# # # #     elif formula_type == 'Bosim_m':
# # # #         f = formula_obj.bosim_m_formula
# # # #     elif formula_type == 'Bosim_sm':
# # # #         f = formula_obj.bosim_sm_formula
# # # #     elif formula_type == 'Bosim_mm':
# # # #         f = formula_obj.bosim_mm_formula
# # # #     elif formula_type == 'Suv_sathi':
# # # #         f = formula_obj.suv_sathi_formula
# # # #     elif formula_type == 'Temperatura':
# # # #         f = formula_obj.temperatura_formula
# # # #     elif formula_type == 'Suv_sarfi':
# # # #         f = formula_obj.suv_sarfi_formula
# # # #     elif formula_type == 'Loyqaligi':
# # # #         f = formula_obj.loyqaligi_formula

# # # #     try:
# # # #         return eval(
# # # #             f.formula,
# # # #             {"__builtins__": {}},
# # # #             {
# # # #                 "x": raw_value,
# # # #                 "A": Datchik.A,
# # # #                 "B": Datchik.B,
# # # #                 "C": Datchik.C,
# # # #                 "D": Datchik.D
# # # #             }
# # # #         )

# # # #     except Exception:
# # # #         return raw_value


# # # # class Command(BaseCommand):
# # # #     help = "Import datchik logs from CSV"

# # # #     def handle(self, *args, **options):
# # # #         # folder = "C:\\Users\\user\\Desktop\\ftp\\omnialog_885_shelemer"
# # # #         rows = read_csv("mLog_22_12_25__15_42_29.csv")
# # # #         # print(rows) 

# # # #         if not rows:
# # # #             self.stdout.write(self.style.ERROR("CSV fayl topilmadi yoki bo'sh"))
# # # #             return

# # # #         header = None
# # # #         start_index = 0


# # # #         for i, row in enumerate(rows):
# # # #             # print("nechta",row)
# # # #             if row and row[0] == "Date Time":
# # # #                 header = row
# # # #                 # print(header)
# # # #                 start_index = i + 1
# # # #                 break

# # # #         if not header:
# # # #             self.stdout.write(self.style.ERROR("Header topilmadi"))
# # # #             return


# # # #         datchik_map = {(d.title): d for d in Datchik.objects.all()}
# # # #         print(datchik_map)

# # # #         logs = []

# # # #         for row in rows[start_index:]:
# # # #             if not row:
# # # #                 continue


# # # #             record = {header[i]: row[i] if i < len(row) else None for i in range(len(header))}

# # # #             record_date = parse_datetime(record["Date Time"].replace("/", "-"))

# # # #             temp_buffer = {}


# # # #             for col, val in record.items():
# # # #                 datchik_title = get_datchik_title(col)
# # # #                 if not datchik_title:
# # # #                     continue

# # # #                 if datchik_title not in datchik_map:
# # # #                     continue

# # # #                 if datchik_title not in temp_buffer:
# # # #                     temp_buffer[key] = {
# # # #                         "pressure": None,
# # # #                         "temperature": None
# # # #                     }

# # # #                 if "bosim" in col:
# # # #                     temp_buffer[key]["bosim"] = to_float(val)

# # # #                 if "temp" in col:
# # # #                     temp_buffer[key]["temperatura"] = to_float(val)


# # # #             for key, values in temp_buffer.items():
# # # #                 datchik = datchik_map.get(key)
# # # #                 if not datchik:
# # # #                     continue

# # # #                 bosim = apply_formula(datchik, values["bosim"],)
# # # #                 bosim_m = apply_formula(datchik, values["bosim"]*0.10119,)
# # # #                 bosim_sm = apply_formula(datchik, values["bosim"]*0.10119*100,)
# # # #                 bosim_mm = apply_formula(datchik, values["bosim"]*0.10119*100*10,)
# # # #                 suv_sathi = apply_formula(datchik, values["bosim"]*0.10119*100,)
# # # #                 temperatura = apply_formula(datchik, values["temperatura"],)
# # # #                 suv_sarfi = apply_formula(datchik, values["bosim"]*0.10119*100,)
# # # #                 # loyqaligi = models.FloatField(null=True, blank=True)


# # # #                 logs.append(
# # # #                     DatchikLog(
# # # #                         datchik=datchik,
# # # #                         sana=record_date,
# # # #                         bosim=bosim,
# # # #                         bosim_m=bosim_m,
# # # #                         bosim_sm=bosim_sm,
# # # #                         bosim_mm=bosim_mm,
# # # #                         suv_sathi=suv_sathi,
# # # #                         temperatura=temperatura,
# # # #                         suv_sarfi=suv_sarfi,
                        
# # # #                     )
# # # #                 )

# # # #         if logs:
# # # #             DatchikLog.objects.bulk_create(logs)

# # # #         self.stdout.write(self.style.SUCCESS(f"{len(logs)} ta log saqlandi"))

# # # # from django.core.management.base import BaseCommand
# # # # from django.utils.dateparse import parse_datetime
# # # # import re
# # # # from app.management.commands.csv_reader import read_all_csv_from_folder
# # # # from app.models import Datchik, DatchikLog


# # # # def to_float(val):
# # # #     if val in (None, "", "N.C.", "  NAN", "NAN"):
# # # #         return None
# # # #     try:
# # # #         return float(val)
# # # #     except ValueError:
# # # #         return None


# # # # def apply_formula(datchik, raw_value):
# # # #     if raw_value is None:
# # # #         return None
# # # #     if not hasattr(datchik, "formula") or not datchik.formula:
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
# # # #     help = "Import datchik logs from CSV and apply formulas"

# # # #     def handle(self, *args, **options):
# # # #         folder = "C:\\Users\\user\\Desktop\\ftp\\omnialog_885_shelemer"
# # # #         rows = read_all_csv_from_folder(folder)

# # # #         if not rows:
# # # #             self.stdout.write(self.style.ERROR("CSV fayl topilmadi yoki bo'sh"))
# # # #             return

# # # #         # Header qatorini topamiz
# # # #         header = None
# # # #         start_index = 0
# # # #         for i, row in enumerate(rows):
# # # #             if row and row[0] == "Date Time":
# # # #                 header = row
# # # #                 start_index = i + 1
# # # #                 break

# # # #         if not header:
# # # #             self.stdout.write(self.style.ERROR("Header topilmadi"))
# # # #             return

# # # #         # Barcha datchiklarni bazadan olamiz va nomini normalizatsiya qilamiz
# # # #         datchik_map = {normalize_name(d.title): d for d in Datchik.objects.all()}

# # # #         logs = []

# # # #         # Har bir qatorni CSVdan o‘qib chiqamiz
# # # #         for row in rows[start_index:]:
# # # #             if not row:
# # # #                 continue

# # # #             record = {header[i]: row[i] if i < len(row) else None for i in range(len(header))}
# # # #             record_date = parse_datetime(record["Date Time"].replace("/", "-"))
# # # #             if not record_date:
# # # #                 continue

# # # #             temp_buffer = {}

# # # #             for col, val in record.items():
# # # #                 datchik_title = get_datchik_title(col)
# # # #                 if not datchik_title:
# # # #                     continue

# # # #                 key = normalize_name(datchik_title)

# # # #                 if key not in datchik_map:
# # # #                     continue

# # # #                 if key not in temp_buffer
# # # #                     temp_buffer[key] = {
# # # #                         "pressure": None,
# # # #                         "temperature": None
# # # #                     }

# # # #                 if "bosim" in col or "Z" in col or "X" in col or "Y" in col:  # bosim yoki boshqa param
# # # #                     temp_buffer[key]["pressure"] = to_float(val)
# # # #                 if "temp" in col or "T" in col:  # temp bilan tugagan ustunlar
# # # #                     temp_buffer[key]["temperature"] = to_float(val)

# # # #             # Loglarni yaratamiz
# # # #             for key, values in temp_buffer.items():
# # # #                 datchik = datchik_map.get(key)
# # # #                 if not datchik:
# # # #                     continue

# # # #                 pressure = apply_formula(datchik, values["pressure"])
# # # #                 temperature = apply_formula(datchik, values["temperature"])

# # # #                 logs.append(
# # # #                     DatchikLog(
# # # #                         datchik=datchik,
# # # #                         record_date=record_date,
# # # #                         pressure=pressure,
# # # #                         temperature=temperature,
# # # #                     )
# # # #                 )

# # # #         # Bulk create bilan saqlaymiz
# # # #         if logs:
# # # #             DatchikLog.objects.bulk_create(logs)

# # # #         self.stdout.write(self.style.SUCCESS(f"{len(logs)} ta log saqlandi"))

# # # from django.core.management.base import BaseCommand
# # # from django.utils.dateparse import parse_datetime
# # # from app.management.commands.csv_reader import read_csv
# # # from app.models import Datchik, DatchikLog, DatchikFormula


# # # # ===================== YORDAMCHI =====================

# # # def to_float(val):
# # #     if val in (None, "", "N.C.", "NAN", "  NAN"):
# # #         return None
# # #     try:
# # #         return float(val)
# # #     except Exception:
# # #         return None


# # # def normalize(col):
# # #     return col.lower().strip()


# # # def get_datchik_title(column_name):
# # #     """
# # #     Column name'dan datchik title'ni ajratadi.
# # #     Misol: 'PO-82 bosim' -> 'PO-82'
# # #     """
# # #     col = normalize(column_name)

# # #     keywords = ["bosimi", "bosim", "temp", "loyqa"]

# # #     for k in keywords:
# # #         if k in col:  # oldida yoki orqasida bo‘lishi mumkin
# # #             return column_name.lower().replace(k, "").strip()

# # #     # Agar hech nima topilmasa, asl nomni qaytarish
# # #     return column_name.strip()


# # # def get_value_type(column_name):
# # #     """
# # #     Column name'dan qiymat turini aniqlaydi
# # #     """
# # #     col = normalize(column_name)

# # #     if "bosimi" in col:
# # #         return "bosimi"
# # #     if "bosim" in col:
# # #         return "bosim"
# # #     if "temp" in col:
# # #         return "temperatura"
# # #     if "loyqa" in col:
# # #         return "loyqa"

# # #     return None

# # # def apply_formula(datchik, raw_value, formula_type):
# # #     if raw_value is None:
# # #         return None

# # #     if not hasattr(datchik, "formula") or not datchik.formula:
# # #         return raw_value

# # #     formula = datchik.formula

# # #     f = {
# # #         "bosim": formula.bosim_formula,
# # #         "bosim_m": formula.bosim_m_formula,
# # #         "bosim_sm": formula.bosim_sm_formula,
# # #         "bosim_mm": formula.bosim_mm_formula,
# # #         "suv_sathi": formula.suv_sathi_formula,
# # #         "temperatura": formula.temperatura_formula,
# # #         "suv_sarfi": formula.suv_sarfi_formula,
# # #         "loyqa": formula.loyqaligi_formula,
# # #     }.get(formula_type)

# # #     if not f:
# # #         return raw_value

# # #     try:
# # #         return eval(
# # #             f,
# # #             {"__builtins__": {}},
# # #             {
# # #                 "x": raw_value,
# # #                 "A": datchik.A,
# # #                 "B": datchik.B,
# # #                 "C": datchik.C,
# # #                 "D": datchik.D
# # #             }
# # #         )
# # #     except Exception:
# # #         return raw_value


# # # # ===================== COMMAND =====================

# # # class Command(BaseCommand):
# # #     help = "Import datchik logs from CSV"

# # #     def handle(self, *args, **options):
# # #         rows = read_csv("mLog_22_12_25__15_42_29.csv")

# # #         if not rows:
# # #             self.stdout.write(self.style.ERROR("CSV bo'sh yoki topilmadi"))
# # #             return

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

# # #         datchik_map = {d.title: d for d in Datchik.objects.select_related("formula")}
# # #         logs = []

# # #         for row in rows[start_index:]:
# # #             if not row:
# # #                 continue

# # #             record = {header[i]: row[i] if i < len(row) else None for i in range(len(header))}
# # #             record_date = parse_datetime(record["Date Time"].replace("/", "-"))

# # #             temp_buffer = {}

# # #             for col, val in record.items():
# # #                 datchik_title = get_datchik_title(col)
# # #                 value_type = get_value_type(col)

# # #                 if not datchik_title or not value_type:
# # #                     continue

# # #                 if datchik_title not in datchik_map:
# # #                     continue

# # #                 if datchik_title not in temp_buffer:
# # #                     temp_buffer[datchik_title] = {
# # #                         "bosim": None,
# # #                         "temperatura": None,
# # #                         "loyqa": None
# # #                     }

# # #                 temp_buffer[datchik_title][value_type] = to_float(val)

# # #             for key, values in temp_buffer.items():
# # #                 datchik = datchik_map.get(key)
# # #                 if not datchik:
# # #                     continue

# # #                 bosim_raw = None
# # #                 for key in values:
# # #                     if "bosim" in key.lower():  # "bosim", "bosimi", "bosim_1" ham ishlaydi
# # #                         bosim_raw = values[key]
# # #                         break

# # #                 try:
# # #                     formula_obj = datchik.formula
# # #                 except Datchik.formula.RelatedObjectDoesNotExist:
# # #                     formula_obj = None

# # #                 logs.append(
# # #                     DatchikLog(
# # #                         formula=formula_obj,   # ✅ endi crash bo‘lmaydi
# # #                         sana=record_date,

# # #                         bosim=apply_formula(datchik, bosim_raw, "bosim"),
# # #                         bosim_m=apply_formula(datchik, bosim_raw if bosim_raw else None, "bosim_m"),
# # #                         bosim_sm=apply_formula(datchik, bosim_raw if bosim_raw else None, "bosim"),
# # #                         bosim_mm=apply_formula(datchik, bosim_raw if bosim_raw else None, "bosim"),

# # #                         suv_sathi=apply_formula(datchik, bosim_raw if bosim_raw else None, "suv_sathi"),
# # #                         temperatura=apply_formula(datchik, values["temp"], "temperatura"),
# # #                         suv_sarfi=apply_formula(datchik, bosim_raw if bosim_raw else None, "suv_sarfi"),
# # #                         loyqaligi=apply_formula(datchik, values["loyqa"], "loyqa"),
# # #             )
# # #         )


# # #         if logs:
# # #             DatchikLog.objects.bulk_create(logs)

# # #         self.stdout.write(self.style.SUCCESS(f"{len(logs)} ta log saqlandi"))


# from django.core.management.base import BaseCommand
# from django.utils.dateparse import parse_datetime
# from app.management.commands.csv_reader import read_csv
# import re
# from app.models import Datchik, DatchikLog, DatchikFormula

# def to_float(val):
#     """Qiymatni float ga aylantirish, bo'sh yoki N.C. bo'lsa None"""
#     if val in (None, "", "N.C.", "NAN", "  NAN", "-"):
#         return None
#     try:
#         return float(val)
#     except Exception:
#         return None

# def parse_sh_column(column_name):
#     """
#     SH/885/7 Y  -> ('sd.885.d-07', 'bosim_y')
#     SH/8/7 YT   -> ('sd.008.d-07', 'temperatura_y')
#     SH/804/7 Z  -> ('sd.804.d-07', 'bosim_z')
#     """
#     col = column_name.strip()

#     m = re.match(r"SH/(\d+)/(\d+)\s*(X|Y|Z|XT|YT|ZT)", col)
#     if not m:
#         return None, None

#     location, sensor_no, axis = m.groups()

#     datchik_key = f"sd.{int(location):03d}.d-{int(sensor_no):02d}"

#     axis_map = {
#         "X": "bosim_x",
#         "Y": "bosim_y",
#         "Z": "bosim_z",
#         "XT": "temperatura_x",
#         "YT": "temperatura_y",
#         "ZT": "temperatura_z",
#     }

#     return datchik_key, axis_map.get(axis)


# def normalize(col):
#     return col.lower().strip()


# def get_datchik_title(column_name):
#     """
#     Column name'dan datchik title'ni ajratadi.
#     Misol: 'PO-82 bosim' -> 'PO-82'
#     """
#     col = normalize(column_name)
#     keywords = ["bosimi", "bosim", "temp", "loyqa", "X", "Y", "Z", "XT", "YT", "ZT"]

#     for k in keywords:
#         if k in col: 
#             return column_name.lower().replace(k, "").strip()

#     return column_name.strip()


# def get_value_type(column_name):
#     """
#     Column name'dan qiymat turini aniqlaydi
#     """
#     col = normalize(column_name)
#     if "bosimi" in col:
#         return "bosimi"
#     if "bosim" in col:
#         return "bosim"
#     if "temp" in col:
#         return "temperatura"
#     if "loyqa" in col:
#         return "loyqa"
#     if "X" in col:
#         return "bosim_x"
#     if "Y" in col:
#         return "bosim_y"
#     if "Z" in col:
#         return "bosim_z"
#     if "XT" in col:
#         return "temperatura_x"
#     if "YT" in col:
#         return "temperatura_y"
#     if "ZT" in col:
#         return "temperatura_z"
    
    
#     return None


# def apply_formula(datchik, raw_value, formula_type):
#     """
#     Raw value ga datchik formulasini qo'llash.
#     Agar formula bo'lmasa → None qaytariladi (raw value tushmaydi)
#     """
#     if raw_value is None:
#         return None

#     formula = getattr(datchik, "formula", None)
#     if not formula:
#         return None

#     f = {
#         "bosim": formula.bosim_formula,
#         "bosim_m": formula.bosim_m_formula,
#         "bosim_sm": formula.bosim_sm_formula,
#         "bosim_mm": formula.bosim_mm_formula,
#         "suv_sathi": formula.suv_sathi_formula,
#         "temperatura": formula.temperatura_formula,
#         "suv_sarfi": formula.suv_sarfi_formula,
#         "loyqa": formula.loyqaligi_formula,
#         "bosim_x": formula.bosim_x_formula,
#         "temperatura_x": formula.temperatura_y_formula,
#         "bosim_y": formula.bosim_y_formula,
#         "temperatura_y": formula.temperatura_x_formula,
#         "bosim_z": formula.bosim_z_formula,
#         "temperatura_z": formula.temperatura_z_formula,
#     }.get(formula_type)

#     if not f:
#         return None

#     try:
#         return eval(
#             f,
#             {"__builtins__": {}},
#             {
#                 "x": raw_value,
#                 "A": getattr(datchik, "A", 0),
#                 "B": getattr(datchik, "B", 0),
#                 "C": getattr(datchik, "C", 0),
#                 "D": getattr(datchik, "D", 0),
#             }
#         )
#     except Exception:
#         return None 



# class Command(BaseCommand):

#     def handle(self, *args, **options):
#         rows = read_csv("mLog_22_12_25__15_51_55.csv")

#         if not rows:
#             self.stdout.write(self.style.ERROR("CSV bo'sh yoki topilmadi"))
#             return

#         header = None
#         start_index = 0
#         for i, row in enumerate(rows):
#             if row and row[0].lower().strip() in ("date time", "datetime"):
#                 header = row
#                 start_index = i + 1
#                 break

#         if not header:
#             self.stdout.write(self.style.ERROR("Header topilmadi"))
#             return

#         # Datchiklarni bazadan olish
#         datchik_map = {d.title.lower(): d for d in Datchik.objects.select_related("formula")}
#         logs = []

#         for row in rows[start_index:]:
#             if not row:
#                 continue

#             record = {header[i]: row[i] if i < len(row) else None for i in range(len(header))}
#             record_date_raw = record.get("Date Time") or record.get("datetime")
#             if not record_date_raw:
#                 continue

#             record_date = parse_datetime(record_date_raw.replace("/", "-"))
#             if not record_date:
#                 continue

#             temp_buffer = {}

#             # Har bir ustunni ajratish
#             for col, val in record.items():
#                 datchik_title = get_datchik_title(col)
#                 value_type = get_value_type(col)

#                 if not datchik_title or not value_type:
#                     continue

#                 datchik_key = datchik_title.lower()
#                 if datchik_key not in datchik_map:
#                     continue

#                 if datchik_key not in temp_buffer:
#                     temp_buffer[datchik_key] = {
#                         "bosim": None,
#                         "temperatura": None,
#                         "loyqa": None,
#                         "bosim_x": None,
#                         "bosim_y": None,
#                         "bosim_z": None,
#                         "temperatura_x": None,
#                         "temperatura_y": None,
#                         "temperatura_z": None
#                     }

#                 temp_buffer[datchik_key][value_type] = to_float(val)

#             # Log obyektlarini yaratish
#             for key, values in temp_buffer.items():
#                 datchik = datchik_map.get(key)
#                 if not datchik:
#                     continue

#                 # Bosim_raw topish (bosim yoki bosimi)
#                 bosim_raw = None
#                 for k in values:
#                     if "bosim" in k.lower():
#                         bosim_raw = values[k]
#                         break
#                 temperatura_raw = values.get("temperatura")
#                 loyqa_raw = values.get("loyqa")
#                 bosim_x_raw = values.get("bosim_x")
#                 bosim_y_raw = values.get("bosim_y")
#                 bosim_z_raw = values.get("bosim_z")
#                 temperatura_x_raw = values.get("temperatura_x")
#                 temperatura_y_raw = values.get("temperatura_y")
#                 temperatura_z_raw = values.get("temperatura_z")
                

#                 logs.append(
#                     DatchikLog(
#                         formula=getattr(datchik, "formula", None),
#                         sana=record_date,
#                         bosim=apply_formula(datchik, bosim_raw, "bosim"),
#                         bosim_m=apply_formula(datchik, bosim_raw, "bosim_m"),
#                         bosim_sm=apply_formula(datchik, bosim_raw, "bosim_sm"),
#                         bosim_mm=apply_formula(datchik, bosim_raw, "bosim_mm"),
#                         suv_sathi=apply_formula(datchik, bosim_raw, "suv_sathi"),
#                         temperatura=apply_formula(datchik, temperatura_raw, "temperatura"),
#                         suv_sarfi=apply_formula(datchik, bosim_raw, "suv_sarfi"),
#                         loyqaligi=apply_formula(datchik, loyqa_raw, "loyqa"),
#                         bosim_x=apply_formula(datchik,bosim_x_raw, "bosim_x"),
#                         bosim_y=apply_formula(datchik,bosim_y_raw, "bosim_y"),
#                         bosim_z=apply_formula(datchik,bosim_z_raw, "bosim_z"),
#                         temperatura_x=apply_formula(datchik,temperatura_x_raw, "temperatura_x"),
#                         temperatura_y=apply_formula(datchik,temperatura_y_raw, "temperatura_y"),
#                         temperatura_z=apply_formula(datchik,temperatura_z_raw, "temperatura_z"),
#                     )
#                 )

#         if logs:
#             DatchikLog.objects.bulk_create(logs)

#         self.stdout.write(self.style.SUCCESS(f"{len(logs)} ta log saqlandi"))

from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from app.management.commands.csv_reader import read_csv
from app.models import Datchik, DatchikLog
import re

def to_float(val):
    if val in (None, "", "N.C.", "NAN", "  NAN", "-"):
        return None
    try:
        return float(str(val).strip())
    except Exception:
        return None

def normalize(col):
    return col.lower().strip()


def get_datchik_title(column_name):

    col = normalize(column_name)
    keywords = ["bosimi", "bosim", "temp", "loyqa", "X", "Y", "Z", "XT", "YT", "ZT"]

    for k in keywords:
        if k in col: 
            return column_name.lower().replace(k, "").strip()

    return column_name.strip()

def parse_sh_column(column_name):
    """
    SH/804/12 Y  -> ('sh.d-012', 'bosim_y')
    SH/885/7 ZT  -> ('sh.d-007', 'temperatura_z')
    """
    col = column_name.strip()

    m = re.match(r"SH/(\d+)/(\d+)\s*(X|Y|Z|XT|YT|ZT)", col)
    if not m:
        return None, None

    _, sensor_no, axis = m.groups()

    datchik_key = f"sh.d-{int(sensor_no):03d}"

    axis_map = {
        "X": "bosim_x",
        "Y": "bosim_y",
        "Z": "bosim_z",
        "XT": "temperatura_x",
        "YT": "temperatura_y",
        "ZT": "temperatura_z",
    }

    return datchik_key, axis_map.get(axis)



def apply_formula(datchik, raw_value, formula_type):
    if raw_value is None:
        return None

    formula = getattr(datchik, "formula", None)
    if not formula:
        return None

    formula_map = {
        "bosim_x": formula.bosim_x_formula,
        "bosim_y": formula.bosim_y_formula,
        "bosim_z": formula.bosim_z_formula,
        "temperatura_x": formula.temperatura_x_formula,
        "temperatura_y": formula.temperatura_y_formula,
        "temperatura_z": formula.temperatura_z_formula,
    }

    f = formula_map.get(formula_type)
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
    help = "Import SH CSV logs"

    def handle(self, *args, **options):
        rows = read_csv("mLog_22_12_25__15_51_55.csv")

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

        
        datchik_map = {
            d.title.lower(): d
            for d in Datchik.objects.select_related("formula")
        }

        logs = []

        for row in rows[start_index:]:
            if not row:
                continue

            record = {
                header[i]: row[i] if i < len(row) else None
                for i in range(len(header))
            }

            record_date_raw = record.get("Date Time") or record.get("datetime")
            if not record_date_raw:
                continue

            record_date = parse_datetime(record_date_raw.replace("/", "-"))
            if not record_date:
                continue

            temp_buffer = {}

            for col, val in record.items():
                datchik_key, value_type = parse_sh_column(col)

                if not datchik_key or not value_type:
                    continue

                if datchik_key not in datchik_map:
                    continue

                if datchik_key not in temp_buffer:
                    temp_buffer[datchik_key] = {
                        "bosim_x": None,
                        "bosim_y": None,
                        "bosim_z": None,
                        "temperatura_x": None,
                        "temperatura_y": None,
                        "temperatura_z": None,
                    }

                temp_buffer[datchik_key][value_type] = to_float(val)

            
            for key, values in temp_buffer.items():
                datchik = datchik_map.get(key)
                if not datchik:
                    continue

                logs.append(
                    DatchikLog(
                        formula=datchik.formula,
                        sana=record_date,
                        bosim_x=apply_formula(datchik, values["bosim_x"], "bosim_x"),
                        bosim_y=apply_formula(datchik, values["bosim_y"], "bosim_y"),
                        bosim_z=apply_formula(datchik, values["bosim_z"], "bosim_z"),
                        temperatura_x=apply_formula(datchik, values["temperatura_x"], "temperatura_x"),
                        temperatura_y=apply_formula(datchik, values["temperatura_y"], "temperatura_y"),
                        temperatura_z=apply_formula(datchik, values["temperatura_z"], "temperatura_z"),
                    )
                )

        if logs:
            DatchikLog.objects.bulk_create(logs)

        self.stdout.write(self.style.SUCCESS(f"{len(logs)} ta log saqlandi"))
