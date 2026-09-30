from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .models import UserProfile


User = get_user_model()


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    extra = 0
    fields = ('real_name', 'student_id')
    readonly_fields = ('real_name', 'student_id')


admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = (
        'username',
        'real_name',
        'student_id',
        'is_active',
        'is_staff',
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('profile')

    def get_fieldsets(self, request, obj=None):
        if request.user.is_superuser:
            return super().get_fieldsets(request, obj)
        return (
            ('账户审核', {'fields': ('username', 'email', 'is_active')}),
        )

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return super().get_readonly_fields(request, obj)
        readonly_fields = ['username', 'email']
        if obj is not None and obj.pk == request.user.pk:
            readonly_fields.append('is_active')
        return tuple(readonly_fields)

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return super().has_view_permission(request, obj)
        return request.user.is_staff

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return super().has_module_permission(request)
        return request.user.is_staff

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return super().has_change_permission(request, obj)
        return bool(
            request.user.is_staff
            and obj is not None
            and not obj.is_superuser
        )

    def has_add_permission(self, request):
        return request.user.is_superuser and super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return super().has_delete_permission(request, obj)
        return bool(
            request.user.is_staff
            and obj is not None
            and not obj.is_superuser
            and not obj.is_staff
        )

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not request.user.is_superuser:
            actions.pop('delete_selected', None)
        return actions

    @admin.display(description='真实姓名')
    def real_name(self, user):
        profile = getattr(user, 'profile', None)
        return profile.real_name if profile else '-'

    @admin.display(description='学籍号')
    def student_id(self, user):
        profile = getattr(user, 'profile', None)
        return profile.student_id if profile else '-'
