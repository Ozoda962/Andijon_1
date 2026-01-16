# from django.shortcuts import render
# from rest_framework import generics
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from .models import Direction, Location, Section, Datchik, DatchikLog
# from .serializers import DirectionSerializer,LocationSerializer, SectionSerializer, DatchikSerializer

# class DirectionListAPIView(generics.ListAPIView):
#     queryset = Direction.objects.all()
#     serializer_class = DirectionSerializer

# class DirectionDetailAPIView(APIView):
#     def get(self, request, pk):
#         try:
#             direction = Direction.objects.get(pk=pk)
#         except Direction.DoesNotExist:
#             return Response({"error": "Direction not found"}, status=404)

#         locations = direction.direction_locations.all()
#         if locations.exists():
#             return Response({"locations": LocationSerializer(locations, many=True).data})

#         sections = direction.direction_sections.all()
#         if sections.exists():
#             return Response({"sections": SectionSerializer(sections, many=True).data})

#         datchiks = direction.direction_datchiks.all()
#         return Response({"datchiks": DatchikSerializer(datchiks, many=True).data})
    
# class LocationDetailAPIView(APIView):
#     def get(self, request, pk):
#         try:
#             location = Location.objects.get(pk=pk)
#         except Location.DoesNotExist:
#             return Response({"error": "Location not found"}, status=404)

#         sections = location.location_sections.all()
#         if sections.exists():
#             return Response({"sections": SectionSerializer(sections, many=True).data})

#         datchiks = location.location_datchiks.all()
#         return Response({"datchiks": DatchikSerializer(datchiks, many=True).data})
    
# class SectionDetailAPIView(APIView):
#     def get(self, request, pk):
#         try:
#             section = Section.objects.get(pk=pk)
#         except Section.DoesNotExist:
#             return Response({"error": "Section not found"}, status=404)

#         datchiks = section.section_datchiks.all()
#         return Response({"datchiks": DatchikSerializer(datchiks, many=True).data})