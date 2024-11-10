from django.urls import path, include
from artwork import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Pages
    path("", views.index, name="index"),
    path("contact-us/", views.contact_us, name="contact-us"),
    path("about-us/", views.about_us, name="about-us"),
    # Authentication
    path("accounts/login/", views.UserLoginView.as_view(), name="login"),
    path("accounts/logout/", views.user_logout_view, name="logout"),
    path("accounts/register/", views.registration, name="register"),
    path(
        "accounts/password-change/",
        views.UserPasswordChangeView.as_view(),
        name="password_change",
    ),
    path(
        "accounts/password-change-done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="accounts/password_change_done.html"
        ),
        name="password_change_done",
    ),
    path(
        "accounts/password-reset/",
        views.UserPasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "accounts/password-reset-confirm/<uidb64>/<token>/",
        views.UserPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "accounts/password-reset-done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "accounts/password-reset-complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path("accounts/", include("allauth.urls")),
    path(
        "social-login-success/", views.social_login_success, name="social_login_success"
    ),
    path("post", views.PostListView.as_view(), name="post-list"),
    path("post/<int:pk>/", views.PostDetailView.as_view(), name="post-detail"),
    path("post/new/", views.PostCreateView.as_view(), name="post-create"),
    path("post/<int:pk>/update/", views.PostUpdateView.as_view(), name="post-update"),
    path("post/<int:pk>/delete/", views.PostDeleteView.as_view(), name="post-delete"),
    path("post/<int:pk>/qr/", views.qr_code_view, name="qr-view"),
    path("post/<int:pk>/qr/download/", views.download_qr_code, name="qr-download"),
    
    path('post/<int:post_pk>/comment/', views.create_comment, name='create-comment'),
    path('comment/<int:comment_pk>/delete/', views.delete_comment, name='delete-comment'),
    path('comment/<int:comment_pk>/update/', views.update_comment, name='update-comment'),
    
    path('post/<int:post_pk>/faq/', views.create_faq, name='create-faq'),
    path('faq/<int:faq_pk>/update/', views.update_faq, name='update-faq'),
    path('faq/<int:faq_pk>/delete/', views.delete_faq, name='delete-faq'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
