from django.contrib import admin

from django.contrib import admin
from .models import (
    Direction,
    Location,
    Section,
    Datchik,
    DatchikLog,
    DatchikFormula
)

# -------- Inline --------
class LocationInline(admin.TabularInline):
    model = Location
    extra = 0


class SectionInline(admin.TabularInline):
    model = Section
    extra = 0


class DatchikInline(admin.TabularInline):
    model = Datchik
    extra = 0


class DatchikLogInline(admin.TabularInline):
    model = DatchikLog
    extra = 0
    readonly_fields = ("created_at",)


# -------- Admin Panels --------
@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ("id", "title")
    search_fields = ("title",)
    inlines = [LocationInline]


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "direction")
    list_filter = ("direction",)
    search_fields = ("title",)
    inlines = [SectionInline, DatchikInline]


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "location", "direction")
    list_filter = ("direction", "location")
    search_fields = ("title",)
    inlines = [DatchikInline]


@admin.register(Datchik)
class DatchikAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "direction", "location", "section")
    list_filter = ("direction", "location", "section")
    search_fields = ("title",)
    inlines = [DatchikLogInline]


@admin.register(DatchikLog)
class DatchikLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "datchik",
        "pressure",
        "temperature",
        "water_consumption",
        "created_at",
    )
    list_filter = ("created_at", "datchik")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at",)

@admin.register(DatchikFormula)
class DatchikFormulaAdmin(admin.ModelAdmin):
    list_display = ("id", "datchik","formula")
    list_filter = ("datchik", "formula")
    search_fields = ("id","formula")
    