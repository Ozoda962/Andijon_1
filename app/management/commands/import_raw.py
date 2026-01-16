# # app/management/commands/import_raw.py
# import os
# import re
# import datetime
# from typing import Optional, Tuple

# from django.core.management.base import BaseCommand
# from django.utils.dateparse import parse_datetime
# from django.db import transaction
# from django.utils import timezone

# from app.management.commands.csv_reader import read_csv_file
# from app.models import Location, Datchik, RawReading, DataloggerChannel


# # ===================== YORDAMCHI =====================

# def to_float(val):
#     if val in (None, "", "-", "N.C.", "NAN", "  NAN"):
#         return None
#     try:
#         return float(str(val).strip())
#     except Exception:
#         return None


# def norm(s) -> str:
#     return str(s).strip().lower() if s is not None else ""


# def parse_dt(s):
#     if not s:
#         return None
#     dt = parse_datetime(str(s).replace("/", "-"))
#     if not dt:
#         return None
#     if timezone.is_naive(dt):
#         dt = timezone.make_aware(dt, timezone.get_current_timezone())
#     return dt


# def is_csv(fn: str) -> bool:
#     return fn.lower().endswith(".csv")


# # ===================== FORMAT TOPISH =====================

# def detect_mode(rows) -> Optional[str]:
#     for r in rows[:80]:
#         if not r:
#             continue
#         first = norm(r[0])
#         if first in ("date time", "datetime"):
#             return "wired"
#         if first in ("date-and-time",):
#             return "wireless"
#     return None


# def find_header(rows, mode: str):
#     header = None
#     start = 0
#     for i, r in enumerate(rows):
#         if not r:
#             continue
#         first = norm(r[0])
#         if mode == "wired" and first in ("date time", "datetime"):
#             header = r
#             start = i + 1
#             break
#         if mode == "wireless" and first in ("date-and-time", "datetime"):
#             header = r
#             start = i + 1
#             break
#     return header, start


# # ===================== WIRED parsers =====================

# # 1) ATVES: "845-2/X" "845-2/Y" "845-2/Z" "845-2/T"
# ATVES_RE = re.compile(r"^(\d+)-(\d+)\/(X|Y|Z|T)$", re.IGNORECASE)

# def parse_atves_column(col: str) -> Optional[Tuple[int, str, str]]:
#     """
#     returns: (loc_code, datchik_title_lower, value_type)
#     datchik_title: "845-2"
#     value_type: deformatsiya_x/y/z yoki temperatura
#     """
#     m = ATVES_RE.match(col.strip())
#     if not m:
#         return None
#     loc_code = int(m.group(1))
#     idx = int(m.group(2))
#     axis = m.group(3).upper()

#     if axis == "X":
#         vtype = "deformatsiya_x"
#     elif axis == "Y":
#         vtype = "deformatsiya_y"
#     elif axis == "Z":
#         vtype = "deformatsiya_z"
#     else:
#         vtype = "temperatura"

#     d_title = f"{loc_code}-{idx}".lower()
#     return loc_code, d_title, vtype


# # 2) SHELEMER: "SH/804/4 X" "SH/804/4 XT" ...
# SH_RE = re.compile(r"^SH\/(\d+)\/(\d+)\s*(X|XT|Y|YT|Z|ZT)$", re.IGNORECASE)

# def format_sh_no(n: int) -> str:
#     # Siz aytgandek:
#     # 4 -> 04, 14 -> 014, 104 -> 104
#     return f"0{n}" if n < 100 else str(n)

# def parse_sh_column(col: str) -> Optional[Tuple[int, str, str]]:
#     m = SH_RE.match(col.strip())
#     if not m:
#         return None

#     loc_code = int(m.group(1))
#     no = int(m.group(2))
#     suffix = m.group(3).upper()

#     axis = suffix.replace("T", "").lower()  # x/y/z
#     if suffix.endswith("T"):
#         vtype = f"temperatura_{axis}"
#     else:
#         vtype = f"deformatsiya_{axis}"

#     d_title = f"SH.D-{format_sh_no(no)}".lower()
#     return loc_code, d_title, vtype


# # 3) NIVELLER wired: "O.D-0010_A" / "_B" / "_T"
# NIV_RE = re.compile(r"^O\.D-(\d+)_([ABT])$", re.IGNORECASE)

