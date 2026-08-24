from django.db import models

class Comment(models.Model):
    content = models.TextField()
    created_at = models.CharField(max_length=20)

    def __str__(self):
        return self.content[:20]  # Return the first 20 characters of the comment