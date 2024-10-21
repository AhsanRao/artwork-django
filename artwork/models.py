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


class User(AbstractUser):
    is_trainer = models.BooleanField(default=False)


import os
from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files import File
from PIL import Image
import ffmpeg
import qrcode
from io import BytesIO
from django.contrib.sites.models import Site

User = get_user_model()


class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    video = models.FileField(upload_to="post_videos/")
    thumbnail = models.ImageField(upload_to="post_thumbnails/", blank=True, null=True)
    qr_code = models.ImageField(upload_to="post_qr_codes/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    normal_views = models.IntegerField(default=0)
    qr_views = models.IntegerField(default=0)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("post-detail", kwargs={"pk": self.pk})

    def increment_normal_views(self):
        self.normal_views += 1
        self.save()

    def increment_qr_views(self):
        self.qr_views += 1
        self.save()

    def generate_thumbnail(self):
        if not self.video:
            return

        input_file = self.video.path
        output_file = os.path.join(
            os.path.dirname(input_file), f"thumbnail_{self.id}.jpg"
        )

        try:
            (
                ffmpeg.input(input_file, ss="00:00:01")
                .filter("scale", 480, -1)
                .output(output_file, vframes=1)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )

            with open(output_file, "rb") as f:
                self.thumbnail.save(f"thumbnail_{self.id}.jpg", File(f), save=False)

            os.remove(output_file)
        except ffmpeg.Error as e:
            print(f"Error generating thumbnail: {e.stderr.decode()}")

    def generate_qr_code(self):
        current_site = Site.objects.get_current()
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        full_url = f"http://{current_site.domain}{self.get_absolute_url()}?qr=1"
        qr.add_data(full_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        self.qr_code.save(f"qr_code_{self.id}.png", File(buffer), save=False)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new or not self.thumbnail:
            self.generate_thumbnail()

        if is_new or not self.qr_code:
            self.generate_qr_code()

        if self.thumbnail or self.qr_code:
            super().save(update_fields=["thumbnail", "qr_code"])
