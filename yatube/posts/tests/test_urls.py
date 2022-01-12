from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Описание тестовой группы'
        )
        Post.objects.create(
            text='Тестовый текст поста',
            author=cls.author,
            group=cls.group,
            pk=61,
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент
        self.user = User.objects.create_user(username='AngelNad')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.author)
        cache.clear()

    # Проверяем общедоступные страницы
    def test_urls_exists_all_user_at_desired_location(self):
        urls = {
            '/',
            '/group/test-slug/',
            '/profile/auth/',
            '/posts/61/',
        }
        for address in urls:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_url_unexists_at_desired_location(self):
        """Страница /unexisting_page/ доступна любому пользователю."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    # Проверяем доступность страниц для авторизованного пользователя
    def test_post_create_url_exists_at_desired_location(self):
        """Страницы /create/ и /follow/ доступны авториз. пользователю."""
        urls = {
            '/create/',
            '/follow/',
        }
        for address in urls:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_exists_at_desired_location_authorized(self):
        """Страница /posts/61/edit/ доступна автору."""
        response = self.author_client.get('/posts/61/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_urls_uses_correct_template(self):
        """URL-адрес /posts/61/edit/ использует соответствующий шаблон."""
        response = self.author_client.get('/posts/61/edit/')
        self.assertTemplateUsed(response, 'posts/create_post.html')

    # Проверяем редирект для авторизованного пользователя при подписке на себя
    def test_url_redirect_authorized_user_on_profile_yourself(self):
        response = self.author_client.get('/profile/auth/follow/')
        self.assertRedirects(response, '/profile/auth/')

    # Проверяем редиректы для неавторизованного пользователя
    def test_url_redirect_anonymous_on_admin_login(self):
        urls_redirect = {
            '/create/': '/auth/login/?next=/create/',
            '/posts/61/edit/': '/auth/login/?next=/posts/61/edit/',
            '/posts/61/comment/': '/auth/login/?next=/posts/61/comment/',
            '/profile/auth/follow/': '/auth/login/?next=/profile/auth/follow/',
            '/profile/auth/unfollow/':
                '/auth/login/?next=/profile/auth/unfollow/',
        }
        for url, redirect in urls_redirect.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, redirect)

    # Проверка вызываемых шаблонов для каждого адреса
    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/auth/': 'posts/profile.html',
            '/posts/61/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
