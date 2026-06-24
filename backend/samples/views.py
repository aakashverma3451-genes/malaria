import django_filters
from django.db.models import Count
from rest_framework import viewsets

from .models import Project, RawFile, Sample, SequencingRun
from .serializers import (
    ProjectDetailSerializer,
    ProjectListSerializer,
    RawFileSerializer,
    SampleDetailSerializer,
    SampleListSerializer,
    SequencingRunSerializer,
)


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = (
        Project.objects.select_related('created_by')
        .annotate(sample_count=Count('samples'))
    )
    filterset_fields = ['organism', 'created_by']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'name']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProjectListSerializer
        return ProjectDetailSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class SampleFilter(django_filters.FilterSet):
    collection_date = django_filters.DateFromToRangeFilter()
    created_at = django_filters.DateFromToRangeFilter()

    class Meta:
        model = Sample
        fields = ['project', 'species', 'collection_date', 'created_at']


class SampleViewSet(viewsets.ModelViewSet):
    queryset = (
        Sample.objects.select_related('project', 'created_by')
        .annotate(file_count=Count('raw_files'))
    )
    filterset_class = SampleFilter
    search_fields = ['sample_id', 'external_id', 'collection_location']
    ordering_fields = ['created_at', 'collection_date', 'sample_id']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return SampleListSerializer
        return SampleDetailSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class SequencingRunViewSet(viewsets.ModelViewSet):
    queryset = SequencingRun.objects.select_related('created_by')
    serializer_class = SequencingRunSerializer
    filterset_fields = ['instrument']
    search_fields = ['run_id', 'chip_id']
    ordering_fields = ['run_date', 'created_at']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class RawFileViewSet(viewsets.ModelViewSet):
    queryset = RawFile.objects.select_related(
        'sample', 'sequencing_run', 'uploaded_by'
    )
    serializer_class = RawFileSerializer
    filterset_fields = [
        'sample', 'sample__project', 'file_type', 'upload_status', 'is_validated',
    ]
    search_fields = ['original_filename', 'md5_checksum']
    ordering_fields = ['uploaded_at', 'file_size_bytes']
    ordering = ['-uploaded_at']

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
