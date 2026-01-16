# # # import datetime
# # # from collections import defaultdict
# # # from typing import Dict, List, Optional, Tuple

# # # from django.core.management.base import BaseCommand
# # # from django.utils import timezone
# # # from django.utils.dateparse import parse_datetime
# # # from django.db import transaction

# # # from app.models import Datchik, DatchikLog, RawReading


# # # # ===================== YORDAMCHI =====================

# # # def to_dt(s: str) -> Optional[datetime.datetime]:
# # #     if not s:
# # #         return None
# # #     d = parse_datetime(s)
# # #     if not d:
# # #         return None
# # #     if timezone.is_naive(d):
# # #         d = timezone.make_aware(d, timezone.get_current_timezone())
# # #     return d


# # # def floor_minutes(dt: datetime.datetime, minutes: int) -> datetime.datetime:
# # #     # 15-min bucket: 10:07 -> 10:00, 10:16 -> 10:15
# # #     m = (dt.minute // minutes) * minutes
# # #     return dt.replace(minute=m, second=0, microsecond=0)


# # # def safe_eval(expr: str, x: float,z: float, y: float, A=0, B=0, C=0, D=0):
# # #     return eval(
# # #         expr,
# # #         {"__builtins__": {}},
# # #         {"x": x, "X": x, "y": y, "Y": y, "z": z, "Z": z, "A": A or 0, "B": B or 0, "C": C or 0, "D": D or 0},
# # #     )


# # # def apply_formula(datchik: Datchik, raw_value: Optional[float], formula_attr: str) -> Optional[float]:
# # #     """
# # #     formula_attr: 'bosim_formula', 'temperatura_formula', 'bosim_x_formula', ...
# # #     """
# # #     if raw_value is None:
# # #         return None

# # #     formula = getattr(datchik, "formula", None)
# # #     if not formula:
# # #         return None

# # #     expr = getattr(formula, formula_attr, None)
# # #     if not expr:
# # #         return None

# # #     try:
# # #         return safe_eval(
# # #             expr,
# # #             raw_value,
# # #             A=getattr(datchik, "A", 0),
# # #             B=getattr(datchik, "B", 0),
# # #             C=getattr(datchik, "C", 0),
# # #             D=getattr(datchik, "D", 0),
# # #         )
# # #     except Exception:
# # #         return None


# # # # ===================== DATCHIK TURINI ANIQLASH =====================

# # # def detect_kind(d: Datchik) -> str:
# # #     t = (d.title or "").strip().lower()

# # #     if t.startswith("sh.d-"):
# # #         return "shelemer"

# # #     if t.startswith("v/s"):
# # #         return "vodosliv"

# # #     # ATVES: "845-2", "817-6" (faqat raqam-raqam)
# # #     # PO-45 bunga tushmaydi (po harf bor)
# # #     parts = t.split("-")
# # #     if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
# # #         return "atves"

# # #     # default: piezometr (PO, PK, PGL, ... bosim/temp)
# # #     return "piezometr"


# # # # ===================== BUCKET POLICY =====================

# # # POLICY = {
# # #     "piezometr": {"mode": "daily_last"},
# # #     "vodosliv": {"mode": "per_day_hours", "hours": [0, 6, 12, 18, 23]},  # 5 marta
# # #     "atves":    {"mode": "per_day_hours", "hours": [0, 12]},            # 2 marta (xohlasangiz o'zgartiring)
# # #     "shelemer": {"mode": "interval", "minutes": 15},                    # 15 minut
# # # }


# # # # ===================== RAW -> SNAPSHOT (tanlab olish) =====================

# # # def pick_snapshots(
# # #     readings: List[RawReading],
# # #     kind: str
# # # ) -> Dict[datetime.datetime, Dict[str, float]]:
# # #     """
# # #     returns:
# # #       { bucket_ts: {value_type: raw_value, ...}, ... }
# # #     bucket_ts = log.sana bo'ladigan vaqt

# # #     readings list: shu bitta datchik uchun, vaqt bo'yicha aralash bo'lishi mumkin
# # #     """
# # #     pol = POLICY[kind]
# # #     mode = pol["mode"]

# # #     # ts -> value_type -> (ts, value) (oxirgisi qoladi)
# # #     bucket_map: Dict[datetime.datetime, Dict[str, Tuple[datetime.datetime, float]]] = defaultdict(dict)

# # #     if mode == "daily_last":
# # #         for r in readings:
# # #             day = r.ts.date()
# # #             bucket_ts = datetime.datetime.combine(day, datetime.time(23, 59, 0))
# # #             if timezone.is_naive(bucket_ts):
# # #                 bucket_ts = timezone.make_aware(bucket_ts, timezone.get_current_timezone())

# # #             prev = bucket_map[bucket_ts].get(r.value_type)
# # #             if (prev is None) or (r.ts >= prev[0]):
# # #                 bucket_map[bucket_ts][r.value_type] = (r.ts, r.raw_value)

# # #     elif mode == "per_day_hours":
# # #         hours = pol["hours"]  # masalan [0,6,12,18,23]
# # #         for r in readings:
# # #             day = r.ts.date()
# # #             for h in hours:
# # #                 bucket_ts = datetime.datetime.combine(day, datetime.time(h, 0, 0))
# # #                 if timezone.is_naive(bucket_ts):
# # #                     bucket_ts = timezone.make_aware(bucket_ts, timezone.get_current_timezone())

# # #                 # bu bucket uchun qoidamiz: shu soatga eng yaqin "oxirgisi"ni olish
# # #                 # oddiyroq: bucket_ts dan keyingi 2 soat ichidagi oxirgi o'lchovni olish
# # #                 # (sodda va ishlaydi)
# # #                 # Shuning uchun bu yerda bucket_mapni keyin filtrlaymiz: r.ts in [bucket_ts, bucket_ts+2h)
# # #                 # Hozircha faqat keyin ishlatish uchun listga yig'amiz
# # #                 # --- bu usul o'rniga, bucket_ts bo'yicha keyin "window" tanlaymiz ---
# # #         # per_day_hours uchun boshqacha qilamiz: keyin window bilan

# # #         # --- window bilan tanlash ---
# # #         hours = pol["hours"]
# # #         window = datetime.timedelta(hours=2)

# # #         # readingsni ts bo'yicha sort
# # #         readings_sorted = sorted(readings, key=lambda x: x.ts)

# # #         # kunlar ro'yxati
# # #         days = sorted({r.ts.date() for r in readings_sorted})

# # #         for day in days:
# # #             for h in hours:
# # #                 start = datetime.datetime.combine(day, datetime.time(h, 0, 0))
# # #                 if timezone.is_naive(start):
# # #                     start = timezone.make_aware(start, timezone.get_current_timezone())
# # #                 end = start + window
# # #                 bucket_ts = start

# # #                 # shu window ichidagi oxirgi readinglarni tanlash
# # #                 for r in readings_sorted:
# # #                     if r.ts < start:
# # #                         continue
# # #                     if r.ts >= end:
# # #                         break
# # #                     prev = bucket_map[bucket_ts].get(r.value_type)
# # #                     if (prev is None) or (r.ts >= prev[0]):
# # #                         bucket_map[bucket_ts][r.value_type] = (r.ts, r.raw_value)

# # #     elif mode == "interval":
# # #         minutes = pol["minutes"]
# # #         for r in readings:
# # #             bucket_ts = floor_minutes(r.ts, minutes)
# # #             prev = bucket_map[bucket_ts].get(r.value_type)
# # #             if (prev is None) or (r.ts >= prev[0]):
# # #                 bucket_map[bucket_ts][r.value_type] = (r.ts, r.raw_value)

# # #     # endi Tuple(ts,value) -> faqat value qoldiramiz
# # #     out: Dict[datetime.datetime, Dict[str, float]] = {}
# # #     for bts, vmap in bucket_map.items():
# # #         out[bts] = {vt: tv[1] for vt, tv in vmap.items()}
# # #     return out


# # # # ===================== LOG YARATISH =====================

# # # def build_log_from_snapshot(d: Datchik, kind: str, sana: datetime.datetime, snap: Dict[str, float]) -> DatchikLog:
# # #     """
# # #     snap: {value_type: raw_value}
# # #     """
# # #     formula = getattr(d, "formula", None)

# # #     if kind == "piezometr":
# # #         bosim_raw = snap.get("bosim")
# # #         temp_raw = snap.get("temperatura")

# # #         return DatchikLog(
# # #             formula=formula,
# # #             sana=sana,
# # #             bosim=apply_formula(d, bosim_raw, "bosim_formula"),
# # #             bosim_m=apply_formula(d, bosim_raw, "bosim_m_formula"),
# # #             bosim_sm=apply_formula(d, bosim_raw, "bosim_sm_formula"),
# # #             bosim_mm=apply_formula(d, bosim_raw, "bosim_mm_formula"),
# # #             suv_sathi=apply_formula(d, bosim_raw, "suv_sathi_formula"),
# # #             suv_sarfi=apply_formula(d, bosim_raw, "suv_sarfi_formula"),
# # #             temperatura=apply_formula(d, temp_raw, "temperatura_formula"),
# # #         )

# # #     if kind == "vodosliv":
# # #         bosim_raw = snap.get("bosim")
# # #         loyqa_raw = snap.get("loyqa")

# # #         return DatchikLog(
# # #             formula=formula,
# # #             sana=sana,
# # #             bosim=apply_formula(d, bosim_raw, "bosim_formula"),
# # #             suv_sarfi=apply_formula(d, bosim_raw, "suv_sarfi_formula"),
# # #             loyqaligi=apply_formula(d, loyqa_raw, "loyqaligi_formula"),
# # #         )

# # #     if kind == "atves":
# # #         bx = snap.get("bosim_x")
# # #         by = snap.get("bosim_y")
# # #         t = snap.get("temperatura")

