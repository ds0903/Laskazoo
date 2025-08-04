from .forms import CustomUserCreationForm
from .forms import LoginForm

def auth_forms(request):
    return {
        'register_form': CustomUserCreationForm(),
        'login_form': LoginForm(),
    }
