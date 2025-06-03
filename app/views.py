from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User, File, Purchase, Ban, Comment
from .forms import RegistrationForm, LoginForm, UploadForm
from random import choice
from .models import File
from django.db.models import Q, Count
from django.http import Http404, FileResponse, HttpResponseForbidden
from django.db import transaction
from django.core.paginator import Paginator

from django.conf import settings
import os
from django.core.exceptions import ValidationError


def landing_page(request):
    # Archivos más comprados
    purchased_counts = Purchase.objects.values('file').annotate(count=Count('file')).order_by('-count')[:6]
    top_purchased_ids = [entry['file'] for entry in purchased_counts]
    top_purchased_files = File.objects.filter(id__in=top_purchased_ids, is_approved=True)

    # Archivos aleatorios
    random_files = File.objects.filter(is_approved=True).order_by('?')[:6]

    # Últimos archivos subidos
    latest_files = File.objects.filter(is_approved=True).order_by('-upload_date')[:6]

    # Recomendados (placeholder sin sistema de recomendación aún)
    recommended_files = []
    if request.user.is_authenticated:
        recommended_files = File.objects.filter(is_approved=True).order_by('?')[:6]

    return render(request, 'landing.html', {
        'top_purchased_files': top_purchased_files,
        'random_files': random_files,
        'latest_files': latest_files,
        'recommended_files': recommended_files,
    })


def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('landing')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user:
                login(request, user)
                return redirect('landing')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('landing')

def profile_list_view(request):
    query = request.GET.get('q', '')
    users = User.objects.filter(is_active=True)

    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query)
        )

    return render(request, 'profiles.html', {
        'users': users,
        'query': query,
    })

@login_required
def upload_view(request):
    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.save(commit=False)
            file.uploader = request.user
            file.save()
            messages.success(request, "File uploaded and pending approval.")
            return redirect('user_profile', username=request.user.username)
    else:
        form = UploadForm()
    return render(request, 'upload.html', {'form': form})


def file_detail(request, file_id):
    file = get_object_or_404(File, id=file_id)

    # Restrict access to files uploaded by banned users (except admins)
    if not file.uploader.is_active and not (request.user.is_authenticated and request.user.is_admin):
        raise Http404("File not found.")

    # Restrict access to unapproved files unless user is uploader or admin
    if not file.is_approved and not (request.user.is_authenticated and (request.user == file.uploader or request.user.is_admin)):
        raise Http404("File not found.")

    has_access = request.user.is_authenticated and (
        Purchase.objects.filter(user=request.user, file=file).exists() or
        file.uploader == request.user or
        request.user.is_admin
    )

    return render(request, 'file_detail.html', {'file': file, 'has_access': has_access})

@login_required
def purchase_file(request, file_id):
    file = get_object_or_404(File, id=file_id)
    if request.user.coins >= file.price:
        # Prevenir compras duplicadas
        if not Purchase.objects.filter(user=request.user, file=file).exists():
            # Usar una transacción para asegurar que ambas operaciones se realicen correctamente
            with transaction.atomic():
                # Restar monedas del comprador
                request.user.coins -= file.price
                request.user.save()
                # Sumar monedas al vendedor
                seller = file.uploader
                seller.coins += file.price
                seller.save()
                # Crear la compra
                Purchase.objects.create(user=request.user, file=file)
            messages.success(request, "File purchased successfully.")
        else:
            messages.info(request, "You have already purchased this file.")
    else:
        messages.error(request, "Not enough coins.")
    
    return redirect('file_detail', file_id=file.id)

def user_profile(request, username):
    user_profile = get_object_or_404(User, username=username)

    files = File.objects.filter(uploader=user_profile, is_approved=True)

    file_downloads = (
        Purchase.objects.filter(file__in=files)
        .values('file')
        .annotate(downloads=Count('id'))
    )
    downloads_map = {entry['file']: entry['downloads'] for entry in file_downloads}
    for f in files:
        f.downloads = downloads_map.get(f.id, 0)

    # Sumar descargas totales
    total_downloads = sum(downloads_map.values())

    best_seller_data = (
        Purchase.objects.filter(file__uploader=user_profile, file__is_approved=True)
        .values('file')
        .annotate(total=Count('file'))
        .order_by('-total')[:6]
    )
    best_seller_ids = [entry['file'] for entry in best_seller_data]
    best_seller_files = File.objects.filter(id__in=best_seller_ids, is_approved=True)

    sales_map = {entry['file']: entry['total'] for entry in best_seller_data}
    for f in best_seller_files:
        f.total_sales = sales_map.get(f.id, 0)

    return render(request, 'profile.html', {
        'user_profile': user_profile,
        'files': files,
        'best_seller_files': best_seller_files,
        'total_downloads': total_downloads,  # Nuevo contexto agregado
    })


@login_required
def admin_panel(request):
    if not request.user.is_admin:
        return redirect('landing')
    # Solo mostrar archivos PENDIENTES, no los rechazados
    files = File.objects.filter(status='pending')
    users = User.objects.exclude(id=request.user.id)
    return render(request, 'admin_panel.html', {'pending_files': files, 'users': users})

