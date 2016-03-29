from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.core.urlresolvers import reverse
from django.template import loader
from django.views import generic

import datetime

from .forms import QuestionForm, AnswerForm
from .models import Question, CASClient, Answer

class IndexView(generic.ListView):
    template_name = 'quailapp/index.html'
    context_object_name = 'questions'
    def get_queryset(self):
        return Question.objects.all()

# handles what handles when a user uses the vote form on a question
def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        vote = request.POST['vote']
    except (KeyError, Question.DoesNotExist):
        # Redisplay the question voting form.
        return render(request, 'quailapp/index.html', {
            'error_message': "You didn't select a vote.",
            })
    else:
        question.votes += int(vote)
        question.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
    return HttpResponseRedirect(reverse('quailapp:index'))

# handles when user inputs answer for a question through answer form
def get_answer(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    if request.method == 'POST':
        form = AnswerForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            new_answer = Answer(created_on=datetime.datetime.now(), text=data['your_answer'], question=question)
            new_answer.save()
            return HttpResponseRedirect(reverse('quailapp:detail', args=(question.id,)))
    else:
        form = AnswerForm()
    return render(request, 'quailapp/answer.html', {'question': question, 'form': form})

# detail view = what you see when you click on a question (its answers, votes, etc)
class DetailView(generic.DetailView):
    model = Question
    template_name = 'quailapp/detail.html'
    form = AnswerForm()
    def get_queryset(self):
        return Question.objects.all()

def get_question(request):
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            new_question = Question(created_on=datetime.datetime.now(), text=data['your_question'], votes=0)
            new_question.save()
            return redirect('/')
    else:
        form = QuestionForm()
    return render(request, 'quailapp/question.html', {'form': form})

def delete_questions(request):
    Question.objects.all().delete()
    return HttpResponse('All questions have been deleted!')

# delete all the answers associated with a specific question
def delete_answers(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    question.answer_set.all().delete()
    return HttpResponse('All answers have been deleted!')

def hello_world(request):
    return HttpResponse('Hello world!')

def login(request):

    C = CASClient(request)
    # if you already logged in
    if 'ticket' in request.GET:
        netid = C.Authenticate()
        if not netid:
            return redirect(C.redirect_url())
        return HttpResponse(netid + ' logged in')

    # otherwise redirect to CAS login page appropriately
    else:
        return redirect(C.redirect_url())
