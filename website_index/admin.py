from django.contrib import admin

from .models import Intro, Development, Moment, Activity, Info

admin.site.register(Intro)
admin.site.register(Development)
admin.site.register(Moment)
admin.site.register(Activity)
admin.site.register(Info)