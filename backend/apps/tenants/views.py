import json
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


@ensure_csrf_cookie
def me_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'data': None, 'error': 'not authenticated', 'meta': {}}, status=401)
    return JsonResponse({'data': {'id': request.user.id, 'username': request.user.username}, 'error': None, 'meta': {}})


@csrf_exempt
@require_POST
def login_view(request):
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'data': None, 'error': 'invalid JSON', 'meta': {}}, status=400)
    user = authenticate(request, username=body.get('username'), password=body.get('password'))
    if user is None:
        return JsonResponse({'data': None, 'error': 'invalid credentials', 'meta': {}}, status=400)
    login(request, user)
    return JsonResponse({'data': {'id': user.id, 'username': user.username}, 'error': None, 'meta': {}})


@csrf_exempt
@require_POST
def logout_view(request):
    logout(request)
    return JsonResponse({'data': None, 'error': None, 'meta': {}})
