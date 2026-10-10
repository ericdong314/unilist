from unittest import skip

import lxml.html
from django.db.transaction import TransactionManagementError
from django.test import TestCase
from django.utils import html
from django.urls import reverse

from todolist.forms import EMPTY_ITEM_ERROR, DUPLICATE_ITEM_ERROR
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