# def parse_niveller_column(col: str) -> Optional[Tuple[str, str]]:
#     m = NIV_RE.match(col.strip())
#     if not m:
#         return None
#     num = int(m.group(1))              # 0010 -> 10
#     ch = m.group(2).upper()
#     db_title = f"O.D-{num:03d}".lower()  # 10 -> o.d-010

#     if ch == "A":
#         vtype = "sina"
#     elif ch == "B":
#         vtype = "sinb"
#     else:
#         vtype = "temperatura"
#     return db_title, vtype


# # 4) GENERAL: "PO-45 bosim", "PO-45 bosimi", "PO-45 temp", "V/S 7 loyqa", "V/S 7 loyqaligi"
# GEN_RE = re.compile(r"^(?P<title>.+?)\s+(?P<kind>bosimi|bosim|temp|loyqa|loyqaligi)$", re.IGNORECASE)

# def parse_general_column(col: str) -> Optional[Tuple[str, str]]:
#     m = GEN_RE.match(col.strip())
#     if not m:
#         return None
#     title = m.group("title").strip().lower()
#     kind = m.group("kind").strip().lower()

#     if kind == "temp":
#         return title, "temperatura"   # faylda temp keladi
#     if kind in ("loyqa", "loyqaligi"):
#         return title, "loyqa"
#     return title, "bosim"


# # ===================== WIRELESS parsers =====================

# TYPE_RE = re.compile(r"^type-(\d+)-Ch(\d+)$", re.IGNORECASE)
# ENG_RE  = re.compile(r"^eng-(\d+)-Ch(\d+)$", re.IGNORECASE)

# def is_type_or_eng(col: str) -> bool:
#     c = col.strip().replace('"', "")
#     return (TYPE_RE.match(c) is not None) or (ENG_RE.match(c) is not None)

# # A) value-122441-Ch1
# VAL_RE = re.compile(r"^value-(\d+)-Ch(\d+)$", re.IGNORECASE)

# # B) Tiltmeter: Sensor1-107474-Ch1 / Sensor1-107474-Ch2 / Sensor1-107474-Temp
# TILTM_RE = re.compile(r"^Sensor\d+-(\d+)-(Ch(\d+)|Temp)$", re.IGNORECASE)

# def parse_wireless_column(col: str) -> Optional[Tuple[str, str]]:
#     """
#     returns (node_id, channel_key)
#       channel_key: ch1/ch2/... yoki temp
#     """
#     c = col.strip().replace('"', "")

#     m = VAL_RE.match(c)
#     if m:
#         node_id = m.group(1)
#         ch = f"ch{int(m.group(2))}"
#         return node_id, ch.lower()

#     m2 = TILTM_RE.match(c)
#     if m2:
#         node_id = m2.group(1)
#         if m2.group(2).lower().startswith("ch"):
#             ch = f"ch{int(m2.group(3))}"
#             return node_id, ch.lower()
#         return node_id, "temp"

#     return None


# # C) VW format: freqInHz-119346-VW-Ch1
# VW_RE = re.compile(r"(freqInHz|freqSqInDigit|thermResInOhms)-(\d+)-VW-(Ch\d+)", re.IGNORECASE)

# def parse_vw_column(col: str) -> Optional[Tuple[str, str]]:
#     m = VW_RE.match(col.strip().replace('"', ""))
#     if not m:
#         return None
#     _, node_id, ch = m.groups()
#     return node_id, ch.lower()


# # ===================== COMMAND =====================

# class Command(BaseCommand):
#     help = "CSV (simli+simsiz) -> RawReading import (folder/file). Dublikatlar skip qilinadi."

#     def add_arguments(self, parser):
#         parser.add_argument("path", type=str, help="CSV file path yoki folder path")
#         parser.add_argument("--folder", action="store_true", help="Path folder bo'lsa shuni qo'ying")
#         parser.add_argument("--today-only", action="store_true", help="Faqat bugun modified bo'lgan fayllar")
#         parser.add_argument("--limit", type=int, default=0, help="Test: nechta fayl import qilinsin (0=hammasi)")

#     def handle(self, *args, **opts):
#         base_path = opts["path"]
#         is_folder = bool(opts["folder"])
#         today_only = bool(opts["today_only"])
#         limit = int(opts["limit"] or 0)

