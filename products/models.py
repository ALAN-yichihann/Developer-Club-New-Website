from django.db import models

class Series(models.Model):
    name = models.CharField(max_length=100)
    intro = models.TextField()
    author = author = models.CharField(max_length=100)
    date_added = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'series'

    def __str__(self):
        return self.name

class Product(models.Model):
    series = models.ForeignKey(Series, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
    date_added = models.DateTimeField(auto_now_add=True)
    intro = models.TextField()
    file = models.FileField()

    def __str__(self) -> str:
        return self.name

    
