from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('title', 'text', 'group', 'image')
        labels = {'title': 'Заголовок',
                  'text': 'Текст поста',
                  'group': 'Группа',
                  }
        help_texts = {
            'title': 'Название поста',
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
