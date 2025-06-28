from django.shortcuts import render,redirect
from django.contrib.auth.forms import UserCreationForm,AuthenticationForm
from django.contrib.auth import login,logout
from django.contrib.auth.decorators import login_required

# Create your views here.
# def register_view(request):
#     if(request.method == 'POST'):
#         form = UserCreationForm(request.POST)
#         if(form.is_valid()):
#             login(request,form.save())
#             if('next' in request.POST):
#                 return redirect(request.POST.get('next'))
#             return redirect('thoughtnodes:thoughtnodeslist')
#     else:
#         form = UserCreationForm()
#     return render(request,'profiles/register.html',{'form':form})

def login_view(request):
    if(request.method == 'POST'):
        form = AuthenticationForm(data=request.POST)
        if(form.is_valid()):
            login(request,form.get_user())
            if('next' in request.POST):
                return redirect(request.POST.get('next'))
            return redirect('thoughtnodes:thoughtnodeslist')
    else:
        form = AuthenticationForm()
    return render(request,'profiles/login.html',{'form':form})

def logout_view(request):
    if(request.method == 'POST'):
        logout(request)
        return redirect('profiles:login')

@login_required(login_url='/profiles/login')
def profile_view(request):
    return render(request,'profiles/profile.html')