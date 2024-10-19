from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
import json
import os
import uuid
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Path to  videos.json file
VIDEO_JSON_FILE = os.path.join(os.path.dirname(__file__), 'data/videos.json')
# Path to  courses.json file
COURSES_FILE_PATH = os.path.join(os.path.dirname(__file__),  'data/courses.json')
# Path to  carousel.json file
CAROUSEL_FILE_PATH = os.path.join(os.path.dirname(__file__),  'data/carousel.json')

# --------------------  Admin Login
@csrf_exempt  # Disable CSRF for this view (only for development; in production, handle CSRF properly)
def admin_login(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        # Check credentials
        if username == "admin" and password == "admin":
            return JsonResponse({'status': 'success'}, status=200)
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid credentials'}, status=401)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)


def get_data(request):
    # Path to the JSON file
    json_file_path = os.path.join(os.path.dirname(__file__), 'data/home_data.json')
    
    # Read the JSON file
    with open(json_file_path, 'r') as file:
        data = json.load(file)
        
    return JsonResponse(data, safe=False)  # Set safe=False to allow a list response

# --------------------  Gallery Management

def video_gallery(request):
    # Path to the JSON file
        
    with open(VIDEO_JSON_FILE) as f:
        data = json.load(f)

    return JsonResponse(data, safe=False)

@csrf_exempt  
@require_http_methods(["DELETE"])
def delete_video(request, video_id):
    try:
        # Load existing videos
        with open(VIDEO_JSON_FILE, 'r') as file:
            videos = json.load(file)

        # Find and remove the video with the given ID
        videos = [video for video in videos if video['id'] != video_id]

        # Write updated list back to JSON file
        with open(VIDEO_JSON_FILE, 'w') as file:
            json.dump(videos, file)

        return JsonResponse({'status': 'success', 'message': 'Video deleted'}, status=200)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
def add_video(request):
    data = json.loads(request.body)
    videoUrl = data.get("videoUrl")
    description = data.get("description")
    
    # Load existing videos
    with open(VIDEO_JSON_FILE, "r") as f:  # Update with your actual path
        videos = json.load(f)

    # Create a new video entry
    new_video = {
        "id": str(uuid.uuid4()),  # Generate a unique ID
        "videoUrl": videoUrl,
        "description": description,
    }

    # Prepend new video to existing videos
    videos.insert(0, new_video)  # Insert at the beginning of the list

    # Save updated videos back to the JSON file
    with open(VIDEO_JSON_FILE, "w") as f:  # Update with your actual path
        json.dump(videos, f)

    return JsonResponse({"status": "success", "video": new_video}, status=201)



# --------------------  Courses Management
# Fetch course details by category
def get_course_by_category(request, category):
    courses_data = load_courses_data()
    
    # Filter the category from the list
    course_details = next((course for course in courses_data if course['category'] == category), None)
    
    if course_details:
        return JsonResponse(course_details, safe=False)
    else:
        return JsonResponse({'error': 'Category not found'}, status=404)

# Load the courses data
def load_courses_data():
    with open(COURSES_FILE_PATH, 'r') as file:
        return json.load(file)

# Save updated courses data
def save_courses_data(courses_data):
    with open(COURSES_FILE_PATH, 'w') as file:
        json.dump(courses_data, file, indent=4)
        
@csrf_exempt
def update_course_details(request, category):
    if request.method == 'POST':
        # Load existing courses data
        courses_data = load_courses_data()
        
        images_before=[]
        # images before deletion
        for course in courses_data:
            if course['category'] == category:
                if course['image']:
                    images_before=course['image']
        
        # Get the uploaded images from request.FILES
        uploaded_images = request.FILES.getlist("images")  # Get list of uploaded images

        # Define image storage paths
        react_app_static_path = os.path.join(BASE_DIR, 'client', 'public', 'static', 'image')

        # Initialize image names
        image_names = []

        # Save images to the appropriate directories and get file names
        for image in uploaded_images:
            fs = FileSystemStorage(location=os.path.join(react_app_static_path, 'courses', category))
            image_name = fs.save(image.name, image)
            image_names.append(os.path.basename(image_name))  # Collect new image names

        # Extract other data from request.POST
        help_line=request.POST.get('help_line')
        description = request.POST.getlist('description')  # Get list of descriptions
        goals = request.POST.getlist('goals')  # Get list of goals
        actorCategories = request.POST.getlist('actorCategories')  # Get list of actor categories
        images_present = request.POST.getlist('images_names')  # Get list of images to delete (images_names_remaining)
        
        # Find the course by category in the data
        for course in courses_data:
            if course['category'] == category:
                # Update the description, goals, and actor categories if new values are provided
                course['description'] = description 
                course['goals'] = goals
                course['actorCategories'] = actorCategories
                course['help_line']=help_line
                
                # Step 1: Clear the `image` array
                course['image'] = []  # This will clear the current `image` array
                
                # Step 2: Append images_names_remaining (images_present) and the newly uploaded images
                course['image'].extend(images_present)  # Append images to delete (remaining images)
                course['image'].extend(image_names)  # Append new uploaded image names
                
                # Save the updated data
                save_courses_data(courses_data)
                images_to_remove=[]
                # Find and print images present in images_before but not in image_names
                if images_before:
                    images_to_remove = set(images_before) - set(course['image'])
                
                # Delete the images which are in images_to_remove
                if images_to_remove:
                    for image in images_to_remove:
                        image_path = os.path.join(react_app_static_path, 'courses', category, image)
                        if os.path.exists(image_path):
                            os.remove(image_path)
                            print(f"Deleted image: {image}")

                return JsonResponse({'message': 'Course updated successfully'}, status=200)

        return JsonResponse({'error': 'Category not found'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

# ----------------------------------- User ---------------------------------

def get_courses_by_category(request, category):
    # Path to the courses.json file
    file_path = os.path.join(os.path.dirname(__file__), 'data/courses.json')

    # Load JSON data
    with open(file_path, 'r') as file:
        courses_data = json.load(file)

    # Filter courses based on category
    filtered_courses = [course for course in courses_data if course["category"] == category]

    # If no courses found, return a 404 response
    if not filtered_courses:
        return JsonResponse({"error": "Category not found"}, status=404)

    # Return the filtered courses as JSON response
    return JsonResponse(filtered_courses, safe=False)

from django.views.decorators.csrf import csrf_exempt

# @csrf_exempt
# def add_category(request):
#     if request.method == 'POST':
#         # Get the data from the request
#         data = json.loads(request.body)
#         new_category = {
#             "category": data.get("category"),
#             "card_icon": data.get("card_icon", "faIcon"),
#             "card_image": data.get("card_image", "/static/image/home/cards/default-card.jpeg"),
#             "image": data.get("image", []),
#             "heading": f"Best {data.get('category')} Classes",
#             "description": data.get("description", ["Enter description for the new category."]),
#             "actorCategories": data.get("actorCategories", ["Enter actor categories for the new category."]),
#             "goals": data.get("goals", ["Enter goals for the new category."]),
#         }

#         # Load the courses.json file
#         try:
#             with open(COURSES_FILE_PATH, 'r+') as file:
#                 courses_data = json.load(file)

#                 # Add the new category to the courses data
#                 courses_data["categories"].append(new_category)

#                 # Write the updated data back to the file
#                 file.seek(0)
#                 json.dump(courses_data, file, indent=4)
#                 file.truncate()

#             return JsonResponse({"message": "Category added successfully"}, status=201)
#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=500)

#     return JsonResponse({"error": "Invalid request method"}, status=400)

def get_carousel_images(request):
    try:
        with open(CAROUSEL_FILE_PATH, 'r') as file:
            data = json.load(file)
        return JsonResponse(data, safe=False)
    except FileNotFoundError:
        return JsonResponse({"error": "Carousel data not found."}, status=404)
    
def get_courses(request):
    with open(COURSES_FILE_PATH) as f:
        courses = json.load(f)
    return JsonResponse(courses, safe=False)

@csrf_exempt
def add_carousel_image(request):
    if request.method == 'POST' and request.FILES.getlist('images'):
        try:
            images = request.FILES.getlist('images')
            
            # Define image storage paths
            react_app_static_path = os.path.join(BASE_DIR, 'client', 'public', 'static', 'image')
            
            # Read the existing carousel data
            with open(CAROUSEL_FILE_PATH, 'r+') as file:
                carousel_data = json.load(file)

                new_images = []
                
                for image in images:
                    fs = FileSystemStorage(location=os.path.join(react_app_static_path, 'carousel'))
                    image_name = fs.save(image.name, image)
                    image_name=os.path.basename(image_name)
                    # image_names.append(os.path.basename(image_name))  

                    # Generate unique id using UUID
                    image_id = str(uuid.uuid4())

                    # Add new image data to the list
                    new_image = {
                        "id": image_id,
                        "url": image_name  # Use the file's URL
                    }
                    
                    new_images.append(new_image)
                    carousel_data.append(new_image)

                # Write the updated data back to the file
                file.seek(0)
                json.dump(carousel_data, file, indent=4)
                file.truncate()

            return JsonResponse(new_images, status=201, safe=False)

        except (json.JSONDecodeError, FileNotFoundError):
            return JsonResponse({"error": "Invalid data or carousel file not found."}, status=400)

    return JsonResponse({"error": "Invalid request method or no images found."}, status=405)

@csrf_exempt
def delete_carousel_image(request, image_id):
    if request.method == 'DELETE':
        try:
            # Read the existing carousel data
            with open(CAROUSEL_FILE_PATH, 'r+') as file:
                carousel_data = json.load(file)
                
                # Find the image with the given id
                image_to_delete = next((img for img in carousel_data if img['id'] == image_id), None)
                
                if not image_to_delete:
                    return JsonResponse({"error": "Image not found"}, status=404)

                # Remove the image entry from the JSON data
                carousel_data = [img for img in carousel_data if img['id'] != image_id]

                # Write the updated data back to the file
                file.seek(0)
                json.dump(carousel_data, file, indent=4)
                file.truncate()

                # Remove the image file from the filesystem
                image_path = os.path.join(BASE_DIR, 'client', 'public', 'static', 'image', 'carousel', image_to_delete['url'])
                if os.path.exists(image_path):
                    os.remove(image_path)

            return JsonResponse({"message": "Image deleted successfully"}, status=200)

        except (json.JSONDecodeError, FileNotFoundError):
            return JsonResponse({"error": "Invalid data or carousel file not found"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
def add_category(request):
    if request.method == "POST":
        try:
            # Open the JSON file and load the data (which is a list, not a dictionary)
            with open(COURSES_FILE_PATH, 'r') as file:
                data = json.load(file)

            # Get the new category data from the request
            category_data = json.loads(request.body)

            # Generate a unique UUID for the new category
            new_category_id = str(uuid.uuid4())
            
            # Create the new category object to append to the data (list)
            new_category = {
                "id": new_category_id,
                "category": category_data.get('category', ''),
                "card_icon": category_data.get('card_icon', ''),
                "card_image": category_data.get('card_image', ''),
                "heading": category_data.get('heading', ''),
                "help_line": category_data.get('help_line', ''),
                "description": category_data.get('description', []),
                "actorCategories": category_data.get('actorCategories', []),
                "goals": category_data.get('goals', []),
                "image": category_data.get("images", [])
            }

            # Append the new category to the list
            data.append(new_category)

            # Write the updated data back to the JSON file
            with open(COURSES_FILE_PATH, 'w') as file:
                json.dump(data, file, indent=4)
            print("File written successfully")

            return JsonResponse({"message": "Category added successfully"}, status=200)

        except Exception as e:
            print("Error occurred:", str(e))
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
def delete_category(request, category_id):
    if request.method == 'DELETE':
        try:
            # Load the existing data from the JSON file
            with open(COURSES_FILE_PATH, 'r') as file:
                courses_data = json.load(file)

            for c in courses_data:
                if c['id']==category_id:
                    course_folder_name=c['category']
                    
            print(course_folder_name)
                    
            # Remove the category with the given ID
            courses_data = [course for course in courses_data if course['id'] != category_id]

            # Save the updated data back to the JSON file
            with open(COURSES_FILE_PATH, 'w') as file:
                json.dump(courses_data, file, indent=4)
                
            # Remove the image file from the filesystem
            folder_path = os.path.join(BASE_DIR, 'client', 'public', 'static', 'image', 'courses',course_folder_name)
            
            # delete images folder
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                shutil.rmtree(folder_path)

            return JsonResponse({"message": "Category deleted successfully!"}, status=200)

        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({"message": str(e)}, status=500)
    else:
        return JsonResponse({"message": "Method not allowed"}, status=405)
