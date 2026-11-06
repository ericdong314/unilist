from unittest import skip

import lxml.html
from django.db.transaction import TransactionManagementError
from django.test import TestCase
from django.utils import html
from django.urls import reverse

from todolist.forms import EMPTY_ITEM_ERROR, DUPLICATE_ITEM_ERROR
from acc.models import User
from todolist.models import List, Item


class HomePageTest(TestCase):
    def test_uses_home_template(self):
        response = self.client.get('/todo/')
        self.assertTemplateUsed(response, 'todolist/home.html')

    def test_renders_homepage_content(self):
        response = self.client.get('/todo/')
        self.assertContains(response, 'To-Do')

    def test_renders_input_form(self):
        response = self.client.get("/todo/")
        parsed = lxml.html.fromstring(response.content)
        forms = parsed.cssselect("form[method=post]")
        self.assertIn("/todo/lists/new/", [form.get("action") for form in forms])
        [form] = [form for form in forms if form.get("action") == "/todo/lists/new/"]
        inputs = form.cssselect("input")
        self.assertIn("text", [input.get("name") for input in inputs])


class NewListTest(TestCase):
    def test_can_save_post_request(self):
        self.client.post('/todo/lists/new/', {'text': 'A new item.'})
        self.assertEqual(Item.objects.count(), 1)
        self.assertEqual(Item.objects.last().text, 'A new item.')

    def test_redirect_after_post_request(self):
        response = self.client.post('/todo/lists/new/', {'text': 'A new item.'})
        list_created = List.objects.get()
        self.assertRedirects(response, f'/todo/lists/{list_created.id}/')

    def send_invalid_post(self):
        return self.client.post("/todo/lists/new/", data={"text": ""})

    def test_invalid_post_db_not_save(self):
        self.send_invalid_post()
        self.assertEqual(List.objects.count(), 0)
        self.assertEqual(Item.objects.count(), 0)

    def test_invalid_post_handled_using_correct_template(self):
        response = self.send_invalid_post()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "todolist/home.html")

    def test_invalid_post_error_msg(self):
        response = self.send_invalid_post()
        expected_error = html.escape(EMPTY_ITEM_ERROR)
        self.assertContains(response, expected_error)

    def test_for_invalid_input_sets_is_invalid_class(self):
        response = self.send_invalid_post()
        parsed = lxml.html.fromstring(response.content)
        [input] = parsed.cssselect("input[name=text]")
        self.assertIn("is-invalid", set(input.classes))


