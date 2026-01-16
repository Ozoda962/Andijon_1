from django.db import models


class Direction(models.Model):
    title = models.CharField(max_length=255)
    logo = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.title


class Location(models.Model):
    code = models.PositiveIntegerField(unique=True, null=True, blank=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    direction = models.ForeignKey(
        Direction,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="direction_locations"
    )

    def __str__(self):
        return self.title or f"Location #{self.id}"


class Section(models.Model):
    title = models.CharField(max_length=255)

    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="location_sections"
    )

    direction = models.ForeignKey(
        Direction,
        on_delete=models.CASCADE,
        related_name="direction_sections"
    )

    def __str__(self):
        return self.title


class DatchikType(models.Model):
    title = models.CharField(max_length=100, unique=True)
    interval_minutes = models.PositiveIntegerField(null=True, blank=True)
    per_day = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return self.title


class Datchik(models.Model):
    title = models.CharField(max_length=255)

    direction = models.ForeignKey(
        Direction,
        on_delete=models.CASCADE,
        related_name="direction_datchiks"
    )

    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="location_datchiks"
    )

    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="section_datchiks"
    )

    datchik_type = models.ForeignKey(
        DatchikType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="datchiklar"
    )

    # Pasport koeffitsiyentlari (xohlasangiz formulada ham ishlatasiz)
    A = models.FloatField(null=True, blank=True)
    B = models.FloatField(null=True, blank=True)
    C = models.FloatField(null=True, blank=True)
    D = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.title


class DatchikFormula(models.Model):
    datchik = models.ForeignKey(
        Datchik,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="formulas"   # ko‘p formula bo‘lsa qulay
    )

    # har doim ochiq bo‘lsin
    criterion_1 = models.FloatField(null=True, blank=True)
    criterion_2 = models.FloatField(null=True, blank=True)

    # Piezometr / Byef / Vodosliv
    bosim_MPa = models.CharField(max_length=255, null=True, blank=True)
    bosim_m = models.CharField(max_length=255, null=True, blank=True)
    # bosim_sm = models.CharField(max_length=255, null=True, blank=True)
    # bosim_mm = models.CharField(max_length=255, null=True, blank=True)

    suv_sathi = models.CharField(max_length=255, null=True, blank=True)
    temperatura = models.CharField(max_length=255, null=True, blank=True)
    suv_sarfi = models.CharField(max_length=255, null=True, blank=True)
    loyqa = models.CharField(max_length=255, null=True, blank=True)

    # Shelemer / Otves (deformatsiya)
    deformatsiya_x = models.CharField(max_length=255, null=True, blank=True)
    deformatsiya_y = models.CharField(max_length=255, null=True, blank=True)
    deformatsiya_z = models.CharField(max_length=255, null=True, blank=True)

    temperatura_x = models.CharField(max_length=255, null=True, blank=True)
    temperatura_y = models.CharField(max_length=255, null=True, blank=True)
    temperatura_z = models.CharField(max_length=255, null=True, blank=True)

    vektor_ogish_korsatgichi = models.CharField(max_length=255, null=True, blank=True)
    sina = models.CharField(max_length=255, null=True, blank=True)
    sinb = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        if self.datchik:
            return f"Formula for {self.datchik.title}"
        return f"Formula #{self.id}"


class DatchikLog(models.Model):
    sana = models.DateTimeField(db_index=True)

    formula = models.ForeignKey(
        DatchikFormula,
        on_delete=models.CASCADE,
        related_name="logs",
        null=True,
        blank=True
    )

    # --- Piezometr ---
    bosim_MPa = models.FloatField(null=True, blank=True)
    bosim_m = models.FloatField(null=True, blank=True)
    bosim_sm = models.FloatField(null=True, blank=True)
    bosim_mm = models.FloatField(null=True, blank=True)

    # --- Otves / Shelemer ---
    deformatsiya_x = models.FloatField(null=True, blank=True)
    deformatsiya_y = models.FloatField(null=True, blank=True)
    deformatsiya_z = models.FloatField(null=True, blank=True)

    temperatura_x = models.FloatField(null=True, blank=True)
    temperatura_y = models.FloatField(null=True, blank=True)
    temperatura_z = models.FloatField(null=True, blank=True)

    # --- Niveller ---
    vektor_ogish_korsatgichi = models.FloatField(null=True, blank=True)
    sina = models.FloatField(null=True, blank=True)
    sinb = models.FloatField(null=True, blank=True)

    # --- Umumiy ---
    temperatura = models.FloatField(null=True, blank=True)
    suv_sathi = models.FloatField(null=True, blank=True)
    suv_sarfi = models.FloatField(null=True, blank=True)
    loyqa = models.FloatField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["formula", "sana"],
                name="uniq_log_formula_sana"
            )
        ]

    def __str__(self):
        if self.formula and self.formula.datchik:
            return f"{self.formula.datchik.title} @ {self.sana}"
        return f"DatchikLog #{self.id}"


