from django.shortcuts import render

# Create your views here.
def index(request):
    context = {
        'range_6': range(1, 7),  # 1 to 6
    }
    return render(request, 'index.html', context)

def home(request):
    gallery_range = range(1, 7)  # 1 to 6 for gallery images
    return render(request, "index.html", {"gallery_range": gallery_range})
def about(request):
    gallery_images = [
        {"src": "img/gallery/1.jpg", "caption": "ahana.yoga"},
        {"src": "img/gallery/2.jpg", "caption": "ahana.yoga"},
        {"src": "img/gallery/3.jpg", "caption": "ahana.yoga"},
        {"src": "img/gallery/4.jpg", "caption": "ahana.yoga"},
        {"src": "img/gallery/5.jpg", "caption": "ahana.yoga"},
        {"src": "img/gallery/6.jpg", "caption": "ahana.yoga"},
    ]

    return render(request, "about.html", {"gallery_images": gallery_images})

def about(request):
    return render(request, 'about.html')
def classes(request):
    return render(request, 'classes.html')
def classes_details(request):
    return render(request, 'class-details.html')
def trainers(request):
    return render(request, 'trainers.html')
def events(request):
    return render(request, 'events.html')
def trainer_details(request):
    return render(request, 'trainer-details.html')
def blog(request):
    return render(request, 'blog.html')
def blog_details(request):
    return render(request, 'blog-details.html')
def contact(request):
    return render(request, 'contact.html')
def single_blog(request):
    return render(request, 'single-blog.html')

