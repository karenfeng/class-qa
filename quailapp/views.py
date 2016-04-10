from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.template import loader
from django.views import generic
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
#import numpy as np
#from sklearn.feature_extraction.text import TfidfVectorizer

from django.contrib.auth import login, logout, authenticate
#from .custom_auth_backend import QuailCustomBackend

import datetime, re

import json

from .forms import QuestionForm, AnswerForm, RegisterForm, EnrollForm, CommentForm
from .models import Question, CASClient, Answer, QuailUser, Course, Comment

def index(request):
    try:
        user = QuailUser.objects.get(netid=request.user.netid)
    except ObjectDoesNotExist:
        return redirect('/login')
    # course list as query set
    courses = Course.objects.filter(courseid__in=request.user.course_id_list)
    return render(request, 'quailapp/index.html', {'user':user, 'courses':courses})

# handles what happens when a user uses the vote form on a question
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
        # if user is upvoting
        if (int(vote) == 1) and ((not question.users_upvoted) or (request.user.netid not in question.users_upvoted)): 
            if question.users_downvoted and request.user.netid in question.users_downvoted:
                users_downvoted = question.users_downvoted.replace("|"+request.user.netid, "")
                question.users_downvoted = users_downvoted
            else:
                users_upvoted = question.users_upvoted + '|' + request.user.netid
                question.users_upvoted = users_upvoted
            question.votes += int(vote)
        
        # if user is downvoting
        elif (int(vote) == -1) and ((not question.users_downvoted) or (request.user.netid not in question.users_downvoted)):
            # if user already upvoted and wants to downvote
            if question.users_upvoted and request.user.netid in question.users_upvoted:
                users_upvoted = question.users_upvoted.replace("|"+request.user.netid, "")
                question.users_upvoted = users_upvoted
            else:
                users_downvoted = question.users_downvoted + '|' + request.user.netid
                question.users_downvoted = users_downvoted
            question.votes += int(vote)
        

        # if not question.users_voted:
        #     question.users_voted = request.user.netid
        #     question.votes += int(vote)
        # elif not request.user.netid in question.users_voted:
        #     question.votes += int(vote)
        #     users_voted = question.users_voted + '|' + request.user.netid
        #     question.users_voted = users_voted

        if (question.votes < -10):  # deletes question if it's downvoted to oblivion
            question.delete()
        else:
            question.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
    
    return HttpResponse(question.votes)
    #return HttpResponseRedirect(reverse('quailapp:coursepage', args=(question.course.id,)))

