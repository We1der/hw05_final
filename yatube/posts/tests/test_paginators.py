from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User

NUM_TEST_POSTS = 15


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.user_author = User.objects.create_user(username='auth_client')
        for i in range(NUM_TEST_POSTS):
            Post.objects.create(
                text='Тестовый текст',
                author=cls.user_author,
                group=cls.group,
            )
        cls.guest_client = Client()

    def test_first_page_contains_ten_records(self):
        names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'auth_client'}),
        ]
        for name in names:
            with self.subTest(name=name):
                response = self.guest_client.get(name)
                # Проверка: количество постов на первой странице равно 10.
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        # Проверка: на второй странице должно быть 5 постов.
        names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'auth_client'}),
        ]
        for name in names:
            with self.subTest(name=name):
                response = self.client.get(name, {'page': 2})
                self.assertEqual(len(response.context['page_obj']), 5)
