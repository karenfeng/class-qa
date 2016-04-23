from django import forms
from .models import Course

FEEDBACK_CHOICES = (
    ('1', '1'),
    ('2', '2'),
    ('3', '3'),
    ('4', '4'),
    ('5', '5'),
)

class QuestionForm(forms.Form):
    def __init__(self, *args, **kwargs):
		self.tags = kwargs.pop('tags')
		super(QuestionForm,self).__init__(*args,**kwargs)
		self.fields['tags'] = forms.ModelMultipleChoiceField(widget=forms.CheckboxSelectMultiple(), label='', queryset=self.tags, required=False)
		self.fields['your_question'] = forms.CharField(label='Your question', max_length=100)

class FeedbackForm(forms.Form):
	feedback_choice = forms.ChoiceField(widget=forms.RadioSelect(), label='', choices=FEEDBACK_CHOICES, required=False)
	your_feedback = forms.CharField(label='Your feedback', max_length=200, required=False)

class AnswerForm(forms.Form):
    your_answer = forms.CharField(label='Your answer', max_length=200)

class CommentForm(forms.Form):
    your_comment = forms.CharField(label='Your answer', max_length=300)

class TagForm(forms.Form):
    your_tag = forms.CharField(label='Your tag', max_length=50)

class RegisterForm(forms.Form):
	first_name = forms.CharField(label='First Name:', max_length=100,
		widget=forms.TextInput(attrs={'placeholder': ''}))
	last_name = forms.CharField(label='Last Name:', max_length=100,
		widget=forms.TextInput(attrs={'placeholder': ''}))
	is_student = forms.TypedChoiceField(label='Are you a student?',
		coerce=lambda x: bool(int(x)), choices=[(0,'Lecturer'), (1,'Student')],
		widget=forms.RadioSelect())

class ClassForm(forms.Form):
	your_class = forms.CharField(label='Register class', max_length=50)
	your_professor = forms.CharField(label='Professor', max_length=50)
	start_time = forms.TimeField(label='Start time')
	end_time = forms.TimeField(label='Start time')

class EnrollForm(forms.Form):

	def __init__(self, *args, **kwargs):
		self.courses_available = kwargs.pop('courses_available')
		super(EnrollForm,self).__init__(*args,**kwargs)
		self.fields['courses'] = forms.ModelMultipleChoiceField(widget=forms.CheckboxSelectMultiple(), label='', queryset=self.courses_available)


