from django.shortcuts import render
from django.views.generic import TemplateView

class HomeView(TemplateView):
    template_name = 'home.html'


def error_404(request, exception):
    return render(request,'404.html')

def error_500(request):
    return render(request,'500.html' )

def error_403(request,  exception):
    return render(request,'403.html')
