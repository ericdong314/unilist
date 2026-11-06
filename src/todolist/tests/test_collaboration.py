"""Tests for item completion/deletion, list deletion, sharing and privacy."""
from django.test import TestCase

from acc.models import User
from todolist.forms import ShareListForm
from todolist.models import Item, List
from todolist.views import LIST_DELETED_MESSAGE, SHARE_INVALID_EMAIL_ERROR, SHARE_SELF_ERROR

OWNER_EMAIL = 'owner@example.com'
FRIEND_EMAIL = 'friend@example.com'
STRANGER_EMAIL = 'stranger@example.com'


def messages_in(response):
    return [m.message for m in response.context['messages']]


class CollaborationTestCase(TestCase):
    def setUp(self):
        self.owner = User.objects.create(email=OWNER_EMAIL)
        self.friend = User.objects.create(email=FRIEND_EMAIL)
        self.stranger = User.objects.create(email=STRANGER_EMAIL)
        self.private_list = List.objects.create(owner=self.owner)
        self.private_list.shared_with.add(self.friend)
        self.item = Item.objects.create(text='buy milk', list=self.private_list)
        self.public_list = List.objects.create()
        self.public_item = Item.objects.create(text='public item', list=self.public_list)


class ListModelPermissionsTest(CollaborationTestCase):
    def test_public_list_viewable_by_anyone(self):
        from django.contrib.auth.models import AnonymousUser
        self.assertTrue(self.public_list.can_be_viewed_by(AnonymousUser()))
        self.assertTrue(self.public_list.can_be_viewed_by(self.stranger))

    def test_private_list_viewable_by_owner_and_sharees_only(self):
        from django.contrib.auth.models import AnonymousUser
        self.assertTrue(self.private_list.can_be_viewed_by(self.owner))
        self.assertTrue(self.private_list.can_be_viewed_by(self.friend))
        self.assertFalse(self.private_list.can_be_viewed_by(self.stranger))
        self.assertFalse(self.private_list.can_be_viewed_by(AnonymousUser()))

    def test_is_owned_by(self):
        from django.contrib.auth.models import AnonymousUser
        self.assertTrue(self.private_list.is_owned_by(self.owner))
        self.assertFalse(self.private_list.is_owned_by(self.friend))
        self.assertFalse(self.public_list.is_owned_by(AnonymousUser()))

    def test_items_are_not_done_by_default(self):
        self.assertFalse(self.item.done)

    def test_deleting_list_deletes_its_items(self):
        self.private_list.delete()
        self.assertFalse(Item.objects.filter(pk=self.item.pk).exists())


class PrivateListViewTest(CollaborationTestCase):
    def url(self):
        return f'/todo/lists/{self.private_list.id}/'

    def test_owner_can_view(self):
        self.client.force_login(self.owner)
        self.assertContains(self.client.get(self.url()), 'buy milk')

    def test_sharee_can_view(self):
        self.client.force_login(self.friend)
        self.assertContains(self.client.get(self.url()), 'buy milk')

    def test_stranger_gets_404(self):
        self.client.force_login(self.stranger)
        self.assertEqual(self.client.get(self.url()).status_code, 404)

    def test_anonymous_user_gets_404(self):
        self.assertEqual(self.client.get(self.url()).status_code, 404)

    def test_stranger_cannot_add_items(self):
        self.client.force_login(self.stranger)
        response = self.client.post(self.url(), data={'text': 'sneaky'})
        self.assertEqual(response.status_code, 404)
        self.assertFalse(Item.objects.filter(text='sneaky').exists())

    def test_sharee_can_add_items(self):
        self.client.force_login(self.friend)
        self.client.post(self.url(), data={'text': 'eggs'})
        self.assertTrue(self.private_list.item_set.filter(text='eggs').exists())

    def test_public_list_still_viewable_anonymously(self):
        response = self.client.get(f'/todo/lists/{self.public_list.id}/')
        self.assertContains(response, 'public item')

    def test_shows_owner_and_sharees(self):
        self.client.force_login(self.owner)
        response = self.client.get(self.url())
        self.assertContains(response, f'List owner: {OWNER_EMAIL}')
        self.assertContains(response, f'<li class="list-sharee">{FRIEND_EMAIL}</li>', html=True)

    def test_owner_sees_share_and_delete_controls(self):
        self.client.force_login(self.owner)
        response = self.client.get(self.url())
        self.assertContains(response, 'id="id_share_form"')
        self.assertContains(response, 'id="id_delete_list"')

    def test_sharee_does_not_see_share_or_delete_controls(self):
        self.client.force_login(self.friend)
        response = self.client.get(self.url())
        self.assertNotContains(response, 'id="id_share_form"')
        self.assertNotContains(response, 'id="id_delete_list"')

    def test_page_title_uses_list_name(self):
        self.client.force_login(self.owner)
        self.assertContains(self.client.get(self.url()), '<title>buy milk - To-Do lists</title>')