# # #         return DatchikLog(
# # #             formula=formula,
# # #             sana=sana,
# # #             bosim_x=apply_formula(d, bx, "bosim_x_formula"),
# # #             bosim_y=apply_formula(d, by, "bosim_y_formula"),
# # #             temperatura=apply_formula(d, t, "temperatura_formula"),
# # #         )

# # #     # shelemer
# # #     bx = snap.get("bosim_x")
# # #     by = snap.get("bosim_y")
# # #     bz = snap.get("bosim_z")
# # #     tx = snap.get("temperatura_x")
# # #     ty = snap.get("temperatura_y")
# # #     tz = snap.get("temperatura_z")

# # #     return DatchikLog(
# # #         formula=formula,
# # #         sana=sana,
# # #         bosim_x=apply_formula(d, bx, "bosim_x_formula"),
# # #         bosim_y=apply_formula(d, by, "bosim_y_formula"),
# # #         bosim_z=apply_formula(d, bz, "bosim_z_formula"),
# # #         temperatura_x=apply_formula(d, tx, "temperatura_x_formula"),
# # #         temperatura_y=apply_formula(d, ty, "temperatura_y_formula"),
# # #         temperatura_z=apply_formula(d, tz, "temperatura_z_formula"),
# # #     )


# # # # ===================== COMMAND =====================

# # # class Command(BaseCommand):
# # #     help = "RawReading -> DatchikLog (formula + chastota policy bilan)"

# # #     def add_arguments(self, parser):
# # #         parser.add_argument("--type", type=str, default="all",
# # #                             help="all | piezometr | vodosliv | shelemer | atves")
# # #         parser.add_argument("--from", dest="from_dt", type=str, default="",
# # #                             help="YYYY-MM-DD yoki YYYY-MM-DDTHH:MM:SS")
# # #         parser.add_argument("--to", dest="to_dt", type=str, default="",
# # #                             help="YYYY-MM-DD yoki YYYY-MM-DDTHH:MM:SS")
# # #         parser.add_argument("--dry-run", action="store_true", help="DBga yozmaydi, faqat hisoblaydi")
# # #         parser.add_argument("--limit", type=int, default=0, help="Test uchun: nechta datchik ishlasin (0=hammasi)")

# # #     def handle(self, *args, **opts):
# # #         kind_filter = (opts["type"] or "all").strip().lower()
# # #         dry_run = bool(opts["dry_run"])
# # #         limit = int(opts["limit"] or 0)

# # #         now = timezone.now()

# # #         # default range: oxirgi 2 kun (scheduler uchun yetarli)
# # #         from_dt = to_dt(opts["from_dt"]) if opts["from_dt"] else (now - datetime.timedelta(days=2))
# # #         to_dt_ = to_dt(opts["to_dt"]) if opts["to_dt"] else now

# # #         if from_dt >= to_dt_:
# # #             self.stdout.write(self.style.ERROR("--from >= --to bo'lib qolgan"))
# # #             return

# # #         # datchiklar
# # #         datchiks = list(Datchik.objects.select_related("formula").all())
# # #         if limit > 0:
# # #             datchiks = datchiks[:limit]

# # #         total_logs = 0
# # #         total_d = 0

# # #         bulk_logs: List[DatchikLog] = []

# # #         for d in datchiks:
# # #             kind = detect_kind(d)

# # #             if kind_filter != "all" and kind != kind_filter:
# # #                 continue

# # #             # faqat formula bor datchiklar (xohlasangiz olib tashlaysiz)
# # #             if not getattr(d, "formula", None):
# # #                 continue

# # #             # RAWlarni olib kelamiz
# # #             qs = RawReading.objects.filter(datchik=d, ts__gte=from_dt, ts__lt=to_dt_).order_by("ts")
# # #             readings = list(qs)
# # #             if not readings:
# # #                 continue

# # #             snaps = pick_snapshots(readings, kind)
# # #             if not snaps:
# # #                 continue

# # #             # Dublikatni kamaytirish: shu formula uchun mavjud sanalarni oldindan olib qo'yamiz
# # #             existing_sanas = set(
# # #                 DatchikLog.objects.filter(formula=d.formula, sana__gte=from_dt, sana__lt=to_dt_)
# # #                 .values_list("sana", flat=True)
# # #             )

# # #             created_here = 0
# # #             for sana, snap in snaps.items():
# # #                 if sana in existing_sanas:
# # #                     continue
# # #                 log = build_log_from_snapshot(d, kind, sana, snap)
# # #                 bulk_logs.append(log)
# # #                 created_here += 1

# # #             if created_here:
# # #                 total_d += 1

# # #         if dry_run:
# # #             self.stdout.write(self.style.WARNING(f"[DRY RUN] Yaratiladigan loglar: {len(bulk_logs)}"))
# # #             return

# # #         if bulk_logs:
# # #             with transaction.atomic():
# # #                 # Agar siz Meta unique constraint qo'ysangiz, ignore_conflicts dublikatlarni skip qiladi
# # #                 DatchikLog.objects.bulk_create(bulk_logs, ignore_conflicts=True)
# # #             total_logs = len(bulk_logs)

# # #         self.stdout.write(self.style.SUCCESS(f"Datchiklar: {total_d} ta, Loglar: {total_logs} ta yaratildi"))



# # # app/management/commands/build_logs.py
# # # import datetime
# # # from collections import defaultdict
# # # from typing import Dict, List, Optional, Tuple

# # # from django.core.management.base import BaseCommand
# # # from django.utils import timezone
# # # from django.utils.dateparse import parse_datetime
# # # from django.db import transaction

# # # from app.models import Datchik, DatchikLog, RawReading


# # # # ===================== YORDAMCHI =====================

# # # def to_dt(s: str) -> Optional[datetime.datetime]:
# # #     if not s:
# # #         return None
# # #     d = parse_datetime(s)
# # #     if not d:
# # #         return None
# # #     if timezone.is_naive(d):
# # #         d = timezone.make_aware(d, timezone.get_current_timezone())
# # #     return d


# # # def floor_minutes(dt: datetime.datetime, minutes: int) -> datetime.datetime:
# # #     m = (dt.minute // minutes) * minutes
# # #     return dt.replace(minute=m, second=0, microsecond=0)


# # # def safe_eval(expr: str, x: float, y: float = 0.0, z: float = 0.0, A=0, B=0, C=0, D=0):
# # #     return eval(
# # #         expr,
# # #         {"__builtins__": {}},
# # #         {
# # #             "x": x, "X": x,
# # #             "y": y, "Y": y,
# # #             "z": z, "Z": z,
# # #             "A": A or 0, "B": B or 0, "C": C or 0, "D": D or 0
# # #         },
# # #     )


# # # def apply_formula_1(datchik: Datchik, x_val: Optional[float], formula_attr: str) -> Optional[float]:
# # #     """
# # #     Bitta qiymat bilan formula hisoblash:
# # #       - bosim_MPa, temperatura, deformatsiya_x, sina, ...
# # #     Formulada x ishlaydi.
# # #     """
# # #     if x_val is None:
# # #         return None

# # #     formula = getattr(datchik, "formula", None)
# # #     if not formula:
# # #         return None

# # #     expr = getattr(formula, formula_attr, None)
# # #     if not expr:
# # #         return None

# # #     A = getattr(datchik, "A", 0) or 0
# # #     B = getattr(datchik, "B", 0) or 0
# # #     C = getattr(datchik, "C", 0) or 0
# # #     D = getattr(datchik, "D", 0) or 0

# # #     try:
# # #         return safe_eval(expr, x=x_val, y=0.0, z=0.0, A=A, B=B, C=C, D=D)
# # #     except Exception:
# # #         return None


# # # def apply_formula_xy(datchik: Datchik, x_val: Optional[float], y_val: Optional[float], formula_attr: str) -> Optional[float]:
# # #     """
# # #     2ta qiymat bilan formula:
# # #       - ogish_korsatgichi: x=sina, y=sinb
# # #     """
# # #     formula = getattr(datchik, "formula", None)
# # #     if not formula:
# # #         return None

# # #     expr = getattr(formula, formula_attr, None)
# # #     if not expr:
# # #         return None

# # #     A = getattr(datchik, "A", 0) or 0
# # #     B = getattr(datchik, "B", 0) or 0
# # #     C = getattr(datchik, "C", 0) or 0
# # #     D = getattr(datchik, "D", 0) or 0

# # #     try:
# # #         return safe_eval(
# # #             expr,
# # #             x=(x_val or 0.0),
# # #             y=(y_val or 0.0),
# # #             z=0.0,
# # #             A=A, B=B, C=C, D=D
# # #         )
# # #     except Exception:
# # #         return None


# # # # ===================== DATCHIK TURINI ANIQLASH =====================

# # # def detect_kind(d: Datchik) -> str:
# # #     t = (d.title or "").strip().lower()

# # #     # Shelemer: SH.D-xxx
# # #     if t.startswith("sh.d-"):
# # #         return "shelemer"

# # #     # Vodosliv: V/S ...
# # #     if t.startswith("v/s"):
# # #         return "vodosliv"

# # #     # Niveller / Tiltmeter: O.D-xxx
# # #     if t.startswith("o.d-"):
# # #         return "niveller"

# # #     # Otves: senga mos variant
# # #     if "otves" in t:
# # #         return "atves"

# # #     # default: piezometr (PO/PK/PGL...)
# # #     return "piezometr"


# # # # ===================== BUCKET POLICY =====================

