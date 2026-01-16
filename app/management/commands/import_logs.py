import datetime
import math
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from app.models import Datchik, DatchikFormula, DatchikLog, RawReading


# ===================== TIME HELPERS =====================

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


# ===================== DATCHIK KIND =====================

def detect_kind(d: Datchik) -> str:
    t = (d.title or "").strip().lower()
    if t.startswith("sh.d-"):
        return "shelemer"
    if t.startswith("v/s"):
        return "vodosliv"
    if t.startswith("o.d-"):
        return "niveller"
    if "otves" in t:
        return "atves"
    return "piezometr"


# ===================== POLICY (BUCKET) =====================

POLICY = {
    "piezometr": {"mode": "daily_last"},
    "vodosliv":  {"mode": "per_day_hours", "hours": [0, 6, 12, 18, 23]},
    "atves":     {"mode": "per_day_hours", "hours": [0, 12]},
    "shelemer":  {"mode": "interval", "minutes": 15},
    "niveller":  {"mode": "interval", "minutes": 15},
}


def pick_snapshots(readings: List[RawReading], kind: str) -> Dict[datetime.datetime, Dict[str, float]]:
    """
    returns: {bucket_ts: {value_type: raw_value, ...}}
    """
    pol = POLICY.get(kind) or POLICY["piezometr"]
    mode = pol["mode"]

    bucket_map: Dict[datetime.datetime, Dict[str, Tuple[datetime.datetime, float]]] = defaultdict(dict)

    if mode == "daily_last":
        for r in readings:
            day = r.ts.date()
            bucket_ts = datetime.datetime.combine(day, datetime.time(23, 59, 0))
            if timezone.is_naive(bucket_ts):
                bucket_ts = timezone.make_aware(bucket_ts, timezone.get_current_timezone())

            prev = bucket_map[bucket_ts].get(r.value_type)
            if (prev is None) or (r.ts >= prev[0]):
                bucket_map[bucket_ts][r.value_type] = (r.ts, r.raw_value)

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
                    prev = bucket_map[bucket_ts].get(r.value_type)
                    if (prev is None) or (r.ts >= prev[0]):
                        bucket_map[bucket_ts][r.value_type] = (r.ts, r.raw_value)

    elif mode == "interval":
        minutes = pol["minutes"]
        for r in readings:
            bucket_ts = floor_minutes(r.ts, minutes)
            prev = bucket_map[bucket_ts].get(r.value_type)
            if (prev is None) or (r.ts >= prev[0]):
                bucket_map[bucket_ts][r.value_type] = (r.ts, r.raw_value)

    out: Dict[datetime.datetime, Dict[str, float]] = {}
    for bts, vmap in bucket_map.items():
        out[bts] = {vt: tv[1] for vt, tv in vmap.items()}
    return out


# ===================== SAFE EVAL =====================

_ALLOWED_MATH = {
    "abs": abs,
    "min": min,
    "max": max,
    "round": round,
    "pow": pow,

    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,

    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "pi": math.pi,
    "e": math.e,
}


def safe_eval(expr: str, locals_dict: dict) -> Optional[float]:
    if not expr:
        return None
    try:
        return eval(expr, {"__builtins__": {}}, {**_ALLOWED_MATH, **locals_dict})
    except Exception:
        return None


# ===================== FORMULA SELECT (MEZON) =====================

def _pick_x_for_criteria(snap: Dict[str, float]) -> Optional[float]:
    for key in (
        "bosim_MPa", "bosim_m", "suv_sathi",
        "deformatsiya_x", "deformatsiya_y", "deformatsiya_z",
        "sina", "sinb",
        "temperatura",
    ):
        if key in snap and snap[key] is not None:
            return float(snap[key])
    return None


def choose_formula(d: Datchik, snap: Dict[str, float]) -> Optional[DatchikFormula]:
    formulas = list(d.formulas.all().order_by("id"))
    if not formulas:
        return None

    xval = _pick_x_for_criteria(snap)

    default_f = None
    for f in formulas:
        c1 = f.criterion_1
        c2 = f.criterion_2

        # default formula
        if c1 is None and c2 is None:
            if default_f is None:
                default_f = f
            continue

        if xval is None:
            continue

        lo = c1 if c1 is not None else -float("inf")
        hi = c2 if c2 is not None else float("inf")
        if lo <= xval <= hi:
            return f

    return default_f or formulas[0]


# ===================== FIELD COMPUTE =====================

