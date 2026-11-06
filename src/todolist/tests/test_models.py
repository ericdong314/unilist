from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.test import TestCase
from acc.models import User
from todolist.models import List, Item


class ItemModelTest(TestCase):
    def test_representation(self):
        item = Item(text='I hope to appear.')
        self.assertEqual(str(item), 'I hope to appear.')

    def test_default_text(self):
        item = Item()
        self.assertEqual(item.text, '')

    def test_item_is_related_to_list(self):
        mylist = List.objects.create()
        item = Item.objects.create(list=mylist)
        self.assertIn(item, mylist.item_set.all())

    def test_cannot_save_null_list_items(self):
        mylist = List.objects.create()
        item = Item(list=mylist, text=None)
        with self.assertRaises(IntegrityError) as cm:
            item.save()

    def test_cannot_save_empty_list_item(self):
        mylist = List.objects.create()
        item = Item(list=mylist, text='')
        with self.assertRaises(ValidationError) as cm:
            item.full_clean()

    def test_item_duplication_NOT_allowed(self):
        funny_text = "Please don't laugh!"
        mylist = List.objects.create()
        Item.objects.create(text=funny_text, list=mylist)
        with self.assertRaises(ValidationError) as cm:
            item = Item(text=funny_text, list=mylist)
            item.full_clean()

    def test_CAN_save_same_item_to_different_lists(self):
        funny_text = "Please don't laugh!"
        mylist = List.objects.create()
        urlist = List.objects.create()
        Item.objects.create(text=funny_text, list=mylist)
        item = Item(text=funny_text, list=urlist)
        item.full_clean()  # should not raise


class ListModelTest(TestCase):
    def test_get_absolute_url(self):
        mylist = List.objects.create()
        self.assertEqual(mylist.get_absolute_url(), f'/todo/lists/{mylist.id}/')

    def test_list_item_ordering(self):
        mylist = List.objects.create()
        item1 = Item.objects.create(text='blah', list=mylist)
        item2 = Item.objects.create(text='aha', list=mylist)
        item3 = Item.objects.create(text='bam', list=mylist)
        self.assertSequenceEqual(mylist.item_set.all(), [item1, item2, item3])

    def test_name_is_first_item_text(self):
        mylist = List.objects.create()
        Item.objects.create(text='first item', list=mylist)
        Item.objects.create(text='second item', list=mylist)
        self.assertEqual(mylist.name, 'first item')
        self.assertEqual(str(mylist), 'first item')

    def test_name_of_empty_list_falls_back_to_id(self):
        mylist = List.objects.create()
        self.assertEqual(mylist.name, f'List {mylist.pk}')

    def test_lists_can_have_owners(self):
        user = User.objects.create(email='a@b.com')
        mylist = List.objects.create(owner=user)
        self.assertIn(mylist, user.lists.all())

    def test_list_owner_is_optional(self):
        List.objects.create()  # should not raise

    def test_deleting_owner_keeps_list(self):
        user = User.objects.create(email='a@b.com')
        mylist = List.objects.create(owner=user)
        user.delete()
        mylist.refresh_from_db()
        self.assertIsNone(mylist.owner)