# # # POLICY = {
# # #     "piezometr": {"mode": "daily_last"},
# # #     "vodosliv":  {"mode": "per_day_hours", "hours": [0, 6, 12, 18, 23]},  # 5 marta
# # #     "atves":     {"mode": "per_day_hours", "hours": [0, 12]},            # 2 marta
# # #     "shelemer":  {"mode": "interval", "minutes": 15},                    # 15 minut
# # #     "niveller":  {"mode": "interval", "minutes": 15},                    # 15 minut
# # # }


# # # # ===================== RAW -> SNAPSHOT =====================

# # # def pick_snapshots(readings: List[RawReading], kind: str) -> Dict[datetime.datetime, Dict[str, float]]:
# # #     pol = POLICY.get(kind) or POLICY["piezometr"]
# # #     mode = pol["mode"]

# # #     bucket_map: Dict[datetime.datetime, Dict[str, Tuple[datetime.datetime, float]]] = defaultdict(dict)

# # #     if mode == "daily_last":
# # #         for r in readings:
# # #             day = r.ts.date()
# # #             bucket_ts = datetime.datetime.combine(day, datetime.time(23, 59, 0))
# # #             if timezone.is_naive(bucket_ts):
# # #                 bucket_ts = timezone.make_aware(bucket_ts, timezone.get_current_timezone())

# # #             prev = bucket_map[bucket_ts].get(r.value_type)
# # #             if (prev is None) or (r.ts >= prev[0]):
# # #                 bucket_map[bucket_ts][r.value_type] = (r.ts, r.raw_value)

# # #     elif mode == "per_day_hours":
# # #         hours = pol["hours"]
# # #         window = datetime.timedelta(hours=2)

# # #         readings_sorted = sorted(readings, key=lambda x: x.ts)
# # #         days = sorted({r.ts.date() for r in readings_sorted})

# # #         for day in days:
# # #             for h in hours:
# # #                 start = datetime.datetime.combine(day, datetime.time(h, 0, 0))
# # #                 if timezone.is_naive(start):
# # #                     start = timezone.make_aware(start, timezone.get_current_timezone())
# # #                 end = start + window
# # #                 bucket_ts = start

# # #                 for r in readings_sorted:
# # #                     if r.ts < start:
# # #                         continue
# # #                     if r.ts >= end:
# # #                         break
# # #                     prev = bucket_map[bucket_ts].get(r.value_type)
# # #                     if (prev is None) or (r.ts >= prev[0]):
# # #                         bucket_map[bucket_ts][r.value_type] = (r.ts, r.raw_value)

# # #     elif mode == "interval":
# # #         minutes = pol["minutes"]
# # #         for r in readings:
# # #             bucket_ts = floor_minutes(r.ts, minutes)
# # #             prev = bucket_map[bucket_ts].get(r.value_type)
# # #             if (prev is None) or (r.ts >= prev[0]):
# # #                 bucket_map[bucket_ts][r.value_type] = (r.ts, r.raw_value)

# # #     out: Dict[datetime.datetime, Dict[str, float]] = {}
# # #     for bts, vmap in bucket_map.items():
# # #         out[bts] = {vt: tv[1] for vt, tv in vmap.items()}
# # #     return out


# # # # ===================== LOG YARATISH =====================

# # # def build_log_from_snapshot(d: Datchik, kind: str, sana: datetime.datetime, snap: Dict[str, float]) -> DatchikLog:
# # #     formula = getattr(d, "formula", None)

# # #     if kind == "piezometr":
# # #         bosim_raw = snap.get("bosim")
# # #         temp_raw = snap.get("temperatura")

# # #         return DatchikLog(
# # #             formula=formula,
# # #             sana=sana,
# # #             bosim=apply_formula_1(d, bosim_raw, "bosim_MPa"),
# # #             bosim_m=apply_formula_1(d, bosim_raw, "bosim_m"),
# # #             bosim_sm=apply_formula_1(d, bosim_raw, "bosim_sm"),
# # #             bosim_mm=apply_formula_1(d, bosim_raw, "bosim_mm"),
# # #             suv_sathi=apply_formula_1(d, bosim_raw, "suv_sathi"),
# # #             suv_sarfi=apply_formula_1(d, bosim_raw, "suv_sarfi"),
# # #             temperatura=apply_formula_1(d, temp_raw, "temperatura"),
# # #         )

# # #     if kind == "vodosliv":
# # #         bosim_raw = snap.get("bosim")
# # #         loyqa_raw = snap.get("loyqa")

# # #         return DatchikLog(
# # #             formula=formula,
# # #             sana=sana,
# # #             bosim=apply_formula_1(d, bosim_raw, "bosim_MPa"),
# # #             suv_sarfi=apply_formula_1(d, bosim_raw, "suv_sarfi"),
# # #             loyqa=apply_formula_1(d, loyqa_raw, "loyqa"),
# # #         )

# # #     if kind == "atves":
# # #         # simli: deformatsiya_x/y (+T bo'lishi mumkin)
# # #         # simsiz: ko'pincha deformatsiya_x/y, temperatura yo'q -> None
# # #         dx = snap.get("deformatsiya_x")
# # #         dy = snap.get("deformatsiya_y")
# # #         dz = snap.get("deformatsiya_z")  # bo'lsa
# # #         t = snap.get("temperatura")

# # #         return DatchikLog(
# # #             formula=formula,
# # #             sana=sana,
# # #             deformatsiya_x=apply_formula_1(d, dx, "deformatsiya_x"),
# # #             deformatsiya_y=apply_formula_1(d, dy, "deformatsiya_y"),
# # #             deformatsiya_z=apply_formula_1(d, dz, "deformatsiya_z"),
# # #             temperatura=apply_formula_1(d, t, "temperatura"),
# # #         )

# # #     if kind == "niveller":
# # #         # simli: sina, sinb, temperatura
# # #         # simsiz: ch1->sina, ch2->sinb, temp->temperatura
# # #         a = snap.get("sina")
# # #         b = snap.get("sinb")
# # #         t = snap.get("temperatura")

# # #         return DatchikLog(
# # #             formula=formula,
# # #             sana=sana,
# # #             sina=apply_formula_1(d, a, "sina"),
# # #             sinb=apply_formula_1(d, b, "sinb"),
# # #             # ogish_korsatgichi formulasi x=sina, y=sinb
# # #             ogish_korsatgichi=apply_formula_xy(d, a, b, "ogish_korsatgichi"),
# # #             temperatura=apply_formula_1(d, t, "temperatura"),
# # #         )

# # #     # shelemer
# # #     dx = snap.get("deformatsiya_x")
# # #     dy = snap.get("deformatsiya_y")
# # #     dz = snap.get("deformatsiya_z")
# # #     tx = snap.get("temperatura_x")
# # #     ty = snap.get("temperatura_y")
# # #     tz = snap.get("temperatura_z")

# # #     return DatchikLog(
# # #         formula=formula,
# # #         sana=sana,
# # #         deformatsiya_x=apply_formula_1(d, dx, "deformatsiya_x"),
# # #         deformatsiya_y=apply_formula_1(d, dy, "deformatsiya_y"),
# # #         deformatsiya_z=apply_formula_1(d, dz, "deformatsiya_z"),
# # #         temperatura_x=apply_formula_1(d, tx, "temperatura_x"),
# # #         temperatura_y=apply_formula_1(d, ty, "temperatura_y"),
# # #         temperatura_z=apply_formula_1(d, tz, "temperatura_z"),
# # #     )


# # # # ===================== COMMAND =====================

# # # class Command(BaseCommand):
# # #     help = "RawReading -> DatchikLog (formula + chastota policy bilan)"

# # #     def add_arguments(self, parser):
# # #         parser.add_argument("--type", type=str, default="all",
# # #                             help="all | piezometr | vodosliv | shelemer | atves | niveller")
# # #         parser.add_argument("--from", dest="from_dt", type=str, default="",
# # #                             help="YYYY-MM-DD yoki YYYY-MM-DDTHH:MM:SS")
# # #         parser.add_argument("--to", dest="to_dt", type=str, default="",
# # #                             help="YYYY-MM-DD yoki YYYY-MM-DDTHH:MM:SS")
# # #         parser.add_argument("--dry-run", action="store_true", help="DBga yozmaydi, faqat hisoblaydi")
# # #         parser.add_argument("--limit", type=int, default=0, help="Test uchun: nechta datchik ishlasin (0=hammasi)")

# # #     def handle(self, *args, **opts):
# # #         kind_filter = (opts["type"] or "all").strip().lower()
# # #         dry_run = bool(opts["dry_run"])
# # #         limit = int(opts["limit"] or 0)

# # #         now = timezone.now()
# # #         from_dt = to_dt(opts["from_dt"]) if opts["from_dt"] else (now - datetime.timedelta(days=2))
# # #         to_dt_ = to_dt(opts["to_dt"]) if opts["to_dt"] else now

# # #         if from_dt >= to_dt_:
# # #             self.stdout.write(self.style.ERROR("--from >= --to bo'lib qolgan"))
# # #             return

# # #         datchiks = list(Datchik.objects.select_related("formula").all())
# # #         if limit > 0:
# # #             datchiks = datchiks[:limit]

# # #         bulk_logs: List[DatchikLog] = []
# # #         total_d = 0

# # #         for d in datchiks:
# # #             kind = detect_kind(d)

# # #             if kind_filter != "all" and kind != kind_filter:
# # #                 continue

# # #             if not getattr(d, "formula", None):
# # #                 continue

# # #             readings = list(
# # #                 RawReading.objects.filter(datchik=d, ts__gte=from_dt, ts__lt=to_dt_).order_by("ts")
# # #             )
# # #             if not readings:
# # #                 continue

# # #             snaps = pick_snapshots(readings, kind)
# # #             if not snaps:
# # #                 continue

# # #             existing_sanas = set(
# # #                 DatchikLog.objects.filter(formula=d.formula, sana__gte=from_dt, sana__lt=to_dt_)
# # #                 .values_list("sana", flat=True)
# # #             )