#         # --- Location cache: code -> Location
#         location_cache: dict[int, Optional[Location]] = {}

#         def get_location_by_code(code: int) -> Optional[Location]:
#             if code in location_cache:
#                 return location_cache[code]
#             loc = Location.objects.filter(code=code).first()
#             location_cache[code] = loc
#             return loc

#         # --- Datchik cache: (loc_id, title_lower) -> Datchik
#         datchik_cache: dict[tuple[int, str], Optional[Datchik]] = {}

#         def get_datchik_in_location(loc: Location, title_lower: str) -> Optional[Datchik]:
#             key = (loc.id, title_lower)
#             if key in datchik_cache:
#                 return datchik_cache[key]
#             d = Datchik.objects.filter(location=loc, title__iexact=title_lower).first()
#             datchik_cache[key] = d
#             return d

#         # --- Global datchik map (location kerak bo'lmaganlar: PO-45, V/S 7, O.D-010, ...)
#         global_datchik_map = {d.title.lower(): d for d in Datchik.objects.all()}

#         # --- Wireless channel map: (node_id, channel) -> (datchik, value_type)
#         # channel: ch1/ch2/temp
#         channel_map = {
#             (c.node_id, c.channel.lower()): (c.datchik, c.value_type)
#             for c in DataloggerChannel.objects.select_related("datchik")
#         }

#         # --- Fayllar ro'yxati
#         paths: list[str] = []
#         if is_folder:
#             if not os.path.isdir(base_path):
#                 self.stdout.write(self.style.ERROR("Folder topilmadi"))
#                 return
#             for root, _, files in os.walk(base_path):
#                 for fn in files:
#                     if not is_csv(fn):
#                         continue
#                     fp = os.path.join(root, fn)
#                     if today_only:
#                         mt = datetime.date.fromtimestamp(os.path.getmtime(fp))
#                         if mt != datetime.date.today():
#                             continue
#                     paths.append(fp)
#         else:
#             if not os.path.isfile(base_path):
#                 self.stdout.write(self.style.ERROR("File topilmadi"))
#                 return
#             paths = [base_path]

#         paths.sort(key=lambda p: os.path.getmtime(p))
#         if limit > 0:
#             paths = paths[:limit]

#         total_raw = 0
#         total_files = 0

#         for fpath in paths:
#             rows = read_csv_file(fpath)
#             if not rows:
#                 continue

#             mode = detect_mode(rows)
#             if not mode:
#                 self.stdout.write(self.style.WARNING(f"Format aniqlanmadi: {os.path.basename(fpath)}"))
#                 continue

#             header, start = find_header(rows, mode)
#             if not header:
#                 self.stdout.write(self.style.WARNING(f"Header topilmadi: {os.path.basename(fpath)}"))
#                 continue

#             bulk: list[RawReading] = []
#             src_name = os.path.basename(fpath)

#             for row in rows[start:]:
#                 if not row:
#                     continue

#                 record = {header[i]: row[i] if i < len(row) else None for i in range(len(header))}
#                 dt_raw = record.get("Date Time") or record.get("datetime") or record.get("Date-and-time")
#                 ts = parse_dt(dt_raw)
#                 if not ts:
#                     continue

#                 if mode == "wired":
#                     for col, val in record.items():
#                         if not col:
#                             continue
#                         c0 = norm(col)
#                         if c0 in ("date time", "datetime"):
#                             continue

#                         v = to_float(val)
#                         if v is None:
#                             continue

#                         # 1) ATVES (845-2/X)
#                         atv = parse_atves_column(str(col))
#                         if atv:
#                             loc_code, d_title, vtype = atv
#                             loc = get_location_by_code(loc_code)
#                             if not loc:
#                                 continue
#                             d = get_datchik_in_location(loc, d_title)
#                             if not d:
#                                 continue
#                             bulk.append(RawReading(datchik=d, ts=ts, value_type=vtype, raw_value=v, source_file=src_name))
#                             continue

#                         # 2) SHELEMER (SH/804/4 XT)
#                         sh = parse_sh_column(str(col))
#                         if sh:
#                             loc_code, d_title, vtype = sh
#                             loc = get_location_by_code(loc_code)
#                             if not loc:
#                                 continue
#                             d = get_datchik_in_location(loc, d_title)
#                             if not d:
#                                 continue
#                             bulk.append(RawReading(datchik=d, ts=ts, value_type=vtype, raw_value=v, source_file=src_name))
#                             continue

