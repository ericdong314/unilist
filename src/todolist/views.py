from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ExistingListItemForm, ItemForm
from .models import List

LOGIN_REQUIRED_MESSAGE = "Log in to see your lists."


def home_page(request):
    return render(request, 'todolist/home.html', {'form': ItemForm()})


def view_list(request, list_id):
    our_list = get_object_or_404(List, pk=list_id)
    form = ExistingListItemForm(for_list=our_list)
    if request.method == 'POST':
        form = ExistingListItemForm(for_list=our_list, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect(our_list)
    return render(request, 'todolist/list.html', {'list': our_list, 'form': form})


@require_POST
def new_list(request):
    form = ItemForm(request.POST)
    if form.is_valid():
        owner = request.user if request.user.is_authenticated else None
        nulist = List.objects.create(owner=owner)
        form.save(nulist)
        return redirect(nulist)
    return render(request, 'todolist/home.html', context={'form': form})


def my_lists(request):
    if not request.user.is_authenticated:
        messages.info(request, LOGIN_REQUIRED_MESSAGE)
        return redirect('todolist:home')
    lists = request.user.lists.order_by('-id')
    return render(request, 'todolist/my_lists.html', {'lists': lists})
