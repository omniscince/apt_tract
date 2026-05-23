from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views import View
from .models import User
from .forms import LoginForm, UserCreateForm, ProfileForm


class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        form = LoginForm()
        return render(request, 'users/login.html', {'form': form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)
            if user:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid email or password')
        return render(request, 'users/login.html', {'form': form})


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('login')


@method_decorator(login_required, name='dispatch')
class UserListView(View):
    def get(self, request):
        if request.user.role not in ('owner', 'staff'):
            messages.error(request, 'Access denied')
            return redirect('dashboard')
        users = User.objects.all().order_by('role', 'email') if request.user.is_owner else None
        return render(request, 'users/user_list.html', {'users': users})


@method_decorator(login_required, name='dispatch')
class UserCreateView(View):
    def get(self, request):
        if not request.user.is_owner:
            messages.error(request, 'Access denied')
            return redirect('dashboard')
        form = UserCreateForm()
        return render(request, 'users/user_form.html', {'form': form, 'title': 'Create User'})

    def post(self, request):
        if not request.user.is_owner:
            messages.error(request, 'Access denied')
            return redirect('dashboard')
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, f'User {user.email} created!')
            return redirect('user_list')
        return render(request, 'users/user_form.html', {'form': form, 'title': 'Create User'})


@method_decorator(login_required, name='dispatch')
class UserEditView(View):
    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if not request.user.is_owner and request.user.pk != pk:
            messages.error(request, 'Access denied')
            return redirect('dashboard')
        if request.user.is_owner:
            form = UserCreateForm(instance=user)
        else:
            form = ProfileForm(instance=user)
        return render(request, 'users/user_form.html', {
            'form': form, 'title': 'Edit Profile', 'edit': True,
            'is_owner': request.user.is_owner
        })

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if not request.user.is_owner and request.user.pk != pk:
            messages.error(request, 'Access denied')
            return redirect('dashboard')
        if request.user.is_owner:
            form = UserCreateForm(request.POST, instance=user)
        else:
            form = ProfileForm(request.POST, instance=user)
        if form.is_valid():
            u = form.save(commit=False)
            password = form.cleaned_data.get('password')
            if password:
                u.set_password(password)
            u.save()
            messages.success(request, 'Profile updated!')
            return redirect('user_list')
        return render(request, 'users/user_form.html', {
            'form': form, 'title': 'Edit Profile', 'edit': True,
            'is_owner': request.user.is_owner
        })


@method_decorator(login_required, name='dispatch')
class UserDeleteView(View):
    def post(self, request, pk):
        if not request.user.is_owner:
            messages.error(request, 'Access denied')
            return redirect('dashboard')
        user = get_object_or_404(User, pk=pk)
        if user == request.user:
            messages.error(request, 'You cannot delete yourself')
            return redirect('user_list')
        has_invoices = user.created_invoices.exists() or user.completed_invoices.exists()
        if has_invoices:
            messages.error(request, f'Cannot delete {user.email} — they have existing invoices. Edit their account instead.')
            return redirect('user_list')
        user.delete()
        messages.success(request, 'User deleted')
        return redirect('user_list')


@method_decorator(login_required, name='dispatch')
class PasswordChangeView(View):
    def get(self, request):
        return render(request, 'users/password_change.html', {'title': 'Change Password'})

    def post(self, request):
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not request.user.check_password(old_password):
            messages.error(request, 'Current password is incorrect')
            return render(request, 'users/password_change.html', {'title': 'Change Password'})

        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match')
            return render(request, 'users/password_change.html', {'title': 'Change Password'})

        if len(new_password) < 6:
            messages.error(request, 'Password must be at least 6 characters')
            return render(request, 'users/password_change.html', {'title': 'Change Password'})

        request.user.set_password(new_password)
        request.user.save()
        messages.success(request, 'Password changed successfully')
        return redirect('login')