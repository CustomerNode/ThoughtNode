from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from .models import Thoughtnode
from . import forms
from openai import OpenAI

# Create your views here.
@login_required(login_url='/profiles/login')
def thoughtnodes_list(request):
    thoughtnodes = Thoughtnode.objects.filter(user=request.user).order_by('-date')
    return render(request,'thoughtnodes/thoughtnodes_list.html',{'thoughtnodes':thoughtnodes})

@login_required(login_url='/profiles/login')
def thoughtnode_view(request,slug):
    thoughtnode = Thoughtnode.objects.get(user=request.user,slug=slug)
    return render(request,'thoughtnodes/thoughtnode_view.html',{'thoughtnode':thoughtnode})

@login_required(login_url='/profiles/login')
def thoughtnode_add(request):
    if(request.method == 'POST'):
        form = forms.CreateThoughtnode(request.POST)
        if(form.is_valid()):
            newthoughtnode = form.save(commit=False)
            newthoughtnode.user = request.user
            newthoughtnode.makeslug()
            newthoughtnode.save()
            return redirect('thoughtnodes:viewthoughtnode',newthoughtnode.slug)
    else:
        form = forms.CreateThoughtnode()
    return render(request,'thoughtnodes/thoughtnode_add.html',{'form':form})

@login_required(login_url='/profiles/login')
def thoughtnode_edit(request,slug):
    thoughtnode = Thoughtnode.objects.get(user=request.user,slug=slug)
    if(request.method == 'POST'):
        form = forms.CreateThoughtnode(request.POST,instance=thoughtnode)
        if(form.is_valid()):
            newthoughtnode = form.save(commit=False)
            newthoughtnode.save()
            return redirect('thoughtnodes:viewthoughtnode',newthoughtnode.slug)
    else:
        form = forms.CreateThoughtnode(instance=thoughtnode)
    return render(request,'thoughtnodes/thoughtnode_edit.html',{'form':form,'thoughtnode':thoughtnode})

@login_required(login_url='/profiles/login')
def thoughtnode_delete(request,slug):
    if(request.method == 'POST'):
        thoughtnode = Thoughtnode.objects.get(user=request.user,slug=slug)
        thoughtnode.delete()
        return redirect('thoughtnodes:thoughtnodeslist')

@login_required(login_url='/profiles/login')
def thoughtnode_run(request,slug):
    if(request.method == 'POST'):
        client = OpenAI()
        thoughtnode = Thoughtnode.objects.get(user=request.user,slug=slug)
        gptresponse = client.responses.create(
            model="gpt-4.1",
            input=thoughtnode.prompt
        )
        print(gptresponse.output_text)
        return redirect('thoughtnodes:thoughtnodeslist')