#                         # 3) NIVELLER wired (O.D-0010_A)
#                         nv = parse_niveller_column(str(col))
#                         if nv:
#                             d_title, vtype = nv
#                             d = global_datchik_map.get(d_title)
#                             if not d:
#                                 continue
#                             bulk.append(RawReading(datchik=d, ts=ts, value_type=vtype, raw_value=v, source_file=src_name))
#                             continue

#                         # 4) GENERAL (PO/PK/V/S)
#                         g = parse_general_column(str(col))
#                         if g:
#                             d_title, vtype = g
#                             d = global_datchik_map.get(d_title)
#                             if not d:
#                                 continue
#                             bulk.append(RawReading(datchik=d, ts=ts, value_type=vtype, raw_value=v, source_file=src_name))
#                             continue

#                         else:
#                             # ================= WIRELESS =================
#                             for col, val in record.items():
#                                 if not col:
#                                     continue

#                                 # date ustunini skip
#                                 if norm(col) in ("date-and-time", "datetime"):
#                                     continue

#                                 # type-... va eng-... ustunlarni skip
#                                 if is_type_or_eng(str(col)):
#                                     continue

#                                 v = to_float(val)
#                                 if v is None:
#                                     continue


#                         # 1) value-...-ChN yoki Sensor1-...-ChN/Temp
#                         p = parse_wireless_column(str(col))
#                         if p:
#                             node_id, ch_key = p
#                             mapped = channel_map.get((node_id, ch_key))
#                             if not mapped:
#                                 continue
#                             d, vtype = mapped
#                             bulk.append(RawReading(datchik=d, ts=ts, value_type=vtype, raw_value=v, source_file=src_name))
#                             continue

#                         # 2) VW format
#                         p2 = parse_vw_column(str(col))
#                         if p2:
#                             node_id, ch = p2
#                             mapped = channel_map.get((node_id, ch))
#                             if not mapped:
#                                 continue
#                             d, vtype = mapped
#                             bulk.append(RawReading(datchik=d, ts=ts, value_type=vtype, raw_value=v, source_file=src_name))
#                             continue

#             if bulk:
#                 with transaction.atomic():
#                     RawReading.objects.bulk_create(bulk, ignore_conflicts=True)
#                 total_raw += len(bulk)
#                 total_files += 1
#                 self.stdout.write(self.style.SUCCESS(f"✅ {src_name}: {len(bulk)} RAW"))
#             else:
#                 self.stdout.write(self.style.WARNING(f"⚠️ {src_name}: RAW topilmadi"))

#         self.stdout.write(self.style.SUCCESS(f"Jami fayl: {total_files}, Jami RAW: {total_raw} (dublikatlar skip)"))



# app/management/commands/import_raw.py
import os
import re
import datetime
from typing import Optional, Tuple

from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from django.db import transaction
from django.utils import timezone

from app.management.commands.csv_reader import read_csv_file
from app.models import Location, Datchik, RawReading, DataloggerChannel


# ===================== YORDAMCHI =====================

def to_float(val):
    if val in (None, "", "-", "N.C.", "NAN", "  NAN"):
        return None
    try:
        return float(str(val).strip())
    except Exception:
        return None


def norm(s) -> str:
    return str(s).strip().lower() if s is not None else ""


def parse_dt(s):
    if not s:
        return None
    dt = parse_datetime(str(s).replace("/", "-"))
    if not dt:
        return None
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def is_csv(fn: str) -> bool:
    return fn.lower().endswith(".csv")


# ===================== FORMAT TOPISH =====================

def detect_mode(rows) -> Optional[str]:
    for r in rows[:80]:
        if not r:
            continue
        first = norm(r[0])
        if first in ("date time", "datetime"):
            return "wired"
        if first in ("date-and-time",):
            return "wireless"
    return None


def find_header(rows, mode: str):
    header = None
    start = 0
    for i, r in enumerate(rows):
        if not r:
            continue
        first = norm(r[0])
        if mode == "wired" and first in ("date time", "datetime"):
            header = r
            start = i + 1
            break
        if mode == "wireless" and first in ("date-and-time", "datetime"):
            header = r
            start = i + 1
            break
    return header, start