# # #             created_here = 0
# # #             for sana, snap in snaps.items():
# # #                 if sana in existing_sanas:
# # #                     continue
# # #                 bulk_logs.append(build_log_from_snapshot(d, kind, sana, snap))
# # #                 created_here += 1

# # #             if created_here:
# # #                 total_d += 1

# # #         if dry_run:
# # #             self.stdout.write(self.style.WARNING(f"[DRY RUN] Yaratiladigan loglar: {len(bulk_logs)}"))
# # #             return

# # #         if bulk_logs:
# # #             with transaction.atomic():
# # #                 DatchikLog.objects.bulk_create(bulk_logs, ignore_conflicts=True)

# # #         self.stdout.write(self.style.SUCCESS(f"Datchiklar: {total_d} ta, Loglar: {len(bulk_logs)} ta yaratildi"))



# # # app/management/commands/build_logs.py
# # import datetime
# # from collections import defaultdict
# # from typing import Dict, List, Optional, Tuple

# # from django.core.management.base import BaseCommand
# # from django.utils import timezone
# # from django.utils.dateparse import parse_datetime
# # from django.db import transaction

# # from app.models import Datchik, DatchikLog, RawReading


# # # ===================== YORDAMCHI =====================

# # def to_dt(s: str) -> Optional[datetime.datetime]:
# #     if not s:
# #         return None
# #     d = parse_datetime(s)
# #     if not d:
# #         return None
# #     if timezone.is_naive(d):
# #         d = timezone.make_aware(d, timezone.get_current_timezone())
# #     return d


# # def floor_minutes(dt: datetime.datetime, minutes: int) -> datetime.datetime:
# #     m = (dt.minute // minutes) * minutes
# #     return dt.replace(minute=m, second=0, microsecond=0)


# # def safe_eval(expr: str, x: float, y: float = 0.0, z: float = 0.0, A=0, B=0, C=0, D=0):
# #     return eval(
# #         expr,
# #         {"__builtins__": {}},
# #         {
# #             "x": x, "X": x,
# #             "y": y, "Y": y,
# #             "z": z, "Z": z,
# #             "A": A or 0, "B": B or 0, "C": C or 0, "D": D or 0
# #         },
# #     )


# # # Agar formula bo'lmasa rawni qaytarishni xohlasang True qil
# # FALLBACK_TO_RAW_WHEN_NO_FORMULA = True


# # def apply_formula_1(datchik: Datchik, x_val: Optional[float], formula_attr: str) -> Optional[float]:
# #     """
# #     Bitta qiymat bilan formula:
# #       - bosim_MPa, temperatura, deformatsiya_x, sina, sinb, loyqa, ...
# #     Formulada x ishlaydi.
# #     """
# #     if x_val is None:
# #         return None

# #     formula = getattr(datchik, "formula", None)
# #     if not formula:
# #         return x_val if FALLBACK_TO_RAW_WHEN_NO_FORMULA else None

# #     expr = getattr(formula, formula_attr, None)
# #     if not expr:
# #         return x_val if FALLBACK_TO_RAW_WHEN_NO_FORMULA else None

# #     A = getattr(datchik, "A", 0) or 0
# #     B = getattr(datchik, "B", 0) or 0
# #     C = getattr(datchik, "C", 0) or 0
# #     D = getattr(datchik, "D", 0) or 0

# #     try:
# #         return safe_eval(expr, x=x_val, y=0.0, z=0.0, A=A, B=B, C=C, D=D)
# #     except Exception:
# #         return None


# # def apply_formula_xy(datchik: Datchik, x_val: Optional[float], y_val: Optional[float], formula_attr: str) -> Optional[float]:
# #     """
# #     2 ta qiymat bilan formula:
# #       - ogish_korsatgichi: x=sina, y=sinb
# #     """
# #     formula = getattr(datchik, "formula", None)
# #     if not formula:
# #         if FALLBACK_TO_RAW_WHEN_NO_FORMULA:
# #             return None
# #         return None

# #     expr = getattr(formula, formula_attr, None)
# #     if not expr:
# #         return None

# #     A = getattr(datchik, "A", 0) or 0
# #     B = getattr(datchik, "B", 0) or 0
# #     C = getattr(datchik, "C", 0) or 0
# #     D = getattr(datchik, "D", 0) or 0

# #     try:
# #         return safe_eval(
# #             expr,
# #             x=(x_val or 0.0),
# #             y=(y_val or 0.0),
# #             z=0.0,
# #             A=A, B=B, C=C, D=D
# #         )
# #     except Exception:
# #         return None

# # def eval_expr(expr, x=0, y=0, z=0, A=0, B=0, C=0, D=0):
# #     return eval(
# #         expr,
# #         {"__builtins__": {}},
# #         {"x": x, "y": y, "z": z, "A": A, "B": B, "C": C, "D": D}
# #     )

# # def apply_extras(datchik, target, base_value, x=0, y=0, z=0):
# #     if base_value is None:
# #         return None
# #     f = getattr(datchik, "formula", None)
# #     if not f:
# #         return base_value

# #     result = base_value
# #     extras = f.extra_formulas.filter(target=target, is_active=True).order_by("order")

# #     for ef in extras:
# #         try:
# #             val = eval_expr(
# #                 ef.expression,
# #                 x=x, y=y, z=z,
# #                 A=datchik.A or 0, B=datchik.B or 0, C=datchik.C or 0, D=datchik.D or 0
# #             )
# #             if ef.operation == "add":
# #                 result += val
# #             elif ef.operation == "sub":
# #                 result -= val
# #             elif ef.operation == "mul":
# #                 result *= val
# #             elif ef.operation == "div" and val != 0:
# #                 result /= val
# #         except Exception:
# #             continue

# #     return result


# # # ===================== DATCHIK TURINI ANIQLASH =====================

# # def detect_kind(d: Datchik) -> str:
# #     t = (d.title or "").strip().lower()

# #     if t.startswith("sh.d-"):
# #         return "shelemer"
# #     if t.startswith("v/s"):
# #         return "vodosliv"
# #     if t.startswith("o.d-"):
# #         return "niveller"
# #     if "otves" in t:
# #         return "atves"
# #     return "piezometr"


# # # ===================== BUCKET POLICY =====================

# # POLICY = {
# #     "piezometr": {"mode": "daily_last"},
# #     "vodosliv":  {"mode": "per_day_hours", "hours": [0, 6, 12, 18, 23]},
# #     "atves":     {"mode": "per_day_hours", "hours": [0, 12]},
# #     "shelemer":  {"mode": "interval", "minutes": 15},
# #     "niveller":  {"mode": "interval", "minutes": 15},
# # }


# # # ===================== RAW -> SNAPSHOT =====================

# # def pick_snapshots(readings: List[RawReading], kind: str) -> Dict[datetime.datetime, Dict[str, float]]:
# #     pol = POLICY.get(kind) or POLICY["piezometr"]
# #     mode = pol["mode"]

# #     bucket_map: Dict[datetime.datetime, Dict[str, Tuple[datetime.datetime, float]]] = defaultdict(dict)

# #     if mode == "daily_last":
# #         for r in readings:
# #             day = r.ts.date()
# #             bucket_ts = datetime.datetime.combine(day, datetime.time(23, 59, 0))
# #             if timezone.is_naive(bucket_ts):
# #                 bucket_ts = timezone.make_aware(bucket_ts, timezone.get_current_timezone())

# #             prev = bucket_map[bucket_ts].get(r.value_type)
# #             if (prev is None) or (r.ts >= prev[0]):
# #                 bucket_map[bucket_ts][r.value_type] = (r.ts, r.raw_value)

# #     elif mode == "per_day_hours":
# #         hours = pol["hours"]
# #         window = datetime.timedelta(hours=2)

# #         readings_sorted = sorted(readings, key=lambda x: x.ts)
# #         days = sorted({r.ts.date() for r in readings_sorted})

# #         for day in days:
# #             for h in hours:
# #                 start = datetime.datetime.combine(day, datetime.time(h, 0, 0))
# #                 if timezone.is_naive(start):
# #                     start = timezone.make_aware(start, timezone.get_current_timezone())
# #                 end = start + window
# #                 bucket_ts = start

# #                 for r in readings_sorted:
# #                     if r.ts < start:
# #                         continue
# #                     if r.ts >= end:
# #                         break
# #                     prev = bucket_map[bucket_ts].get(r.value_type)
# #                     if (prev is None) or (r.ts >= prev[0]):
# #                         bucket_map[bucket_ts][r.value_type] = (r.ts, r.raw_value)

# #     elif mode == "interval":
# #         minutes = pol["minutes"]
# #         for r in readings:
# #             bucket_ts = floor_minutes(r.ts, minutes)
# #             prev = bucket_map[bucket_ts].get(r.value_type)
# #             if (prev is None) or (r.ts >= prev[0]):
# #                 bucket_map[bucket_ts][r.value_type] = (r.ts, r.raw_value)

# #     return {bts: {vt: tv[1] for vt, tv in vmap.items()} for bts, vmap in bucket_map.items()}


# # # ===================== LOG YARATISH =====================

# # def build_log_from_snapshot(d: Datchik, kind: str, sana: datetime.datetime, snap: Dict[str, float]) -> DatchikLog:
# #     formula = getattr(d, "formula", None)

# #     # temp fallback: ba'zi RAWlarda value_type="temp" bo'lib qolsa
# #     def get_temp():
# #         return snap.get("temperatura", None) if "temperatura" in snap else snap.get("temp", None)

# #     if kind == "piezometr":
# #         bosim_raw = snap.get("bosim")
# #         temp_raw = get_temp()

