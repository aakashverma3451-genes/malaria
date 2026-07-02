from rest_framework import serializers

from samples.models import Sample

from .models import AnalysisJob, AnalysisJobSample, Result

REFERENCE_GENOMES = {'pf3d7', 'pvivax', 'agambiae'}
NUMERIC_PARAMS = ('min_read_quality', 'min_depth')


class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Result
        fields = [
            'id', 'job', 'result_type', 'file_path', 'summary_data', 'created_at',
        ]
        read_only_fields = ['created_at']


class AnalysisJobListSerializer(serializers.ModelSerializer):
    submitted_by = serializers.StringRelatedField(read_only=True)
    sample_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = AnalysisJob
        fields = [
            'id', 'name', 'workflow_type', 'status', 'progress_percent',
            'sample_count', 'submitted_by', 'submitted_at',
        ]


class AnalysisJobDetailSerializer(serializers.ModelSerializer):
    submitted_by = serializers.StringRelatedField(read_only=True)
    samples = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    sample_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=Sample.objects.all(),
        required=False,
    )
    results = ResultSerializer(many=True, read_only=True)

    class Meta:
        model = AnalysisJob
        fields = [
            'id', 'name', 'workflow_type', 'status', 'parameters',
            'samples', 'sample_ids', 'results', 'celery_task_id',
            'nextflow_run_name', 'submitted_by', 'submitted_at',
            'started_at', 'completed_at', 'error_message',
            'progress_percent', 'output_dir', 'execution_log',
        ]
        read_only_fields = [
            'status', 'celery_task_id', 'nextflow_run_name', 'submitted_by',
            'submitted_at', 'started_at', 'completed_at', 'error_message',
            'progress_percent', 'output_dir', 'execution_log',
        ]

    def validate_parameters(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError('parameters must be a JSON object.')
        for key in NUMERIC_PARAMS:
            if key in value and not isinstance(value[key], (int, float)):
                raise serializers.ValidationError(f'{key} must be a number.')
        ref = value.get('reference_genome')
        if ref is not None and ref not in REFERENCE_GENOMES:
            allowed = ', '.join(sorted(REFERENCE_GENOMES))
            raise serializers.ValidationError(
                f'reference_genome must be one of: {allowed}.'
            )
        return value

    def create(self, validated_data):
        samples = validated_data.pop('sample_ids', [])
        job = AnalysisJob.objects.create(**validated_data)
        self._set_samples(job, samples)
        return job

    def update(self, instance, validated_data):
        samples = validated_data.pop('sample_ids', None)
        instance = super().update(instance, validated_data)
        if samples is not None:
            instance.job_samples.all().delete()
            self._set_samples(instance, samples)
        return instance

    @staticmethod
    def _set_samples(job, samples):
        AnalysisJobSample.objects.bulk_create([
            AnalysisJobSample(job=job, sample=sample, order=order)
            for order, sample in enumerate(samples)
        ])
