from django import forms

class QuestionForm(forms.Form):
    your_question = forms.CharField(label='Your question', max_length=100)

class AnswerForm(forms.Form):
    your_answer = forms.CharField(label='Your answer', max_length=200)
