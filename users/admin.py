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

    @admin.display(description='真实姓名')
    def real_name(self, user):
        profile = getattr(user, 'profile', None)
        return profile.real_name if profile else '-'

    @admin.display(description='学籍号')
    def student_id(self, user):
        profile = getattr(user, 'profile', None)
        return profile.student_id if profile else '-'
