from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="reels-index"),
    path("upload/", views.upload, name="reels-upload"),
    path("jobs/<int:job_id>/", views.detail, name="reels-detail"),
    path("jobs/<int:job_id>/process/", views.process, name="reels-process"),
]
