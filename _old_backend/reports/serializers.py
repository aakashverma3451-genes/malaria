from rest_framework import serializers

from .models import Report


class ReportSerializer(serializers.ModelSerializer):
    generated_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Report
        fields = [
            'id', 'job', 'title', 'report_type', 'file_path',
            'generated_by', 'generated_at',
        ]
        read_only_fields = ['generated_by', 'generated_at']
