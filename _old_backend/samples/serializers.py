from rest_framework import serializers

from .models import Project, RawFile, Sample, SequencingRun


class ProjectListSerializer(serializers.ModelSerializer):
    sample_count = serializers.IntegerField(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'organism', 'sample_count',
            'created_by', 'created_at',
        ]


class ProjectDetailSerializer(serializers.ModelSerializer):
    sample_count = serializers.IntegerField(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'organism', 'sample_count',
            'created_by', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']


class SampleListSerializer(serializers.ModelSerializer):
    file_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Sample
        fields = [
            'id', 'project', 'sample_id', 'external_id', 'species',
            'collection_date', 'collection_location', 'file_count', 'created_at',
        ]


class SampleDetailSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Sample
        fields = [
            'id', 'project', 'sample_id', 'external_id', 'species',
            'collection_date', 'collection_location', 'latitude', 'longitude',
            'metadata', 'notes', 'created_by', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def validate_sample_id(self, value: str) -> str:
        value = (value or '').strip()
        if not value:
            raise serializers.ValidationError(
                'sample_id is required and cannot be blank.'
            )
        return value


class SequencingRunSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = SequencingRun
        fields = [
            'id', 'run_id', 'instrument', 'chip_id', 'run_date',
            'notes', 'created_by', 'created_at',
        ]
        read_only_fields = ['created_by', 'created_at']


class RawFileSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = RawFile
        fields = [
            'id', 'sample', 'sequencing_run', 'file_path', 'original_filename',
            'file_type', 'file_size_bytes', 'md5_checksum', 'is_validated',
            'upload_status', 'uploaded_by', 'uploaded_at',
        ]
        read_only_fields = ['uploaded_by', 'uploaded_at']

    def validate_file_size_bytes(self, value: int) -> int:
        if value <= 0:
            raise serializers.ValidationError(
                'file_size_bytes must be a positive integer.'
            )
        return value
