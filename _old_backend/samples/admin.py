from django.contrib import admin

from .models import Project, RawFile, Sample, SequencingRun


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'organism', 'created_by', 'created_at')
    list_filter = ('organism', 'created_at')
    search_fields = ('name', 'description')
    autocomplete_fields = ('created_by',)


@admin.register(Sample)
class SampleAdmin(admin.ModelAdmin):
    list_display = (
        'sample_id', 'project', 'species', 'collection_date', 'created_by',
    )
    list_filter = ('species', 'collection_date', 'project')
    search_fields = ('sample_id', 'external_id', 'collection_location')
    autocomplete_fields = ('project', 'created_by')


@admin.register(SequencingRun)
class SequencingRunAdmin(admin.ModelAdmin):
    list_display = ('run_id', 'instrument', 'run_date', 'created_by')
    list_filter = ('instrument', 'run_date')
    search_fields = ('run_id', 'chip_id')


@admin.register(RawFile)
class RawFileAdmin(admin.ModelAdmin):
    list_display = (
        'original_filename', 'sample', 'file_type', 'upload_status',
        'is_validated', 'uploaded_at',
    )
    list_filter = ('file_type', 'upload_status', 'is_validated')
    search_fields = ('original_filename', 'md5_checksum')
    autocomplete_fields = ('sample', 'sequencing_run', 'uploaded_by')
