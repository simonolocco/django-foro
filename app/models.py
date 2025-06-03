from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from .storage import protected_storage
from django.core.exceptions import ValidationError

class User(AbstractUser):
    coins = models.IntegerField(default=0)
    is_admin = models.BooleanField(default=False)
    is_brand = models.BooleanField(default=False)

class File(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        )
    title = models.CharField(max_length=255)
    description = models.TextField()
    file = models.FileField(storage=protected_storage, upload_to='')
    image = models.ImageField(upload_to='file_images/', blank=True, null=True)
    price = models.IntegerField()
    uploader = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    is_approved = models.BooleanField(default=False)
    upload_date = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if self.status == 'approved':
            self.is_approved = True
        else:
            self.is_approved = False
        super().save(*args, **kwargs)

class Purchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.ForeignKey(File, on_delete=models.CASCADE)
    purchase_date = models.DateTimeField(default=timezone.now)

class Ban(models.Model):
    banned_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='banned_user')
    banned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='banned_by')
    ban_date = models.DateTimeField(default=timezone.now)

class Comment(models.Model):
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f'Comment by {self.user.username} on {self.file.title}'
    
    def is_reply(self):
        return self.parent is not None
    
    def clean(self):
        # Solo validar para comentarios principales (no respuestas)
        if not self.parent:
            existing_comments = Comment.objects.filter(
                file=self.file,
                user=self.user,
                parent=None
            )
            # Si estamos editando, excluir el comentario actual
            if self.pk:
                existing_comments = existing_comments.exclude(pk=self.pk)
            
            if existing_comments.count() >= 2:
                raise ValidationError('You can only post a maximum of 2 comments per file.')
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
