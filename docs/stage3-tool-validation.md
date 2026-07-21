# Stage 3.1 — Manual Tool Validation (Test Oracle)

Every tool in the single-sample variant-calling chain, run manually in Docker,
with its exact command, inputs, outputs, and **expected results**. This is the
test oracle: when the Nextflow pipeline (Stage 3.2) runs the same steps, its
output must match the numbers here.

All tools run from **quay.io/biocontainers** (not Docker Hub — see "Registry note").

---

## Test dataset (provenance)

| Item | Value |
|---|---|
| Reference | *P. falciparum* 3D7, NCBI RefSeq **GCF_000002765.6** (`reference-data/Pf3D7.fasta`) — 14 chromosomes, 22 MB, contig names `NC_004325.2` … |
| Annotation | matching NCBI GFF3 for the same assembly (`reference-data/Pf3D7.gff`) — 5,457 genes |
| Reads | **simulated** with `wgsim` (seed 42) from the reference — `test-data/PF_TEST_001_R{1,2}.fastq.gz` |
| Read params | 300,000 pairs × 100 bp, mutation rate `-r 0.001`, error `-e 0.001` |

Reads are simulated (not real Pf3k data) on purpose: deterministic input we fully
control, and they map back to the reference so alignment + variant calling produce
real output. Real Pf3k validation is deferred to **Stage 3.4**. `wgsim` also prints
the exact mutations it introduced — that list is the ground-truth variant set for
3.4 concordance checking (regenerate with stdout captured).

### Regenerate the test reads

```bash
docker run --rm -v "$PWD:/data" -w /data pegi3s/wgsim:latest \
  wgsim -N 300000 -1 100 -2 100 -r 0.001 -e 0.001 -S 42 \
  reference-data/Pf3D7.fasta \
  test-data/PF_TEST_001_R1.fastq test-data/PF_TEST_001_R2.fastq
gzip test-data/PF_TEST_001_R*.fastq
```

---

## Registry note

`mirror.gcr.io` (configured in `~/.docker/daemon.json`) only mirrors **official/library**
Docker Hub images, not org images like `staphb/*`. During this work Docker Hub
(`registry-1.docker.io`) was intermittently unreachable, so all bioinformatics tools
are pulled from **quay.io/biocontainers**, which was reliably reachable. Keep using
quay.io biocontainers for the Nextflow `container` directives in Stage 3.2.

## Platform note

The host is Apple Silicon (arm64); biocontainers are amd64. Every tool runs fine under
emulation but prints `WARNING: The requested image's platform (linux/amd64) does not
match … (linux/arm64/v8)`. Harmless, just slower. On an x86 server this disappears.

---

## Reference preparation (one-time)

```bash
# BWA index
docker run --rm -v "$PWD:/data" -w /data quay.io/biocontainers/bwa:0.7.18--he4a0461_1 \
  bwa index reference-data/Pf3D7.fasta                      # -> .amb .ann .bwt .pac .sa

# FASTA index + sequence dictionary (GATK needs both)
docker run --rm -v "$PWD:/data" -w /data quay.io/biocontainers/samtools:1.21--h50ea8bc_0 \
  samtools faidx reference-data/Pf3D7.fasta                 # -> .fai
docker run --rm -v "$PWD:/data" -w /data quay.io/biocontainers/gatk4:4.6.2.0--py310hdfd78af_1 \
  gatk CreateSequenceDictionary -R reference-data/Pf3D7.fasta   # -> Pf3D7.dict
```

---

## Tool chain — command + expected output

Order: **fastp → FastQC → BWA-MEM → samtools sort → MarkDuplicates → HaplotypeCaller → GenotypeGVCFs → SnpEff**

### 1. fastp — QC + trim `quay.io/biocontainers/fastp:1.3.6--h43da1c4_0`

```bash
fastp -i R1.fastq.gz -I R2.fastq.gz \
  -o R1.trimmed.fastq.gz -O R2.trimmed.fastq.gz \
  --json fastp.json --html fastp.html --thread 4
```
**Expected:** 599,998 reads pass filter (0 failed); ~1,352 reads adapter-trimmed;
duplication ≈ 0.001%; insert-size peak ≈ 169. Emits `fastp.json` + `fastp.html`.

### 2. FastQC — read QC report `quay.io/biocontainers/fastqc:0.12.1--hdfd78af_0`

```bash
fastqc R1.fastq.gz R2.fastq.gz --outdir <out>
```
**Expected:** one `_fastqc.html` + `_fastqc.zip` per input. (Simulated reads show a
flat Q30 profile — real data will vary.)

### 3. BWA-MEM — align `quay.io/biocontainers/bwa:0.7.18--he4a0461_1`

