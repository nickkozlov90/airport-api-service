from django.contrib import admin

from .models import (
    Airline,
    Airport,
    AirplaneType,
    Airplane,
    Route,
    Flight,
    Order,
    Ticket,
)

admin.site.register(Airline)
admin.site.register(AirplaneType)
admin.site.register(Route)
admin.site.register(Flight)


@admin.register(Airport)
class AirportListingAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "closest_big_city"]


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
