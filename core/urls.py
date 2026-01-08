from django.contrib import admin
from django.urls import path
from app.views import DirectionListAPIView, DirectionDetailAPIView, LocationDetailAPIView,SectionDetailAPIView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('direction/',DirectionListAPIView.as_view()),
    path('directions/<int:pk>/', DirectionDetailAPIView.as_view()),
    path('locations/<int:pk>/', LocationDetailAPIView.as_view()),
    path('sections/<int:pk>/', SectionDetailAPIView.as_view()),
]
