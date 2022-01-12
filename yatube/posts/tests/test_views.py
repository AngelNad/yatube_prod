from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from yatube.settings import PAGE_COUNT

from ..models import Follow, Group, Post

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Описание тестовой группы'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.author,
            group=cls.group,
            pk=61,
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент для 1-го пользователя
        self.user = User.objects.create_user(username='AngelNad')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # Создаем авторизованый клиент для 2-го пользователя
        self.user2 = User.objects.create_user(username='Neo')
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)
        # Создаем авторизованый клиент для автора
        self.author_client = Client()
        self.author_client.force_login(self.author)
        cache.clear()

    # Проверяем используемые шаблоны
    def test_all_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "reverse(name): имя_html_шаблона"
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_posts',
                    kwargs={'slug': 'test-slug'}): 'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': 'auth'}):
                'posts/profile.html',
            reverse('posts:post_detail', args={61}): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', args={61}): 'posts/create_post.html',
        }
        # Проверяем, что при обращении к name
        # вызывается соответствующий HTML-шаблон
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                if reverse_name == reverse('posts:post_edit', args={61}):
                    response = self.author_client.get(reverse_name)
                else:
                    response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def check_context_contains_page(self, context, post=False):
        """Создаём метод проверки наполнения поста"""
        if post:
            self.assertIn('post_user', context)
            post = context['post_user']
        else:
            self.assertIn('page_obj', context)
            post = context['page_obj'][0]
        self.assertEqual(post.text, PostPagesTests.post.text)
        self.assertEqual(post.author, PostPagesTests.author)
        self.assertEqual(post.group, PostPagesTests.group)

    def test_page_show_correct_context(self):
        """Шаблон сформирован с правильным контекстом."""
        names_pages = {
            (reverse('posts:index'), False),
            (reverse('posts:group_posts',
                     kwargs={'slug': 'test-slug'}), False),
            (reverse('posts:profile', kwargs={'username': 'auth'}), False),
            (reverse('posts:post_detail', args={61}), True),
        }
        for name, post_check in names_pages:
            with self.subTest(name=name):
                response = self.guest_client.get(name)
                self.check_context_contains_page(response.context, post_check)

    def test_create_post_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response1 = self.authorized_client.get(reverse('posts:post_create'))
        response2 = self.author_client.get(reverse('posts:post_edit',
                                                   args={61}))
        var_response = (response1, response2)
        # Словарь ожидаемых типов полей формы:
        # указываем, объектами какого класса должны быть поля формы
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        # Проверяем, что типы полей формы в словаре context
        # соответствуют ожиданиям
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                for response in var_response:
                    form_field = response.context.get('form').fields.get(value)
                    # Проверяет, что поле формы является экземпляром
                    # указанного класса
                    self.assertIsInstance(form_field, expected)

    def test_new_post_with_group_appears_at_desired_location(self):
        posts_count = Post.objects.count()
        Post.objects.create(
            text='Тестовый текст поста',
            author=PostPagesTests.author,
            group=PostPagesTests.group,
            pk=62,
        )
        list_urls = {
            reverse('posts:index'),
            reverse('posts:group_posts',
                    kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'auth'})
        }
        posts_count_after = Post.objects.count()
        self.assertEqual(posts_count_after, posts_count + 1)
        for urls in list_urls:
            response = self.client.get(urls)
            self.assertIn('page_obj', response.context)
        response = self.client.get(reverse('posts:group_posts',
                                           kwargs={'slug': 'leo'}))
        self.assertNotIn('page_obj', response.context)

    def test_image_exists_new_create_post(self):
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        post = Post.objects.create(
            text='Текст поста с картинкой',
            author=self.user,
            group=self.group,
            image=uploaded,
        )
        urls = (
            reverse('posts:index'),
            reverse('posts:profile', args={self.user}),
            reverse('posts:group_posts',
                    kwargs={'slug': 'test-slug'}),
            reverse('posts:post_detail', kwargs={'post_id': post.id}),
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                if url == reverse('posts:post_detail',
                                  kwargs={'post_id': post.id}):
                    self.assertEqual(response.context['post_user'].image,
                                     post.image)
                else:
                    self.assertEqual(response.context['page_obj'][0].image,
                                     post.image)
                # Вариант проверки через assertContains
                # (в задании именно через словарь context, поэтому код выше)
                # self.assertContains(response, '<img')

    def test_cash_index(self):
        posts_count = Post.objects.count()
        post_new = Post.objects.create(
            text='Тестовый cash текст поста',
            author=self.user,
            group=PostPagesTests.group,
        )
        response = self.author_client.get(reverse('posts:index'))
        response_count = len(response.context['page_obj'])
        self.assertEqual(posts_count + 1, response_count)
        self.assertEqual(response.context['page_obj'][0].text,
                         post_new.text)
        self.assertEqual(response.context['page_obj'][0].group,
                         post_new.group)
        self.assertEqual(response.context['page_obj'][0].author,
                         post_new.author)
        page_cached = response.content
        post_new.delete()
        response = self.author_client.get(reverse('posts:index'))
        self.assertEqual(page_cached, response.content)
        cache.clear()
        response = self.author_client.get(reverse('posts:index'))
        self.assertNotEqual(page_cached, response.content)
        response_count_last = len(response.context['page_obj'])
        self.assertEqual(posts_count, response_count_last)

    def test_authorized_user_follow(self):
        # проверяем, что авторизованный пользователь
        # может подписываться на других пользователей
        url_follow = reverse('posts:profile_follow', args={self.author})
        url_profile = reverse('posts:profile', args={self.author})
        response = self.authorized_client.get(url_follow)
        self.assertRedirects(response, url_profile)
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=self.author,
            ).exists()
        )

    def test_authorized_user_unfollow_other_author(self):
        # проверяем, что авторизованный пользователь
        # может удалять других пользователей из своих подписок
        Follow.objects.create(user=self.user, author=self.author)
        url_profile = reverse('posts:profile', args={self.author})
        url_unfollow = reverse('posts:profile_unfollow', args={self.author})
        response_unfollow = self.authorized_client.get(url_unfollow)
        self.assertRedirects(response_unfollow, url_profile)
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.author,
            ).exists()
        )

    def test_new_post_appears_following_user_page(self):
        following = Follow.objects.create(user=self.user, author=self.author)
        url_following = reverse('posts:follow_index')
        text_new_post = 'Текст поста для подписки'
        new_post = Post.objects.create(text=text_new_post, author=self.author)
        self.assertTrue(
            Post.objects.filter(
                text=text_new_post,
                author=self.author).exists()
        )
        # проверяем, что в ленте подписанного user пост есть
        response = self.authorized_client.get(url_following)
        new_post_from_context = response.context['page_obj'][0]
        self.assertContains(response, new_post_from_context)
        # удаляем подписку user и новый пост
        following.delete()
        new_post.delete()

    def test_new_post_not_appears_following_other_user_page(self):
        following = Follow.objects.create(user=self.user, author=self.author)
        url_following = reverse('posts:follow_index')
        text_new_post = 'Текст поста для подписки'
        new_post = Post.objects.create(text=text_new_post, author=self.author)
        self.assertTrue(
            Post.objects.filter(
                text=text_new_post,
                author=self.author).exists()
        )
        # проверяем, что в ленте у неподписанного user2 поста нет
        response = self.authorized_client2.get(url_following)
        self.assertEqual(response.context['page_obj'].object_list.count(), 0)
        # удаляем подписку user и новый пост
        following.delete()
        new_post.delete()


