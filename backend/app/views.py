from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.template import loader
from .forms import ChatForm
from .consumers import ChatConsumer
from .models import ChatRoom, generate_room_code, purge_expired_rooms
import uuid


# Create your views here.

def home(request):
    return render(request, 'app/home.html')


def create_room(request):
    # if this function provoked from frontend eventhandler button click,
    # it will be a GET request, so we can simply generate a new room and return a room code
    if request.method == 'GET':
        purge_expired_rooms()
        room_code = generate_room_code()
        room = ChatRoom.objects.create(code=room_code)
        request.session['controller_token'] = room.controller_token

        if request.GET.get('format') == 'json':
            return JsonResponse({
                'room_code': room_code,
                'role': 'root',
                'controller_token': room.controller_token,
            })

        # redirect to a dedicated room URL so refreshing doesn't create another room
        from django.urls import reverse
        return redirect(reverse('room', kwargs={'room_code': room_code}) + '?root=1')
    else:
        return HttpResponse("Invalid request method.", status=405)

def join_room(request, room_code=None):
    if request.method == 'GET' and request.GET.get('format') == 'json':
        purge_expired_rooms()
        room_code = (room_code or request.GET.get('room_code', '')).strip().upper()
        try:
            ChatRoom.objects.get(code=room_code, is_active=True)
            return JsonResponse({'room_code': room_code, 'role': 'user'})
        except ChatRoom.DoesNotExist:
            return JsonResponse({'error': 'Room not found or inactive.'}, status=404)

    if request.method == 'POST':
        room_code = request.POST.get('room_code')
        # read the db and check if is_active == True
        try:
            room = ChatRoom.objects.get(code=room_code, is_active=True)
            return redirect('room', room_code=room_code, permanent=False)
        except ChatRoom.DoesNotExist:
            return HttpResponse("Room not found or inactive.", status=404)
    else:
        return HttpResponse("Invalid request method.", status=405)


def room(request, room_code):
    purge_expired_rooms()
    try:
        room = ChatRoom.objects.get(code=room_code, is_active=True)
    except ChatRoom.DoesNotExist:
        return HttpResponse("Room not found or inactive.", status=404)

    is_root = (
        request.GET.get('root') == '1'
        and request.session.get('controller_token') == room.controller_token
    )
    return render(request, 'app/chat.html', {
        'room_code': room_code,
        'is_root': is_root,
        'controller_token': room.controller_token if is_root else '',
    })

        
        



def index(request):
    if request.method == 'POST':
        form = ChatForm(request.POST)
        if form.is_valid():
            # Process the form data here
            message = form.cleaned_data['message']

            return render(request, 'app/chat.html', {'form': form, 'message': message})
    else:
        form = ChatForm()
        return render(request, 'app/chat.html', {'form': form, 'message': None})

