from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.template import loader
from django.views import generic
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.contrib import messages
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from django.contrib.auth import login, logout, authenticate
#from .custom_auth_backend import QuailCustomBackend

import datetime, re
from datetime import timedelta

import json
from django.core import serializers

from .forms import QuestionForm, AnswerForm, RegisterForm, EnrollForm, CommentForm, TagForm, FeedbackForm
from .models import Question, CASClient, Answer, QuailUser, Course, Comment, Tag, Feedback, AllNetids, ProvidedFeedback

def index(request):
    try:
        user = QuailUser.objects.get(netid=request.user.netid)
    except ObjectDoesNotExist:
        return redirect('/login')
    # course list as query set
    courses = Course.objects.filter(courseid__in=request.user.course_id_list)
    starredQuestions = Question.objects.filter(users_starred__contains=user.netid)

    if request.method == 'POST':
        feedback_id = request.POST['feedback']
        feedback = Feedback.objects.get(pk=feedback_id)
        feedback.is_live = False
        feedback.save()
        return HttpResponseRedirect(reverse('quailapp:index'))

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
    if request.is_ajax():
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
    return HttpResponse("success")
    
    # if (question.is_live == True):
    #     return HttpResponseRedirect(reverse('quailapp:coursepage_live', args=(question.course.id,)))
    # else:
    #     return HttpResponseRedirect(reverse('quailapp:coursepage_archive', args=(question.course.id,)))

