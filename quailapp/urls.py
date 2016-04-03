from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required

from . import views

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^index$', login_required(views.IndexView.as_view()), name='index'),
    url(r'^get$', views.get_question, name='get'),
    url(r'^delete$', views.delete_questions, name='delete'),
    url(r'^(?P<question_id>[a-zA-Z0-9]+)/deleteans/$', views.delete_answers, name='deleteans'), # deletes answers assoc w/ question
    url(r'^(?P<pk>[0-9][a-zA-Z0-9]+)/$', login_required(views.DetailView.as_view()), name='detail'), # messy solution; question ids too long
    url(r'^(?P<question_id>[a-zA-Z0-9]+)/vote/$', views.vote, name='vote'), # vote for a specific question
    url(r'^(?P<question_id>[a-zA-Z0-9]+)/answer/$', views.get_answer, name='answer'), # answer a specific question
    url(r'^hello$', views.hello_world, name='hello'),
    url(r'^login$', views.login_CAS, name='login'),
    url(r'^(?P<netid>[a-zA-Z0-9]+)/create$', views.create_account, name='create'),
    url(r'^userinfo$', views.user_info, name='userinfo'),
    url(r'^(?P<pk>[a-zA-Z0-9]+)/coursepage/$', login_required(views.CourseDetailView.as_view()), name='coursepage'),
    #url(r'^class$', views.register_class, name='class'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

