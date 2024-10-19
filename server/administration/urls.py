from django.urls import path
from .views import get_data,video_gallery,admin_login,delete_video,add_video,get_courses_by_category,get_course_by_category,update_course_details,get_carousel_images,get_courses,add_carousel_image,delete_carousel_image,add_category,delete_category

urlpatterns = [
    path('data/', get_data, name='get_data'),
    path('videos/', video_gallery, name='video_gallery'),
    path('adminlogin/', admin_login, name='admin_login'),
    path('deletevideo/<str:video_id>/', delete_video, name='delete_video'),  # URL for deleting a video
    path('addvideo/', add_video, name='add_video'), 
    path('courses/<str:category>/', get_courses_by_category, name='get_courses_by_category'),
    path('admincourses/<str:category>/', get_course_by_category, name='get_courses'),
    path('admincourses/update/<str:category>/', update_course_details, name='update_courses'),
    path('allcourses/', get_courses, name='get_courses'),
    # path('admincategory/addcategory/', add_category, name='add_category'),
    path('carousel/', get_carousel_images, name='carousel_images'),
    path('carousel/add/', add_carousel_image, name='add_carousel_image'),
    path('carousel/delete/<str:image_id>/', delete_carousel_image, name='delete_carousel_image'),
    path('admincategory/addcategory/', add_category, name='add_category'),
    path('deletecategory/<str:category_id>/', delete_category, name='delete_category'),
]
