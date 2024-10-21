from django.shortcuts import render, redirect
from artwork.forms import (
    LoginForm,
    RegistrationForm,
    UserPasswordResetForm,
    UserSetPasswordForm,
    UserPasswordChangeForm,
)
from django.contrib.auth import logout, get_user_model
from django.contrib.auth import views as auth_views
from django.contrib import messages
from allauth.socialaccount.models import SocialAccount
from django.core.mail import send_mail
from django.conf import settings
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.http import HttpResponseForbidden, HttpResponse
from .models import Post
from django.db.models import F
from django.db import transaction

User = get_user_model()


# Authentication
def registration(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("/accounts/login/")
    else:
        form = RegistrationForm()

    context = {"form": form}
    return render(request, "accounts/sign-up.html", context)


class UserLoginView(auth_views.LoginView):
    template_name = "accounts/sign-in.html"
    form_class = LoginForm
    success_url = "/"


class UserPasswordResetView(auth_views.PasswordResetView):
    template_name = "accounts/password_reset.html"
    form_class = UserPasswordResetForm


class UserPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    form_class = UserSetPasswordForm


class UserPasswordChangeView(auth_views.PasswordChangeView):
    template_name = "accounts/password_change.html"
    form_class = UserPasswordChangeForm


def user_logout_view(request):
    logout(request)
    return redirect("/accounts/login/")


# Pages
def index(request):
    return render(request, "pages/index.html")


def contact_us(request):
    return render(request, "pages/contact-us.html")


def about_us(request):
    return render(request, "pages/about-us.html")


def social_login_success(request):
    user = request.user
    if user.is_authenticated:
        social_account = SocialAccount.objects.filter(
            user=user, provider__in=["google", "apple"]
        ).first()

        if social_account:
            # Check if this is a new social account
            if social_account.date_joined == social_account.last_login:
                try:
                    # Send welcome email
                    send_mail(
                        "Welcome to Our Platform",
                        f"Thank you for joining us via {social_account.provider}!",
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=True,
                    )

                    if social_account.extra_data.get("given_name"):
                        user.first_name = social_account.extra_data["given_name"]
                    if social_account.extra_data.get("family_name"):
                        user.last_name = social_account.extra_data["family_name"]
                    user.save()

                    messages.success(
                        request,
                        f"Welcome! Your account has been created using {social_account.provider}.",
                    )
                except Exception as e:
                    print(f"Error during social login processing: {str(e)}")
                    messages.warning(
                        request,
                        "We encountered an issue setting up your account. Please contact support if you experience any problems.",
                    )
            else:
                messages.info(
                    request,
                    f"Welcome back! You've successfully logged in with {social_account.provider}.",
                )
        else:
            messages.info(request, "You've successfully logged in.")

    else:
        messages.error(request, "There was an issue with your login. Please try again.")

    return redirect("/")  # Redirect to home page or dashboard


class PostListView(LoginRequiredMixin, ListView):
    model = Post
    template_name = "blog/post_list.html"
    context_object_name = "posts"
    ordering = ["-created_at"]


class PostDetailView(LoginRequiredMixin, DetailView):
    model = Post
    template_name = "blog/post_detail.html"

    def get(self, request, *args, **kwargs):
        with transaction.atomic():
            self.object = self.get_object()
            if "qr" in request.GET:
                self.object.qr_views = F("qr_views") + 1
            else:
                self.object.normal_views = F("normal_views") + 1
            self.object.save(update_fields=["qr_views", "normal_views"])

            # Refresh the object to get the updated view counts
            self.object.refresh_from_db()

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class PostCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Post
    fields = ["title", "description", "video"]
    template_name = "blog/post_form.html"

    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)
        self.object.generate_thumbnail()
        self.object.generate_qr_code()
        return response

    def test_func(self):
        return self.request.user.is_trainer


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    fields = ["title", "description", "video"]
    template_name = "blog/post_form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        if "video" in form.changed_data:
            self.object.generate_thumbnail()
        self.object.generate_qr_code()

        return response

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author and self.request.user.is_trainer


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    success_url = reverse_lazy("post-list")

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author and self.request.user.is_trainer

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)


def qr_code_view(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.qr_views = F("qr_views") + 1
    post.save()
    return redirect("post-detail", pk=pk)


def download_qr_code(request, pk):
    if not request.user.is_trainer:
        return HttpResponseForbidden()
    qr_code = get_object_or_404(QRCode, post__pk=pk)
    response = HttpResponse(qr_code.qr_code, content_type="image/png")
    response["Content-Disposition"] = f'attachment; filename="qr_code-{pk}.png"'
    return response
