from django.urls import path
from app import views

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.landing_page, name='landing'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('upload/', views.upload_view, name='upload'),
    path('file/<int:file_id>/', views.file_detail, name='file_detail'),
    path('purchase/<int:file_id>/', views.purchase_file, name='purchase'),
    path('profile/<str:username>/', views.user_profile, name='user_profile'),
    path('admin_panel/', views.admin_panel, name='admin_panel'),
    path('admin_detail/file/<int:file_id>/', views.admin_file_detail, name='admin_file_detail'),
    path('approve/<int:file_id>/', views.approve_file, name='approve_file'),
    path('reject/<int:file_id>/', views.reject_file, name='reject_file'),
    path('ban/<int:user_id>/', views.ban_user, name='ban_user'),
    path('profiles/', views.profile_list_view, name='profile_list'),
    path('brands/', views.brand_list_view, name='brand_list'),
    path('protected-file/<int:file_id>/', views.protected_file_view, name='protected_file'),
    path('file/<int:file_id>/comments/', views.file_comments, name='file_comments'),
    path('comments/', views.comments_list, name='comments_list'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)