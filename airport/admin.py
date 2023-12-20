from django.contrib import admin

from .models import (
    Airport,
    AirplaneType,
    Airplane,
    Crew,
    Route,
    Flight,
    Order,
    Ticket,
)

admin.site.register(AirplaneType)
admin.site.register(Crew)
admin.site.register(Route)
admin.site.register(Flight)


@admin.register(Airport)
class AirportListingAdmin(admin.ModelAdmin):
    list_display = ["name", "short_name", "closest_big_city"]


@admin.register(Airplane)
class AirplaneListingAdmin(admin.ModelAdmin):
    list_display = ["name", "airplane_type", "capacity"]


@admin.register(Order)
class OrderListingAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "created_at",
    ]


@admin.register(Ticket)
class TicketListingAdmin(admin.ModelAdmin):
    list_display = [
        "order",
        "flight",
        "row",
        "seat",
    ]
