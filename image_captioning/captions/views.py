from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from .forms import ImageUploadForm
from .models import UploadedImage, Caption
import requests
import base64
import json
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from dotenv import load_dotenv
import os

load_dotenv()

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
        # Create a form instance and populate it with data from the request
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():

            image = form.cleaned_data['image']
            caption = generate_caption(image)
            fs = FileSystemStorage()
            filename = fs.save(image.name, image)
            uploaded_image = UploadedImage.objects.create(user=request.user, image=filename)

            # Save the caption in the session to display after redirect
            for caption_text in caption:
                    Caption.objects.create(image=uploaded_image, text=caption_text)
            request.session['caption'] = caption
            return redirect('upload_image')
    else:
        form = ImageUploadForm()

    # Retrieve the caption from the session if available
    caption = request.session.pop('caption', None)
    return render(request, 'upload.html', {'form': form, 'captions': caption})

def generate_caption(image):

    # Endpoint for the image captioning model
    endpoint = "https://us-central1-aiplatform.googleapis.com/v1/projects/image-captioning-424715/locations/us-central1/publishers/google/models/imagetext:predict"

    # Read the image file and encode it in base64
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
            "sampleCount": 3, 
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
    
    # Return the error message if the response is not successful
    if response.status_code != 200:
        return "Error generating caption"
    
    # Return the captions
    return response.json()['predictions']

def get_google_access_token():
    # Load the service account credentials and get an access token
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, 'image-captioning-424715-abc35ed4ae6b.json')
    credentials = service_account.Credentials.from_service_account_file(
        filename,
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
    credentials.refresh(Request())
    return credentials.token

def profile(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Retrieve the uploaded images for the current user
    uploaded_images = UploadedImage.objects.filter(user=request.user).order_by('-uploaded_at')
    return render(request, 'profile.html', {'uploaded_images': uploaded_images})
