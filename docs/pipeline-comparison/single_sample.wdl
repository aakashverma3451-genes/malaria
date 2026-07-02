version 1.0

# ─────────────────────────────────────────────────────────────────────────────
# Single-sample variant calling — WDL sketch (engine-comparison artifact).
# Stages: fastp QC/trim -> BWA-MEM align -> GATK MarkDuplicates + HaplotypeCaller
#         -> SnpEff annotate. Target: P. falciparum (Pf3D7).
# NOTE: container tags and reference index handling are illustrative, not a
#       hardened production pipeline.
# Run (miniwdl):  miniwdl run single_sample.wdl -i inputs.json
# ─────────────────────────────────────────────────────────────────────────────

workflow SingleSampleVariantCalling {
    input {
        String sample_id
        File fastq_r1
        File fastq_r2
        File reference_fasta           # Pf3D7.fasta
        File reference_fasta_index     # .fai
        File reference_dict            # .dict  (required by GATK)
        Array[File] bwa_index_files    # .amb .ann .bwt .pac .sa
        String snpeff_db = "Pfalciparum3D7"
        Int min_base_quality = 20
    }

    call FastpQC {
        input: sample_id = sample_id, fastq_r1 = fastq_r1, fastq_r2 = fastq_r2,
               min_base_quality = min_base_quality
    }

    call BwaAlign {
        input: sample_id = sample_id,
               fastq_r1 = FastpQC.trimmed_r1, fastq_r2 = FastpQC.trimmed_r2,
               reference_fasta = reference_fasta, bwa_index_files = bwa_index_files
    }

    call CallVariants {
        input: sample_id = sample_id,
               bam = BwaAlign.sorted_bam, bam_index = BwaAlign.sorted_bai,
               reference_fasta = reference_fasta,
               reference_fasta_index = reference_fasta_index,
               reference_dict = reference_dict
    }

    call AnnotateVariants {
        input: sample_id = sample_id, vcf = CallVariants.vcf, snpeff_db = snpeff_db
    }

    output {
        File qc_report     = FastpQC.qc_json
        File sorted_bam    = BwaAlign.sorted_bam
        File raw_vcf       = CallVariants.vcf
        File annotated_vcf = AnnotateVariants.annotated_vcf
    }
}

task FastpQC {
    input {
        String sample_id
        File fastq_r1
        File fastq_r2
        Int min_base_quality
    }
    command <<<
        fastp \
          --in1 ~{fastq_r1} --in2 ~{fastq_r2} \
          --out1 ~{sample_id}.trimmed.R1.fastq.gz \
          --out2 ~{sample_id}.trimmed.R2.fastq.gz \
          --qualified_quality_phred ~{min_base_quality} \
          --json ~{sample_id}.fastp.json
    >>>
    output {
        File trimmed_r1 = "~{sample_id}.trimmed.R1.fastq.gz"
        File trimmed_r2 = "~{sample_id}.trimmed.R2.fastq.gz"
        File qc_json    = "~{sample_id}.fastp.json"
    }
    runtime {
        docker: "quay.io/biocontainers/fastp:0.23.4--h5f740d0_0"
        cpu: 4
        memory: "8 GB"
    }
}

task BwaAlign {
    input {
        String sample_id
        File fastq_r1
        File fastq_r2
        File reference_fasta
        Array[File] bwa_index_files
    }
    command <<<
        set -euo pipefail
        # BWA expects the index files beside the reference.
        for f in ~{sep=' ' bwa_index_files}; do ln -s "$f" .; done
        bwa mem -t 4 \
            -R "@RG\tID:~{sample_id}\tSM:~{sample_id}\tPL:ILLUMINA" \
            ~{reference_fasta} ~{fastq_r1} ~{fastq_r2} \
          | samtools sort -@ 4 -o ~{sample_id}.sorted.bam -
        samtools index ~{sample_id}.sorted.bam
    >>>
    output {
        File sorted_bam = "~{sample_id}.sorted.bam"
        File sorted_bai = "~{sample_id}.sorted.bam.bai"
    }
    runtime {
        docker: "quay.io/biocontainers/bwa:0.7.17--he4a0461_11"
        cpu: 4
        memory: "16 GB"
    }
}

task CallVariants {
    input {
        String sample_id
        File bam
        File bam_index
        File reference_fasta
        File reference_fasta_index
        File reference_dict
    }
    command <<<
        set -euo pipefail
        gatk MarkDuplicates -I ~{bam} -O ~{sample_id}.dedup.bam \
            -M ~{sample_id}.dup_metrics.txt
        samtools index ~{sample_id}.dedup.bam
        gatk HaplotypeCaller \
            -R ~{reference_fasta} \
            -I ~{sample_id}.dedup.bam \
            -O ~{sample_id}.vcf.gz
    >>>
    output {
        File vcf = "~{sample_id}.vcf.gz"
    }
    runtime {
        docker: "broadinstitute/gatk:4.5.0.0"
        cpu: 2
        memory: "16 GB"
    }
}

task AnnotateVariants {
    input {
        String sample_id
        File vcf
        String snpeff_db
    }
    command <<<
        snpEff -Xmx8g ~{snpeff_db} ~{vcf} > ~{sample_id}.annotated.vcf
    >>>
    output {
        File annotated_vcf = "~{sample_id}.annotated.vcf"
    }
    runtime {
        docker: "quay.io/biocontainers/snpeff:5.2--hdfd78af_0"
        cpu: 2
        memory: "8 GB"
    }
}