```bash
bwa mem -t 4 -R '@RG\tID:PF_TEST_001\tSM:PF_TEST_001\tPL:ILLUMINA\tLB:lib1' \
  reference-data/Pf3D7.fasta R1.trimmed.fastq.gz R2.trimmed.fastq.gz -o aln.sam
```
The `@RG` read group is **required** — GATK refuses BAMs without one.

### 4. samtools — sort + index + QC `quay.io/biocontainers/samtools:1.21--h50ea8bc_0`

```bash
samtools sort -@ 4 -o sorted.bam aln.sam
samtools index sorted.bam
samtools flagstat sorted.bam
```
**Expected (flagstat oracle):** 599,998 total reads · **100.00% mapped** ·
**100.00% properly paired** · 0 singletons. (100% because reads were simulated from
this exact reference — real data is typically 90–99%.) Delete the large `.sam` after.

### 5. GATK MarkDuplicates `quay.io/biocontainers/gatk4:4.6.2.0--py310hdfd78af_1`

```bash
gatk MarkDuplicates -I sorted.bam -O markdup.bam -M markdup.metrics.txt
samtools index markdup.bam
```
**Expected:** PERCENT_DUPLICATION ≈ 0.00004 (11 duplicate pairs of 299,999) — near
zero is correct for simulated reads. Emits a metrics file.

### 6. GATK HaplotypeCaller — per-sample GVCF

```bash
gatk HaplotypeCaller -R reference-data/Pf3D7.fasta -I markdup.bam \
  -O PF_TEST_001.g.vcf.gz -ERC GVCF
```
**Expected:** ~2 min (emulated), processes ~113,690 regions, emits a ~13 MB GVCF.
`-ERC GVCF` is what makes joint genotyping (Stage 7) possible later.

### 7. GATK GenotypeGVCFs — final VCF

```bash
gatk GenotypeGVCFs -R reference-data/Pf3D7.fasta \
  -V PF_TEST_001.g.vcf.gz -O PF_TEST_001.vcf.gz
```
**Expected (variant-count oracle):** **9,699 variant records**. Standard VCF with
AC/AF/DP/QD/MQ INFO fields and per-sample GT:AD:DP:GQ:PL.

### 8. SnpEff — functional annotation `quay.io/biocontainers/snpeff:5.4.0c--hdfd78af_0`

> **Finding (the kind manual validation is meant to surface):** SnpEff's built-in
> `Plasmodium_falciparum` database uses PlasmoDB-style contig names, which do **not**
> match our NCBI `NC_…` names — annotating against it would flag every variant
> "chromosome not found." Fix: build a **custom** SnpEff DB from the NCBI GFF for the
> same assembly, so contig names match. Do this once; reuse the built DB.

```bash
# one-time custom DB build
mkdir -p snpeff-data/Pf3D7_NCBI
cp reference-data/Pf3D7.fasta snpeff-data/Pf3D7_NCBI/sequences.fa
cp reference-data/Pf3D7.gff   snpeff-data/Pf3D7_NCBI/genes.gff
snpEff build -gff3 -noCheckCds -noCheckProtein \
  -dataDir <abs>/snpeff-data -configOption Pf3D7_NCBI.genome=Pf3D7 Pf3D7_NCBI
# -> snpEffectPredictor.bin (~4.6 MB)

# annotate
snpEff -dataDir <abs>/snpeff-data -configOption Pf3D7_NCBI.genome=Pf3D7 \
  -stats snpeff_summary.html Pf3D7_NCBI PF_TEST_001.vcf.gz > PF_TEST_001.annotated.vcf
```
**Expected:** all 9,699 records gain an `ANN=` field. Effect breakdown (sanity check):

| effect | count |
|---|---|
| upstream_gene_variant | 23,480 |
| downstream_gene_variant | 23,259 |
| intergenic_region | 7,724 |
| missense_variant | 3,480 |
| synonymous_variant | 750 |
| frameshift_variant | 644 |
| intron_variant | 573 |
| stop_gained | 309 |

(One variant can carry multiple effects, so effect counts exceed the record count.)

---

## Status

All eight steps validated end-to-end on the simulated dataset. Tool versions,
commands, and expected numbers above are the oracle for **Stage 3.2** (porting each
step to a Nextflow DSL2 module) — the pipeline's output on this same input must match.

### Tool image reference (all quay.io/biocontainers unless noted)

| Tool | Image |
|---|---|
| wgsim (test-data gen) | `pegi3s/wgsim:latest` (Docker Hub) |
| fastp | `fastp:1.3.6--h43da1c4_0` |
| FastQC | `fastqc:0.12.1--hdfd78af_0` |
| BWA | `bwa:0.7.18--he4a0461_1` |
| samtools | `samtools:1.21--h50ea8bc_0` |
| GATK4 | `gatk4:4.6.2.0--py310hdfd78af_1` |
| SnpEff | `snpeff:5.4.0c--hdfd78af_0` |
