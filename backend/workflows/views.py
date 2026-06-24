import django_filters
from django.db.models import Count
from rest_framework import viewsets

from .models import AnalysisJob, Result
from .serializers import (
    AnalysisJobDetailSerializer,
    AnalysisJobListSerializer,
    ResultSerializer,
)


class AnalysisJobFilter(django_filters.FilterSet):
    submitted_at = django_filters.DateFromToRangeFilter()

    class Meta:
        model = AnalysisJob
        fields = ['status', 'workflow_type', 'submitted_by', 'submitted_at']


class AnalysisJobViewSet(viewsets.ModelViewSet):
    queryset = (
        AnalysisJob.objects.select_related('submitted_by')
        .annotate(sample_count=Count('samples'))
        .prefetch_related('results')
    )
    filterset_class = AnalysisJobFilter
    search_fields = ['name']
    ordering_fields = ['submitted_at', 'status', 'progress_percent']
    ordering = ['-submitted_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return AnalysisJobListSerializer
        return AnalysisJobDetailSerializer

    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user)


class ResultViewSet(viewsets.ModelViewSet):
    queryset = Result.objects.select_related('job')
    serializer_class = ResultSerializer
    filterset_fields = ['job', 'result_type']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
