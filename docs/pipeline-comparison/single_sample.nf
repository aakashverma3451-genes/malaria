#!/usr/bin/env nextflow
nextflow.enable.dsl = 2

/*
 * ─────────────────────────────────────────────────────────────────────────────
 * Single-sample variant calling — Nextflow (DSL2) sketch (engine-comparison).
 * Stages: fastp QC/trim -> BWA-MEM align -> GATK MarkDuplicates + HaplotypeCaller
 *         -> SnpEff annotate. Target: P. falciparum (Pf3D7).
 * NOTE: container tags / reference index handling are illustrative. A real build
 *       would use combined (mulled) bwa+samtools images and pre-built indices.
 * Run:  nextflow run single_sample.nf \
 *         --sample_id PF001 --fastq_r1 r1.fq.gz --fastq_r2 r2.fq.gz
 * ─────────────────────────────────────────────────────────────────────────────
 */

params.sample_id        = null
params.fastq_r1         = null
params.fastq_r2         = null
params.reference        = "${projectDir}/../../reference-data/Pf3D7.fasta"
params.snpeff_db        = "Pfalciparum3D7"
params.min_base_quality = 20
params.outdir           = "results"

process FASTP_QC {
    tag "$sample_id"
    container 'quay.io/biocontainers/fastp:0.23.4--h5f740d0_0'
    cpus 4
    memory '8 GB'
    publishDir "${params.outdir}/qc", mode: 'copy', pattern: '*.json'

    input:
        tuple val(sample_id), path(r1), path(r2)

    output:
        tuple val(sample_id),
              path("${sample_id}.trimmed.R1.fastq.gz"),
              path("${sample_id}.trimmed.R2.fastq.gz"), emit: trimmed
        path "${sample_id}.fastp.json", emit: qc

    script:
    """
    fastp --in1 $r1 --in2 $r2 \
        --out1 ${sample_id}.trimmed.R1.fastq.gz \
        --out2 ${sample_id}.trimmed.R2.fastq.gz \
        --qualified_quality_phred ${params.min_base_quality} \
        --json ${sample_id}.fastp.json
    """
}

process BWA_ALIGN {
    tag "$sample_id"
    container 'quay.io/biocontainers/bwa:0.7.17--he4a0461_11'
    cpus 4
    memory '16 GB'

    input:
        tuple val(sample_id), path(r1), path(r2)
        path reference

    output:
        tuple val(sample_id),
              path("${sample_id}.sorted.bam"),
              path("${sample_id}.sorted.bam.bai"), emit: bam

    script:
    """
    bwa index $reference
    bwa mem -t ${task.cpus} \
        -R "@RG\\tID:${sample_id}\\tSM:${sample_id}\\tPL:ILLUMINA" \
        $reference $r1 $r2 \
      | samtools sort -@ ${task.cpus} -o ${sample_id}.sorted.bam -
    samtools index ${sample_id}.sorted.bam
    """
}

process CALL_VARIANTS {
    tag "$sample_id"
    container 'broadinstitute/gatk:4.5.0.0'
    cpus 2
    memory '16 GB'
    publishDir "${params.outdir}/vcf", mode: 'copy'

    input:
        tuple val(sample_id), path(bam), path(bai)
        path reference

    output:
        tuple val(sample_id), path("${sample_id}.vcf.gz"), emit: vcf

    script:
    """
    gatk MarkDuplicates -I $bam -O ${sample_id}.dedup.bam -M ${sample_id}.dup_metrics.txt
    samtools index ${sample_id}.dedup.bam
    gatk HaplotypeCaller -R $reference -I ${sample_id}.dedup.bam -O ${sample_id}.vcf.gz
    """
}

process ANNOTATE {
    tag "$sample_id"
    container 'quay.io/biocontainers/snpeff:5.2--hdfd78af_0'
    cpus 2
    memory '8 GB'
    publishDir "${params.outdir}/annotated", mode: 'copy'

    input:
        tuple val(sample_id), path(vcf)

    output:
        path "${sample_id}.annotated.vcf"

    script:
    """
    snpEff -Xmx8g ${params.snpeff_db} $vcf > ${sample_id}.annotated.vcf
    """
}

workflow {
    reads = Channel.of(
        tuple(params.sample_id, file(params.fastq_r1), file(params.fastq_r2))
    )
    ref = file(params.reference)

    FASTP_QC(reads)
    BWA_ALIGN(FASTP_QC.out.trimmed, ref)
    CALL_VARIANTS(BWA_ALIGN.out.bam, ref)
    ANNOTATE(CALL_VARIANTS.out.vcf)
}
