from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^get$', views.get_question, name='get'),
    url(r'^delete$', views.delete_questions, name='delete'),
    url(r'^hello$', views.hello_world, name='hello'),
    url(r'^login$', views.login, name='login'),
]
