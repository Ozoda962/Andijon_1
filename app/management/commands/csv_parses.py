import csv
from django.utils.dateparse import parse_datetime

SENSOR_MAP = {
    "Temp": "temperature",
    "Temperature": "temperature",
    "bosimi": "pressure",
    "AtmPressure": "pressure",
    "WaterHighPizometr": "water_high_pizometr",
    "WaterHighBef": "water_high_bef",
    "Humidity": "humidity",
    "WaterConsumption": "water_consumption",
    "BlurLevel": "blur_level",
    "DeviationIndicator": "deviation_indicator",
    "SinA": "sin_A",
    "SinB": "sin_B",
    "ShiftX": "shift_X",
    "ShiftY": "shift_Y"
}

def detect_file_type(header):
    if any("Node ID" in h for h in header) or any("freqInHz" in h for h in header):
        return 1
    elif any("Date Time" in h for h in header):
        return 2
    else:
        return 0

def parse_type_1(file_path):
    logs = []
    with open(file_path, newline='', encoding="utf-8") as f:
        rows = list(csv.reader(f))
    if len(rows) < 10:
        return logs

    header = rows[9]
    for data in rows[10:]:
        timestamp = parse_datetime(data[0].replace("/", "-"))
        for i, key in enumerate(header):
            if key in SENSOR_MAP and data[i]:
                try:
                    value = float(data[i])
                except ValueError:
                    continue
                logs.append({
                    "sensor_key": key,
                    "value": value,
                    "time": timestamp
                })
    return logs

def parse_type_2(file_path):
    logs = []
    with open(file_path, newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            timestamp = parse_datetime(row["Date Time"].replace("/", "-"))
            for key, val in row.items():
                if key not in SENSOR_MAP or val in ("", "NAN", "N.C."):
                    continue
                try:
                    value = float(val)
                except ValueError:
                    continue
                logs.append({
                    "sensor_key": key,
                    "value": value,
                    "time": timestamp
                })
    return logs
