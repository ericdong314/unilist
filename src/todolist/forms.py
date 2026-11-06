from todolist.models import Item
from django import forms

EMPTY_ITEM_ERROR = "You can't have an empty list item"
DUPLICATE_ITEM_ERROR = "There is already such an item in the list."


class ItemForm(forms.Form):
    text = forms.CharField(error_messages={'required': EMPTY_ITEM_ERROR}, required=True)


    def save(self, for_list):
        return Item.objects.create(text=self.cleaned_data['text'], list=for_list)


class ExistingListItemForm(ItemForm):
    def __init__(self, for_list, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._list = for_list

    def clean_text(self):
        text = self.cleaned_data['text']
        if self._list.item_set.filter(text=text).exists():
            raise forms.ValidationError(DUPLICATE_ITEM_ERROR)
        return text

    def save(self):
        return super().save(for_list=self._list)


class ShareListForm(forms.Form):
    sharee = forms.EmailField()

    def clean_sharee(self):
        return self.cleaned_data['sharee'].strip().lower()
