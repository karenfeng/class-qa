from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import sys, os, cgi, urllib, re

# Create your models here.

class AllNetids(models.Model):
  all_netids = models.TextField()

class QuailUserManager(BaseUserManager):
  #def create_user(self, netid, first_name, last_name, is_student, courses_by_name=None, password=None):
  def create_user(self, netid, first_name, last_name, is_student, courses_by_id=None, password=None):
    if not netid:
      raise ValueError('User must have netid')
    #new_user = self.model(netid=netid, first_name=first_name, last_name=last_name, is_student=is_student, courses_by_name=courses_by_name)
    new_user = self.model(netid=netid, first_name=first_name, last_name=last_name, is_student=is_student, courses_by_id=courses_by_id)
    new_user.set_password(password)
    new_user.save(using=self._db)
    return new_user

  def create_superuser(self, netid, first_name, last_name, is_student, password):
    user = self.create_user(netid, first_name, last_name, is_student, password=password)
    user.is_admin = True
    user.is_staff = True
    user.save(using=self._db)
    return user

class QuailUser(AbstractBaseUser, PermissionsMixin):
  netid = models.TextField(unique=True)
  first_name = models.TextField()
  last_name = models.TextField()
  is_student = models.BooleanField()
  is_admin = models.BooleanField(default=False)
  is_staff = models.BooleanField(default=False)
  is_active = models.BooleanField(default=True)
  chosen_filter = models.CharField(default='-votes', max_length=10) # kinda hack-y. maybe ajax will fix.

  courses_by_id = models.TextField(max_length=10)

  USERNAME_FIELD = 'netid'
  REQUIRED_FIELDS = ['first_name', 'last_name', 'is_student']

  objects = QuailUserManager()

  def get_full_name(self):
    return self.netid

  def get_short_name(self):
    return self.netid

  def __unicode__(self):
    return self.netid

  def has_perm(self, perm, obj=None):
    return True

  def has_module_perms(self, app_label):
    return True

  def course_id_list(self):
    return self.courses_by_id.split('|')

  def courses_as_list(self):
    course_list = []
    course_ids = self.courses_by_id.split('|')
    for courseid in course_ids:
      if courseid != '':
        course_list.append(Course.objects.get(courseid=courseid))
    return course_list

class Course(models.Model):
  dept = models.TextField(max_length=3) # new
  num = models.TextField(max_length=3)  # new
  title = models.TextField()  # new
  #name = models.TextField()
  courseid = models.TextField() # new
  professor = models.TextField()
  starttime = models.TimeField(null=False)
  endtime = models.TimeField(null=False)
  days = models.CharField(max_length=10)
  archive_type = models.TextField(default='every_lecture') # allow profs to change how questions are archived

  def days_as_list(self):
    weekdays = []
    for d in self.days:
      if (d == '0'):
        weekdays.append('M')
      elif (d == '1'):
        weekdays.append('T')
      elif (d == '2'):
        weekdays.append('w')
      elif (d == '3'):
        weekdays.append('Th')
      else:
        weekdays.append('F')
    return weekdays

  def days_as_string(self):
    weekdays = ""
    for d in self.days:
      if (d == '0'):
        weekdays += 'M/'
      elif (d == '1'):
        weekdays += 'T/'
      elif (d == '2'):
        weekdays += 'W/'
      elif (d == '3'):
        weekdays += 'Th/'
      else:
        weekdays += 'F/'
    return weekdays[:len(weekdays)-1]

  def __unicode__(self):
    depts = self.dept.split('/')
    nums = self.num.split('/')
    name = ""
    for i in range(len(depts)):
      name += depts[i] + " " + nums[i] + '/'
    name = name[:len(name)-1]
    return '%s: %s' % (name, self.title)  

class Tag(models.Model):
  text = models.TextField() # the actual tag name itself
  course = models.ForeignKey(Course, null=True) # tags associated with a course
  questions = models.TextField(default="")  # question ids under this tag
  submitter = models.ForeignKey(QuailUser, null=True)

  def __unicode__(self):
    return self.text
    
