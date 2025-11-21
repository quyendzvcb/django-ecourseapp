from django.contrib import admin
from django import forms
from django.db.models import Count
from django.http import request
from django.template.response import TemplateResponse
from django.utils.safestring import mark_safe
from courses.models import Category, Course, Lesson, Tag, Comment, Like
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django.urls import path

class CategoryAdmin(admin.ModelAdmin):
    # list_display = ['id', 'subject', 'created_date', 'active']
    # search_fields = ['subject']
    # list_filter = ['id', 'subject', 'created_date']
    list_display = ['pk', 'name']
    list_filter = ['id', 'name']
    search_fields = ['name']

class CourseForm(forms.ModelForm):
    description = forms.CharField(widget=CKEditorUploadingWidget)

    class Meta:
        model = Course
        fields = '__all__'


# class TagInlineAdmin(admin.StackedInline):
#     model = Course.tags.through


class CourseAdmin(admin.ModelAdmin):
    list_display = ['pk', 'subject', 'created_date', 'updated_date', 'category', 'active']
    readonly_fields = ['img']
    # inlines = [TagInlineAdmin]
    form = CourseForm

    def img(self, course):
        if course:
            return mark_safe(
                '<img src="/static/{url}" width="120" />' \
                    .format(url=course.image.name)
            )

    class Media:
        css = {
            'all': ('/static/css/style.css',)
        }


class MyAdminSite(admin.AdminSite):
    site_header = 'eCourses App'

    def get_urls(self):
        return [path('stats-view/', self.stats_view)] + super().get_urls()

    def stats_view(self, request):
        stats = Category.objects.annotate(count=Count('course')).values('id','name', 'count')

        return TemplateResponse(request, 'admin/stats.html', {'stats': stats})

admin_site = MyAdminSite()

# Register your models here.
admin_site.register(Category, CategoryAdmin)
admin_site.register(Course, CourseAdmin)
admin_site.register(Lesson)
admin_site.register(Tag)
admin_site.register(Comment)

