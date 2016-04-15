from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.template import loader
from django.views import generic
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
#import sys
#sys.path.append("numpy_path")
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

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

    starredQuestions = Question.objects.filter(users_starred__contains=user.netid)
    return render(request, 'quailapp/index.html', {'user':user, 'courses':courses, 'starred_questions':starredQuestions})

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

# handles what happens when a user stars a question
def star(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    star = request.POST['star']
    
    if question.users_starred and request.user.netid in question.users_starred:
        users_starred = question.users_starred.replace("|"+request.user.netid, "")
    else:
        users_starred = question.users_starred + '|' + request.user.netid
    
    question.stars += int(star)
    question.users_starred = users_starred    
    question.save()
    
    return HttpResponse(question.stars)

# handles what happens when someone pins a question to the coursepage
def pin(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    is_pinned = int(request.POST['pin'])
    if (is_pinned == 1):
        question.is_pinned = True
    else:
        question.is_pinned = False
    question.save()
    if (question.is_live == True):
        return HttpResponseRedirect(reverse('quailapp:coursepage_live', args=(question.course.id,)))
    else:
        return HttpResponseRedirect(reverse('quailapp:coursepage_archive', args=(question.course.id,)))

def coursepage_live(request, course_id):

    course = get_object_or_404(Course, pk=course_id)    
    # check if course is live
    user = request.user
    now = datetime.datetime.now()

    to_archive = False
    live_month = False
    live_day = False
    live_time = False
    days = course.days
    diff_days = 0
    diff_weeks = 0
    if (now.month >= 1 and now.month < 6):
        live_month = True
    if (re.search(str(now.weekday()), course.days)):
        live_day = True
    if (now.time() < course.endtime and now.time() > course.starttime):
        live_time = True
    if (live_month and live_day and live_time):
        if (course.archive_type == 'every_other_lecture'):
            weekday = now.weekday()
            if (len(days) < 2):
                diff_days = 0
                diff_weeks = 1   # default to archiving every other week
            else:
                for i in range(len(days)):
                    if (weekday == int(days[i])):
                        index = i
                diff_days = (weekday - int(days[index-1])) % 7
                diff_weeks = 0
            time_buffer = now - datetime.timedelta(hours=3,days=diff_days, weeks=diff_weeks)
            to_archive = True
        elif (course.archive_type == 'every_lecture'):
            time_buffer = now - datetime.timedelta(hours=3)
            to_archive = True
            
    if (course.archive_type == 'every_week'):
        time_buffer = now - datetime.timedelta(days=7)
        to_archive = True
    elif (course.archive_type == 'every_two_weeks'):
        time_buffer = now - datetime.timedelta(days=14)
        to_archive = True
    elif (course.archive_type == 'every_month'):
        time_buffer = now - datetime.timedelta(days=30)
        to_archive = True

    if (to_archive == True):
        updated_questions = course.question_set.all().filter(is_live=True, created_on__lte=time_buffer)
        updated_questions.update(is_live=False)
    live_questions = course.question_set.all().filter(is_live=True)
    questions_pinned = live_questions.filter(is_pinned=True).order_by(user.chosen_filter)
    questions_unpinned = live_questions.exclude(is_pinned=True).order_by(user.chosen_filter)
        
    # if a question is posted
    if request.method == 'POST':
        form = QuestionForm(request.POST)

        # if the user chooses a filter
        if ('filter' in request.POST):
            chosen_filter = request.POST['filter']
            if (chosen_filter == 'newest'):
                user.chosen_filter = '-created_on'
                user.save()
                questions_pinned = questions_pinned.order_by('-created_on')
                questions_unpinned = questions_unpinned.order_by('-created_on')
            elif (chosen_filter == 'oldest'):
                user.chosen_filter = 'created_on'
                user.save()
                questions_pinned = questions_pinned.order_by('created_on')
                questions_unpinned = questions_unpinned.order_by('created_on')
            else:
                user.chosen_filter = '-votes'
                user.save()
                questions_pinned = questions_pinned.order_by('-votes')
                questions_unpinned = questions_unpinned.order_by('-votes')

        # if the user submits a question
        if form.is_valid():
            data = form.cleaned_data
            new_question = Question(text=data['your_question'], course=course, submitter=request.user, votes=0, is_live=True)
            new_question.save()
            return HttpResponseRedirect(reverse('quailapp:coursepage_live', args=(course.id,)))   
    else:
        form = QuestionForm()

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

    if request.is_ajax() and request.method == 'GET':
        return render(request, 'quailapp/questionreload.html', {'form': form, 'course': course, 
        'questions_pinned': questions_pinned, 'questions': questions, 'user': request.user,
        'courses': Course.objects.filter(courseid__in=user.course_id_list)})
    return render(request, 'quailapp/coursepage_live.html', {'form': form, 'course': course, 
        'questions_pinned': questions_pinned, 'questions': questions, 'user': request.user,
        'courses': Course.objects.filter(courseid__in=user.course_id_list)})


def coursepage_archive(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user
    archived_questions = course.question_set.all().exclude(is_live=True)
    questions_pinned = archived_questions.filter(is_pinned=True).order_by(user.chosen_filter)
    questions_unpinned = archived_questions.exclude(is_pinned=True).order_by(user.chosen_filter)
        
    # if a question is posted
    if request.method == 'POST':
        # if the user chooses a filter
        if ('filter' in request.POST):
            chosen_filter = request.POST['filter']
            if (chosen_filter == 'newest'):
                user.chosen_filter = '-created_on'
                user.save()
                questions_pinned = questions_pinned.order_by('-created_on')
                questions_unpinned = questions_unpinned.order_by('-created_on')
            elif (chosen_filter == 'oldest'):
                user.chosen_filter = 'created_on'
                user.save()
                questions_pinned = questions_pinned.order_by('created_on')
                questions_unpinned = questions_unpinned.order_by('created_on')
            else:
                user.chosen_filter = '-votes'
                user.save()
                questions_pinned = questions_pinned.order_by('-votes')
                questions_unpinned = questions_unpinned.order_by('-votes')

        if ('archive_type' in request.POST):
            chosen_type = request.POST['archive_type']
            course.archive_type = chosen_type
            course.save()

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
    return render(request, 'quailapp/coursepage_archive.html', {'course': course, 
        'questions_pinned': questions_pinned, 'questions': questions, 'user': request.user,
        'courses': Course.objects.filter(courseid__in=user.course_id_list)})

'''
# course detail view - shows all questions associated with the course
def coursepage(request, course_id):
    course = get_object_or_404(Course, pk=course_id)    
    # check if course is live
    now = datetime.datetime.now()
    time_buffer = now - datetime.timedelta(hours=6)
    live_questions = course.question_set.all().filter(is_live=True)
    live_month = False
    live_day = False
    live_time = False
    if (now.month >= 1 and now.month < 6):
        live_month = True
    if (re.search(str(now.weekday()), course.days)):
        live_day = True
    if (now.time() < course.endtime and now.time() > course.starttime):
        live_time = True
    if (live_month and live_day and live_time):
        updated_questions = live_questions.filter(created_on__lte=time_buffer)
        updated_questions.update(is_live=False)
        #course.is_live = True
        #course.save()
    return redirect('/'+course.id+'/coursepage_live')
'''

def delete_from_coursepage(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    course = question.course
    question.delete()
    if (question.is_live == True):
        return HttpResponseRedirect(reverse('quailapp:coursepage_live', args=(course.id,)))
    else:
        return HttpResponseRedirect(reverse('quailapp:coursepage_archive', args=(course.id,)))

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
    return render(request, 'quailapp/detail.html', {'question': question, 'form': form, 'comment_form': comment_form, 'user': user,
        'courses': Course.objects.filter(courseid__in=request.user.course_id_list)})

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
    if request.method == 'POST' and request.is_ajax():
        new_course_ids = ''
        course_list = user.courses_by_id.split('|')
        course_to_unenroll = Course.objects.get(pk=request.POST['courseid'])
        for course in course_list:
            if (course != course_to_unenroll.courseid):
                new_course_ids += course + '|'
        new_course_ids = new_course_ids[:len(new_course_ids)-1]
        user.courses_by_id = new_course_ids
        user.save()
        return HttpResponse("success")
        return HttpResponseRedirect(reverse('quailapp:userinfo'))
    return render(request, 'quailapp/userinfo.html', {'user':user, 'courses':courses,
        'courses': Course.objects.filter(courseid__in=user.course_id_list)})

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

def change_name(request):
    if request.is_ajax():
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        user = request.user
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        return HttpResponse(user.first_name + " " + user.last_name)

def edit_question(request, question_id):
    if request.is_ajax():
        question = get_object_or_404(Question, pk=question_id)
        question.text = request.POST['text']
        question.save()
        return HttpResponse(question.text)

def edit_answer(request, question_id):
    if request.is_ajax():
        question = get_object_or_404(Question, pk=question_id)
        
        question.answer.text = request.POST['text']
        question.answer.save()

        return HttpResponse(question.answer.text)

def home(request):
    return render(request, 'quailapp/home.html')
