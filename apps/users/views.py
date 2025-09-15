from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse
from .forms import CustomUserCreationForm, LoginForm, ProfileForm
from django.contrib.auth.decorators import login_required



class UserLoginView(View):
    form_class = LoginForm
    template_name = 'zoosvit/users/login.html'

    def get(self, request):
        return render(request, self.template_name, {'login_form': self.form_class()})

    def post(self, request):
        form = self.form_class(request.POST)
        error = None
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )
            if user:
                login(request, user)

                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'redirect_url': '/'})
                return redirect('/')
            error = 'Невірний логін або пароль'
        else:
            error = 'Будь ласка, виправте помилки у формі'


        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return render(
                request,
                'zoosvit/users/login_form.html',
                {'login_form': form, 'error': error},
                status=400
            )


        return render(request, self.template_name, {
            'login_form': form,
            'error': error
        })

class UserLogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('/')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'redirect_url': '/'})
            return redirect('home')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return render(request, 'zoosvit/users/register_form.html', {'form': form}, status=400)

            return render(request, 'zoosvit/users/register.html', {'form': form})

    else:
        form = CustomUserCreationForm()

    return render(request, 'zoosvit/users/register.html', {'form': form})

@login_required
def profile_view(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, 'Дані оновлено ✔️')
        return redirect('users:profile')
    return render(request, 'zoosvit/users/profile.html', {'form': form})
