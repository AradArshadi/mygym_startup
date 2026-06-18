from django.contrib import admin
from .models import Facility, Gym, GymImage, ImportBatch, MembershipPlan, TrainerProfile


class MembershipPlanInline(admin.TabularInline):
    model = MembershipPlan
    extra = 1


class GymImageInline(admin.TabularInline):
    model = GymImage
    extra = 1


@admin.register(ImportBatch)
class ImportBatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'source', 'city', 'country', 'total_found', 'total_created', 'total_updated', 'created_at')
    list_filter = ('source', 'city', 'country')
    search_fields = ('city', 'country', 'source', 'notes')
    readonly_fields = ('created_at',)


@admin.register(Gym)
class GymAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'owner', 'starting_price', 'status', 'is_imported', 'is_claimed', 'source', 'created_at')
    list_filter = ('status', 'city', 'facilities', 'is_imported', 'is_claimed', 'source')
    search_fields = ('name', 'city', 'address', 'external_id')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [MembershipPlanInline, GymImageInline]


admin.site.register(Facility)
admin.site.register(MembershipPlan)
admin.site.register(GymImage)
admin.site.register(TrainerProfile)
