from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, File
from .models import User, File, Comment

class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email']

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class UploadForm(forms.ModelForm):
    class Meta:
        model = File
        fields = ['title', 'description', 'file', 'image', 'price']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter file title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter file description', 'rows': 4}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter price in coins'}),
        }
        labels = {
            'title': 'Title',
            'description': 'Description',
            'file': 'Upload File',
            'image': 'Upload Preview Image',
            'price': 'Price (in coins)',
        }
        help_texts = {
            'image': 'Upload a preview image for your file (optional)',
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Share your thoughts about this file...',
                'class': 'w-full px-3 py-2 bg-black bg-opacity-30 border border-gray-600 text-white placeholder-gray-400 focus:outline-none focus:border-red-500 transition-colors duration-200'
            })
        }
