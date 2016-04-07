from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import sys, os, cgi, urllib, re

# Create your models here.

# class QuailUser(models.Model):
#   netid = models.TextField()
#   first_name = models.TextField()
#   last_name = models.TextField()
#   is_student = models.BooleanField()
#   #classes = models.ForeignField(Course, null=True)

#   def __unicode__(self):
#     return self.netid
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

  courses_by_id = models.TextField(max_length=10)
  #classes = models.ForeignKey(Course, null=True)

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
    for i in range(len(course_ids)):
      course_list.append(Course.objects.get(courseid=course_ids[i]))
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

  def __unicode__(self):
    depts = self.dept.split('/')
    nums = self.num.split('/')
    name = ""
    for i in range(len(depts)):
      name += depts[i] + " " + nums[i] + '/'
    name = name[:len(name)-1]
    return '%s: %s' % (name, self.title)  

class Question(models.Model):
    created_on = models.DateTimeField(null=True)
    text = models.TextField()
    votes = models.IntegerField(default=0)
    submitter = models.ForeignKey(QuailUser, null=True)
    rank_score = models.FloatField(default=0.0)
    course = models.ForeignKey(Course, null=True)

    class Meta:
      ordering = ['-votes']

    def __unicode__(self):
        return self.text

class Answer(models.Model):
  created_on = models.DateTimeField(null=True) 
  text = models.TextField()
  submitter = models.ForeignKey(QuailUser, null=True)
  question = models.OneToOneField(Question, null=True, on_delete=models.CASCADE)

  def __unicode__(self):
    return self.text

class Comment(models.Model):
  created_on = models.DateTimeField(null=True) 
  text = models.TextField()
  submitter = models.ForeignKey(QuailUser, null=True)
  question = models.ForeignKey(Question, null=True, on_delete=models.CASCADE)

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