class PaginatorViewsTest(TestCase):
    # Здесь создаются фикстуры: клиент и 13 тестовых записей.
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.count_new_post = 13
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Описание тестовой группы'
        )

        for n in range(cls.count_new_post):
            cls.post = Post.objects.create(
                text=f'Тестовая запись {n}',
                author=cls.user,
                group=cls.group,
            )
            cache.clear()

    def test_paginator_page_contains_page_count_records(self):
        list_urls = (
            reverse('posts:index'),
            reverse('posts:group_posts',
                    kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'auth'})
        )
        for url in list_urls:
            response1 = self.client.get(url)
            self.assertEqual(len(response1.context['page_obj']), PAGE_COUNT)
            response2 = self.client.get(reverse('posts:index') + '?page=2')
            self.assertEqual(len(response2.context['page_obj']),
                             PaginatorViewsTest.count_new_post - PAGE_COUNT)
            cache.clear()


class ErrorTestClass(TestCase):
    def setUp(self):
        self.client = Client()

    def test_error_page(self):
        response = self.client.get('/nonexist-page/')
        # Проверяется, что статус ответа сервера - 404
        self.assertEqual(response.status_code, 404)
        # Проверяется, что используется шаблон core/404.html
        self.assertTemplateUsed(response, 'core/404.html')
