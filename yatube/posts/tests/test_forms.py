import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()

# Создаем временную папку для медиа-файлов;
# на момент теста медиа папка будет переопределена
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


# Для сохранения media-файлов в тестах будет использоваться
# временная папка TEMP_MEDIA_ROOT, а потом мы ее удалим
@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент
        self.user = User.objects.create_user(username='AngelNad')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        # Для тестирования загрузки изображений
        # берём байт-последовательность картинки,
        # состоящей из двух пикселей: белого и чёрного
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
        form_data = {
            'text': 'Тестовый текст',
            'group': PostFormTests.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        expected_redirect = reverse('posts:profile',
                                    args={self.user})
        self.assertRedirects(response, expected_redirect)
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(response.context['page_obj'][0].text,
                         form_data['text'])
        self.assertEqual(response.context['page_obj'][0].group.id,
                         form_data['group'])
        self.assertEqual(response.context['page_obj'][0].author,
                         self.user)
        # Проверяем, что при отправке поста с картинкой
        # создаётся запись в базе данных
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                image=f'posts/{uploaded.name}',
                group=PostFormTests.group.id
            ).exists()
        )

    def test_edit_post(self):
        form_data = {
            'text': 'Изменённый текст',
            'group': PostFormTests.group.id,
        }
        posts_count = Post.objects.count()
        response = self.author_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostFormTests.post.pk}),
            data=form_data, follow=True
        )
        expected_redirect = reverse(
            'posts:post_detail', kwargs={'post_id': PostFormTests.post.pk})
        self.assertRedirects(response, expected_redirect)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(Post.objects.filter(text=form_data['text']).exists())

    def test_not_create_post_and_redirect_on_admin_login_for_anonymous(self):
        # Проверяем невозможность опубликования поста
        # для неавторизованного пользователя
        form_data = {
            'text': 'Тестовый текст',
            'group': PostFormTests.group.id,
        }
        posts_count = Post.objects.count()
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        rdr = reverse('users:login') + '?next=' + reverse('posts:post_create')
        self.assertRedirects(response, rdr)
        self.assertEqual(Post.objects.count(), posts_count)

    def test_add_comment_auth_user_appears_at_desired_location(self):
        # проверяем создание комментария авторизованным пользователем
        # на странице другого пользователя,
        comments_count = Comment.objects.count()
        post = Post.objects.create(
            text='Текст поста для теста комментария',
            author=self.user,
            group=self.group,
        )
        form_data = {
            'text': 'Тестовый комментарий поста',
            'post': PostFormTests.post,
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.pk}),
            data=form_data,
            follow=True
        )
        comments_count2 = Comment.objects.count()
        self.assertEqual(comments_count2, comments_count + 1)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': post.pk})
        )
        self.assertEqual(response.context['post_comments'][0].text,
                         form_data['text'])

    def test_not_add_comment_anonymous_user(self):
        # проверяем, что комментарий неавторизованного пользователя
        # не создается и происходит редирект на страницу логина
        comments_count = Comment.objects.count()
        post = Post.objects.create(
            text='Текст поста для теста комментария',
            author=self.user,
            group=self.group,
        )
        form_data = {
            'text': 'Тестовый комментарий поста',
            'post': PostFormTests.post,
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.pk}),
            data=form_data,
            follow=True
        )
        rdr_expected = reverse('users:login'
                               ) + '?next=' + reverse(
            'posts:add_comment', kwargs={'post_id': post.pk})
        self.assertRedirects(response, rdr_expected)
        self.assertEqual(Comment.objects.count(), comments_count)
