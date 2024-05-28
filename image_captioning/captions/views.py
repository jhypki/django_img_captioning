from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from .forms import ImageUploadForm
import requests
import base64
import json
from google.oauth2 import service_account
from google.auth.transport.requests import Request

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(request, username=username, password=raw_password)
            if user is not None:
                login(request, user)
                return redirect('upload_image')
    elif request.user.is_authenticated:
        return redirect('upload_image')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('upload_image')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    elif request.user.is_authenticated:
        return redirect('upload_image')
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def upload_image(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.cleaned_data['image']
            caption = generate_caption(image)
            return render(request, 'upload.html', {'form': form, 'caption': caption})
    else:
        form = ImageUploadForm()
    return render(request, 'upload.html', {'form': form})

def generate_caption(image):
    endpoint = "https://us-central1-aiplatform.googleapis.com/v1/projects/image-captioning-424715/locations/us-central1/publishers/google/models/imagetext:predict"

    content = image.read()
    encoded_content = base64.b64encode(content).decode('utf-8')

    # Prepare the request payload
    payload = {
        "instances": [
            {
                "image": {
                    "bytesBase64Encoded": encoded_content,
                }
            }
        ],
        "parameters": {
            "sampleCount": 1,
            "language": "en",
        }
    }

    # Get the access token
    access_token = get_google_access_token()

    # Headers for the request
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }

    # Make the POST request
    response = requests.post(endpoint, json=payload, headers=headers)
    json.dumps(response.json(), indent=2)
    
    if response.status_code != 200:
        return "Error generating caption"
    return response.json()['predictions'][0].capitalize()

def get_google_access_token():
    # Load the service account credentials and get an access token
    credentials = service_account.Credentials.from_service_account_file(
        r'C:\Users\kubah\Desktop\django_img_captioning\image-captioning-424715-abc35ed4ae6b.json',
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
    credentials.refresh(Request())
    return credentials.token