# ===================== WIRED parsers =====================

# 1) ATVES: "845-2/X" "845-2/Y" "845-2/Z" "845-2/T"
ATVES_RE = re.compile(r"^(\d+)-(\d+)\/(X|Y|Z|T)$", re.IGNORECASE)

def parse_atves_column(col: str) -> Optional[Tuple[int, str, str]]:
    m = ATVES_RE.match(col.strip())
    if not m:
        return None
    loc_code = int(m.group(1))
    idx = int(m.group(2))
    axis = m.group(3).upper()

    if axis == "X":
        vtype = "deformatsiya_x"
    elif axis == "Y":
        vtype = "deformatsiya_y"
    elif axis == "Z":
        vtype = "deformatsiya_z"
    else:
        vtype = "temperatura"

    d_title = f"{loc_code}-{idx}".lower()
    return loc_code, d_title, vtype


# 2) SHELEMER: "SH/804/4 X" "SH/804/4 XT" ...
SH_RE = re.compile(r"^SH\/(\d+)\/(\d+)\s*(X|XT|Y|YT|Z|ZT)$", re.IGNORECASE)

def format_sh_no(n: int) -> str:
    # siz aytgandek: 4->04, 14->014, 104->104
    return f"0{n}" if n < 100 else str(n)

def parse_sh_column(col: str) -> Optional[Tuple[int, str, str]]:
    m = SH_RE.match(col.strip())
    if not m:
        return None

    loc_code = int(m.group(1))
    no = int(m.group(2))
    suffix = m.group(3).upper()

    axis = suffix.replace("T", "").lower()  # x/y/z
    if suffix.endswith("T"):
        vtype = f"temperatura_{axis}"
    else:
        vtype = f"deformatsiya_{axis}"

    d_title = f"sh.d-{format_sh_no(no)}".lower()
    return loc_code, d_title, vtype


# 3) NIVELLER wired: "O.D-0010_A" / "_B" / "_T"
NIV_RE = re.compile(r"^O\.D-(\d+)_([ABT])$", re.IGNORECASE)

def parse_niveller_column(col: str) -> Optional[Tuple[str, str]]:
    m = NIV_RE.match(col.strip())
    if not m:
        return None
    num = int(m.group(1))               # 0010 -> 10
    ch = m.group(2).upper()
    db_title = f"o.d-{num:03d}".lower()  # 10 -> o.d-010

    if ch == "A":
        vtype = "sina"
    elif ch == "B":
        vtype = "sinb"
    else:
        vtype = "temperatura"
    return db_title, vtype


# 4) GENERAL: "PO-45 bosim", "PO-45 temp", "V/S 7 loyqa"
GEN_RE = re.compile(r"^(?P<title>.+?)\s+(?P<kind>bosimi|bosim|temp|loyqa|loyqaligi)$", re.IGNORECASE)

def parse_general_column(col: str) -> Optional[Tuple[str, str]]:
    m = GEN_RE.match(col.strip())
    if not m:
        return None
    title = m.group("title").strip().lower()
    kind = m.group("kind").strip().lower()

    if kind == "temp":
        return title, "temperatura"
    if kind in ("loyqa", "loyqaligi"):
        return title, "loyqa"
    # MUHIM: modelda bosim_MPa
    return title, "bosim_MPa"


# ===================== WIRELESS parsers =====================

TYPE_RE = re.compile(r"^type-(\d+)-Ch(\d+)$", re.IGNORECASE)
ENG_RE  = re.compile(r"^eng-(\d+)-Ch(\d+)$", re.IGNORECASE)

def is_type_or_eng(col: str) -> bool:
    c = col.strip().replace('"', "")
    return (TYPE_RE.match(c) is not None) or (ENG_RE.match(c) is not None)

# A) value-122441-Ch1
VAL_RE = re.compile(r"^value-(\d+)-Ch(\d+)$", re.IGNORECASE)

# B) Tiltmeter: Sensor1-107474-Ch1 / Sensor1-107474-Ch2 / Sensor1-107474-Temp
TILTM_RE = re.compile(r"^Sensor\d+-(\d+)-(Ch(\d+)|Temp)$", re.IGNORECASE)

