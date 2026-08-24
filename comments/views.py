from django.shortcuts import render

from .models import Comment

# Create your views here.
def comment_list(request):
    """评论页面"""
    comments = Comment.objects.all()
    context = {'comments': comments}
    return render(request, 'comments/comment_list.html', context)