class ToggleItemTest(CollaborationTestCase):
    def toggle(self, item):
        return self.client.post(f'/todo/items/{item.id}/toggle/')

    def test_marks_item_done_then_not_done(self):
        self.toggle(self.public_item)
        self.public_item.refresh_from_db()
        self.assertTrue(self.public_item.done)
        self.toggle(self.public_item)
        self.public_item.refresh_from_db()
        self.assertFalse(self.public_item.done)

    def test_redirects_to_list(self):
        self.assertRedirects(self.toggle(self.public_item), self.public_list.get_absolute_url())

    def test_done_item_is_shown_checked_and_struck_through(self):
        self.toggle(self.public_item)
        response = self.client.get(self.public_list.get_absolute_url())
        self.assertContains(response, 'item-done')
        self.assertContains(response, 'checked')
        self.assertContains(response, '<s class="text-body-secondary">1: public item</s>', html=True)

    def test_get_not_allowed(self):
        response = self.client.get(f'/todo/items/{self.public_item.id}/toggle/')
        self.assertEqual(response.status_code, 405)

    def test_sharee_can_toggle(self):
        self.client.force_login(self.friend)
        self.toggle(self.item)
        self.item.refresh_from_db()
        self.assertTrue(self.item.done)

    def test_stranger_cannot_toggle(self):
        self.client.force_login(self.stranger)
        self.assertEqual(self.toggle(self.item).status_code, 404)
        self.item.refresh_from_db()
        self.assertFalse(self.item.done)

    def test_missing_item_404(self):
        self.assertEqual(self.client.post('/todo/items/999/toggle/').status_code, 404)


class DeleteItemTest(CollaborationTestCase):
    def delete(self, item):
        return self.client.post(f'/todo/items/{item.id}/delete/')

    def test_deletes_item_and_redirects_to_list(self):
        response = self.delete(self.public_item)
        self.assertRedirects(response, self.public_list.get_absolute_url())
        self.assertFalse(Item.objects.filter(pk=self.public_item.pk).exists())

    def test_get_not_allowed(self):
        response = self.client.get(f'/todo/items/{self.public_item.id}/delete/')
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Item.objects.filter(pk=self.public_item.pk).exists())

    def test_stranger_cannot_delete(self):
        self.client.force_login(self.stranger)
        self.assertEqual(self.delete(self.item).status_code, 404)
        self.assertTrue(Item.objects.filter(pk=self.item.pk).exists())

    def test_sharee_can_delete(self):
        self.client.force_login(self.friend)
        self.delete(self.item)
        self.assertFalse(Item.objects.filter(pk=self.item.pk).exists())

    def test_deleted_text_can_be_added_again(self):
        self.delete(self.public_item)
        self.client.post(self.public_list.get_absolute_url(), data={'text': 'public item'})
        self.assertTrue(self.public_list.item_set.filter(text='public item').exists())


