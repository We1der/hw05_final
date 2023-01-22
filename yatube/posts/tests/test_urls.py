from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.user_author = User.objects.create_user(username='auth_client')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user_author,
            group=cls.group,
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованых клиентов (обычного и автора поста)
        self.authorized_client = Client()
        self.user = User.objects.create_user(username='not_author_client')
        self.authorized_client.force_login(self.user)

        self.authorized_author_client = Client()
        self.authorized_author_client.force_login(PostURLTests.user_author)

    def test_not_authorized_urls_exists(self):
        """Страницы доступные для не авторизованных пользователей"""
        urls = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'auth_client'}),
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page(self):
        """Переход на несуществующую страницу вернет ошибку 404"""
        response = self.guest_client.get('/test_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': 'not_author_client'}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
                'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
                'posts/create_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_author_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_redirect_not_auth_client(self):
        """Перенаправление неавторизованного пользователя на страницу входа"""
        urls = [
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            reverse('posts:post_create'),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertRedirects(
                    response,
                    f'/auth/login/?next={url}'
                )