def coursepage_live(request, course_id):

    course = get_object_or_404(Course, pk=course_id)    
    # check if course is live
    user = request.user
    now = datetime.datetime.now()
    course_id_list = user.courses_by_id.split('|')
    feedback_for_course = user.providedfeedback_set.all().get(course=course)
    display_feedback = True

    to_archive = False
    live_month = False
    live_day = False
    live_time = False
    days = course.days

    diff_days = 0
    diff_weeks = 0
    if (now.month >= 1 and now.month < 6):
        live_month = True
    if (re.search(str(now.weekday()), days)):
        live_day = True
    if (now.time() < course.endtime and now.time() > course.starttime):
        live_time = True
    if (live_month and live_day and live_time):
        lecture_date = now.date()
        # update the provided feedback to False with new lecture
        feedback_for_course.provided_feedback = False
        feedback_for_course.save()
        display_feedback = False
        if (course.archive_type == 'every_other_lecture'):
            weekday = now.weekday()
            if (len(days) < 2):
                diff_days = 0
                diff_weeks = 1   # default to archiving every other week if lecture is once a week
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
    else:
        # find out when the last lecture was
        last_lecture = -1
        int_days = [-1] # buffer for the first day
        for day in days:
            int_days.append(int(day))
        int_days.append(10) # a buffer for the last day
        for i in range(len(int_days)-1):
            if now.weekday() == int_days[i]:
                if now.time() < course.starttime:
                    if len(days) == 1:
                        last_lecture = -1
                    else:
                        if i == 1:
                            last_lecture = int_days[i-3]
                        else:
                            last_lecture = int_days[i-1]
                else:
                    last_lecture = int_days[i]
                break
            elif now.weekday() > int_days[i] and now.weekday() < int_days[i+1]:
                if i == 0:
                    last_lecture = int_days[i-2]
                    break
                else:
                    last_lecture = int_days[i]
                    break
        diff = (now.weekday() - last_lecture) % 7
        # if the class only meets once a week, default to the last week's lecture
        if last_lecture == -1:
            diff = 7
        lecture_date = (now - datetime.timedelta(days=diff)).date()
    
    # save the last lecture date to the course
    course.last_lecture = lecture_date
    course.save()

    # check if the user has any feedback before the last lecture
    if (len(user.feedback_set.filter(course=course, lecture_date__gte=lecture_date)) > 0):
        feedback_for_course.provided_feedback = True
        feedback_for_course.save()
    else:
        feedback_for_course.provided_feedback = False
        feedback_for_course.save()

    # if course isn't currently live, check for other archive types   
    if (course.archive_type == 'every_week'):
        time_buffer = now - datetime.timedelta(days=7)
        to_archive = True
    elif (course.archive_type == 'every_two_weeks'):
        time_buffer = now - datetime.timedelta(days=14)
        to_archive = True
    elif (course.archive_type == 'every_month'):
        time_buffer = now - datetime.timedelta(days=30)
        to_archive = True

    # if there are questions to archive, archive them; otherwise display the normal live questions
    if (to_archive == True):
        updated_questions = course.question_set.all().filter(is_live=True, created_on__lte=time_buffer)
        updated_questions.update(is_live=False)
        # updated_feedback = course.feedback_set.all().filter(is_live=True, created_on__lte=time_buffer)
        # updated_feedback.update(is_live=False, archived_on=now.date())
    
    # feedback and questions to display on live page
    live_questions = course.question_set.all().filter(is_live=True)
    live_feedback = course.feedback_set.all().filter(is_live=True)
    questions_pinned = live_questions.filter(is_pinned=True).order_by(user.chosen_filter)
    questions_unpinned = live_questions.exclude(is_pinned=True).order_by(user.chosen_filter)

    # checking if user has already submitted feedback for this course
    provided_feedback = False
    if feedback_for_course.provided_feedback == True:
        provided_feedback = True
    else:
        provided_feedback = False
    # for i in range(len(course_id_list)):
    #     if course.courseid == course_id_list[i]:
    #         if user.provided_feedback[i] == '1':
    #             provided_feedback = True
    #         else:
    #             provided_feedback = False      

    # search functionality for questions
    if ('q' in request.GET) and request.GET['q'].strip():
         query_string = request.GET['q']
         terms = query_string.split()
         questions_found = live_questions
         for term in terms:
             question_ids_found = []
             for question in questions_found:
                if (re.search(re.escape(term), question.text, re.I)):
                     question_ids_found.append(question.id)
             questions_found = questions_found.filter(pk__in=question_ids_found)
 
         found_entries = Question.objects.all().filter(pk__in=question_ids_found)
         questions_pinned = found_entries.filter(is_pinned=True).order_by(user.chosen_filter)
         questions_unpinned = found_entries.exclude(is_pinned=True).order_by(user.chosen_filter) 

    if ('tag' in request.GET):
        tag = request.GET['tag']
        if (tag == 'all_tags'):
            found_entries = live_questions
        else:
            questions_found = live_questions
            question_ids_found = []
            for question in questions_found:
                if (re.search(re.escape(tag), question.tags)):
                    question_ids_found.append(question.id)
            found_entries = Question.objects.all().filter(pk__in=question_ids_found)
        questions_pinned = found_entries.filter(is_pinned=True).order_by(user.chosen_filter)
        questions_unpinned = found_entries.exclude(is_pinned=True).order_by(user.chosen_filter)
        #return HttpResponse("HI")
        #return render(request, 'quailapp/temp.html', {'course': course, 'questions_pinned': questions_pinned, 'questions': questions, 'user': request.user,
        #'courses': Course.objects.filter(courseid__in=user.course_id_list)})
    
    # if a question is posted
    if request.method == 'POST':
        # if the user chooses a filter
        if ('filter' in request.POST):
            form = QuestionForm(tags=course.tag_set.all())
            tag_form = TagForm()
            #feedback_form = FeedbackForm()
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

        else:
            form = QuestionForm(request.POST, tags=course.tag_set.all())
            tag_form = TagForm(request.POST)
 
            if form.is_valid():
                data = form.cleaned_data
                tags = ''
                for tag in data['tags']:
                    tags = tags + '|' + tag.id
                new_question = Question(text=data['your_question'], course=course, submitter=user, votes=0, is_live=True, tags=tags)
                new_question.save()
                for tag in data['tags']:
                    tag.questions = tag.questions + '|' + new_question.id
                    tag.save()
                return HttpResponseRedirect(reverse('quailapp:coursepage_live', args=(course.id,)))

            if tag_form.is_valid():
                data = tag_form.cleaned_data
                new_tag = Tag(text=data['your_tag'], course=course, submitter=request.user)
                new_tag.save()
                return HttpResponseRedirect(reverse('quailapp:coursepage_live', args=(course.id,))) 
    else:
        form = QuestionForm(tags=course.tag_set.all())
        tag_form = TagForm()
        #feedback_form = FeedbackForm()

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

    return render(request, 'quailapp/coursepage_live.html', {'course': course, 'form': form, 'tag_form': tag_form,
        'questions_pinned': questions_pinned, 'questions': questions, 'user': request.user, 'display_feedback': display_feedback,
        'provided_feedback': provided_feedback, 'courses': Course.objects.filter(courseid__in=user.course_id_list)})

