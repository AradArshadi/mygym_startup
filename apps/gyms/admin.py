from django.contrib import admin
from .models import Facility, Gym, GymImage, MembershipPlan, TrainerProfile


class MembershipPlanInline(admin.TabularInline):
    model = MembershipPlan
    extra = 1


class GymImageInline(admin.TabularInline):
    model = GymImage
    extra = 1


@admin.register(Gym)
class GymAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'owner', 'starting_price', 'status', 'created_at')
    list_filter = ('status', 'city', 'facilities')
    search_fields = ('name', 'city', 'address')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [MembershipPlanInline, GymImageInline]


admin.site.register(Facility)
admin.site.register(MembershipPlan)
admin.site.register(GymImage)
admin.site.register(TrainerProfile)
