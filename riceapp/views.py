import os
import uuid
import cv2
from django.conf import settings
from django.shortcuts import render
from .forms import ImageUploadForm

# Function to detect broken rice grains
def detect_broken_rice(img_path):
    img = cv2.imread(img_path)

    # Safety check: if image can't be read
    if img is None:
        raise ValueError(f"Could not read image: {img_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 120, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 100:
            x, y, w, h = cv2.boundingRect(cnt)

            # Check if it's broken (small size)
            if w < 30 or h < 30:
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)  # Red box
            else:
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Green box

    # Save result image
    output_filename = f"{uuid.uuid4()}.jpg"
    output_path = os.path.join(settings.MEDIA_ROOT, output_filename)
    cv2.imwrite(output_path, img)

    return output_filename

# Django view
def index(request):
    result_image = None

    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            image_file = form.cleaned_data['image']

            # Create a unique filename
            filename = f"{uuid.uuid4()}_{image_file.name}"
            saved_path = os.path.join(settings.MEDIA_ROOT, filename)

            # Ensure media directory exists
            os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

            # Save uploaded image
            with open(saved_path, 'wb+') as destination:
                for chunk in image_file.chunks():
                    destination.write(chunk)

            try:
                # Process the saved image
                result_filename = detect_broken_rice(saved_path)
                result_image = settings.MEDIA_URL + result_filename
            except Exception as e:
                return render(request, 'riceapp/index.html', {
                    'form': form,
                    'error': f"Error processing image: {e}"
                })

    else:
        form = ImageUploadForm()

    return render(request, 'riceapp/index.html', {
        'form': form,
        'result_image': result_image
    })