def user_feedback(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user
    user_feedback = user.feedback_set.all().filter(course=course)
    feedback_for_course = user.providedfeedback_set.all().get(course=course)
    lecture_date = course.last_lecture

    # check if the user has any feedback before the last lecture
    if (len(user.feedback_set.filter(course=course, lecture_date__gte=lecture_date)) > 0):
        feedback_for_course.provided_feedback = True
        feedback_for_course.save()
    else:
        feedback_for_course.provided_feedback = False
        feedback_for_course.save()

    if request.method == 'POST':
        feedback_form = FeedbackForm(request.POST)
        if feedback_form.is_valid():
            data = feedback_form.cleaned_data
            
            choice = data['feedback_choice']
            feedback = data['your_feedback']
            
            new_feedback = Feedback(text=feedback, course=course, submitter=user, is_live=True, feedback_choice=choice, lecture_date=lecture_date)  
            new_feedback.save()

            # update the provided feedback to True
            feedback_for_course.provided_feedback = True
            feedback_for_course.save()

            return HttpResponseRedirect(reverse('quailapp:user_feedback', args=(course.id,))) 
    else:
        feedback_form = FeedbackForm()

    # checking if user has already submitted feedback for this course
    provided_feedback = False
    if feedback_for_course.provided_feedback == True:
        provided_feedback = True
    else:
        provided_feedback = False

    return render(request, 'quailapp/user_feedback.html', {'course': course, 'lecture_date': lecture_date,
        'feedback_form': feedback_form, 'user': request.user, 'user_feedback': user_feedback, 'provided_feedback': provided_feedback,
        'courses': Course.objects.filter(courseid__in=user.course_id_list)})

def coursepage_archive(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user
    archived_questions = course.question_set.all().exclude(is_live=True)
    archived_feedback = course.feedback_set.all().exclude(is_live=True)
    questions_pinned = archived_questions.filter(is_pinned=True).order_by(user.chosen_filter)
    questions_unpinned = archived_questions.exclude(is_pinned=True).order_by(user.chosen_filter)    

    if ('q' in request.GET) and request.GET['q'].strip():
         query_string = request.GET['q']
         terms = query_string.split()
         questions_found = archived_questions
         for term in terms:
             question_ids_found = []
             for question in questions_found:
                if (re.search(re.escape(term), question.text, re.I)):
                     question_ids_found.append(question.id)
             questions_found = questions_found.filter(pk__in=question_ids_found)
 
         found_entries = Question.objects.all().filter(pk__in=question_ids_found)
         questions_pinned = found_entries.filter(is_pinned=True).order_by(user.chosen_filter)
         questions_unpinned = found_entries.exclude(is_pinned=True).order_by(user.chosen_filter) 

    if ('tag' in request.GET):
        tag = request.GET['tag']
        if (tag == 'all_tags'):
            found_entries = archived_questions
        else:
            questions_found = archived_questions
            question_ids_found = []
            for question in questions_found:
                if (re.search(re.escape(tag), question.tags)):
                    question_ids_found.append(question.id)
            found_entries = Question.objects.all().filter(pk__in=question_ids_found)
        questions_pinned = found_entries.filter(is_pinned=True).order_by(user.chosen_filter)
        questions_unpinned = found_entries.exclude(is_pinned=True).order_by(user.chosen_filter)

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

    # counting the number of stars in each feedback
    counter = [0] * 6
    for feedback in course.feedback_set.all():
        if feedback.feedback_choice != '' and not feedback.is_live:
            count = int(feedback.feedback_choice)
            counter[count] += 1

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
    return render(request, 'quailapp/coursepage_archive.html', {'course': course, 'archived_feedback': archived_feedback,
        'questions_pinned': questions_pinned, 'questions': questions, 'user': request.user, 'counter': counter,
        'courses': Course.objects.filter(courseid__in=user.course_id_list)})

def delete_tag_from_coursepage(request, tag_id):
    tag = get_object_or_404(Tag, pk=tag_id)
    course = tag.course
    questions = tag.questions.split('|')
    for q in questions:
        if q != '':
            question = Question.objects.get(pk=q)
            question_tags = question.tags.replace("|"+tag.id, "")
            question.tags = question_tags
            question.save()
    tag.delete()
    return HttpResponseRedirect(reverse('quailapp:coursepage_live', args=(course.id,)))

def delete_from_coursepage(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    is_live = question.is_live
    course = question.course
    tags = question.tags.split('|')
    for tag in tags:
        if tag != '':
            t = Tag.objects.get(pk=tag)
            t_questions = t.questions.replace("|"+question.id, "")
            t.questions = t_questions
            t.save()
    question.delete()
    if (is_live == True):
        return HttpResponseRedirect(reverse('quailapp:coursepage_live', args=(course.id,)))
    else:
        return HttpResponseRedirect(reverse('quailapp:coursepage_archive', args=(course.id,)))

def delete_from_userinfo(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    tags = question.tags.split('|')
    for tag in tags:
        if tag != '':
            t = Tag.objects.get(pk=tag.id)
            t_questions = t.questions.replace("|"+question.id, "")
            t.questions = t_questions
            t.save()
    question.delete()
    return HttpResponseRedirect(reverse('quailapp:userinfo'))

def delete_feedback(request, feedback_id):
    feedback = get_object_or_404(Feedback, pk=feedback_id)
    user = request.user
    course = feedback.course
    last_lecture = course.last_lecture
    lecture_date = feedback.lecture_date

    # if the deleted feedback was for the last lecture, allow the user to submit feedback again
    if (last_lecture == lecture_date):
        feedback_for_course = user.providedfeedback_set.all().get(course=course)
        feedback_for_course.provided_feedback = False
        feedback_for_course.save()

    feedback.delete()
    return HttpResponseRedirect(reverse('quailapp:user_feedback', args=(course.id,)))

def archived_feedback(request):
    user = request.user
    archived_feedback = user.feedback_set.all().exclude(is_live=True)
    courses = Course.objects.filter(courseid__in=user.course_id_list)

    # counting the number of stars in each feedback
    counter = [0] * 6
    percents = [0] * 6
    total = 0.0
    for course in courses:
        for feedback in course.feedback_set.all():
            if feedback.feedback_choice != '' and not feedback.is_live:
                count = int(feedback.feedback_choice)
                counter[count] += 1
                total += 1
    for count in range(1,6):
        percents[count] = int((counter[count]/total)*100)
    return render(request, 'quailapp/archived_feedback.html', {'archived_feedback': archived_feedback,
        'counter': counter, 'percents': percents, 'total': int(total), 'user': user, 'courses': courses})

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
        'courses': Course.objects.filter(courseid__in=user.course_id_list)})

# def get_question(request):
#     # otherwise can post a question
#     if request.method == 'POST':
#         form = QuestionForm(request.POST)
#         if form.is_valid():
#             for tag in data['tags']:
#                 tags = tags + '|' + tag.id
#             new_question = Question(text=data['your_question'], course=course, submitter=user, votes=0, is_live=True, tags=tags)
#             new_question.save()
#             for tag in data['tags']:
#                 tag.questions = tag.questions + '|' + new_question.id
#                 tag.save()
#         return redirect('/index')
#     else:
#         form = QuestionForm()
#     return render(request, 'quailapp/question.html', {'form': form})

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
    
    ## lecturer student validation 
    if request.is_ajax():
        # check if student
        all_netids_object = AllNetids.objects.all()
        all_netids = all_netids_object[0].all_netids
        if request.GET['is_student'] == "1":
            if netid in all_netids:
                return HttpResponse("yes")
            else:
                return HttpResponse("")
        # check if lecturer
        else:
            if netid not in all_netids:
                return HttpResponse("yes")
            else:
                return HttpResponse("")

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

        # delete the feedback for that course
        feedback_for_course = user.providedfeedback_set.all().get(course=course_to_unenroll)
        feedback_for_course.delete()

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
                # add provided_feedback
                new_provided_feedback = ProvidedFeedback(submitter=user, provided_feedback=False, course=course)
                new_provided_feedback.save()
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


def answered_questions(request, course_id):

    if request.is_ajax():
        course = get_object_or_404(Course, pk=course_id)
        questions = Question.objects.filter(submitter=request.user, course=course, is_live=True)
        
        # all questions that have been answered in the last X seconds... 
        q_ids = []
        now = datetime.datetime.now()
        for q in questions:
            try:
                if (q.answer.created_on + timedelta(seconds=10) >= now):
                    q_ids.append(q.id)
            except:
                pass
        if not q_ids:
            return HttpResponse("")
        # serialize into json response
        questions_answered = Question.objects.filter(pk__in=q_ids)
        data = serializers.serialize('json', questions_answered)
        return HttpResponse(data, content_type='application/json')

def home(request):
    return render(request, 'quailapp/home.html')

