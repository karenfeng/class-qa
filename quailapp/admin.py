from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
# Register your models here
from .models import Question, Answer, QuailUser, Course, Tag, Feedback, AllNetids, ProvidedFeedback, Category


class UserCreationForm(forms.ModelForm):
	password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
	password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

	class Meta:
		model = QuailUser
		fields = ('netid', 'first_name', 'last_name', 'is_student', 'courses_by_id')

	def clean_password2(self):
        # Check that the two password entries match
		password1 = self.cleaned_data.get("password1")
		password2 = self.cleaned_data.get("password2")
		if password1 and password2 and password1 != password2:
			raiseforms.ValidationError("Passwords don't match")
			return password2

	def save(self, commit=True):
		# Save the provided password in hashed format
		user = super(UserCreationForm, self).save(commit=False)
		user.set_password(self.cleaned_data["password1"])
		if commit:
			user.save()
		return user    

class UserChangeForm(forms.ModelForm):
	"""A form for updating users. Includes all the fields on
	the user, but replaces the password field with admin's
	password hash display field.
	"""
	password = ReadOnlyPasswordHashField()

	class Meta:
		model = QuailUser
		fields = ('netid', 'first_name', 'last_name', 'is_student', 'courses_by_id', 'is_active', 'is_admin')

	def clean_password(self):
		# Regardless of what the user provides, return the initial value.
		# This is done here, rather than on the field, because the
		# field does not have access to the initial value
		return self.initial["password"]

class UserAdmin(BaseUserAdmin):
	# The forms to add and change user instances
	form = UserChangeForm
	add_form = UserCreationForm

	# The fields to be used in displaying the User model.
	# These override the definitions on the base UserAdmin
	# that reference specific fields on auth.User.
	list_display = ('netid', 'first_name', 'last_name', 'is_student', 'courses_by_id', 'is_admin')
	list_filter = ('is_admin',)
	fieldsets = (
		(None, {'fields': ('netid', 'password')}),
		('Personal info', {'fields': ('first_name', 'last_name', 'is_student','courses_by_id')}),
		('Permissions', {'fields': ('is_admin',)}),
	)
	# add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
	# overrides get_fieldsets to use this attribute when creating a user.
	add_fieldsets = (
		(None, {
			'classes': ('wide',),
			'fields': ('netid', 'first_name', 'last_name', 'is_student', 'password1', 'password2')}
		),
	)
	search_fields = ('netid',)
	ordering = ('netid',)
	filter_horizontal = ()

# Now register the new UserAdmin...
admin.site.register(QuailUser, UserAdmin)
# ... and, since we're not using Django's built-in permissions,
# unregister the Group model from admin.
admin.site.unregister(Group)

class AllNetidsAdmin(admin.ModelAdmin): pass
admin.site.register(AllNetids, AllNetidsAdmin)

class QuestionAdmin(admin.ModelAdmin): pass
admin.site.register(Question, QuestionAdmin)

class AnswerAdmin(admin.ModelAdmin): pass
admin.site.register(Answer, AnswerAdmin)

#class QuailUserAdmin(admin.ModelAdmin): pass
#admin.site.register(QuailUser, QuailUserAdmin)

class CourseAdmin(admin.ModelAdmin): pass
admin.site.register(Course, CourseAdmin)

class TagAdmin(admin.ModelAdmin): pass
admin.site.register(Tag, TagAdmin)

class FeedbackAdmin(admin.ModelAdmin): pass
admin.site.register(Feedback, FeedbackAdmin)

class ProvidedFeedbackAdmin(admin.ModelAdmin): pass
admin.site.register(ProvidedFeedback, ProvidedFeedbackAdmin)

class CategoryAdmin(admin.ModelAdmin): pass
admin.site.register(Category, CategoryAdmin)