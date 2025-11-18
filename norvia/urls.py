"""
URL configuration for norvia project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('account/', include('account.urls')),
    path('', include('interface.urls')),
    path('control/', include('manager.urls')),

    # 1. Password Reset (User enters email)
    path('password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='account/forgot_password.html',
            email_template_name='account/password_reset_email.txt',   # plain text fallback
            html_email_template_name='account/password_reset_email.html',  # HTML email
            subject_template_name='account/password_reset_subject.txt',
            success_url='/password-reset/done/'
        ),
        name='password_reset'),

    # 2. Password Reset Email Sent Page
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='account/password_reset_sent.html',
        ),
        name='password_reset_done'
    ),

    # 3. Link in Email → Reset Password Form
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='account/password_reset_confirm.html'
        ),
        name='password_reset_confirm'
    ),

    # 4. Password Reset Complete Page
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='account/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)