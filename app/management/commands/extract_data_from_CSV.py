from django.core.management.base import BaseCommand
from app.management.commands.csv_reader import read_csv


class Command(BaseCommand):
    help = "Import piezometers from CSV"

    def handle(self, *args, **options):

        rows = read_csv('65073-readings-2025_12_20_00_00_00.csv')

        meta_data = {}
        measurements = []

        header = None
        data_start_index = 0

        for i, row in enumerate(rows):
            if not row:
                continue

            
            if row[0] == "Date-and-time":
                header = row
                data_start_index = i + 1
                break

            key = row[0]
            value = row[1] if len(row) > 1 and row[1] != "" else None
            meta_data[key] = value

        
        for row in rows[data_start_index:]:
            if not row:
                continue

            record = {}
            for i, col in enumerate(header):
                record[col] = row[i] if i < len(row) and row[i] != "" else None
                
            

            measurements.append(record)
            print(measurements)


            
        self.stdout.write(self.style.SUCCESS("META DATA:"))
        for k, v in meta_data.items():
            self.stdout.write(f"{k}: {v}")

        self.stdout.write(self.style.SUCCESS("\nFIRST MEASUREMENT:"))
        self.stdout.write(str(measurements[0]))

        self.stdout.write(self.style.SUCCESS("\nImport finished"))
