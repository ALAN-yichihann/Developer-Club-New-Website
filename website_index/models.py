from django.db import models

# Create your models here.
class Intro(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()

    def __str__(self):
        return self.title

class Development(models.Model):
    title = models.CharField(max_length=50)
    content = models.TextField()

    def __str__(self):
        return self.title

class Moment(models.Model):
    title = models.CharField(max_length=50)
    picture = models.ImageField(upload_to="website_index/%Y/%m/")

    def __str__(self) -> str:
        return self.title

class Activity(models.Model):
    title = models.CharField(max_length=50)
    content = models.TextField()

    class Meta:
        verbose_name_plural = 'Activities'

    def __str__(self):
        return self.title

class Info(models.Model):
    title = models.CharField(max_length=50)
    content = models.TextField()
    communication = models.TextField()

    def __str__(self):
        return self.title 