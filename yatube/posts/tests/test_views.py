import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
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
            image=uploaded,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            text='Тестовый текст поста',
            author=cls.user_author,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Создаём неавторизованный клиент
        self.guest_client = Client()
        # Создаём авторизованный клиент
        self.user = User.objects.create_user(username='not_author_client')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # Создаём авторизованный автор клиент
        self.authorized_author_client = Client()
        self.authorized_author_client.force_login(PostPagesTests.user_author)

        cache.clear()

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "имя_html_шаблона: reverse(name)"
        templates_page_names = {
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
        # Проверяем, что при обращении к name
        # вызывается соответствующий HTML-шаблон
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = (self.authorized_client.get(reverse('posts:index')))
        self.assertEqual(response.context.get('page_obj')[0], self.post)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'})))
        self.assertEqual(response.context.get('group'), self.group)
        self.assertEqual(response.context.get('page_obj')[0], self.post)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'auth_client'})))
        self.assertEqual(response.context.get('author'), self.user_author)
        self.assertEqual(response.context.get('page_obj')[0], self.post)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})))
        self.assertEqual(response.context.get('post'), self.post)
        # Проверка комментарий появляется на странице поста
        self.assertEqual(response.context.get('comments')[0], self.comment)
        # Проверка изображение передается в context
        self.assertEqual(response.context.get('post').image, self.post.image)

    def test_forms_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = (self.authorized_author_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_forms_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = (self.authorized_author_client.get(
            reverse('posts:post_create')))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_pages_img_in_context(self):
        """Изображение передается в словаре context"""
        urls = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'auth_client'}),
        ]
        for url in urls:
            response = self.authorized_author_client.get(url)
            with self.subTest(response=response):
                self.assertEqual(
                    response.context.get('page_obj')[0].image, self.post.image
                )

    def test_index_cache(self):
        """Кэш работает на главной странице"""
        url_index = reverse('posts:index')
        response = self.authorized_author_client.get(url_index)
        content_response = response.content
        # Создаём пост
        self.authorized_author_client.post(
            reverse('posts:post_create'),
            data={'text': 'Тестовый текст cache'},
            follow=True
        )
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст cache',
            ).exists()
        )

        create_response = self.authorized_author_client.get(url_index)
        create_response_content = create_response.content
        self.assertEqual(content_response, create_response_content)

        cache.clear()
        clear_response = self.authorized_author_client.get(url_index)
        clear_response_content = clear_response.content
        # print(clear_response_content)
        self.assertNotEqual(content_response, clear_response_content)

    def test_auth_user_follow(self):
        """Подписка на автора"""
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user_author.username})
        )
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=self.user_author,
            ).exists()
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(response.context.get('page_obj')[0], self.post)

    def test_auth_user_unfollow(self):
        """Отписка от автора"""
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.user_author.username})
        )
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.user_author,
            ).exists()
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertListEqual(response.context.get('page_obj').object_list, [])
