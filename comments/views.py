from django.shortcuts import render

# Create your views here.
def comment_list(request):
    """评论页面"""
    return render(request, 'comments/comment_list.html')