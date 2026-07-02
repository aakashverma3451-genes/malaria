from rest_framework import viewsets

from .models import Report
from .serializers import ReportSerializer


class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.select_related('job', 'generated_by')
    serializer_class = ReportSerializer
    filterset_fields = ['job', 'report_type']
    search_fields = ['title']
    ordering_fields = ['generated_at']
    ordering = ['-generated_at']

    def perform_create(self, serializer):
        serializer.save(generated_by=self.request.user)
