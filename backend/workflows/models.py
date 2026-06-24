from __future__ import annotations

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class WorkflowType(models.TextChoices):
    """The analysis pipelines the platform can run."""
    SINGLE_SAMPLE_QC = 'single_qc', 'Single sample — QC'
    SINGLE_SAMPLE_FULL = 'single_full', 'Single sample — full (QC + align + call + annotate)'
    POPULATION_JOINT_CALLING = 'pop_joint', 'Population — joint calling'
    POPULATION_STRUCTURE = 'pop_structure', 'Population — structure'
    POPULATION_PHYLOGENETICS = 'pop_phylo', 'Population — phylogenetics'
    POPULATION_SELECTION = 'pop_selection', 'Population — selection'
    POPULATION_FULL = 'pop_full', 'Population — full'


class AnalysisJob(models.Model):
    """A single submission of a workflow over one or more samples."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        QUEUED = 'queued', 'Queued'
        RUNNING = 'running', 'Running'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
        CANCELLED = 'cancelled', 'Cancelled'

    name = models.CharField(max_length=255, blank=True)
    workflow_type = models.CharField(max_length=20, choices=WorkflowType.choices)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    parameters = models.JSONField(default=dict)
    samples = models.ManyToManyField(
        'samples.Sample',
        through='AnalysisJobSample',
        related_name='analysis_jobs',
    )
    celery_task_id = models.CharField(max_length=255, blank=True)
    nextflow_run_name = models.CharField(max_length=255, blank=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='submitted_jobs',
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    progress_percent = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    output_dir = models.CharField(max_length=1000, blank=True)
    execution_log = models.TextField(blank=True)

    class Meta:
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['workflow_type']),
        ]

    def __str__(self) -> str:
        return self.name or f'{self.get_workflow_type_display()} #{self.pk}'


class AnalysisJobSample(models.Model):
    """Through table linking a job to its samples, preserving order."""

    job = models.ForeignKey(
        AnalysisJob,
        on_delete=models.CASCADE,
        related_name='job_samples',
    )
    sample = models.ForeignKey(
        'samples.Sample',
        on_delete=models.CASCADE,
        related_name='job_samples',
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        constraints = [
            models.UniqueConstraint(
                fields=['job', 'sample'],
                name='unique_job_sample',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.job} — {self.sample}'


class Result(models.Model):
    """An output artifact produced by an analysis job."""

    class ResultType(models.TextChoices):
        QC_REPORT = 'qc_report', 'QC report'
        ALIGNMENT_STATS = 'alignment_stats', 'Alignment stats'
        VARIANT_CALLS = 'variant_calls', 'Variant calls'
        ANNOTATED_VARIANTS = 'annotated_variants', 'Annotated variants'
        FWS = 'fws', 'Fws'
        IBD_MATRIX = 'ibd_matrix', 'IBD matrix'
        ADMIXTURE = 'admixture', 'Admixture'
        PHYLOGENETIC_TREE = 'phylogenetic_tree', 'Phylogenetic tree'
        DIVERSITY_STATS = 'diversity_stats', 'Diversity stats'
        SELECTION_SCAN = 'selection_scan', 'Selection scan'
        FULL_REPORT = 'full_report', 'Full report'
        OTHER = 'other', 'Other'

    job = models.ForeignKey(
        AnalysisJob,
        on_delete=models.CASCADE,
        related_name='results',
    )
    result_type = models.CharField(max_length=20, choices=ResultType.choices)
    file_path = models.CharField(max_length=1000, blank=True)
    summary_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.get_result_type_display()} ({self.job})'
