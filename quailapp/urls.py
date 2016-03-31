from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'), # use generic view
    url(r'^get$', views.get_question, name='get'),
    url(r'^delete$', views.delete_questions, name='delete'),
    url(r'^(?P<question_id>[a-zA-Z0-9]+)/deleteans/$', views.delete_answers, name='deleteans'), # deletes answers assoc w/ question
    url(r'^(?P<pk>[0-9][a-zA-Z0-9]+)/$', views.DetailView.as_view(), name='detail'), # messy solution; question ids too long
    url(r'^(?P<question_id>[a-zA-Z0-9]+)/vote/$', views.vote, name='vote'), # vote for a specific question
    url(r'^(?P<question_id>[a-zA-Z0-9]+)/answer/$', views.get_answer, name='answer'), # answer a specific question
    url(r'^hello$', views.hello_world, name='hello'),
    url(r'^login$', views.login, name='login'),
    url(r'^(?P<netid>[a-zA-Z0-9]+)/create$', views.create_account, name='create'),
    #url(r'^class$', views.register_class, name='class'),
]
