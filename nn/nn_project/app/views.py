from base64 import urlsafe_b64decode
from tempfile import template

from django.contrib.auth.hashers import PBKDF2PasswordHasher
from django.core.files.storage import default_storage
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.db import connection
from django.urls import reverse
from django.utils.crypto import pbkdf2
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.translation.template import context_re
import os

def main(request):
    template = 'main.html'
    id_user = None
    if 'id_application' in request.POST:
        id_application = request.POST.get('id_application')
        id_status = request.POST.get('id_status')
        with connection.cursor() as cursor:
            cursor.callproc('application_id_patch', [id_application, id_status])

    with connection.cursor() as cursor:
        cursor.callproc('applications_get', [id_user])
        apps = dictfetchall(cursor)
        ids = []
        applications = []
        if 'id_image' in request.POST:
            filename = request.POST.get('id_image')
            path = os.path.join('photos', filename)
            filedata = default_storage.open(path, mode='rb')
            response = HttpResponse(filedata, content_type='application')
            response['Content-Disposition'] = f'attachment;filename="{filename}"'
            response.status_code = 200
            return response
        for app in apps:
            if app['pk_application'] not in ids:
                application = {}
                application['id_user'] = app['fk_user']
                application['id_application'] = app['pk_application']
                application['car_number'] = app['car_number']
                application['description'] = app['description']
                application['id_status'] = app['fk_status']
                application['title'] = app['title']
                application['images'] = []
                if app['pk_image']:
                    image = {}
                    image['id_image'] = app['pk_image']
                    image['file_name'] = app['file_name']
                    image['file_ext'] = app['file_ext']
                    application['images'].append(image)
                applications.append(application)
                ids.append(app['pk_application'])
            else:
                for application in applications:
                    if app['pk_application'] == application['id_application']:
                        image = {}
                        image['id_image'] = app['pk_image']
                        image['file_name'] = app['file_name']
                        image['file_ext'] = app['file_ext']
                        application['images'].append(image)

    with connection.cursor() as cursor:
        cursor.callproc('statuses_get')
        statuses = dictfetchall(cursor)

    context = {
        'applications': applications,
        'statuses': statuses,
    }
    return render(request, template, context)

def activate(request, id_user_urlencode, token_urlencode):
    id_user = force_str(urlsafe_base64_decode(id_user_urlencode))
    token = force_str(urlsafe_base64_decode(token_urlencode))
    with connection.cursor() as cursor:
        cursor.callproc('users_get', [id_user, None, None])
        users = dictfetchall(cursor)
    if len(users) != 1:
        return HttpResponse('Неверная ссылка', status=400)
    user = users[0]
    hasher = PBKDF2PasswordHasher()
    if not hasher.verify(user.get('email'), token):
        return HttpResponse('Неверная ссылка', status=400)
    with connection.cursor() as cursor:
        cursor.callproc('users_id_patch', [id_user, 1])
    return HttpResponse('Почта подтверждена', status=200)

def new_app(request, id_type_offense):
    template = 'new_app.html'
    if 'applications_post' in request.POST:
        car_number = request.POST.get('car_number')
        description = request.POST.get('description')
        id_user = 1
        id_status = 1

        with connection.cursor() as cursor:
            cursor.callproc('applications_post', [car_number, description, id_user, id_type_offense, id_status])
            res = dictfetchall(cursor)
            last_id_application = res[0].get('last_id_application')
            print(last_id_application)

    if 'files' in request.FILES:
        files = request.FILES.getlist('files')
        for file in files:
            file_title = file.name
            file_name, file_ext = os.path.splitext(file_title)
            file_ext = file_ext.lstrip('.')
            if file_ext in ('jpeg', 'jpg', 'png'):
                with connection.cursor() as cursor:
                    cursor.callproc('images_post', [file_name, file_ext, last_id_application])
                    res = dictfetchall(cursor)
                    last_id_image = res[0].get('last_id_image')
                new_file_name = f'{last_id_image}.{file_ext}'
                path = os.path.join('photos', new_file_name)
                default_storage.save(path,file)
    context = {}
    return render(request, template, context)

def types(request):
    template = 'types.html'
    context = {}
    with connection.cursor() as cursor:
        cursor.callproc('types_get')
        types = dictfetchall(cursor)

    context['types'] = types

    return render(request, template, context)

def signup(request):
    template = 'signup.html'
    context = {}
    if 'users_post' in request.POST:
        lastname = request.POST.get('lastname')
        firstname = request.POST.get('firstname')
        middlename = request.POST.get('middlename')
        username = request.POST.get('username')
        password = request.POST.get('password')
        hasher = PBKDF2PasswordHasher()
        password_hash = hasher.encode(password, salt='extra')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        is_admin = 0
        is_active = 0
        token = None
        with connection.cursor() as cursor:
            cursor.callproc('users_get', [None, None, email])
            users = dictfetchall(cursor)
        if len(users) > 0:
            return HttpResponse('Такой email уже существует', status_code=400)
        with connection.cursor() as cursor:
            cursor.callproc('users_post',[lastname, firstname, middlename, username, password_hash, email, phone , is_admin, is_active, token])
            users = dictfetchall(cursor)
            user = users[0]
            print(user)
        token = hasher.encode(email, salt='extra')
        print(token)
        id_user_urlencode = urlsafe_base64_encode(force_bytes(user.get('id_user')))
        token_urlencode = urlsafe_base64_encode(force_bytes(token))
        print(id_user_urlencode)
        print(token_urlencode)
        activation_url = request.build_absolute_uri(
            reverse('activate', kwargs={'id_user_urlencode': id_user_urlencode, 'token_urlencode': token_urlencode}))
        print(activation_url)
    return render(request, template, context)

def login(request):
    template = 'login.html'
    context = {}
    return render(request, template, context)

def types(request):
    template = 'types.html'
    context = {}
    return render(request, template, context)

def logout(request):
    return redirect('main')

def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns,row))
        for row in cursor.fetchall()
    ]