# #         return DatchikLog(
# #             formula=formula,
# #             sana=sana,
# #             bosim_MPa=apply_formula_1(d, bosim_raw, "bosim_MPa"),
# #             bosim_m=apply_formula_1(d, bosim_raw, "bosim_m"),
# #             bosim_sm=apply_formula_1(d, bosim_raw, "bosim_sm"),
# #             bosim_mm=apply_formula_1(d, bosim_raw, "bosim_mm"),
# #             suv_sathi=apply_formula_1(d, bosim_raw, "suv_sathi"),
# #             suv_sarfi=apply_formula_1(d, bosim_raw, "suv_sarfi"),
# #             temperatura=apply_formula_1(d, temp_raw, "temperatura"),
# #         )

# #     if kind == "vodosliv":
# #         bosim_raw = snap.get("bosim")
# #         loyqa_raw = snap.get("loyqa")

# #         return DatchikLog(
# #             formula=formula,
# #             sana=sana,
# #             bosim_MPa=apply_formula_1(d, bosim_raw, "bosim_MPa"),
# #             suv_sarfi=apply_formula_1(d, bosim_raw, "suv_sarfi"),
# #             loyqa=apply_formula_1(d, loyqa_raw, "loyqa"),
# #         )

# #     if kind == "atves":
# #         dx = snap.get("deformatsiya_x")
# #         dy = snap.get("deformatsiya_y")
# #         dz = snap.get("deformatsiya_z")
# #         t = get_temp()

# #         return DatchikLog(
# #             formula=formula,
# #             sana=sana,
# #             deformatsiya_x=apply_formula_1(d, dx, "deformatsiya_x"),
# #             deformatsiya_y=apply_formula_1(d, dy, "deformatsiya_y"),
# #             deformatsiya_z=apply_formula_1(d, dz, "deformatsiya_z"),
# #             temperatura=apply_formula_1(d, t, "temperatura"),
# #         )

# #     if kind == "niveller":
# #         a = snap.get("sina")
# #         b = snap.get("sinb")
# #         t = get_temp()

# #         return DatchikLog(
# #             formula=formula,
# #             sana=sana,
# #             sina=apply_formula_1(d, a, "sina"),
# #             sinb=apply_formula_1(d, b, "sinb"),
# #             ogish_korsatgichi=apply_formula_xy(d, a, b, "ogish_korsatgichi"),
# #             temperatura=apply_formula_1(d, t, "temperatura"),
# #         )

# #     # shelemer
# #     dx = snap.get("deformatsiya_x")
# #     dy = snap.get("deformatsiya_y")
# #     dz = snap.get("deformatsiya_z")
# #     tx = snap.get("temperatura_x")
# #     ty = snap.get("temperatura_y")
# #     tz = snap.get("temperatura_z")

# #     return DatchikLog(
# #         formula=formula,
# #         sana=sana,
# #         deformatsiya_x=apply_formula_1(d, dx, "deformatsiya_x"),
# #         deformatsiya_y=apply_formula_1(d, dy, "deformatsiya_y"),
# #         deformatsiya_z=apply_formula_1(d, dz, "deformatsiya_z"),
# #         temperatura_x=apply_formula_1(d, tx, "temperatura_x"),
# #         temperatura_y=apply_formula_1(d, ty, "temperatura_y"),
# #         temperatura_z=apply_formula_1(d, tz, "temperatura_z"),
# #     )


# # # ===================== COMMAND =====================

# # class Command(BaseCommand):
# #     help = "RawReading -> DatchikLog (formula + chastota policy bilan)"

# #     def add_arguments(self, parser):
# #         parser.add_argument("--type", type=str, default="all",
# #                             help="all | piezometr | vodosliv | shelemer | atves | niveller")
# #         parser.add_argument("--from", dest="from_dt", type=str, default="",
# #                             help="YYYY-MM-DD yoki YYYY-MM-DDTHH:MM:SS")
# #         parser.add_argument("--to", dest="to_dt", type=str, default="",
# #                             help="YYYY-MM-DD yoki YYYY-MM-DDTHH:MM:SS")
# #         parser.add_argument("--dry-run", action="store_true", help="DBga yozmaydi, faqat hisoblaydi")
# #         parser.add_argument("--limit", type=int, default=0, help="Test uchun: nechta datchik ishlasin (0=hammasi)")

# #     def handle(self, *args, **opts):
# #         kind_filter = (opts["type"] or "all").strip().lower()
# #         dry_run = bool(opts["dry_run"])
# #         limit = int(opts["limit"] or 0)

# #         now = timezone.now()
# #         from_dt = to_dt(opts["from_dt"]) if opts["from_dt"] else (now - datetime.timedelta(days=2))
# #         to_dt_ = to_dt(opts["to_dt"]) if opts["to_dt"] else now

# #         if from_dt >= to_dt_:
# #             self.stdout.write(self.style.ERROR("--from >= --to bo'lib qolgan"))
# #             return

# #         datchiks = list(Datchik.objects.select_related("formula").all())
# #         if limit > 0:
# #             datchiks = datchiks[:limit]

# #         bulk_logs: List[DatchikLog] = []
# #         total_d = 0

# #         for d in datchiks:
# #             kind = detect_kind(d)

# #             if kind_filter != "all" and kind != kind_filter:
# #                 continue

# #             # xohlasang buni olib tashlaysan:
# #             # formula bo'lmasa ham rawni logga yozish mumkin (FALLBACK_TO_RAW_WHEN_NO_FORMULA=True bo'lsa)
# #             # ammo UniqueConstraint formula+sana bo'lgani uchun formula NULL bo'lsa muammo bo'ladi.
# #             # Shuning uchun formula bo'lmaganlarni o'tkazib yuboramiz:
# #             if not getattr(d, "formula", None):
# #                 continue

# #             readings = list(
# #                 RawReading.objects.filter(datchik=d, ts__gte=from_dt, ts__lt=to_dt_).order_by("ts")
# #             )
# #             if not readings:
# #                 continue

# #             snaps = pick_snapshots(readings, kind)
# #             if not snaps:
# #                 continue

# #             existing_sanas = set(
# #                 DatchikLog.objects.filter(formula=d.formula, sana__gte=from_dt, sana__lt=to_dt_)
# #                 .values_list("sana", flat=True)
# #             )

# #             created_here = 0
# #             for sana, snap in snaps.items():
# #                 if sana in existing_sanas:
# #                     continue
# #                 bulk_logs.append(build_log_from_snapshot(d, kind, sana, snap))
# #                 created_here += 1

# #             if created_here:
# #                 total_d += 1

# #         if dry_run:
# #             self.stdout.write(self.style.WARNING(f"[DRY RUN] Yaratiladigan loglar: {len(bulk_logs)}"))
# #             return

# #         if bulk_logs:
# #             with transaction.atomic():
# #                 DatchikLog.objects.bulk_create(bulk_logs, ignore_conflicts=True)

# #         self.stdout.write(self.style.SUCCESS(f"Datchiklar: {total_d} ta, Loglar: {len(bulk_logs)} ta yaratildi"))



# import datetime
# import math
# from collections import defaultdict
# from typing import Dict, List, Optional, Tuple

# from django.core.management.base import BaseCommand
# from django.utils import timezone
# from django.utils.dateparse import parse_datetime
# from django.db import transaction

# from app.models import Datchik, DatchikLog, RawReading, DatchikFormula


# # =========================================================
# # TIME HELPERS
# # =========================================================

# def to_dt(s: str) -> Optional[datetime.datetime]:
#     if not s:
#         return None
#     d = parse_datetime(s)
#     if not d:
#         return None
#     if timezone.is_naive(d):
#         d = timezone.make_aware(d, timezone.get_current_timezone())
#     return d


# def floor_minutes(dt: datetime.datetime, minutes: int) -> datetime.datetime:
#     m = (dt.minute // minutes) * minutes
#     return dt.replace(minute=m, second=0, microsecond=0)


# # =========================================================
# # SAFE EVAL (formula)
# # =========================================================

# def safe_eval(expr: str, *, x: float = 0.0, y: float = 0.0, z: float = 0.0, A=0, B=0, C=0, D=0) -> float:
#     """
#     Formulada ishlaydigan o'zgaruvchilar:
#       x,y,z,A,B,C,D
#     """
#     return eval(
#         expr,
#         {"__builtins__": {}},
#         {
#             "x": x, "X": x,
#             "y": y, "Y": y,
#             "z": z, "Z": z,
#             "A": A or 0, "B": B or 0, "C": C or 0, "D": D or 0,
#             "sqrt": math.sqrt,
#             "sin": math.sin,
#             "cos": math.cos,
#             "tan": math.tan,
#             "abs": abs,
#             "pow": pow,
#         },
#     )


# def apply_formula_1(d: Datchik, f: DatchikFormula, x_val: Optional[float], formula_field: str) -> Optional[float]:
#     """
#     Formula maydonidan (masalan: f.bosim_MPa) expr olib, x orqali hisoblaydi.
#     """
#     if x_val is None:
#         return None

#     expr = getattr(f, formula_field, None)
#     if not expr:
#         # formula bo'sh bo'lsa rawni qaytarib yuboramiz (sizga qulay bo'ladi)
#         return float(x_val)

#     A = getattr(d, "A", 0) or 0
#     B = getattr(d, "B", 0) or 0
#     C = getattr(d, "C", 0) or 0
#     D = getattr(d, "D", 0) or 0

#     try:
#         return float(safe_eval(expr, x=float(x_val), y=0.0, z=0.0, A=A, B=B, C=C, D=D))
#     except Exception:
#         return None


# def apply_formula_xy(d: Datchik, f: DatchikFormula, x_val: Optional[float], y_val: Optional[float], formula_field: str) -> Optional[float]:
#     """
#     ogish_korsatgichi: x=sina, y=sinb
#     """
#     expr = getattr(f, formula_field, None)
#     if not expr:
#         return None

