from django.test import TestCase
from posts.models import Comment, Follow, Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user2 = User.objects.create_user(username='auth2')

        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.user2,
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тест коммент'
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = PostModelTest.group
        post = PostModelTest.post
        comment = PostModelTest.comment
        follow = PostModelTest.follow
        models_str = {
            group: 'Тестовая группа',
            post: 'Тестовый пост',
            comment: 'Тест коммент',
            follow: f'{self.user.username} -> {self.user2.username}',
        }
        for model, expected_value in models_str.items():
            with self.subTest(model=model):
                self.assertEqual(str(model), expected_value)

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        comment = PostModelTest.comment
        follow = PostModelTest.follow
        field_verboses = {
            post: {
                'text': 'Текст поста',
                'pub_date': 'Дата публикации',
                'author': 'Автор',
                'group': 'Группа',
            },
            comment: {
                'post': 'Пост комментария',
                'author': 'Автор',
                'created': 'Дата публикации комментария',
            },
            follow: {
                'user': 'Пользователь',
                'author': 'Автор',
            },
        }
        for model in field_verboses.keys():
            for field, expected_value in field_verboses[model].items():
                with self.subTest(field=field):
                    self.assertEqual(
                        model._meta.get_field(field).verbose_name,
                        expected_value
                    )

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        comment = PostModelTest.comment
        field_help_texts = {
            post: {
                'text': 'Введите текст поста',
                'group': 'Группа, к которой будет относиться пост',
            },
            comment: {
                'text': 'Введите текст комментария',
            }
        }
        for model in field_help_texts.keys():
            for field, expected_value in field_help_texts[model].items():
                with self.subTest(field=field):
                    self.assertEqual(
                        model._meta.get_field(field).help_text, expected_value
                    )