def parse_wireless_column(col: str) -> Optional[Tuple[str, str]]:
    c = col.strip().replace('"', "")

    m = VAL_RE.match(c)
    if m:
        node_id = m.group(1)
        ch = f"ch{int(m.group(2))}"
        return node_id, ch.lower()

    m2 = TILTM_RE.match(c)
    if m2:
        node_id = m2.group(1)
        if m2.group(2).lower().startswith("ch"):
            ch = f"ch{int(m2.group(3))}"
            return node_id, ch.lower()
        return node_id, "temp"

    return None

# C) VW format: freqInHz-119346-VW-Ch1
VW_RE = re.compile(r"(freqInHz|freqSqInDigit|thermResInOhms)-(\d+)-VW-(Ch\d+)", re.IGNORECASE)

def parse_vw_column(col: str) -> Optional[Tuple[str, str]]:
    m = VW_RE.match(col.strip().replace('"', ""))
    if not m:
        return None
    _, node_id, ch = m.groups()
    return node_id, ch.lower()


# ===================== COMMAND =====================

class Command(BaseCommand):
    help = "CSV (simli+simsiz) -> RawReading import (folder/file). Dublikatlar skip qilinadi."

    def add_arguments(self, parser):
        parser.add_argument("path", type=str, help="CSV file path yoki folder path")
        parser.add_argument("--folder", action="store_true", help="Path folder bo'lsa shuni qo'ying")
        parser.add_argument("--today-only", action="store_true", help="Faqat bugun modified bo'lgan fayllar")
        parser.add_argument("--limit", type=int, default=0, help="Test: nechta fayl import qilinsin (0=hammasi)")

    def handle(self, *args, **opts):
        base_path = opts["path"]
        is_folder = bool(opts["folder"])
        today_only = bool(opts["today_only"])
        limit = int(opts["limit"] or 0)

        # --- Location cache: code -> Location
        location_cache: dict[int, Optional[Location]] = {}

        def get_location_by_code(code: int) -> Optional[Location]:
            if code in location_cache:
                return location_cache[code]
            loc = Location.objects.filter(code=code).first()
            location_cache[code] = loc
            return loc

        # --- Datchik cache: (loc_id, title_lower) -> Datchik
        datchik_cache: dict[tuple[int, str], Optional[Datchik]] = {}

        def get_datchik_in_location(loc: Location, title_lower: str) -> Optional[Datchik]:
            key = (loc.id, title_lower)
            if key in datchik_cache:
                return datchik_cache[key]
            # title__iexact ga LOWER berish shart emas, lekin biz title_lower yuboryapmiz
            d = Datchik.objects.filter(location=loc, title__iexact=title_lower).first()
            datchik_cache[key] = d
            return d

        # --- Global datchik map (location kerak bo'lmaganlar: PO-45, V/S 7, O.D-010, ...)
        global_datchik_map = {d.title.lower(): d for d in Datchik.objects.all()}

        # --- Wireless channel map: (node_id, channel) -> (datchik, value_type)
        channel_map = {
            (c.node_id.strip(), c.channel.strip().lower()): (c.datchik, c.value_type)
            for c in DataloggerChannel.objects.select_related("datchik").all()
        }

        # --- Fayllar ro'yxati
        paths: list[str] = []
        if is_folder:
            if not os.path.isdir(base_path):
                self.stdout.write(self.style.ERROR("Folder topilmadi"))
                return
            for root, _, files in os.walk(base_path):
                for fn in files:
                    if not is_csv(fn):
                        continue
                    fp = os.path.join(root, fn)
                    if today_only:
                        mt = datetime.date.fromtimestamp(os.path.getmtime(fp))
                        if mt != datetime.date.today():
                            continue
                    paths.append(fp)
        else:
            if not os.path.isfile(base_path):
                self.stdout.write(self.style.ERROR("File topilmadi"))
                return
            paths = [base_path]

        paths.sort(key=lambda p: os.path.getmtime(p))
        if limit > 0:
            paths = paths[:limit]

        total_raw = 0
        total_files = 0

        for fpath in paths:
            rows = read_csv_file(fpath)
            if not rows:
                continue

            mode = detect_mode(rows)
            if not mode:
                self.stdout.write(self.style.WARNING(f"Format aniqlanmadi: {os.path.basename(fpath)}"))
                continue

            header, start = find_header(rows, mode)
            if not header:
                self.stdout.write(self.style.WARNING(f"Header topilmadi: {os.path.basename(fpath)}"))
                continue

            bulk: list[RawReading] = []
            src_name = os.path.basename(fpath)

            for row in rows[start:]:
                if not row:
                    continue

                record = {header[i]: row[i] if i < len(row) else None for i in range(len(header))}

                dt_raw = record.get("Date Time") or record.get("datetime") or record.get("Date-and-time") or record.get("Date-and-Time")
                ts = parse_dt(dt_raw)
                if not ts:
                    continue

                # ===================== WIRED =====================
                if mode == "wired":
                    for col, val in record.items():
                        if not col:
                            continue
                        c0 = norm(col)
                        if c0 in ("date time", "datetime"):
                            continue

                        v = to_float(val)
                        if v is None:
                            continue

                        # 1) ATVES
                        atv = parse_atves_column(str(col))
                        if atv:
                            loc_code, d_title, vtype = atv
                            loc = get_location_by_code(loc_code)
                            if not loc:
                                continue
                            d = get_datchik_in_location(loc, d_title)
                            if not d:
                                continue
                            bulk.append(RawReading(datchik=d, ts=ts, value_type=vtype, raw_value=v, source_file=src_name))
                            continue

                        # 2) SHELEMER
                        sh = parse_sh_column(str(col))
                        if sh:
                            loc_code, d_title, vtype = sh
                            loc = get_location_by_code(loc_code)
                            if not loc:
                                continue
                            d = get_datchik_in_location(loc, d_title)
                            if not d:
                                continue
                            bulk.append(RawReading(datchik=d, ts=ts, value_type=vtype, raw_value=v, source_file=src_name))
                            continue

                        # 3) NIVELLER wired
                        nv = parse_niveller_column(str(col))
                        if nv:
                            d_title, vtype = nv
                            d = global_datchik_map.get(d_title)
                            if not d:
                                continue
                            bulk.append(RawReading(datchik=d, ts=ts, value_type=vtype, raw_value=v, source_file=src_name))
                            continue

                        # 4) GENERAL
                        g = parse_general_column(str(col))
                        if g:
                            d_title, vtype = g
                            d = global_datchik_map.get(d_title)
                            if not d:
                                continue
                            bulk.append(RawReading(datchik=d, ts=ts, value_type=vtype, raw_value=v, source_file=src_name))
                            continue

                    continue  # keyingi row

                # ===================== WIRELESS =====================
                if mode == "wireless":
                    for col, val in record.items():
                        if not col:
                            continue

                        c0 = norm(col)
                        if c0 in ("date-and-time", "date-and-time ", "datetime"):
                            continue

                        if is_type_or_eng(str(col)):
                            continue

                        v = to_float(val)
                        if v is None:
                            continue

                        # 1) value-... yoki Sensor...-Temp
                        p = parse_wireless_column(str(col))
                        if p:
                            node_id, ch_key = p
                            mapped = channel_map.get((str(node_id).strip(), str(ch_key).strip().lower()))
                            if not mapped:
                                continue
                            d, vtype = mapped
                            bulk.append(RawReading(datchik=d, ts=ts, value_type=vtype, raw_value=v, source_file=src_name))
                            continue

                        # 2) VW format
                        p2 = parse_vw_column(str(col))
                        if p2:
                            node_id, ch = p2
                            mapped = channel_map.get((str(node_id).strip(), str(ch).strip().lower()))
                            if not mapped:
                                continue
                            d, vtype = mapped
                            bulk.append(RawReading(datchik=d, ts=ts, value_type=vtype, raw_value=v, source_file=src_name))
                            continue

            if bulk:
                with transaction.atomic():
                    RawReading.objects.bulk_create(bulk, ignore_conflicts=True)
                total_raw += len(bulk)
                total_files += 1
                self.stdout.write(self.style.SUCCESS(f"✅ {src_name}: {len(bulk)} RAW"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️ {src_name}: RAW topilmadi"))

        self.stdout.write(self.style.SUCCESS(f"Jami fayl: {total_files}, Jami RAW: {total_raw} (dublikatlar skip)"))
