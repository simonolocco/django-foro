from django.contrib import admin
from app.models import User, File, Purchase, Ban

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_active', 'is_staff')
    search_fields = ('username', 'email')
    list_filter = ('is_active', 'is_staff')

class FileAdmin(admin.ModelAdmin):
    list_display = ('title', 'uploader', 'is_approved', 'upload_date')  # corrected here
    search_fields = ('title', 'uploader__username')
    list_filter = ('is_approved', 'upload_date')  # corrected here

class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('user', 'file', 'purchase_date')
    search_fields = ('user__username', 'file__title')
    list_filter = ('purchase_date',)

class BanAdmin(admin.ModelAdmin):
    list_display = ('banned_user', 'banned_by', 'ban_date')
    search_fields = ('banned_user__username', 'banned_by__username')
    list_filter = ('ban_date',)

admin.site.register(User, UserAdmin)
admin.site.register(File, FileAdmin)
admin.site.register(Purchase, PurchaseAdmin)
admin.site.register(Ban, BanAdmin)