LOG_FIELDS = [
    "bosim_MPa", "bosim_m", "bosim_sm", "bosim_mm",
    "deformatsiya_x", "deformatsiya_y", "deformatsiya_z",
    "temperatura_x", "temperatura_y", "temperatura_z",
    "sina", "sinb", "vektor_ogish_korsatgichi",
    "temperatura", "suv_sathi", "suv_sarfi", "loyqa",
]


def compute_field(d: Datchik, f: DatchikFormula, field: str, snap: Dict[str, float]) -> Optional[float]:
    expr = getattr(f, field, None)
    raw_val = snap.get(field)

    A = float(getattr(d, "A", 0) or 0)
    B = float(getattr(d, "B", 0) or 0)
    C = float(getattr(d, "C", 0) or 0)
    D = float(getattr(d, "D", 0) or 0)

    # expr yo'q bo'lsa -> raw (sina/sinb ham shunday ishlaydi)
    if not expr:
        return float(raw_val) if raw_val is not None else None

    locals_dict = {
        "A": A, "B": B, "C": C, "D": D,
        "x": 0.0, "y": 0.0, "z": 0.0,
    }

    # snap qiymatlarni localsga ham qo'shamiz
    for k, v in snap.items():
        if v is None:
            continue
        if isinstance(k, str) and k.isidentifier():
            locals_dict[k] = float(v)

    # ✅ BYEF vektor og'ish: x=deformatsiya_x, y=deformatsiya_y
    if field == "vektor_ogish_korsatgichi":
        dx = snap.get("deformatsiya_x")
        dy = snap.get("deformatsiya_y")
        locals_dict["x"] = float(dx) if dx is not None else 0.0
        locals_dict["y"] = float(dy) if dy is not None else 0.0
        locals_dict["z"] = 0.0
        return safe_eval(expr, locals_dict)

    # Axis rule: *_x => x, *_y => y, *_z => z
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

    # oddiy scalar: formulada x=raw(field)
    locals_dict["x"] = float(raw_val) if raw_val is not None else 0.0
    locals_dict["y"] = 0.0
    locals_dict["z"] = 0.0
    return safe_eval(expr, locals_dict)


def build_log(d: Datchik, sana: datetime.datetime, snap: Dict[str, float]) -> Optional[DatchikLog]:
    f = choose_formula(d, snap)
    if not f:
        return None

    log = DatchikLog(
        sana=sana,
        formula=f,
    )

    for field in LOG_FIELDS:
        setattr(log, field, compute_field(d, f, field, snap))

    return log


# ===================== COMMAND =====================

class Command(BaseCommand):
    help = "RawReading -> DatchikLog (faqat DBdan). Mezonga ko'ra formula tanlaydi."

    def add_arguments(self, parser):
        parser.add_argument("--type", type=str, default="all",
                            help="all | piezometr | vodosliv | shelemer | atves | niveller")
        parser.add_argument("--from", dest="from_dt", type=str, default="",
                            help="YYYY-MM-DD yoki YYYY-MM-DDTHH:MM:SS")
        parser.add_argument("--to", dest="to_dt", type=str, default="",
                            help="YYYY-MM-DD yoki YYYY-MM-DDTHH:MM:SS")
        parser.add_argument("--limit", type=int, default=0, help="Test: nechta datchik (0=hammasi)")
        parser.add_argument("--dry-run", action="store_true", help="DBga yozmaydi")

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

        bulk: List[DatchikLog] = []
        total_d = 0

        for d in datchiks:
            kind = detect_kind(d)
            if kind_filter != "all" and kind != kind_filter:
                continue

            readings = list(
                RawReading.objects.filter(datchik=d, ts__gte=from_dt, ts__lt=to_dt_).order_by("ts")
            )
            if not readings:
                continue

            snaps = pick_snapshots(readings, kind)
            if not snaps:
                continue

            created_here = 0
            for sana, snap in snaps.items():
                log = build_log(d, sana, snap)
                if not log:
                    continue
                bulk.append(log)
                created_here += 1

            if created_here:
                total_d += 1

        if dry_run:
            self.stdout.write(self.style.WARNING(f"[DRY RUN] Yaratiladigan loglar: {len(bulk)}"))
            return

        if bulk:
            with transaction.atomic():
                DatchikLog.objects.bulk_create(bulk, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS(f"✅ Datchiklar: {total_d} ta, Loglar: {len(bulk)} ta yaratildi"))
