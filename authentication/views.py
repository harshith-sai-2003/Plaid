from django.shortcuts import render, redirect
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpResponse

from plaid_api.models import PlaidCredential

# Create your views here.
def register(request):
    if request.method=='POST':
        password=request.POST['password']
        email=request.POST['email']
        first_name=request.POST.get('first_name','default value')
        last_name=request.POST.get('last_name', 'default value')

        user=User.objects.create_user(username=email,email=email,password=password)
        user.first_name=first_name
        user.last_name=last_name
        user.save()

        login(request,user)

        return HttpResponseRedirect('/')
    else:
        return render(request,'authentication/register.html')

def login_view(request):
    if request.method=='POST':
        email=request.POST['email']
        password=request.POST['password']
        user=authenticate(username=email,password=password)
        if user is not None:
            login(request,user)
            try:
                p=PlaidCredential.objects.get(user=user)
                request.session['access_token']=p.access_token
            except PlaidCredential.DoesNotExist:
                pass
            if request.GET.get('next'):
                return HttpResponseRedirect(request.GET.get('next'))
            return HttpResponseRedirect('/')
        else:
            return HttpResponse('Invalid Login')
    else:
        return render(request, 'authentication/login.html')


@login_required(login_url='/auth/login/')
def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/')

