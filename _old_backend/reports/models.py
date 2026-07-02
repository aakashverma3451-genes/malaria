from __future__ import annotations

from django.conf import settings
from django.db import models


class Report(models.Model):
    """A generated PDF report for an analysis job."""

    class ReportType(models.TextChoices):
        SINGLE_SAMPLE = 'single_sample', 'Single sample'
        POPULATION = 'population', 'Population'
        CUSTOM = 'custom', 'Custom'

    job = models.ForeignKey(
        'workflows.AnalysisJob',
        on_delete=models.CASCADE,
        related_name='reports',
    )
    title = models.CharField(max_length=255)
    report_type = models.CharField(max_length=20, choices=ReportType.choices)
    file_path = models.CharField(max_length=1000)
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='reports',
    )

    class Meta:
        ordering = ['-generated_at']

    def __str__(self) -> str:
        return self.title
