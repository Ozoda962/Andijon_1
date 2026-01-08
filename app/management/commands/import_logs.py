# # from django.core.management.base import BaseCommand
# # import csv
# # from app.models import Datchik, DatchikLog
# # from app.csv_reader import get_all_csv_files
# # from app.csv_parses import parse_type_1, parse_type_2, detect_file_type, SENSOR_MAP

# # class Command(BaseCommand):
# #     help = "FTP papkadagi barcha CSV fayllarni import qiladi"

# #     def handle(self, *args, **options):
# #         base_dir = "C:\\Users\\user\\Desktop\\ftp" 
# #         csv_files = get_all_csv_files(base_dir)

# #         for file_path in csv_files:
# #             with open(file_path, newline='', encoding="utf-8") as f:
# #                 header = next(csv.reader(f))
# #             file_type = detect_file_type(header)

# #             if file_type == 1:
# #                 logs = parse_type_1(file_path)
# #             elif file_type == 2:
# #                 logs = parse_type_2(file_path)
# #             else:
# #                 print(f"Noma'lum format: {file_path}")
# #                 continue

# #             for item in logs:
# #                 datchik, _ = Datchik.objects.get_or_create(
# #                     title=item["sensor_key"],
# #                     defaults={"direction": None, "location": None, "section": None}
# #                 )

# #                 field_name = None
# #                 for key, val in SENSOR_MAP.items():
# #                     if key in item["sensor_key"]:
# #                         field_name = val
# #                         break

# #                 if field_name:
# #                     DatchikLog.objects.create(
# #                         datchik=datchik,
# #                         **{field_name: item["value"]},
# #                         record_date=item["time"]
# #                     )

# #             print(f"✅ Import qilindi: {file_path}")


# from django.core.management.base import BaseCommand
# import csv
# from app.models import Datchik, DatchikLog
# from app.csv_reader import get_all_csv_files
# from app.csv_parses import parse_type_1, parse_type_2, detect_file_type, SENSOR_MAP

# class Command(BaseCommand):
#     help = "FTP papkadagi barcha CSV fayllarni import qiladi"

#     def handle(self, *args, **options):
#         base_dir = "C:\\Users\\user\\Desktop\\ftp"  
#         csv_files = get_all_csv_files(base_dir)

#         for file_path in csv_files:
           
#             with open(file_path, newline='', encoding="utf-8") as f:
#                 try:
#                     first_rows = [next(f) for _ in range(10)]
#                 except StopIteration:
#                     continue
           
#             file_type = detect_file_type(first_rows[-1].split(","))

#             if file_type == 1:
#                 logs = parse_type_1(file_path)
#             elif file_type == 2:
#                 logs = parse_type_2(file_path)
#             else:
#                 print(f"Noma'lum format: {file_path}")
#                 continue

#             for item in logs:
#                 try:
#                     datchik = Datchik.objects.get(title=item["sensor_key"])
#                 except Datchik.DoesNotExist:
#                     print(f"Datchik topilmadi: {item['sensor_key']}")
#                     continue

#                 field_name = None
#                 for key, val in SENSOR_MAP.items():
#                     if key in item["sensor_key"]:
#                         field_name = val
#                         break

#                 if field_name:
#                     DatchikLog.objects.create(
#                         datchik=datchik,
#                         **{field_name: item["value"]},
#                         record_date=item["time"]
#                     )

#             print(f"✅ Import qilindi: {file_path}")



from django.core.management.base import BaseCommand
from app.models import Datchik, DatchikLog
from app.management.commands.csv_reader import get_all_csv_files
from app.management.commands.csv_parses import parse_type_1, parse_type_2, detect_file_type, SENSOR_MAP

class Command(BaseCommand):
    help = "FTP papkadagi barcha CSV fayllardan datchik loglarini import qiladi"

    def handle(self, *args, **options):
        base_dir = "C:\\Users\\user\\Desktop\\ftp"
        csv_files = get_all_csv_files(base_dir)

        all_datchiks = {d.title: d for d in Datchik.objects.all()}
        total_logs = 0

        for file_path in csv_files:
            with open(file_path, newline='', encoding="utf-8") as f:
                try:
                    first_rows = [next(f) for _ in range(10)]
                except StopIteration:
                    continue

            file_type = detect_file_type(first_rows[0].split(","))

            if file_type == 1:
                logs_data = parse_type_1(file_path)
            elif file_type == 2:
                logs_data = parse_type_2(file_path)
            else:
                print(f"Noma'lum format: {file_path}")
                continue

            logs_to_create = []
            for item in logs_data:
                datchik_title = item["sensor_key"]
                if datchik_title not in all_datchiks:
                    print(f"Datchik topilmadi: {datchik_title}")
                    continue

                datchik = all_datchiks[datchik_title]

                field_name = None
                for key, val in SENSOR_MAP.items():
                    if key in datchik_title:
                        field_name = val
                        break

                if field_name:
                    logs_to_create.append(
                        DatchikLog(
                            datchik=datchik,
                            record_date=item["time"],
                            **{field_name: item["value"]}
                        )
                    )

            if logs_to_create:
                DatchikLog.objects.bulk_create(logs_to_create)
                total_logs += len(logs_to_create)

            print(f"✅ Import qilindi: {file_path}, loglar soni: {len(logs_to_create)}")

        self.stdout.write(self.style.SUCCESS(f"Umumiy saqlangan loglar: {total_logs}"))