#     A = getattr(d, "A", 0) or 0
#     B = getattr(d, "B", 0) or 0
#     C = getattr(d, "C", 0) or 0
#     D = getattr(d, "D", 0) or 0

#     try:
#         return float(
#             safe_eval(
#                 expr,
#                 x=float(x_val or 0.0),
#                 y=float(y_val or 0.0),
#                 z=0.0,
#                 A=A, B=B, C=C, D=D
#             )
#         )
#     except Exception:
#         return None


# # =========================================================
# # DATCHIK TYPE DETECT
# # =========================================================

# def detect_kind(d: Datchik) -> str:
#     t = (d.title or "").strip().lower()
#     if t.startswith("sh.d-"):
#         return "shelemer"
#     if t.startswith("v/s"):
#         return "vodosliv"
#     if t.startswith("o.d-"):
#         return "niveller"
#     if "otves" in t:
#         return "otves"
#     if "byef" in t or "byev" in t or "byef" in (getattr(getattr(d, "datchik_type", None), "title", "") or "").lower():
#         return "byef"
#     # default
#     return "piezometr"


# # =========================================================
# # BUCKET POLICY
# # =========================================================

# POLICY = {
#     "piezometr": {"mode": "daily_last"},
#     "byef":      {"mode": "daily_last"},
#     "vodosliv":  {"mode": "per_day_hours", "hours": [0, 6, 12, 18, 23]},
#     "otves":     {"mode": "per_day_hours", "hours": [0, 12]},
#     "shelemer":  {"mode": "interval", "minutes": 15},
#     "niveller":  {"mode": "interval", "minutes": 15},
# }


# # =========================================================
# # RAW -> SNAPSHOTS
# # =========================================================

# def pick_snapshots(readings: List[RawReading], kind: str) -> Dict[datetime.datetime, Dict[str, float]]:
#     pol = POLICY.get(kind) or POLICY["piezometr"]
#     mode = pol["mode"]

#     bucket_map: Dict[datetime.datetime, Dict[str, Tuple[datetime.datetime, float]]] = defaultdict(dict)

#     def put(bucket_ts: datetime.datetime, r: RawReading):
#         prev = bucket_map[bucket_ts].get(r.value_type)
#         if (prev is None) or (r.ts >= prev[0]):
#             bucket_map[bucket_ts][r.value_type] = (r.ts, r.raw_value)

#     if mode == "daily_last":
#         for r in readings:
#             day = r.ts.date()
#             bucket_ts = datetime.datetime.combine(day, datetime.time(23, 59, 0))
#             if timezone.is_naive(bucket_ts):
#                 bucket_ts = timezone.make_aware(bucket_ts, timezone.get_current_timezone())
#             put(bucket_ts, r)

#     elif mode == "per_day_hours":
#         hours = pol["hours"]
#         window = datetime.timedelta(hours=2)

#         readings_sorted = sorted(readings, key=lambda x: x.ts)
#         days = sorted({r.ts.date() for r in readings_sorted})

#         for day in days:
#             for h in hours:
#                 start = datetime.datetime.combine(day, datetime.time(h, 0, 0))
#                 if timezone.is_naive(start):
#                     start = timezone.make_aware(start, timezone.get_current_timezone())
#                 end = start + window
#                 bucket_ts = start

#                 for r in readings_sorted:
#                     if r.ts < start:
#                         continue
#                     if r.ts >= end:
#                         break
#                     put(bucket_ts, r)

#     elif mode == "interval":
#         minutes = pol["minutes"]
#         for r in readings:
#             bucket_ts = floor_minutes(r.ts, minutes)
#             put(bucket_ts, r)

#     # Tuple(ts,val) -> val
#     return {bts: {vt: tv[1] for vt, tv in vmap.items()} for bts, vmap in bucket_map.items()}


# # =========================================================
# # FORMULA SELECTOR (criterion_1 / criterion_2)
# # =========================================================

# def choose_formula(d: Datchik, snap: Dict[str, float]) -> Optional[DatchikFormula]:
#     """
#     Siz aytgandek:
#       - bitta datchikda bir nechta formula bo'ladi
#       - criterion_1 va criterion_2 ga qarab to'g'ri formulasini tanlaymiz
#     Qoida (simple):
#       - snap ichidan 'bosim_MPa' yoki 'bosim' yoki 'deformatsiya_x' yoki 'sina' topib qiymat olamiz
#       - agar criterion_1 va criterion_2 berilgan bo'lsa: criterion_1 <= x <= criterion_2
#       - criterionlar bo'sh bo'lsa: "default formula" deb qabul qilamiz
#       - bir nechta mos kelsa: birinchisini olamiz (id kichigi)
#     """
#     formulas = list(d.formulas.all().order_by("id"))  # related_name="formulas"
#     if not formulas:
#         return None

#     # x qiymatini topish (qaysi tur bo'lsa shundan)
#     x = None
#     for key in ("bosim_MPa", "bosim", "deformatsiya_x", "sina"):
#         if key in snap and snap.get(key) is not None:
#             x = snap.get(key)
#             break

#     # agar x topilmasa ham default formula qaytarishga harakat qilamiz
#     defaults = [f for f in formulas if f.criterion_1 is None and f.criterion_2 is None]
#     if x is None:
#         return defaults[0] if defaults else formulas[0]

#     x = float(x)

#     # mos formula
#     matched = []
#     for f in formulas:
#         c1 = f.criterion_1
#         c2 = f.criterion_2
#         if c1 is None and c2 is None:
#             continue
#         if c1 is not None and x < float(c1):
#             continue
#         if c2 is not None and x > float(c2):
#             continue
#         matched.append(f)

#     if matched:
#         return matched[0]
#     if defaults:
#         return defaults[0]
#     return formulas[0]


# # =========================================================
# # SNAP GETTERS (temp vs temperatura)
# # =========================================================

# def get_temp(snap: Dict[str, float]) -> Optional[float]:
#     # sizda ba'zi joyda faqat temp bo'lib keladi dedingiz
#     if "temperatura" in snap and snap.get("temperatura") is not None:
#         return snap.get("temperatura")
#     if "temp" in snap and snap.get("temp") is not None:
#         return snap.get("temp")
#     return None


# # =========================================================
# # BUILD LOG
# # =========================================================

# def build_log_from_snapshot(d: Datchik, kind: str, sana: datetime.datetime, snap: Dict[str, float]) -> Optional[DatchikLog]:
#     f = choose_formula(d, snap)
#     if not f:
#         return None

#     if kind in ("piezometr", "byef"):
#         bosim_raw = snap.get("bosim_MPa", None)
#         if bosim_raw is None:
#             bosim_raw = snap.get("bosim", None)
#         t_raw = get_temp(snap)

#         log = DatchikLog(
#             formula=f,
#             sana=sana,
#             bosim_MPa=apply_formula_1(d, f, bosim_raw, "bosim_MPa"),
#             bosim_m=apply_formula_1(d, f, bosim_raw, "bosim_m"),
#             suv_sathi=apply_formula_1(d, f, snap.get("suv_sathi"), "suv_sathi"),
#             temperatura=apply_formula_1(d, f, t_raw, "temperatura"),
#         )

#         # BYEF vektor og'ish (x/y dan)
#         if kind == "byef":
#             dx = snap.get("deformatsiya_x")
#             dy = snap.get("deformatsiya_y")
#             # agar formulada vektor_ogish_korsatgichi yozilgan bo'lsa formula ishlaydi,
#             # yozilmagan bo'lsa sqrt(x^2+y^2)
#             if getattr(f, "vektor_ogish_korsatgichi", None):
#                 log.vektor_ogish_korsatgichi = apply_formula_xy(d, f, dx, dy, "vektor_ogish_korsatgichi")
#             else:
#                 if dx is not None and dy is not None:
#                     log.vektor_ogish_korsatgichi = float(math.sqrt(float(dx) ** 2 + float(dy) ** 2))
#         return log

#     if kind == "vodosliv":
#         # faqat suv_sarfi + loyqa (bosim kerak emas dedingiz)
#         sarf_raw = snap.get("suv_sarfi")
#         loyqa_raw = snap.get("loyqa")
#         return DatchikLog(
#             formula=f,
#             sana=sana,
#             suv_sarfi=apply_formula_1(d, f, sarf_raw, "suv_sarfi"),
#             loyqa=apply_formula_1(d, f, loyqa_raw, "loyqa"),
#         )

#     if kind in ("otves",):
#         dx = snap.get("deformatsiya_x")
#         dy = snap.get("deformatsiya_y")
#         t = get_temp(snap)

#         return DatchikLog(
#             formula=f,
#             sana=sana,
#             deformatsiya_x=apply_formula_1(d, f, dx, "deformatsiya_x"),
#             deformatsiya_y=apply_formula_1(d, f, dy, "deformatsiya_y"),
#             temperatura=apply_formula_1(d, f, t, "temperatura"),
#         )

#     if kind == "niveller":
#         a = snap.get("sina")
#         b = snap.get("sinb")
#         t = get_temp(snap)

#         return DatchikLog(
#             formula=f,
#             sana=sana,
#             sina=apply_formula_1(d, f, a, "sina"),
#             sinb=apply_formula_1(d, f, b, "sinb"),
#             ogish_korsatgichi=apply_formula_xy(d, f, a, b, "ogish_korsatgichi"),
#             temperatura=apply_formula_1(d, f, t, "temperatura"),
#         )

#     # shelemer
#     dx = snap.get("deformatsiya_x")
#     dy = snap.get("deformatsiya_y")
#     dz = snap.get("deformatsiya_z")
#     tx = snap.get("temperatura_x")
#     ty = snap.get("temperatura_y")
#     tz = snap.get("temperatura_z")