class ListViewTest(TestCase):
    def test_uses_list_view_template(self):
        my_list = List.objects.create()
        response = self.client.get(f'/todo/lists/{my_list.id}/')
        self.assertTemplateUsed(response, 'todolist/list.html')

    def test_renders_input_form(self):
        mylist = List.objects.create()
        url = f"/todo/lists/{mylist.id}/"
        response = self.client.get(url)
        parsed = lxml.html.fromstring(response.content)
        forms = parsed.cssselect("form[method=post]")
        self.assertIn(url, [form.get("action") for form in forms])
        [form] = [form for form in forms if form.get("action") == url]
        inputs = form.cssselect("input")
        self.assertIn('text', [input.get("name") for input in inputs])

    def test_display_only_items_on_that_list(self):
        # Arrange/Given
        mylist = List.objects.create()
        Item.objects.create(text='foo', list=mylist)
        Item.objects.create(text='bar', list=mylist)

        another_list = List.objects.create()
        Item.objects.create(text='I should be on another_list', list=another_list)

        # Act/When
        response = self.client.get(f'/todo/lists/{mylist.id}/')

        # Assert/Then
        self.assertContains(response, 'foo')
        self.assertContains(response, 'bar')
        self.assertNotContains(response, 'I should be on another_list')

    def test_can_save_post_request_to_an_existing_list(self):
        mylist = List.objects.create()
        self.client.post(f'/todo/lists/{mylist.id}/', {'text': 'first item.'})
        self.client.post(f'/todo/lists/{mylist.id}/', {'text': 'second item.'})
        self.assertEqual(Item.objects.filter(list=mylist).count(), 2)

    def test_redirect_after_post_request(self):
        mylist = List.objects.create()
        otherlist = List.objects.create()  # test for silliness
        response = self.client.post(f'/todo/lists/{mylist.id}/', {'text': 'A new item.'})
        self.assertRedirects(response, f'/todo/lists/{mylist.id}/')

    def send_invalid_post(self):
        mylist = List.objects.create()
        return self.client.post(f"/todo/lists/{mylist.id}/", data={"text": ""})

    def test_invalid_post_nothing_saved_to_db(self):
        self.send_invalid_post()
        self.assertEqual(Item.objects.count(), 0)

    def test_invalid_post_handled_with_list_template(self):
        response = self.send_invalid_post()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "todolist/list.html")

    def test_invalid_post_gets_error_msg(self):
        response = self.send_invalid_post()
        expected_error = html.escape(EMPTY_ITEM_ERROR)
        self.assertContains(response, expected_error)

    def try_to_create_a_duplicate_item(self):
        unique_text = 'I want to be unique.'
        mylist = List.objects.create()
        Item.objects.create(text=unique_text, list=mylist)
        return self.client.post(reverse('todolist:view_list', args=[mylist.id]), data={'text': unique_text})

    def test_duplicate_item_saves_not_to_db(self):
        self.try_to_create_a_duplicate_item()
        self.assertEqual(Item.objects.count(), 1)

    def test_duplicate_item_creation_handled_with_list_template(self):
        response = self.try_to_create_a_duplicate_item()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'todolist/list.html')

    def test_duplicate_item_creation_gets_error_msg(self):
        response = self.try_to_create_a_duplicate_item()
        expected_error = html.escape(DUPLICATE_ITEM_ERROR)
        self.assertContains(response, expected_error)


class ListViewNotFoundTest(TestCase):
    def test_missing_list_returns_404(self):
        response = self.client.get('/todo/lists/999/')
        self.assertEqual(response.status_code, 404)

    def test_post_to_missing_list_returns_404(self):
        response = self.client.post('/todo/lists/999/', data={'text': 'x'})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Item.objects.count(), 0)


class NewListOwnershipTest(TestCase):
    def test_get_not_allowed(self):
        response = self.client.get('/todo/lists/new/')
        self.assertEqual(response.status_code, 405)

    def test_list_owner_is_saved_if_user_is_authenticated(self):
        user = User.objects.create(email='a@b.com')
        self.client.force_login(user)
        self.client.post('/todo/lists/new/', data={'text': 'new item'})
        self.assertEqual(List.objects.get().owner, user)

    def test_list_has_no_owner_if_user_is_anonymous(self):
        self.client.post('/todo/lists/new/', data={'text': 'new item'})
        self.assertIsNone(List.objects.get().owner)


class MyListsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(email='a@b.com')

    def test_redirects_anonymous_user_to_home(self):
        response = self.client.get('/todo/lists/mine/')
        self.assertRedirects(response, '/todo/')

    def test_uses_my_lists_template(self):
        self.client.force_login(self.user)
        response = self.client.get('/todo/lists/mine/')
        self.assertTemplateUsed(response, 'todolist/my_lists.html')

    def test_shows_only_the_users_own_lists(self):
        mine = List.objects.create(owner=self.user)
        Item.objects.create(text='my item', list=mine)
        theirs = List.objects.create(owner=User.objects.create(email='x@y.com'))
        Item.objects.create(text='their item', list=theirs)
        self.client.force_login(self.user)
        response = self.client.get('/todo/lists/mine/')
        self.assertContains(response, 'my item')
        self.assertContains(response, mine.get_absolute_url())
        self.assertNotContains(response, 'their item')

    def test_shows_message_when_no_lists(self):
        self.client.force_login(self.user)
        response = self.client.get('/todo/lists/mine/')
        self.assertContains(response, "You don't have any lists yet.")

    def test_navbar_links_to_my_lists_when_logged_in(self):
        self.client.force_login(self.user)
        response = self.client.get('/todo/')
        self.assertContains(response, 'href="/todo/lists/mine/"')
