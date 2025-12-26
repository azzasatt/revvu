from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

# ============ ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ ============
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True, verbose_name='Биография')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='Аватар')
    website = models.URLField(blank=True, verbose_name='Веб-сайт')
    instagram = models.CharField(max_length=100, blank=True, verbose_name='Instagram')
    location = models.CharField(max_length=100, blank=True, verbose_name='Местоположение')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'

    def __str__(self):
        return f'Профиль {self.user.username}'

# Сигналы для автоматического создания профиля
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

# ============ ПОСТЫ ============
class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts', verbose_name='Автор')
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    content = models.TextField(verbose_name='Описание')
    image = models.ImageField(upload_to='posts/', blank=True, null=True, verbose_name='Изображение')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    views = models.IntegerField(default=0, verbose_name='Просмотры')
    
    # Поле для лайков - МНОГИЕ КО МНОГИМ
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True, verbose_name='Лайки')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'
    
    def __str__(self):
        return f'{self.title} - {self.user.username}'
    
    # Метод для получения количества лайков
    def get_likes_count(self):
        return self.likes.count()
    
    # Метод для проверки, лайкнул ли пользователь пост
    def is_liked_by_user(self, user):
        if user.is_authenticated:
            return self.likes.filter(id=user.id).exists()
        return False

# ============ КОММЕНТАРИИ ============
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', verbose_name='Пост')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Автор')
    content = models.TextField(verbose_name='Текст комментария')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
    
    def __str__(self):
        return f'Комментарий от {self.user.username} к "{self.post.title[:30]}..."'