#     return DatchikLog(
#         formula=f,
#         sana=sana,
#         deformatsiya_x=apply_formula_1(d, f, dx, "deformatsiya_x"),
#         deformatsiya_y=apply_formula_1(d, f, dy, "deformatsiya_y"),
#         deformatsiya_z=apply_formula_1(d, f, dz, "deformatsiya_z"),
#         temperatura_x=apply_formula_1(d, f, tx, "temperatura_x"),
#         temperatura_y=apply_formula_1(d, f, ty, "temperatura_y"),
#         temperatura_z=apply_formula_1(d, f, tz, "temperatura_z"),
#     )


# # =========================================================
# # COMMAND
# # =========================================================

# class Command(BaseCommand):
#     help = "RawReading -> DatchikLog (formula + chastota policy + criterion selector)"

#     def add_arguments(self, parser):
#         parser.add_argument("--type", type=str, default="all",
#                             help="all | piezometr | byef | vodosliv | shelemer | otves | niveller")
#         parser.add_argument("--from", dest="from_dt", type=str, default="",
#                             help="YYYY-MM-DD yoki YYYY-MM-DDTHH:MM:SS")
#         parser.add_argument("--to", dest="to_dt", type=str, default="",
#                             help="YYYY-MM-DD yoki YYYY-MM-DDTHH:MM:SS")
#         parser.add_argument("--dry-run", action="store_true", help="DBga yozmaydi, faqat hisoblaydi")
#         parser.add_argument("--limit", type=int, default=0, help="Test uchun: nechta datchik ishlasin (0=hammasi)")

#     def handle(self, *args, **opts):
#         kind_filter = (opts["type"] or "all").strip().lower()
#         dry_run = bool(opts["dry_run"])
#         limit = int(opts["limit"] or 0)

#         now = timezone.now()
#         from_dt = to_dt(opts["from_dt"]) if opts["from_dt"] else (now - datetime.timedelta(days=2))
#         to_dt_ = to_dt(opts["to_dt"]) if opts["to_dt"] else now

#         if from_dt >= to_dt_:
#             self.stdout.write(self.style.ERROR("--from >= --to bo'lib qolgan"))
#             return

#         qs_d = Datchik.objects.all().prefetch_related("formulas")
#         datchiks = list(qs_d)
#         if limit > 0:
#             datchiks = datchiks[:limit]

#         bulk_logs: List[DatchikLog] = []
#         touched_datchiks = 0

#         for d in datchiks:
#             kind = detect_kind(d)
#             if kind_filter != "all" and kind != kind_filter:
#                 continue

#             if not d.formulas.exists():
#                 # formula yo'q bo'lsa log yaratmaymiz (unique constraint formula+sana bor)
#                 continue

#             readings = list(
#                 RawReading.objects.filter(datchik=d, ts__gte=from_dt, ts__lt=to_dt_).order_by("ts")
#             )
#             if not readings:
#                 continue

#             snaps = pick_snapshots(readings, kind)
#             if not snaps:
#                 continue

#             # bu datchik formulalarining idlari
#             formula_ids = list(d.formulas.values_list("id", flat=True))

#             # existing sanalar: shu datchikdagi barcha formulalar bo'yicha
#             existing_sanas = set(
#                 DatchikLog.objects.filter(formula_id__in=formula_ids, sana__gte=from_dt, sana__lt=to_dt_)
#                 .values_list("sana", flat=True)
#             )

#             created_here = 0
#             for sana, snap in snaps.items():
#                 if sana in existing_sanas:
#                     continue

#                 log = build_log_from_snapshot(d, kind, sana, snap)
#                 if log is None:
#                     continue
#                 bulk_logs.append(log)
#                 created_here += 1

#             if created_here:
#                 touched_datchiks += 1

#         if dry_run:
#             self.stdout.write(self.style.WARNING(f"[DRY RUN] Yaratiladigan loglar: {len(bulk_logs)}"))
#             return

#         if bulk_logs:
#             with transaction.atomic():
#                 DatchikLog.objects.bulk_create(bulk_logs, ignore_conflicts=True)

#         self.stdout.write(self.style.SUCCESS(
#             f"Datchiklar: {touched_datchiks} ta, Loglar: {len(bulk_logs)} ta yaratildi"
#         ))


import datetime
import math
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.db import transaction

from app.models import Datchik, DatchikLog, RawReading, DatchikFormula


# =========================================================
# TIME HELPERS
# =========================================================

def to_dt(s: str) -> Optional[datetime.datetime]:
    if not s:
        return None
    d = parse_datetime(s)
    if not d:
        return None
    if timezone.is_naive(d):
        d = timezone.make_aware(d, timezone.get_current_timezone())
    return d


