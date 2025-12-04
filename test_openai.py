import os
import django
from django.conf import settings
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projet_eatandfit.settings')
django.setup()

print("OPENAI_API_KEY from settings:", settings.OPENAI_API_KEY)
print("OPENAI_API_KEY from env:", os.getenv('OPENAI_API_KEY'))

from users.views import estimate_nutrition_with_openai

# Test with a sample image path (you can replace with an actual image)
# For now, let's assume there's a test image in media
test_image_path = 'media/profile_pics/images_2.jpeg'  # Replace with actual path if needed

if os.path.exists(test_image_path):
    try:
        result = estimate_nutrition_with_openai(test_image_path)
        print("API Key is working! Result:", result)
    except Exception as e:
        print("Error:", str(e))
else:
    print("Test image not found. Please provide a valid image path.")
