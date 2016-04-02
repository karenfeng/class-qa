from django import forms

class QuestionForm(forms.Form):
    your_question = forms.CharField(label='Your question', max_length=100)

class AnswerForm(forms.Form):
    your_answer = forms.CharField(label='Your answer', max_length=200)

class RegisterForm(forms.Form):
	first_name = forms.CharField(label='First Name:', max_length=100,
		widget=forms.TextInput(attrs={'placeholder': ''}))
	last_name = forms.CharField(label='Last Name:', max_length=100,
		widget=forms.TextInput(attrs={'placeholder': ''}))
	is_student = forms.ChoiceField(label='Are you a student?', \
			choices=[('s','Student'), ('l', 'Lecturer')], widget=forms.RadioSelect())

class ClassForm(forms.Form):
	your_class = forms.CharField(label='Register class', max_length=50)
	your_professor = forms.CharField(label='Professor', max_length=50)
	start_time = forms.TimeField(label='Start time')
	end_time = forms.TimeField(label='Start time')