from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image
from django.urls import reverse
import ffmpeg
import os
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from typing import Any
import subprocess
from pathlib import Path

class User(AbstractUser):
    is_trainer = models.BooleanField(default=False)  # type: ignore

User = get_user_model()

class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    video = models.FileField(upload_to="post_videos/")
    thumbnail = models.ImageField(upload_to="post_thumbnails/", blank=True, null=True)
    qr_code = models.ImageField(upload_to="post_qr_codes/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    normal_views = models.IntegerField(default=0)  # type: ignore
    qr_views = models.IntegerField(default=0)  # type: ignore

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self):
        return reverse("post-detail", kwargs={"pk": self.pk})

    def increment_normal_views(self):
        Post.objects.filter(pk=self.pk).update(normal_views=models.F('normal_views') + 1)  # type: ignore

    def increment_qr_views(self):
        Post.objects.filter(pk=self.pk).update(qr_views=models.F('qr_views') + 1)  # type: ignore

    def generate_thumbnail(self):
        if not self.video:
            return

        input_file = self.video.path
        output_file = os.path.join(
            os.path.dirname(input_file), f"thumbnail_{self.pk}.jpg"
        )

        try:
            # Create the ffmpeg stream
            probe = ffmpeg.probe(input_file)
            stream = (
                ffmpeg
                .input(input_file, ss=1)  # Take frame at 1 second
                .filter('scale', 480, -1)
                .output(output_file, vframes=1)
                .overwrite_output()
            )
            
            # Run the ffmpeg command
            ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)

            # Save the thumbnail
            with open(output_file, "rb") as f:
                self.thumbnail.save(f"thumbnail_{self.pk}.jpg", File(f), save=False)

            # Clean up
            if os.path.exists(output_file):
                os.remove(output_file)

        except (ffmpeg.Error, subprocess.CalledProcessError) as e:
            print(f"Error generating thumbnail: {str(e)}")
        except Exception as e:
            print(f"Unexpected error generating thumbnail: {str(e)}")

    def generate_qr_code(self):
        current_site = Site.objects.get_current()
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        full_url = f"http://{current_site.domain}{self.get_absolute_url()}?qr=1"
        qr.add_data(full_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer)  
        buffer.seek(0)

        self.qr_code.save(f"qr_code_{self.pk}.png", File(buffer), save=False)  # type: ignore

    def save(self, *args: Any, **kwargs: Any):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new or not self.thumbnail:
            self.generate_thumbnail()

        if is_new or not self.qr_code:
            self.generate_qr_code()

        if self.thumbnail or self.qr_code:
            super().save(update_fields=["thumbnail", "qr_code"])

    @property
    def root_comments(self):
        """Get only the root comments (not replies)"""
        return self.comments.filter(parent=None)  # type: ignore
    
    @property
    def ordered_faqs(self):
        return self.faqs.all()

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Comment by {self.author.get_username()} on {self.post.title}'  # type: ignore

    @property
    def is_reply(self):
        return self.parent is not None

    @property 
    def get_replies(self):
        return Comment.objects.filter(parent=self).order_by('created_at')  # type: ignore

class FAQ(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='faqs')
    question = models.CharField(max_length=255)
    answer = models.TextField()
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"FAQ for {self.post.title}: {self.question}"