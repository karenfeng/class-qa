from django.db import models


class Question(models.Model):
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    text = models.TextField()
    votes = models.IntegerField()    
