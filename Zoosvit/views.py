from django.shortcuts import render, get_object_or_404

from django.core.paginator import Paginator
from django.db.models import Count

def home(request):
    return render(request, 'zoosvit/home.html')
