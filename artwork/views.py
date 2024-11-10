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
from .models import Post, FAQ
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
        context['comments'] = self.object.root_comments
        return self.render_to_response(context)


from django.core.files.uploadedfile import TemporaryUploadedFile
from django.core.files import File
import os
import subprocess

class PostCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Post
    fields = ["title", "description", "video"]
    template_name = "blog/post_form.html"

    def form_valid(self, form):
        try:
            # Set the author
            form.instance.author = self.request.user
            
            # First save to get the instance
            self.object = form.save(commit=False)
            
            # Generate thumbnail before saving
            if self.object.video:
                input_file = self.object.video.path
                output_file = os.path.join(
                    os.path.dirname(input_file),
                    f"thumbnail_{os.path.basename(input_file)}.jpg"
                )
                
                try:
                    # Use ffmpeg to generate thumbnail
                    command = [
                        'ffmpeg',
                        '-i', input_file,
                        '-ss', '00:00:01',
                        '-vframes', '1',
                        '-vf', 'scale=480:-1',
                        '-y',
                        output_file
                    ]
                    
                    subprocess.run(command, check=True, capture_output=True)
                    
                    # Save the thumbnail if it was generated
                    if os.path.exists(output_file):
                        with open(output_file, 'rb') as thumb_file:
                            self.object.thumbnail.save(
                                f"thumbnail_{os.path.basename(input_file)}.jpg",
                                File(thumb_file),
                                save=False
                            )
                        os.remove(output_file)
                except Exception as e:
                    print(f"Thumbnail generation error: {str(e)}")

            # Save the object
            self.object.save()

            # Handle FAQs
            faqs_data = self.request.POST.getlist('faq_question[]')
            faq_answers = self.request.POST.getlist('faq_answer[]')
            for i, (question, answer) in enumerate(zip(faqs_data, faq_answers)):
                if question and answer:
                    FAQ.objects.create(
                        post=self.object,
                        question=question,
                        answer=answer,
                        order=i
                    )

            # Generate QR code
            self.object.generate_qr_code()
            self.object.save()

            return super(PostCreateView, self).form_valid(form)

        except Exception as e:
            print(f"Form validation error: {str(e)}")
            raise

    def test_func(self):
        return self.request.user.is_trainer

class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    fields = ["title", "description", "video"]
    template_name = "blog/post_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['faqs'] = self.object.ordered_faqs
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Handle FAQs
        existing_faqs = set(self.object.faqs.values_list('id', flat=True))
        updated_faqs = set()
        
        faqs_data = self.request.POST.getlist('faq_question[]')
        faq_answers = self.request.POST.getlist('faq_answer[]')
        faq_ids = self.request.POST.getlist('faq_id[]')
        
        for i, (question, answer, faq_id) in enumerate(zip(faqs_data, faq_answers, faq_ids)):
            if question and answer:
                if faq_id:  # Update existing FAQ
                    faq = FAQ.objects.get(id=faq_id)
                    faq.question = question
                    faq.answer = answer
                    faq.order = i
                    faq.save()
                    updated_faqs.add(int(faq_id))
                else:  # Create new FAQ
                    faq = FAQ.objects.create(
                        post=self.object,
                        question=question,
                        answer=answer,
                        order=i
                    )
                    
        # Delete FAQs that weren't updated
        to_delete = existing_faqs - updated_faqs
        FAQ.objects.filter(id__in=to_delete).delete()
        
        if 'video' in form.changed_data:
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


from django.http import JsonResponse
from .models import Comment
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied

# Comment Views
@login_required
@require_POST
def create_comment(request, post_pk):
    """Create a new comment or reply"""
    post = get_object_or_404(Post, pk=post_pk)
    parent_id = request.POST.get('parent_id')
    content = request.POST.get('content')

    if not content:
        return JsonResponse({'error': 'Comment content is required'}, status=400)

    # Check if this is a reply
    if parent_id:
        # Only trainers can reply
        if not request.user.is_trainer:
            raise PermissionDenied("Only trainers can reply to comments")
        parent_comment = get_object_or_404(Comment, pk=parent_id)
        if parent_comment.post != post:
            return JsonResponse({'error': 'Invalid parent comment'}, status=400)

    comment = Comment.objects.create(
        post=post,
        author=request.user,
        content=content,
        parent_id=parent_id if parent_id else None
    )

    return JsonResponse({
        'id': comment.id,
        'content': comment.content,
        'author': comment.author.username,
        'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'is_reply': comment.is_reply,
    })

@login_required
def delete_comment(request, comment_pk):
    """Delete a comment"""
    comment = get_object_or_404(Comment, pk=comment_pk)

    # Check if user is authorized to delete the comment
    if comment.author != request.user and not request.user.is_trainer:
        raise PermissionDenied("You don't have permission to delete this comment")

    comment.delete()
    return JsonResponse({'message': 'Comment deleted successfully'})

@login_required
def update_comment(request, comment_pk):
    """Update a comment"""
    comment = get_object_or_404(Comment, pk=comment_pk)

    # Check if user is authorized to edit the comment
    if comment.author != request.user:
        raise PermissionDenied("You don't have permission to edit this comment")

    content = request.POST.get('content')
    if not content:
        return JsonResponse({'error': 'Comment content is required'}, status=400)

    comment.content = content
    comment.save()

    return JsonResponse({
        'id': comment.id,
        'content': comment.content,
        'updated_at': comment.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
    })
    
    
    
@login_required
@require_POST
def create_faq(request, post_pk):
    """Create a new FAQ for a post"""
    if not request.user.is_trainer:
        return JsonResponse({'error': 'Only trainers can add FAQs'}, status=403)
    
    post = get_object_or_404(Post, pk=post_pk)
    question = request.POST.get('question')
    answer = request.POST.get('answer')
    order = request.POST.get('order', 0)

    if not question or not answer:
        return JsonResponse({'error': 'Both question and answer are required'}, status=400)

    faq = FAQ.objects.create(
        post=post,
        question=question,
        answer=answer,
        order=order
    )

    return JsonResponse({
        'id': faq.id,
        'question': faq.question,
        'answer': faq.answer,
        'order': faq.order,
        'created_at': faq.created_at.strftime('%Y-%m-%d %H:%M:%S'),
    })

@login_required
def update_faq(request, faq_pk):
    """Update an existing FAQ"""
    if not request.user.is_trainer:
        return JsonResponse({'error': 'Only trainers can update FAQs'}, status=403)
    
    faq = get_object_or_404(FAQ, pk=faq_pk)
    
    if request.method == 'POST':
        question = request.POST.get('question')
        answer = request.POST.get('answer')
        order = request.POST.get('order')

        if question:
            faq.question = question
        if answer:
            faq.answer = answer
        if order is not None:
            faq.order = order

        faq.save()

        return JsonResponse({
            'id': faq.id,
            'question': faq.question,
            'answer': faq.answer,
            'order': faq.order,
            'updated_at': faq.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        })

@login_required
def delete_faq(request, faq_pk):
    """Delete an FAQ"""
    if not request.user.is_trainer:
        return JsonResponse({'error': 'Only trainers can delete FAQs'}, status=403)
    
    faq = get_object_or_404(FAQ, pk=faq_pk)
    faq.delete()
    
    return JsonResponse({'message': 'FAQ deleted successfully'})