class DataloggerChannel(models.Model):
    node_id = models.CharField(max_length=50)      # 114724, 107474, 122441
    channel = models.CharField(max_length=10)      # ch1, ch2, temp

    datchik = models.ForeignKey(
        Datchik,
        on_delete=models.CASCADE,
        related_name="channels"
    )

    VALUE_TYPES = [
        ("bosim_MPa", "Bosim_MPa"),
        ("bosim_m", "Bosim m"),
        ("bosim_sm", "Bosim sm"),
        ("bosim_mm", "Bosim mm"),
        ("deformatsiya_x", "Deformatsiya X"),
        ("deformatsiya_y", "Deformatsiya Y"),
        ("deformatsiya_z", "Deformatsiya Z"),
        ("sina", "Sin(A)"),
        ("sinb", "Sin(B)"),
        ("vektor_ogish_korsatgichi", "Vektor Og'ish"),
        ("temperatura", "Temperatura"),
        ("temperatura_x", "Temperatura X"),
        ("temperatura_y", "Temperatura Y"),
        ("temperatura_z", "Temperatura Z"),
        ("suv_sathi", "Suv sathi"),
        ("suv_sarfi", "Suv sarfi"),
        ("loyqa", "Loyqa"),
    ]
    value_type = models.CharField(max_length=50, choices=VALUE_TYPES)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["node_id", "channel"], name="uniq_node_channel")
        ]

    def save(self, *args, **kwargs):
        if self.channel:
            self.channel = self.channel.strip().lower()   # "Ch1" -> "ch1"
        if self.node_id:
            self.node_id = self.node_id.strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.node_id} {self.channel} → {self.datchik.title} [{self.value_type}]"


class RawReading(models.Model):
    VALUE_TYPES = [
        ("bosim_MPa", "Bosim_MPa"),
        ("bosim_m", "Bosim m"),
        ("bosim_sm", "Bosim sm"),
        ("bosim_mm", "Bosim mm"),
        ("deformatsiya_x", "Deformatsiya X"),
        ("deformatsiya_y", "Deformatsiya Y"),
        ("deformatsiya_z", "Deformatsiya Z"),
        ("sina", "Sin(A)"),
        ("sinb", "Sin(B)"),
        ("vektor_ogish_korsatgichi", "Vektor Og'ish"),
        ("temperatura", "Temperatura"),
        ("temperatura_x", "Temperatura X"),
        ("temperatura_y", "Temperatura Y"),
        ("temperatura_z", "Temperatura Z"),
        ("loyqa", "Loyqa"),
        ("suv_sathi", "Suv sathi"),
        ("suv_sarfi", "Suv sarfi"),
    ]

    datchik = models.ForeignKey(Datchik, on_delete=models.CASCADE, related_name="raw_readings")
    ts = models.DateTimeField(db_index=True)
    value_type = models.CharField(max_length=50, db_index=True, choices=VALUE_TYPES)
    raw_value = models.FloatField(null=True, blank=True)

    source_file = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["datchik", "ts", "value_type"], name="uniq_raw_datchik_ts_type")
        ]
        indexes = [
            models.Index(fields=["datchik", "ts"]),
            models.Index(fields=["value_type", "ts"]),
        ]

    def __str__(self):
        return f"{self.datchik.title} {self.value_type} @ {self.ts}"


class DatchikState(models.Model):
    datchik = models.OneToOneField(
        Datchik,
        on_delete=models.CASCADE,
        related_name="state"
    )
    last_log_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"State: {self.datchik.title}"