class Question(models.Model):
    created_on = models.DateTimeField(auto_now_add=True)
    text = models.TextField()
    votes = models.IntegerField(default=0)
    stars = models.IntegerField(default=0)
    submitter = models.ForeignKey(QuailUser, null=True)
    rank_score = models.FloatField(default=0.0)
    course = models.ForeignKey(Course, null=True)
    is_pinned = models.BooleanField(default=False)
    is_live = models.BooleanField(default=True)
    tags = models.TextField(null=True, default="") # allow tags (separated by '|')

    users_upvoted = models.TextField(null=True, blank=True, default="")
    users_downvoted = models.TextField(null=True, blank=True, default="")
    users_starred = models.TextField(null=True, blank=True, default="")

    class Meta:
      ordering = ['-votes']

    def __unicode__(self):
        return self.text

    def tags_as_list(self):
      tag_list = []
      tag_ids = self.tags.split('|')
      for tag in tag_ids:
        if tag != '':
          tag_list.append(Tag.objects.get(pk=tag))
      return tag_list

class Answer(models.Model):
  created_on = models.DateTimeField(auto_now_add=True) 
  text = models.TextField()
  submitter = models.ForeignKey(QuailUser, null=True)
  question = models.OneToOneField(Question, null=True, on_delete=models.CASCADE)

  def __unicode__(self):
    return self.text

class Comment(models.Model):
  created_on = models.DateTimeField(auto_now_add=True) 
  text = models.TextField()
  submitter = models.ForeignKey(QuailUser, null=True)
  question = models.ForeignKey(Question, null=True, on_delete=models.CASCADE)

  def __unicode__(self):
    return self.text

class Feedback(models.Model):
  created_on = models.DateTimeField(auto_now_add=True) 
  archived_on = models.DateField(null=True)
  text = models.TextField(null=True, blank=True, default="")
  submitter = models.ForeignKey(QuailUser, null=True)
  course = models.ForeignKey(Course, null=True, on_delete=models.CASCADE)
  is_live = models.BooleanField(default=True)
  feedback_choice = models.CharField(max_length=5, null=True)

  class Meta:
      ordering = ['-created_on']

  def __unicode__(self):
    return self.text

# for CAS login..
class CASClient:
   def __init__(self, request):
      self.cas_url = 'https://fed.princeton.edu/cas/'
      self.request = request
   def Authenticate(self):
      # If the request contains a login ticket, try to validate it
      if 'ticket' in self.request.GET:
         netid = self.Validate(self.request.GET['ticket'])
         if netid != None:
            return netid
   

   def redirect_url(self):
      login_url = self.cas_url + 'login' + '?service=' + urllib.quote(self.ServiceURL())
      return login_url
      
   def redirect_url_logout(self):
      logout_url = self.cas_url + 'logout' + '?service=' + urllib.quote(self.ServiceURL_logout())
      return logout_url


   def Validate(self, ticket):
      val_url = self.cas_url + "validate" + \
         '?service=' + urllib.quote(self.ServiceURL()) + \
         '&ticket=' + urllib.quote(ticket)
      r = urllib.urlopen(val_url).readlines()   # returns 2 lines
      if len(r) == 2 and re.match("yes", r[0]) != None:
         return r[1].strip()
      return None

   def ServiceURL_logout(self):
      ret = 'http://' + self.request.META['HTTP_HOST'] + "/"
      ret = re.sub(r'ticket=[^&]*&?', '', ret)
      ret = re.sub(r'\?&?$|&$', '', ret)
      return ret

   def ServiceURL(self):
      ret = 'http://' + self.request.META['HTTP_HOST'] + self.request.META['PATH_INFO']
      ret = re.sub(r'ticket=[^&]*&?', '', ret)
      ret = re.sub(r'\?&?$|&$', '', ret)
      return ret
      #if os.environ.has_key('REQUEST_URI'):
      #   ret = 'http://' + os.environ['HTTP_HOST'] + os.environ['REQUEST_URI']
      #   ret = re.sub(r'ticket=[^&]*&?', '', ret)
      #   ret = re.sub(r'\?&?$|&$', '', ret)
      #   return ret
         #$url = preg_replace('/ticket=[^&]*&?/', '', $url);
         #return preg_replace('/?&?$|&$/', '', $url);
      #return "something is badly wrong"
 
def main():
  print "CASClient does not run standalone"
if __name__ == '__main__':
  main()
