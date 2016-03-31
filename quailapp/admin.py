from django.contrib import admin

# Register your models here
from .models import Question, Answer, QuailUser, Course

class QuestionAdmin(admin.ModelAdmin): pass
admin.site.register(Question, QuestionAdmin)

class AnswerAdmin(admin.ModelAdmin): pass
admin.site.register(Answer, AnswerAdmin)

class QuailUserAdmin(admin.ModelAdmin): pass
admin.site.register(QuailUser, QuailUserAdmin)

class CourseAdmin(admin.ModelAdmin): pass
admin.site.register(Course, CourseAdmin)