# handles what happens when someone pins a question to the coursepage
def pin(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    is_pinned = int(request.POST['pin'])
    if (is_pinned == 1):
        question.is_pinned = True
    else:
        question.is_pinned = False
    question.save()
    return HttpResponseRedirect(reverse('quailapp:coursepage', args=(question.course.id,)))

# course detail view - shows all questions associated with the course
def coursepage(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    questions_pinned = course.question_set.all().filter(is_pinned=True)
    questions_unpinned = course.question_set.all().exclude(is_pinned=True)
    
    # view (unpinned) questions 5 at a time
    paginator = Paginator(questions_unpinned, 5) # Show 5 questions per page
    page = request.GET.get('page')
    try:
        questions = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        questions = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        questions = paginator.page(paginator.num_pages)
    
    # if a question is posted
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            new_question = Question(text=data['your_question'], course=course, submitter=request.user, votes=0)
            new_question.save()
            return HttpResponseRedirect(reverse('quailapp:coursepage', args=(course.id,)))
    else:
        form = QuestionForm()
        #sortby_form = SortByForm()
    return render(request, 'quailapp/coursepage.html', {'form': form, 'course': course, 
        'questions_pinned': questions_pinned, 'questions': questions, 'user': request.user})
    #def get_queryset(self):
    #    return Question.objects.all()

def delete_from_coursepage(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    course = question.course
    question.delete()
    return HttpResponseRedirect(reverse('quailapp:coursepage', args=(course.id,)))

def delete_from_userinfo(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    question.delete()
    return HttpResponseRedirect(reverse('quailapp:userinfo'))

# detail view = what you see when you click on a question (its answers, votes, etc)
def question_detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    user = request.user
    if request.method == 'POST':
        form = AnswerForm(request.POST)
        comment_form = CommentForm(request.POST)
        # if an answer is posted
        if form.is_valid():
            data = form.cleaned_data
            new_answer = Answer(text=data['your_answer'], question=question, submitter=request.user)
            new_answer.save()
            return HttpResponseRedirect(reverse('quailapp:detail', args=(question.id,)))
        # if a comment is posted
        if comment_form.is_valid():
            data = comment_form.cleaned_data
            new_comment = Comment(text=data['your_comment'], question=question, submitter=request.user)
            new_comment.save()
            return HttpResponseRedirect(reverse('quailapp:detail', args=(question.id,)))
    else:
        form = AnswerForm()
        comment_form = CommentForm()
    return render(request, 'quailapp/detail.html', {'question': question, 'form': form, 'comment_form': comment_form, 'user': user})

def get_question(request):
    # otherwise can post a question
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            new_question = Question(text=data['your_question'], submitter=request.user, votes=0)
            new_question.save()
            return redirect('/index')
    else:
        form = QuestionForm()
    return render(request, 'quailapp/question.html', {'form': form})

# delete all the answers associated with a specific question
def delete_answer(request, answer_id):
    answer = get_object_or_404(Answer, pk=answer_id)
    question = answer.question
    answer.delete()
    return HttpResponseRedirect(reverse('quailapp:detail',args=(question.id,)))

def login_CAS(request):

    C = CASClient(request)
    # if you already logged in
    if 'ticket' in request.GET:
        netid = C.Authenticate()
        if not netid:
            return redirect(C.redirect_url())

        # log user in, if account already created
        user = authenticate(username=netid, request=request)
        if user is not None:
            login(request, user)
            return redirect('/index')
        else:
            return redirect(netid+'/create')

    # otherwise redirect to CAS login page appropriately
    else:
        return redirect(C.redirect_url())

def logout_CAS(request):
    # log out of django
    logout(request)

    # log out of CAS
    C = CASClient(request)
    return redirect(C.redirect_url_logout())


# create a new account for a user 
def create_account(request, netid):
    # save new user in the database 
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            new_user = QuailUser(netid=netid, first_name=data['first_name'], last_name=data['last_name'],
                is_student=data['is_student'])
            new_user.save()

            # automatically log the user in 
            user = authenticate(username=netid, request=request)
            login(request, user)
            return HttpResponseRedirect(reverse('quailapp:userinfo'))
        else:
            return render(request, 'quailapp/create.html', {'form':form, 'netid':netid})

    # query for user with netid 
    else: 
        try:
            user = QuailUser.objects.get(netid=netid)
        except ObjectDoesNotExist:
            form = RegisterForm()
            return render(request, 'quailapp/create.html', {'form':form, 'netid':netid})
        return redirect('/index')

def user_info(request):
    try:
        user = QuailUser.objects.get(netid=request.user.netid)
    except ObjectDoesNotExist:
        return redirect('/login')
    
    # course list as query set
    courses = Course.objects.filter(courseid__in=request.user.course_id_list)

    # handle unenroll requests
    if request.method == 'POST':
        new_course_ids = ''
        course_list = user.courses_by_id.split('|')
        course_to_unenroll = Course.objects.get(pk=request.POST['courseid'])
        for course in course_list:
            if (course != course_to_unenroll.courseid):
                new_course_ids += course + '|'
        new_course_ids = new_course_ids[:len(new_course_ids)-1]
        user.courses_by_id = new_course_ids
        user.save()
        return HttpResponseRedirect(reverse('quailapp:userinfo'))
    return render(request, 'quailapp/userinfo.html', {'user':user, 'courses':courses})

# this is a bit messy.. combining raw html with django forms, should stick with one or the other? 
def enroll(request):
    # searching classes
    #if request.is_ajax():
        #return HttpResponse(request.GET)
        #return HttpResponse(request.GET['q'])
    if request.is_ajax():
        query_string = request.GET['q']
        terms = query_string.split()
        courses_found = Course.objects.exclude(courseid__in=request.user.course_id_list)
        for term in terms:
            course_ids_found = []
            for course in courses_found:
                if (re.search(term, course.dept, re.I)):
                    course_ids_found.append(course.courseid)
                    continue
                if (re.search(term, course.num, re.I)):
                    course_ids_found.append(course.courseid)
                    continue
                if (re.search(term, course.title, re.I)):
                    course_ids_found.append(course.courseid)
                    continue
            courses_found = courses_found.filter(courseid__in=course_ids_found)

        found_entries = Course.objects.filter(courseid__in=course_ids_found).order_by('dept')
        form = EnrollForm(courses_available=found_entries)
        courses_enrolled = Course.objects.filter(courseid__in=request.user.course_id_list)
        return render(request, 'quailapp/enrollform.html', {'form': form})
        #return render(request, 'quailapp/enroll.html', {'form':form, 'courses_enrolled':courses_enrolled, 'query_string':query_string})

    if request.method == 'POST':
        courses_available = Course.objects.exclude(courseid__in=request.user.course_id_list)
        form = EnrollForm(request.POST, courses_available=courses_available)
        if form.is_valid():
            data = form.cleaned_data
            # add new courses to existing ones
            user = QuailUser.objects.get(netid=request.user.netid)
            courses = user.courses_by_id + '|'
            for course in data['courses']:
                courses = courses + course.courseid + '|'
            user.courses_by_id = courses[:len(courses)-1]
            user.save()
            return HttpResponseRedirect(reverse('quailapp:userinfo'))
    else:
        courses_enrolled = Course.objects.filter(courseid__in=request.user.course_id_list)
        courses_available = Course.objects.exclude(courseid__in=request.user.course_id_list)
        form = EnrollForm(courses_available=courses_available)
        return render(request, 'quailapp/enroll.html', {'form':form, 'courses_enrolled':courses_enrolled})

def similar_question(request):
    if request.is_ajax():
        target_question = request.GET['simQ']
        course_id = request.GET['course']

        course = get_object_or_404(Course, pk=course_id)
        questions = Question.objects.filter(course=course)
        questions_text_lower = [] # questions with all lower case text
        questions_text_upper = [] # questions as they were submitted with upper case text with their id

        for q in questions:
            questions_text_lower.append(q.text.lower())
            questions_text_upper.append((q.text + "\n", q.id))
            #return HttpResponse((q.id, q.text))
        questions_text_lower.append(target_question)
        questions_text_upper.append(target_question)

        # run Tfidf algorithm
        tfidf = TfidfVectorizer(stop_words='english').fit_transform(questions_text_lower)

        # take cosine similarity by taking dot product
        pairwise_similarity = (tfidf * tfidf.T).A[len(questions_text_lower)-1] 
        max_similarity = max(np.delete(pairwise_similarity, len(questions_text_lower)-1))
        max_index = np.where(pairwise_similarity == max_similarity)[0]

        #corner case for if there are no similar questions
        if(max_similarity == 0.0): return HttpResponse("")

        best_match = questions_text_upper[max_index]
        return HttpResponse(best_match)

def home(request):
    return render(request, 'quailapp/home.html')
