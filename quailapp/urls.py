from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required

from . import views

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^index$', login_required(views.index), name='index'),
    #url(r'^get$', login_required(views.get_question), name='get'), # deprecated
    url(r'^(?P<answer_id>[a-zA-Z0-9]+)/deleteans/$', login_required(views.delete_answer), name='deleteans'), # deletes answers assoc w/ question
    url(r'^(?P<question_id>[0-9][a-zA-Z0-9]+)/$', login_required(views.question_detail), name='detail'), # messy solution; question ids too long
    url(r'^(?P<question_id>[a-zA-Z0-9]+)/vote/$', login_required(views.vote), name='vote'), # vote for a specific question
    url(r'^(?P<question_id>[a-zA-Z0-9]+)/star/$', login_required(views.star), name='star'), # star a specific question
    url(r'^(?P<question_id>[a-zA-Z0-9]+)/pin/$', login_required(views.pin), name='pin'), # pin a specific question
    url(r'^(?P<question_id>[a-zA-Z0-9]+)/answer/$', login_required(views.get_answer), name='answer'), # answer a specific question
    url(r'^login$', views.login_CAS, name='login'),
    url(r'^logout$', views.logout_CAS, name='logout'),
    url(r'^(?P<netid>[a-zA-Z0-9]+)/create$', views.create_account, name='create'),
    url(r'^userinfo$', login_required(views.user_info), name='userinfo'),
    url(r'^enroll$', login_required(views.enroll), name='enroll'),
    #url(r'^(?P<course_id>[a-zA-Z0-9]+)/coursepage/$', login_required(views.coursepage), name='coursepage'),
    url(r'^(?P<course_id>[a-zA-Z0-9]+)/coursepage_live/$', login_required(views.coursepage_live), name='coursepage_live'),
    url(r'^(?P<course_id>[a-zA-Z0-9]+)/coursepage_archive/$', login_required(views.coursepage_archive), name='coursepage_archive'),
    url(r'^(?P<question_id>[a-zA-Z0-9]+)/delete_from_coursepage/$', login_required(views.delete_from_coursepage), name='delete_from_coursepage'), # a little hacky.
    url(r'^(?P<tag_id>[a-zA-Z0-9]+)/delete_tag_from_coursepage/$', login_required(views.delete_tag_from_coursepage), name='delete_tag_from_coursepage'), # a little hacky.
    url(r'^(?P<question_id>[a-zA-Z0-9]+)/delete_from_info/$', login_required(views.delete_from_userinfo), name='delete_from_userinfo'),
    url(r'^similar_question$', login_required(views.similar_question), name='similar_question'),
    url(r'^change_name$', login_required(views.change_name), name='change_name'),
    url(r'^(?P<question_id>[a-zA-Z0-9]+)/edit_question/$', login_required(views.edit_question), name='edit_question'),
    url(r'^(?P<question_id>[a-zA-Z0-9]+)/edit_answer/$', login_required(views.edit_answer), name='edit_answer'),
    url(r'^(?P<course_id>[a-zA-Z0-9]+)/answered_questions/$', login_required(views.answered_questions), name='answered_questions'),
    url(r'^(?P<category_id>[a-zA-Z0-9]+)/answered_questions_social/$', login_required(views.answered_questions_social), name='answered_questions_social'),
    url(r'^(?P<course_id>[a-zA-Z0-9]+)/feedback/$', login_required(views.user_feedback), name='user_feedback'),
    url(r'^(?P<feedback_id>[a-zA-Z0-9]+)/feedback/delete$', login_required(views.delete_feedback), name='delete_feedback'),
    url(r'^archived_feedback$', login_required(views.archived_feedback), name='archived_feedback'),
    url(r'^social$', login_required(views.social_home), name='social_home'),
    url(r'^(?P<category_id>[a-zA-Z0-9]+)/social/$', login_required(views.social_category), name='social_category'),
    url(r'^(?P<question_id>[0-9][a-zA-Z0-9]+)/social$', login_required(views.social_detail), name='social_detail'), # messy solution; there CANNOT be a trailing slash, otherwise will confuse w/ social category link
    url(r'^(?P<question_id>[a-zA-Z0-9]+)/delete_from_social/$', login_required(views.delete_from_social), name='delete_from_social'), # a little hacky.
    url(r'^(?P<tag_id>[a-zA-Z0-9]+)/delete_tag_from_social/$', login_required(views.delete_tag_from_social), name='delete_tag_from_social'), # a little hacky.

    #url(r'^class$', views.register_class, name='class'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