def floor_minutes(dt: datetime.datetime, minutes: int) -> datetime.datetime:
    m = (dt.minute // minutes) * minutes
    return dt.replace(minute=m, second=0, microsecond=0)


# =========================================================
# SAFE EVAL (formula)
# =========================================================

_ALLOWED_MATH = {
    "abs": abs,
    "min": min,
    "max": max,
    "round": round,
    "pow": pow,
    "sqrt": math.sqrt,

    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,

    "pi": math.pi,
    "e": math.e,
}


def safe_eval(expr: str, locals_dict: dict) -> Optional[float]:
    """
    Formulada ishlaydigan o'zgaruvchilar:
      x,y,z,A,B,C,D va math funksiyalar
    """
    if not expr:
        return None
    try:
        return eval(expr, {"__builtins__": {}}, {**_ALLOWED_MATH, **locals_dict})
    except Exception:
        return None


# =========================================================
# DATCHIK TYPE DETECT
# =========================================================

def detect_kind(d: Datchik) -> str:
    """
    Eslatma: BYEF alohida "kind" bo'lsa policy/vektor uchun qulay.
    Sizda byef title ichida bo'lishi yoki datchik_type.title da bo'lishi mumkin.
    """
    t = (d.title or "").strip().lower()
    dtype = (getattr(getattr(d, "datchik_type", None), "title", "") or "").strip().lower()

    if t.startswith("sh.d-"):
        return "shelemer"
    if t.startswith("v/s"):
        return "vodosliv"
    if t.startswith("o.d-"):
        return "niveller"
    if "otves" in t:
        return "otves"
    if ("byef" in t) or ("byev" in t) or ("byef" in dtype) or ("byev" in dtype):
        return "byef"
    return "piezometr"


# =========================================================
# BUCKET POLICY
# =========================================================

POLICY = {
    "piezometr": {"mode": "daily_last"},
    "byef":      {"mode": "daily_last"},
    "vodosliv":  {"mode": "per_day_hours", "hours": [0, 6, 12, 18, 23]},
    "otves":     {"mode": "per_day_hours", "hours": [0, 12]},
    "shelemer":  {"mode": "interval", "minutes": 15},
    "niveller":  {"mode": "interval", "minutes": 15},
}


# =========================================================
# RAW -> SNAPSHOTS
# =========================================================

def pick_snapshots(readings: List[RawReading], kind: str) -> Dict[datetime.datetime, Dict[str, float]]:
    pol = POLICY.get(kind) or POLICY["piezometr"]
    mode = pol["mode"]

    bucket_map: Dict[datetime.datetime, Dict[str, Tuple[datetime.datetime, float]]] = defaultdict(dict)

    def put(bucket_ts: datetime.datetime, r: RawReading):
        prev = bucket_map[bucket_ts].get(r.value_type)
        if (prev is None) or (r.ts >= prev[0]):
            bucket_map[bucket_ts][r.value_type] = (r.ts, r.raw_value)

    if mode == "daily_last":
        for r in readings:
            day = r.ts.date()
            bucket_ts = datetime.datetime.combine(day, datetime.time(23, 59, 0))
            if timezone.is_naive(bucket_ts):
                bucket_ts = timezone.make_aware(bucket_ts, timezone.get_current_timezone())
            put(bucket_ts, r)

    elif mode == "per_day_hours":
        hours = pol["hours"]
        window = datetime.timedelta(hours=2)

        readings_sorted = sorted(readings, key=lambda x: x.ts)
        days = sorted({r.ts.date() for r in readings_sorted})

        for day in days:
            for h in hours:
                start = datetime.datetime.combine(day, datetime.time(h, 0, 0))
                if timezone.is_naive(start):
                    start = timezone.make_aware(start, timezone.get_current_timezone())
                end = start + window
                bucket_ts = start

                for r in readings_sorted:
                    if r.ts < start:
                        continue
                    if r.ts >= end:
                        break
                    put(bucket_ts, r)

    elif mode == "interval":
        minutes = pol["minutes"]
        for r in readings:
            bucket_ts = floor_minutes(r.ts, minutes)
            put(bucket_ts, r)

    return {bts: {vt: tv[1] for vt, tv in vmap.items()} for bts, vmap in bucket_map.items()}


# =========================================================
# FORMULA SELECTOR (criterion_1 / criterion_2)
# =========================================================

def _pick_x_for_criteria(snap: Dict[str, float]) -> Optional[float]:
    """
    mezon solishtirish uchun bitta 'x' topib olamiz.
    Ustuvorlikni xohlasangiz o'zgartirasiz.
    """
    for key in (
        "bosim_MPa", "bosim_m", "suv_sathi",
        "deformatsiya_x", "deformatsiya_y", "deformatsiya_z",
        "sina", "sinb",
        "temperatura",
    ):
        if key in snap and snap.get(key) is not None:
            return float(snap[key])
    return None


def choose_formula(d: Datchik, snap: Dict[str, float]) -> Optional[DatchikFormula]:
    formulas = list(d.formulas.all().order_by("id"))  # related_name="formulas"
    if not formulas:
        return None

    xval = _pick_x_for_criteria(snap)

    default_f = None
    for f in formulas:
        c1 = f.criterion_1
        c2 = f.criterion_2

        if c1 is None and c2 is None:
            if default_f is None:
                default_f = f
            continue

        if xval is None:
            continue

        lo = float(c1) if c1 is not None else -float("inf")
        hi = float(c2) if c2 is not None else float("inf")
        if lo <= float(xval) <= hi:
            return f

    return default_f or formulas[0]


# =========================================================
# SNAP GETTER (temp vs temperatura)
# =========================================================

def get_temp(snap: Dict[str, float]) -> Optional[float]:
    if snap.get("temperatura") is not None:
        return snap.get("temperatura")
    if snap.get("temp") is not None:
        return snap.get("temp")
    return None


# =========================================================
# COMPUTE FIELD (x/y/z qoidalari)
# =========================================================

LOG_FIELDS = [
    "bosim_MPa", "bosim_m", "bosim_sm", "bosim_mm",
    "deformatsiya_x", "deformatsiya_y", "deformatsiya_z",
    "temperatura_x", "temperatura_y", "temperatura_z",
    "sina", "sinb", "vektor_ogish_korsatgichi",
    "temperatura", "suv_sathi", "suv_sarfi", "loyqa",
]


def compute_field(d: Datchik, f: DatchikFormula, field: str, snap: Dict[str, float], *, kind: str) -> Optional[float]:
    """
    Qoidalar:
    - expr bo'lmasa -> raw qiymat
    - vektor_ogish_korsatgichi (BYEF): x=deformatsiya_x, y=deformatsiya_y
    - *_x -> x=raw(field)
    - *_y -> y=raw(field)
    - *_z -> z=raw(field)
    - oddiy scalar (sina/sinb ham): x=raw(field)
    """
    expr = getattr(f, field, None)
    raw_val = snap.get(field)

    # expr yo'q bo'lsa -> raw
    if not expr:
        return float(raw_val) if raw_val is not None else None

    A = float(getattr(d, "A", 0) or 0)
    B = float(getattr(d, "B", 0) or 0)
    C = float(getattr(d, "C", 0) or 0)
    D = float(getattr(d, "D", 0) or 0)

    locals_dict = {
        "A": A, "B": B, "C": C, "D": D,
        "x": 0.0, "y": 0.0, "z": 0.0,
    }

    # snap qiymatlarni ham localsga qo'shamiz (xohlasangiz)
    for k, v in snap.items():
        if v is None:
            continue
        if isinstance(k, str) and k.isidentifier():
            locals_dict[k] = float(v)

    # BYEF vektor og'ish: x=deformatsiya_x, y=deformatsiya_y
    if field == "vektor_ogish_korsatgichi":
        dx = snap.get("deformatsiya_x")
        dy = snap.get("deformatsiya_y")
        locals_dict["x"] = float(dx) if dx is not None else 0.0
        locals_dict["y"] = float(dy) if dy is not None else 0.0
        locals_dict["z"] = 0.0
        return safe_eval(expr, locals_dict)

    # axis fields: *_x/_y/_z
    if field.endswith("_x"):
        v = snap.get(field)
        locals_dict["x"] = float(v) if v is not None else 0.0
        locals_dict["y"] = 0.0
        locals_dict["z"] = 0.0
        return safe_eval(expr, locals_dict)

    if field.endswith("_y"):
        v = snap.get(field)
        locals_dict["x"] = 0.0
        locals_dict["y"] = float(v) if v is not None else 0.0
        locals_dict["z"] = 0.0
        return safe_eval(expr, locals_dict)

    if field.endswith("_z"):
        v = snap.get(field)
        locals_dict["x"] = 0.0
        locals_dict["y"] = 0.0
        locals_dict["z"] = float(v) if v is not None else 0.0
        return safe_eval(expr, locals_dict)

    # oddiy scalar: x=raw(field)  (sina/sinb shu yerga tushadi)
    locals_dict["x"] = float(raw_val) if raw_val is not None else 0.0
    locals_dict["y"] = 0.0
    locals_dict["z"] = 0.0
    return safe_eval(expr, locals_dict)


# =========================================================
# BUILD LOG (kind bo'yicha snap mapping)
# =========================================================

def build_log_from_snapshot(d: Datchik, kind: str, sana: datetime.datetime, snap: Dict[str, float]) -> Optional[DatchikLog]:
    f = choose_formula(d, snap)
    if not f:
        return None

    # temp key normalize (ba'zi joyda temp keladi)
    if snap.get("temperatura") is None and snap.get("temp") is not None:
        snap = dict(snap)
        snap["temperatura"] = snap.get("temp")

    # piezometr/byef: bosim raw key'lari (bosim_MPa yoki bosim)
    if kind in ("piezometr", "byef"):
        if snap.get("bosim_MPa") is None and snap.get("bosim") is not None:
            snap = dict(snap)
            snap["bosim_MPa"] = snap.get("bosim")

    log = DatchikLog(formula=f, sana=sana)

    for field in LOG_FIELDS:
        # vodoslivda bosimlarni yozmaymiz, faqat suv_sarfi/loyqa (+xohlasang temperatura)
        if kind == "vodosliv" and field not in ("suv_sarfi", "loyqa"):
            continue

        # otvesda asosan deformatsiya_x/y (+temperatura) kerak
        if kind == "otves" and field not in ("deformatsiya_x", "deformatsiya_y", "temperatura"):
            continue

        # nivellerda sina/sinb/temperatura (+ogish_korsatgichi) kerak
        if kind == "niveller" and field not in ("sina", "sinb", "temperatura", "ogish_korsatgichi"):
            continue

        # shelemerda deformatsiya_xyz va temperatura_xyz kerak (xohlasangiz temperatura umumiy ham qo'shasiz)
        if kind == "shelemer" and field not in (
            "deformatsiya_x", "deformatsiya_y", "deformatsiya_z",
            "temperatura_x", "temperatura_y", "temperatura_z",
        ):
            continue

        # byefda deformatsiya_x/y va vektor_ogish (+temperatura ixtiyoriy)
        if kind == "byef" and field not in ("deformatsiya_x", "deformatsiya_y", "vektor_ogish_korsatgichi", "temperatura"):
            # bosim_MPa/bosim_m/suv_sathi ham bo'lsa yozishni xohlasangiz shu filterdan olib tashlang
            continue

        val = compute_field(d, f, field, snap, kind=kind)
        setattr(log, field, val)

    return log


# =========================================================
# COMMAND
# =========================================================

class Command(BaseCommand):
    help = "RawReading -> DatchikLog (policy + criterion selector + byef vektor)"

    def add_arguments(self, parser):
        parser.add_argument("--type", type=str, default="all",
                            help="all | piezometr | byef | vodosliv | shelemer | otves | niveller")
        parser.add_argument("--from", dest="from_dt", type=str, default="",
                            help="YYYY-MM-DD yoki YYYY-MM-DDTHH:MM:SS")
        parser.add_argument("--to", dest="to_dt", type=str, default="",
                            help="YYYY-MM-DD yoki YYYY-MM-DDTHH:MM:SS")
        parser.add_argument("--dry-run", action="store_true", help="DBga yozmaydi, faqat hisoblaydi")
        parser.add_argument("--limit", type=int, default=0, help="Test: nechta datchik (0=hammasi)")

    def handle(self, *args, **opts):
        kind_filter = (opts["type"] or "all").strip().lower()
        dry_run = bool(opts["dry_run"])
        limit = int(opts["limit"] or 0)

        now = timezone.now()
        from_dt = to_dt(opts["from_dt"]) if opts["from_dt"] else (now - datetime.timedelta(days=2))
        to_dt_ = to_dt(opts["to_dt"]) if opts["to_dt"] else now

        if not from_dt or not to_dt_ or from_dt >= to_dt_:
            self.stdout.write(self.style.ERROR("Vaqt oralig'i xato: --from < --to bo'lishi kerak"))
            return

        qs_d = Datchik.objects.all().prefetch_related("formulas")
        datchiks = list(qs_d)
        if limit > 0:
            datchiks = datchiks[:limit]

        bulk_logs: List[DatchikLog] = []
        touched_datchiks = 0

        for d in datchiks:
            kind = detect_kind(d)
            if kind_filter != "all" and kind != kind_filter:
                continue

            if not d.formulas.exists():
                # unique constraint formula+sana bor
                continue

            readings = list(
                RawReading.objects.filter(datchik=d, ts__gte=from_dt, ts__lt=to_dt_).order_by("ts")
            )
            if not readings:
                continue

            snaps = pick_snapshots(readings, kind)
            if not snaps:
                continue

            # mezon bo'yicha formula tanlanadi (har sana har xil formula bo'lishi mumkin)
            # shuning uchun oldindan existing_sanas bilan qattiq kesmaymiz;
            # lekin tezlik uchun: shu datchik formulalari bo'yicha sanalarni olamiz
            formula_ids = list(d.formulas.values_list("id", flat=True))
            existing_sanas = set(
                DatchikLog.objects.filter(formula_id__in=formula_ids, sana__gte=from_dt, sana__lt=to_dt_)
                .values_list("sana", flat=True)
            )

            created_here = 0
            for sana, snap in snaps.items():
                if sana in existing_sanas:
                    continue

                log = build_log_from_snapshot(d, kind, sana, snap)
                if log is None:
                    continue

                bulk_logs.append(log)
                created_here += 1

            if created_here:
                touched_datchiks += 1

        if dry_run:
            self.stdout.write(self.style.WARNING(f"[DRY RUN] Yaratiladigan loglar: {len(bulk_logs)}"))
            return

        if bulk_logs:
            with transaction.atomic():
                DatchikLog.objects.bulk_create(bulk_logs, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS(
            f"✅ Datchiklar: {touched_datchiks} ta, Loglar: {len(bulk_logs)} ta yaratildi"
        ))
