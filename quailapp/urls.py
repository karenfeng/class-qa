from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required

from . import views

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^index$', login_required(views.index), name='index'),
    url(r'^get$', login_required(views.get_question), name='get'),
    url(r'^(?P<answer_id>[a-zA-Z0-9]+)/deleteans/$', login_required(views.delete_answer), name='deleteans'), # deletes answers assoc w/ question
    url(r'^(?P<question_id>[0-9][a-zA-Z0-9]+)/$', login_required(views.question_detail), name='detail'), # messy solution; question ids too long
    url(r'^(?P<question_id>[a-zA-Z0-9]+)/vote/$', login_required(views.vote), name='vote'), # vote for a specific question
    url(r'^(?P<question_id>[a-zA-Z0-9]+)/pin/$', login_required(views.pin), name='pin'), # vote for a specific question
    #url(r'^(?P<question_id>[a-zA-Z0-9]+)/answer/$', login_required(views.get_answer), name='answer'), # answer a specific question
    url(r'^login$', views.login_CAS, name='login'),
    url(r'^logout$', views.logout_CAS, name='logout'),
    url(r'^(?P<netid>[a-zA-Z0-9]+)/create$', views.create_account, name='create'),
    url(r'^userinfo$', login_required(views.user_info), name='userinfo'),
    url(r'^enroll$', login_required(views.enroll), name='enroll'),
    url(r'^(?P<course_id>[a-zA-Z0-9]+)/coursepage/$', login_required(views.coursepage), name='coursepage'),
    url(r'^(?P<question_id>[a-zA-Z0-9]+)/delete_from_coursepage/$', login_required(views.delete_from_coursepage), name='delete_from_coursepage'), # a little hacky.
    url(r'^(?P<question_id>[a-zA-Z0-9]+)/delete_from_info/$', login_required(views.delete_from_userinfo), name='delete_from_userinfo'),
    #url(r'^class$', views.register_class, name='class'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
