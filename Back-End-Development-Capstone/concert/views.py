import requests as req
import os
from django.contrib.auth import login, logout
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from concert.forms import LoginForm, SignUpForm
from concert.models import Concert, ConcertAttending

# Create your views here.
SONGS_SERVICE_URL = os.getenv("SONGS_SERVICE_URL")
PHOTOS_SERVICE_URL = os.getenv("PHOTOS_SERVICE_URL")


def signup(request: HttpRequest):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        try:
            user = User.objects.filter(username=username).first()
            if user:
                return render(
                    request,
                    "signup.html",
                    {"form": SignUpForm, "message": "user already exist"},
                )
            user = User.objects.create(
                username=username, password=make_password(password)
            )
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        except User.DoesNotExist:
            return render(request, "signup.html", {"form": SignUpForm})
    return render(request, "signup.html", {"form": SignUpForm})


def index(request):
    return render(request, "index.html")


def songs(request):
    songs = req.get(SONGS_SERVICE_URL).json()
    return render(request, "songs.html", {"songs": songs["songs"]})


def photos(request):
    photos = req.get(PHOTOS_SERVICE_URL).json()
    return render(request, "photos.html", {"photos": photos})


def login_view(request: HttpRequest):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                login(request, user)
                return HttpResponseRedirect(reverse("index"))
            else:
                raise User.DoesNotExist  # actually the user is exist, but idc
        except User.DoesNotExist:
            return render(
                request,
                "login.html",
                {"form": LoginForm, "message": "Invalid username/password"},
            )
    return render(request, "login.html", {"form": LoginForm})


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("login"))


def concerts(request: HttpRequest):
    if request.user.is_authenticated:
        concert_list = []
        concert_objects = Concert.objects.all()
        for item in concert_objects:
            try:
                status = item.attendee.filter(user=request.user).first().attending
            except:
                status = "-"
            concert_list.append({"concert": item, "status": status})
        return render(request, "concerts.html", {"concerts": concert_list})
    else:
        return HttpResponseRedirect(reverse("login"))


def concert_detail(request, id):
    if request.user.is_authenticated:
        obj = Concert.objects.get(pk=id)
        try:
            status = obj.attendee.filter(user=request.user).first().attending
        except:
            status = "-"
        return render(
            request,
            "concert_detail.html",
            {
                "concert_details": obj,
                "status": status,
                "attending_choices": ConcertAttending.AttendingChoices.choices,
            },
        )
    else:
        return HttpResponseRedirect(reverse("login"))
    pass


def concert_attendee(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            concert_id = request.POST.get("concert_id")
            attendee_status = request.POST.get("attendee_choice")
            concert_attendee_object = ConcertAttending.objects.filter(
                concert_id=concert_id, user=request.user
            ).first()
            if concert_attendee_object:
                concert_attendee_object.attending = attendee_status
                concert_attendee_object.save()
            else:
                ConcertAttending.objects.create(
                    concert_id=concert_id, user=request.user, attending=attendee_status
                )

        return HttpResponseRedirect(reverse("concerts"))
    else:
        return HttpResponseRedirect(reverse("index"))