class DeleteListTest(CollaborationTestCase):
    def delete(self, our_list):
        return self.client.post(f'/todo/lists/{our_list.id}/delete/')

    def test_owner_can_delete_list(self):
        self.client.force_login(self.owner)
        response = self.delete(self.private_list)
        self.assertRedirects(response, '/todo/lists/mine/')
        self.assertFalse(List.objects.filter(pk=self.private_list.pk).exists())
        self.assertFalse(Item.objects.filter(pk=self.item.pk).exists())

    def test_shows_deleted_message(self):
        self.client.force_login(self.owner)
        response = self.client.post(f'/todo/lists/{self.private_list.id}/delete/', follow=True)
        self.assertIn(LIST_DELETED_MESSAGE, messages_in(response))

    def test_sharee_cannot_delete_list(self):
        self.client.force_login(self.friend)
        self.assertEqual(self.delete(self.private_list).status_code, 404)
        self.assertTrue(List.objects.filter(pk=self.private_list.pk).exists())

    def test_nobody_can_delete_public_list(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.delete(self.public_list).status_code, 404)
        self.assertTrue(List.objects.filter(pk=self.public_list.pk).exists())

    def test_get_not_allowed(self):
        self.client.force_login(self.owner)
        response = self.client.get(f'/todo/lists/{self.private_list.id}/delete/')
        self.assertEqual(response.status_code, 405)


class ShareListTest(CollaborationTestCase):
    def share(self, email, our_list=None, **kwargs):
        our_list = our_list or self.private_list
        return self.client.post(f'/todo/lists/{our_list.id}/share/', data={'sharee': email}, **kwargs)

    def test_owner_can_share_with_existing_user(self):
        self.client.force_login(self.owner)
        response = self.share(STRANGER_EMAIL)
        self.assertRedirects(response, self.private_list.get_absolute_url())
        self.assertIn(self.stranger, self.private_list.shared_with.all())

    def test_sharing_with_new_email_creates_user(self):
        self.client.force_login(self.owner)
        self.share('newbie@example.com')
        newbie = User.objects.get(email='newbie@example.com')
        self.assertIn(newbie, self.private_list.shared_with.all())

    def test_email_is_normalised(self):
        self.client.force_login(self.owner)
        self.share('  Newbie@Example.COM ')
        self.assertTrue(self.private_list.shared_with.filter(email='newbie@example.com').exists())

    def test_sharing_twice_is_harmless(self):
        self.client.force_login(self.owner)
        self.share(FRIEND_EMAIL)
        self.assertEqual(self.private_list.shared_with.count(), 1)

    def test_shows_success_message(self):
        self.client.force_login(self.owner)
        response = self.share(STRANGER_EMAIL, follow=True)
        self.assertIn(f'List shared with {STRANGER_EMAIL}.', messages_in(response))

    def test_cannot_share_with_self(self):
        self.client.force_login(self.owner)
        response = self.share(OWNER_EMAIL, follow=True)
        self.assertIn(SHARE_SELF_ERROR, messages_in(response))
        self.assertFalse(self.private_list.shared_with.filter(pk=self.owner.pk).exists())

    def test_invalid_email_rejected(self):
        self.client.force_login(self.owner)
        response = self.share('not-an-email', follow=True)
        self.assertIn(SHARE_INVALID_EMAIL_ERROR, messages_in(response))
        self.assertEqual(self.private_list.shared_with.count(), 1)

    def test_sharee_cannot_reshare(self):
        self.client.force_login(self.friend)
        self.assertEqual(self.share(STRANGER_EMAIL).status_code, 404)
        self.assertNotIn(self.stranger, self.private_list.shared_with.all())

    def test_public_list_cannot_be_shared(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.share(STRANGER_EMAIL, our_list=self.public_list).status_code, 404)

    def test_shared_list_appears_on_sharees_my_lists(self):
        self.client.force_login(self.friend)
        response = self.client.get('/todo/lists/mine/')
        self.assertContains(response, 'Shared with me')
        self.assertContains(response, self.private_list.get_absolute_url())
        self.assertContains(response, OWNER_EMAIL)

    def test_no_shared_section_when_nothing_shared(self):
        self.client.force_login(self.stranger)
        self.assertNotContains(self.client.get('/todo/lists/mine/'), 'Shared with me')


class ShareListFormTest(TestCase):
    def test_requires_valid_email(self):
        self.assertFalse(ShareListForm(data={'sharee': 'nope'}).is_valid())
        self.assertFalse(ShareListForm(data={'sharee': ''}).is_valid())

    def test_lowercases_email(self):
        form = ShareListForm(data={'sharee': 'A@B.COM'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['sharee'], 'a@b.com')
