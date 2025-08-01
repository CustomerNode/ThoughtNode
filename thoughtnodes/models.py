from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
import datetime

# Create your models here.
frequency_options = (
    ('Daily','Daily'),
    ('Weekly','Weekly'),
    ('Monthly','Monthly'),
)
class Thoughtnode(models.Model):
    title = models.CharField(max_length=50)
    query = models.TextField()
    prompt = models.TextField()
    frequency = models.CharField(max_length=7,choices=frequency_options)
    slug = models.SlugField()
    date = models.DateTimeField()
    user = models.ForeignKey(User,on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    def makeslug(self):
        self.date = datetime.datetime.now()
        self.slug = slugify(self.user.username+self.date.strftime('%Y%m%d%H%M%S'))