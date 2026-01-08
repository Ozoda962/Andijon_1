from rest_framework import serializers
from .models import Direction, Location, Section, Datchik, DatchikLog

class DirectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Direction
        fields = '__all__'


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'


class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = '__all__'

    
    def validate(self, data):
        if data['direction'] != data['location'].direction:
            raise serializers.ValidationError("Section direction must match Location direction.")
        return data


class DatchikSerializer(serializers.ModelSerializer):
    class Meta:
        model = Datchik
        fields = '__all__'

   
    def validate(self, data):
        if data.get('section') and data['section'].direction != data['direction']:
            raise serializers.ValidationError("Datchik's section direction must match its direction.")
        return data


class DatchikLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatchikLog
        fields = '__all__'

    
    def validate(self, data):
        if data.get('humidity') and not data['humidity'].replace('.', '', 1).isdigit():
            raise serializers.ValidationError("Humidity should be a number.")
        return data
