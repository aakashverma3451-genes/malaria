from django.conf import settings
from django.db import models


class Organism(models.TextChoices):
    """Target organisms handled by the platform."""
    P_FALCIPARUM = 'pf', 'Plasmodium falciparum'
    P_VIVAX = 'pv', 'Plasmodium vivax'
    A_GAMBIAE = 'ag', 'Anopheles gambiae'
    OTHER = 'other', 'Other'


class Project(models.Model):
    """A research project grouping related samples."""

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    organism = models.CharField(
        max_length=10,
        choices=Organism.choices,
        default=Organism.OTHER,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='projects',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'created_by'],
                name='unique_project_name_per_user',
            ),
        ]

    def __str__(self) -> str:
        return self.name


class Sample(models.Model):
    """A biological sample belonging to a project."""

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='samples',
    )
    sample_id = models.CharField(
        max_length=100,
        help_text="The lab's identifier for this sample.",
    )
    external_id = models.CharField(
        max_length=100,
        blank=True,
        help_text='External identifier, e.g. a MalariaGEN ID.',
    )
    species = models.CharField(
        max_length=10,
        choices=Organism.choices,
        default=Organism.OTHER,
    )
    collection_date = models.DateField(null=True, blank=True)
    collection_location = models.CharField(max_length=255, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='samples',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['sample_id', 'project'],
                name='unique_sample_id_per_project',
            ),
        ]
        indexes = [
            models.Index(fields=['sample_id']),
            models.Index(fields=['species']),
        ]

    def __str__(self) -> str:
        return self.sample_id


class SequencingRun(models.Model):
    """A sequencing run that produced one or more raw files."""

    class Instrument(models.TextChoices):
        ILLUMINA_MISEQ = 'illumina_miseq', 'Illumina MiSeq'
        ILLUMINA_HISEQ = 'illumina_hiseq', 'Illumina HiSeq'
        ILLUMINA_NEXTSEQ = 'illumina_nextseq', 'Illumina NextSeq'
        ILLUMINA_NOVASEQ = 'illumina_novaseq', 'Illumina NovaSeq'
        ION_TORRENT = 'ion_torrent', 'Ion Torrent'
        NANOPORE = 'nanopore', 'Oxford Nanopore'
        OTHER = 'other', 'Other'

    run_id = models.CharField(max_length=100, unique=True)
    instrument = models.CharField(
        max_length=20,
        choices=Instrument.choices,
        default=Instrument.OTHER,
    )
    chip_id = models.CharField(
        max_length=100,
        blank=True,
        help_text='Flowcell / chip barcode.',
    )
    run_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='sequencing_runs',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.run_id


class RawFile(models.Model):
    """A raw data file (FASTQ/BAM/VCF) attached to a sample."""

    class FileType(models.TextChoices):
        FASTQ_R1 = 'fastq_r1', 'FASTQ R1'
        FASTQ_R2 = 'fastq_r2', 'FASTQ R2'
        FASTQ_SINGLE = 'fastq_single', 'FASTQ single-end'
        BAM = 'bam', 'BAM'
        VCF = 'vcf', 'VCF'
        OTHER = 'other', 'Other'

    class UploadStatus(models.TextChoices):
        UPLOADING = 'uploading', 'Uploading'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    sample = models.ForeignKey(
        Sample,
        on_delete=models.CASCADE,
        related_name='raw_files',
    )
    sequencing_run = models.ForeignKey(
        SequencingRun,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='raw_files',
    )
    file_path = models.CharField(max_length=1000)
    original_filename = models.CharField(max_length=500)
    file_type = models.CharField(max_length=20, choices=FileType.choices)
    file_size_bytes = models.BigIntegerField()
    md5_checksum = models.CharField(max_length=32, blank=True)
    is_validated = models.BooleanField(default=False)
    upload_status = models.CharField(
        max_length=20,
        choices=UploadStatus.choices,
        default=UploadStatus.UPLOADING,
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='uploaded_files',
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['upload_status']),
        ]

    def __str__(self) -> str:
        return self.original_filename
