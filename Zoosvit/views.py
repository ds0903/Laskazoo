from django.shortcuts import render

def home(request):
    return render(request, 'zoosvit/home.html')
