from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from acc.models import User
from .forms import ExistingListItemForm, ItemForm, ShareListForm
from .models import Item, List

LOGIN_REQUIRED_MESSAGE = "Log in to see your lists."
LIST_DELETED_MESSAGE = "List deleted."
SHARE_SELF_ERROR = "You already own this list."
SHARE_INVALID_EMAIL_ERROR = "Please enter a valid email address to share with."


def get_viewable_list(request, list_id):
    """Fetch a list the current user may see. Private lists are reported as
    missing (404) rather than forbidden, so their existence isn't leaked."""
    our_list = get_object_or_404(List, pk=list_id)
    if not our_list.can_be_viewed_by(request.user):
        raise Http404("No such list")
    return our_list


def get_owned_list(request, list_id):
    our_list = get_viewable_list(request, list_id)
    if not our_list.is_owned_by(request.user):
        raise Http404("No such list")
    return our_list


def home_page(request):
    return render(request, 'todolist/home.html', {'form': ItemForm()})


def view_list(request, list_id):
    our_list = get_viewable_list(request, list_id)
    form = ExistingListItemForm(for_list=our_list)
    if request.method == 'POST':
        form = ExistingListItemForm(for_list=our_list, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect(our_list)
    return render(request, 'todolist/list.html', {
        'list': our_list,
        'form': form,
        'share_form': ShareListForm(),
        'is_owner': our_list.is_owned_by(request.user),
    })


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
    return render(request, 'todolist/my_lists.html', {
        'lists': request.user.lists.order_by('-id'),
        'shared_lists': request.user.shared_lists.order_by('-id'),
    })


@require_POST
def toggle_item(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    get_viewable_list(request, item.list_id)
    item.done = not item.done
    item.save(update_fields=['done'])
    return redirect(item.list)


@require_POST
def delete_item(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    our_list = get_viewable_list(request, item.list_id)
    item.delete()
    return redirect(our_list)


@require_POST
def delete_list(request, list_id):
    our_list = get_owned_list(request, list_id)
    our_list.delete()
    messages.success(request, LIST_DELETED_MESSAGE)
    return redirect('todolist:my_lists')


@require_POST
def share_list(request, list_id):
    our_list = get_owned_list(request, list_id)
    form = ShareListForm(request.POST)
    if not form.is_valid():
        messages.error(request, SHARE_INVALID_EMAIL_ERROR)
        return redirect(our_list)
    email = form.cleaned_data['sharee']
    if email == our_list.owner_id:
        messages.error(request, SHARE_SELF_ERROR)
        return redirect(our_list)
    # Users are just email addresses, so the sharee needn't have logged in yet.
    sharee, _ = User.objects.get_or_create(email=email)
    our_list.shared_with.add(sharee)
    messages.success(request, f"List shared with {email}.")
    return redirect(our_list)
