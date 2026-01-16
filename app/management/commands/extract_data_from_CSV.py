from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from app.management.commands.csv_reader import read_csv
from app.models import (
    Datchik,
    DatchikLog,
    DatchikFormula,
    DataloggerChannel,
)
import re


def to_float(val):
    """Qiymatni float ga aylantirish"""
    if val in (None, "", "N.C.", "NAN", "  NAN"):
        return None
    try:
        return float(val)
    except Exception:
        return None


def parse_vw_column(column_name):
    """
    freqInHz-119346-VW-Ch1 →
    (node_id, channel, value_type)
    """
    m = re.match(
        r"(freqInHz|freqSqInDigit|thermResInOhms)-(\d+)-VW-(Ch\d+)",
        column_name.strip().replace('"','')
    )
    print(m)
    if not m:
        return None

    signal, node_id, ch = m.groups()
    ch = ch.lower()

    if signal in ("freqInHz", "freqSqInDigit"):
        value_type = "bosim"
    elif signal == "thermResInOhms":
        value_type = "temperatura"
    else:
        return None

    return node_id, ch, value_type



def apply_formula(datchik, raw_value, formula_type):
    """
    Raw value ga datchik formulasini qo'llash.
    Formula bo'lmasa → None
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
                "A": datchik.A or 0,
                "B": datchik.B or 0,
                "C": datchik.C or 0,
                "D": datchik.D or 0,
            }
        )
    except Exception:
        return None


class Command(BaseCommand):
    help = "Import SIMSIZ (VW) datalogger CSV files"

    def handle(self, *args, **options):
        # folder = "C:\\Users\\user\\Desktop\\ftp\\gateway\\bosimsiz"
        rows = read_csv("119346-readings-2025_12_21_05_00_00.csv")
        print(rows)
        

        if not rows:
            self.stdout.write(self.style.ERROR("CSV bo'sh yoki topilmadi"))
            return

        header = None
        start_index = 0

        for i, row in enumerate(rows):
            if row and row[0].strip().lower() in ("date-and-time", "datetime"):
                header = row
                start_index = i + 1
                break

        if not header:
            self.stdout.write(self.style.ERROR("Header topilmadi"))
            return

        channel_map = {
            (c.node_id, c.channel.lower()): c.datchik
            for c in DataloggerChannel.objects.select_related("datchik", "datchik__formula")
        }

        logs = []

        for row in rows[start_index:]:
            if not row:
                continue

            record = {
                header[i]: row[i] if i < len(row) else None
                for i in range(len(header))
            }

            record_date_raw = record.get("Date-and-time") or record.get("datetime")
            if not record_date_raw:
                continue

            record_date = parse_datetime(record_date_raw.replace("/", "-"))
            if not record_date:
                continue

            temp_buffer = {}

            for col, val in record.items():
                vw = parse_vw_column(col)
                if not vw:
                    continue

                node_id, ch, value_type = vw
                datchik = channel_map.get((node_id, ch))
                if not datchik:
                    continue

                key = datchik.title.lower()
                if key not in temp_buffer:
                    temp_buffer[key] = {
                        "datchik": datchik,
                        "bosim": None,
                        "temperatura": None,
                        "loyqa": None,
                    }

                temp_buffer[key][value_type] = to_float(val)

            for data in temp_buffer.values():
                datchik = data["datchik"]

                bosim_raw = data.get("bosim")
                temperatura_raw = data.get("temperatura")

                logs.append(
                    DatchikLog(
                        formula=datchik.formula,
                        sana=record_date,
                        bosim=apply_formula(datchik, bosim_raw, "bosim"),
                        bosim_m=apply_formula(datchik, bosim_raw, "bosim_m"),
                        bosim_sm=apply_formula(datchik, bosim_raw, "bosim_sm"),
                        bosim_mm=apply_formula(datchik, bosim_raw, "bosim_mm"),
                        suv_sathi=apply_formula(datchik, bosim_raw, "suv_sathi"),
                        temperatura=apply_formula(datchik, temperatura_raw, "temperatura"),
                        suv_sarfi=apply_formula(datchik, bosim_raw, "suv_sarfi"),
                    )
                )

        if logs:
            DatchikLog.objects.bulk_create(logs)

        self.stdout.write(
            self.style.SUCCESS(f"{len(logs)} ta simsiz log saqlandi")
        )
