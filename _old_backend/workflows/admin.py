from django.contrib import admin

from .models import AnalysisJob, AnalysisJobSample, Result


class AnalysisJobSampleInline(admin.TabularInline):
    model = AnalysisJobSample
    extra = 0
    autocomplete_fields = ('sample',)


@admin.register(AnalysisJob)
class AnalysisJobAdmin(admin.ModelAdmin):
    list_display = (
        '__str__', 'workflow_type', 'status', 'progress_percent',
        'submitted_by', 'submitted_at',
    )
    list_filter = ('status', 'workflow_type', 'submitted_at')
    search_fields = ('name', 'nextflow_run_name', 'celery_task_id')
    inlines = [AnalysisJobSampleInline]
    autocomplete_fields = ('submitted_by',)


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('result_type', 'job', 'created_at')
    list_filter = ('result_type', 'created_at')
    search_fields = ('file_path',)
    autocomplete_fields = ('job',)
