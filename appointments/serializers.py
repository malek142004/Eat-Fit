from rest_framework import serializers
from .models import TrainingProgram, Feedback

class TrainingProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingProgram
        fields = ['id', 'user', 'title', 'description', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ['id', 'client', 'coach', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'client', 'created_at']