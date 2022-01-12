from django.urls import path

from . import views

app_name = 'posts'

urlpatterns = [
    # Главная страница
    path('', views.index, name='index'),
    # Страница сообществ
    path('group/<slug:slug>/', views.group_posts, name='group_posts'),
    # Профайл пользователя
    path('profile/<str:username>/', views.profile, name='profile'),
    # Просмотр записи
    path('posts/<int:post_id>/', views.post_detail, name='post_detail'),
    # Создание записи
    path('create/', views.post_create, name='post_create'),
    # Редактирование записи
    path('posts/<int:post_id>/edit/', views.post_edit, name='post_edit'),
    # Добавление комментария к записи
    path(
        'posts/<int:post_id>/comment/',
        views.add_comment,
        name='add_comment'
    ),
    # Список постов по подписке
    path('follow/', views.follow_index, name='follow_index'),
    # Подписка на пост
    path(
        'profile/<str:username>/follow/',
        views.profile_follow,
        name='profile_follow'
    ),
    # Отписка на пост
    path(
        'profile/<str:username>/unfollow/',
        views.profile_unfollow,
        name='profile_unfollow'
    ),
    # Лайк/дизлайк поста
    path(
        'posts/<int:post_id>/like/',
        views.post_like,
        name='post_like'
    ),
    # Дизлайк поста
    path(
        'posts/<int:post_id>/dislike/',
        views.post_dislike,
        name='post_dislike'
    ),
]
