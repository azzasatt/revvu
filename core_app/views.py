from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse  # ← ДОБАВЬТЕ ЭТОТ ИМПОРТ
from .models import Post, Comment, UserProfile
from .forms import CustomUserCreationForm, PostForm, UserProfileForm, CommentForm




from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# ============ ГЛАВНАЯ СТРАНИЦА ============
def home_view(request):
    """Главная страница со всеми постами"""
    posts = Post.objects.all().order_by('-created_at')
    return render(request, 'home.html', {'posts': posts})

# ============ АУТЕНТИФИКАЦИЯ ============
def register_view(request):
    """Регистрация нового пользователя"""
    if request.user.is_authenticated:
        return redirect('core_app:home')

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}!')
            return redirect('core_app:home')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'register.html', {'form': form})


def login_view(request):
    """Вход в систему"""
    if request.user.is_authenticated:
        return redirect('core_app:home')

    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'С возвращением, {user.username}!')
            return redirect('core_app:home')
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    """Выход из системы"""
    logout(request)
    messages.info(request, 'Вы вышли из системы.')
    return redirect('core_app:login_view')

# ============ ПРОФИЛЬ ============
def profile_view(request, username=None):
    """Просмотр профиля пользователя"""
    if username:
        user = get_object_or_404(User, username=username)
    else:
        # Если username не указан, показываем профиль текущего пользователя
        if not request.user.is_authenticated:
            return redirect('core_app:login_view')
        user = request.user
    
    posts = Post.objects.filter(user=user).order_by('-created_at')
    
    return render(request, 'profile.html', {
        'profile_user': user,
        'posts': posts,
        'post_count': posts.count()
    })


@login_required
def edit_profile_view(request):
    """Редактирование профиля"""
    user = request.user
    
    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST, request.FILES, instance=user.profile)
        
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('core_app:profile', username=user.username)
    else:
        profile_form = UserProfileForm(instance=user.profile)
    
    return render(request, 'edit_profile.html', {
        'profile_form': profile_form,
    })

# ============ ПОСТЫ ============
def post_detail(request, post_id):
    """Детали поста с комментариями"""
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all()
    
    if request.method == 'POST' and request.user.is_authenticated:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.user = request.user
            comment.save()
            return redirect('core_app:post_detail', post_id=post.id)
    else:
        comment_form = CommentForm()
    
    return render(request, 'post_detail.html', {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
    })


@login_required
def post_create(request):
    """Создание нового поста"""
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            messages.success(request, 'Пост успешно создан!')
            return redirect('core_app:post_detail', post_id=post.id)
    else:
        form = PostForm()
    
    return render(request, 'post_form.html', {'form': form})


@login_required
def post_edit(request, post_id):
    """Редактирование существующего поста"""
    post = get_object_or_404(Post, id=post_id)
    
    if request.user != post.user:
        messages.error(request, 'Вы не можете редактировать этот пост.')
        return redirect('core_app:post_detail', post_id=post.id)
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Пост успешно обновлен!')
            return redirect('core_app:post_detail', post_id=post.id)
    else:
        form = PostForm(instance=post)
    
    return render(request, 'post_form.html', {'form': form, 'post': post})


@login_required
def post_delete(request, post_id):
    """Удаление поста"""
    post = get_object_or_404(Post, id=post_id)
    
    if request.user != post.user:
        messages.error(request, 'Вы не можете удалить этот пост.')
        return redirect('core_app:post_detail', post_id=post.id)
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Пост успешно удален!')
        return redirect('core_app:profile', username=request.user.username)
    
    return render(request, 'post_delete.html', {'post': post})

# ============ КОММЕНТАРИИ ============
@login_required
def add_comment(request, post_id):
    """Добавление комментария"""
    post = get_object_or_404(Post, id=post_id)
    
    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.user = request.user
            comment.save()
            messages.success(request, 'Комментарий добавлен!')
    
    return redirect('core_app:post_detail', post_id=post.id)


@login_required
def delete_comment(request, comment_id):
    """Удаление комментария"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    if request.user != comment.user:
        messages.error(request, 'Вы не можете удалить этот комментарий.')
        return redirect('core_app:post_detail', post_id=comment.post.id)
    
    if request.method == 'POST':
        post_id = comment.post.id
        comment.delete()
        messages.success(request, 'Комментарий удален!')
        return redirect('core_app:post_detail', post_id=post_id)
    
    return render(request, 'comment_delete.html', {'comment': comment})



@login_required
def like_post(request, post_id):
    """Обработка лайков через AJAX"""
    print(f"Like post {post_id} - Method: {request.method}")  # Для отладки
    print(f"User: {request.user}")  # Для отладки
    print(f"Headers: {dict(request.headers)}")  # Для отладки
    
    if request.method == 'POST':
        try:
            post = Post.objects.get(id=post_id)
            
            if request.user in post.likes.all():
                post.likes.remove(request.user)
                liked = False
            else:
                post.likes.add(request.user)
                liked = True
            
            return JsonResponse({
                'success': True,
                'liked': liked,
                'likes_count': post.likes.count()
            })
            
        except Post.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Post not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    # Если не POST, все равно обрабатываем (для тестирования)
    print("Not a POST request, but processing anyway for testing")
    try:
        post = Post.objects.get(id=post_id)
        
        if request.user in post.likes.all():
            post.likes.remove(request.user)
            liked = False
        else:
            post.likes.add(request.user)
            liked = True
        
        return JsonResponse({
            'success': True,
            'liked': liked,
            'likes_count': post.likes.count()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)