# Nueva función para ver detalles del archivo
@login_required
def admin_file_detail(request, file_id):
    if not request.user.is_admin:
        return redirect('landing')
    
    file = get_object_or_404(File, id=file_id)
    has_access = True  # Admin siempre tiene acceso
    
    return render(request, 'file_detail.html', {
        'file': file, 
        'has_access': has_access,
        'is_admin_view': True
    })

@login_required
def approve_file(request, file_id):
    if request.user.is_admin:
        file = get_object_or_404(File, id=file_id)
        file.status = 'approved'
        file.is_approved = True  # Para mantener compatibilidad
        file.save()
        messages.success(request, f'File "{file.title}" has been approved.')
    return redirect('admin_panel')

@login_required
def reject_file(request, file_id):
    if request.user.is_admin:
        file = get_object_or_404(File, id=file_id)
        file_title = file.title  # Guardar el título antes de borrar
        
        # Borrar el archivo físico del servidor
        try:
            if file.file and os.path.exists(file.file.path):
                os.remove(file.file.path)
        except Exception as e:
            print(f"Error deleting file: {e}")
        
        # Borrar el registro de la base de datos
        file.delete()
        
        messages.success(request, f'File "{file_title}" has been rejected and permanently deleted.')
    else:
        messages.error(request, 'You do not have permission to perform this action.')
    return redirect('admin_panel')


@login_required
def ban_user(request, user_id):
    if request.user.is_admin:
        user = get_object_or_404(User, id=user_id)
        Ban.objects.create(banned_user=user, banned_by=request.user)
        user.is_active = False
        user.save()
    return redirect('admin_panel')

def brand_list_view(request):
    query = request.GET.get('q', '')

    brands = User.objects.filter(is_brand=True)
    if query:
        brands = brands.filter(username__icontains=query)

    # Adjuntar top 3 archivos más vendidos por cada brand
    for brand in brands:
        top_files = (
            File.objects
            .filter(uploader=brand)
            .annotate(purchases=Count('purchase'))
            .order_by('-purchases')[:3]
        )
        brand.top_files = top_files

    return render(request, 'brands.html', {
        'brands': brands,
        'query': query,
    })

@login_required
def protected_file_view(request, file_id):
    # Obtener el archivo
    file = get_object_or_404(File, id=file_id)

    # Verificar si el usuario tiene acceso (compró o es uploader o admin)
    user = request.user
    has_access = (
        Purchase.objects.filter(user=user, file=file).exists() or
        file.uploader == user or
        user.is_admin
    )
    if not has_access:
        return HttpResponseForbidden("No tiene permiso para acceder a este archivo.")

    # Construir la ruta absoluta del archivo protegido
    # Aquí asumimos que 'file.file.name' guarda solo el nombre relativo, no la ruta completa
    # Ajusta la ruta según donde guardes los archivos protegidos
    file_path = os.path.join(settings.PROTECTED_FILES_ROOT, os.path.basename(file.file.name))

    if not os.path.exists(file_path):
        raise Http404("Archivo no encontrado.")

    # Devolver el archivo como respuesta eficiente
    return FileResponse(open(file_path, 'rb'), content_type='application/octet-stream')

# Nuevas vistas para el sistema de comentarios

def file_comments(request, file_id):
    file = get_object_or_404(File, id=file_id, is_approved=True)
    comments = Comment.objects.filter(file=file, parent=None).prefetch_related('replies', 'user')
    
    # Verificar si el usuario puede comentar (debe haber comprado el archivo)
    can_comment = False
    user_comment_count = 0
    
    if request.user.is_authenticated:
        can_comment = (
            Purchase.objects.filter(user=request.user, file=file).exists() or
            file.uploader == request.user or
            request.user.is_admin
        )
        
        # Contar comentarios principales del usuario (no respuestas)
        user_comment_count = Comment.objects.filter(
            file=file,
            user=request.user,
            parent=None
        ).count()
    
    if request.method == 'POST' and request.user.is_authenticated and can_comment:
        content = request.POST.get('content')
        parent_id = request.POST.get('parent_id')
        
        if content:
            parent = None
            if parent_id:
                parent = get_object_or_404(Comment, id=parent_id, file=file)
                # Solo el vendedor puede responder a comentarios
                if request.user != file.uploader:
                    messages.error(request, "Only the seller can reply to comments.")
                    return redirect('file_comments', file_id=file.id)
            else:
                # Verificar límite de comentarios principales
                if user_comment_count >= 2:
                    messages.error(request, "You can only post a maximum of 2 comments per file.")
                    return redirect('file_comments', file_id=file.id)
            
            try:
                Comment.objects.create(
                    file=file,
                    user=request.user,
                    content=content,
                    parent=parent
                )
                messages.success(request, "Comment posted successfully!")
            except ValidationError as e:
                messages.error(request, str(e))
            
            return redirect('file_comments', file_id=file.id)
    
    return render(request, 'file_comments.html', {
        'file': file,
        'comments': comments,
        'can_comment': can_comment,
        'user_comment_count': user_comment_count,
    })

@login_required
def comments_list(request):
    comments = Comment.objects.filter(parent=None).select_related('user', 'file').prefetch_related('replies').order_by('-created_at')
    
    paginator = Paginator(comments, 12)  # 12 comentarios por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'comments_list.html', {
        'comments': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
    })