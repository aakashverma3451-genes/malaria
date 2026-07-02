# Pipeline engine comparison: WDL vs Nextflow

**Purpose:** a decision aid for choosing the platform's pipeline engine.
These are *sketches*, not production pipelines — container tags and reference
index handling are illustrative.

Both files implement the **same single-sample variant-calling workflow** for
*P. falciparum* (Pf3D7), so the syntax can be compared directly:

```
fastp (QC + trim)  ->  BWA-MEM align + sort  ->  GATK MarkDuplicates +
HaplotypeCaller  ->  SnpEff annotate
```

- [`single_sample.wdl`](single_sample.wdl) — WDL 1.0 (run with miniwdl or Cromwell)
- [`single_sample.nf`](single_sample.nf) — Nextflow DSL2

## Side-by-side trade-offs

| Dimension | WDL | Nextflow |
|---|---|---|
| Language feel | Declarative, explicit `task`/`workflow` blocks; easy to read/review | Groovy DSL + dataflow channels; more powerful, steeper curve |
| Data flow | Explicit `call X { input: ... }` wiring | Channels (`emit:` / `.out`) — implicit, great for parallel fan-out |
| Curated pipelines | Broad GATK Best-Practices WDLs | **nf-core** — large library of peer-reviewed pipelines |
| Engines | miniwdl (light, Python), Cromwell (JVM), Terra | Single `nextflow` binary |
| Executors | SLURM/SGE/cloud via Cromwell backends | SLURM/SGE/AWS Batch/K8s built-in |
| Resume / caching | Cromwell call-caching | `-resume` (excellent, widely used) |
| Containers | `runtime { docker: ... }` | `container '...'` (Docker/Singularity/Conda) |
| Best fit | GATK-centric / clinical / cloud-native (Terra) | Academic genomics, HPC + cloud, reuse via nf-core |

## Why it doesn't affect the backend

From Django/Celery the engine is launched the **same way** — a worker shells out
and monitors a subprocess:

```python
# Nextflow
subprocess.run(["nextflow", "run", "single_sample.nf",
                "--sample_id", sid, "--fastq_r1", r1, "--fastq_r2", r2])

# WDL (miniwdl)
subprocess.run(["miniwdl", "run", "single_sample.wdl", "-i", "inputs.json"])
```

Either way the `AnalysisJob` model, status/progress tracking, and output parsing
into `Result` rows are identical. **The choice is about the bioinformatics
ecosystem and team familiarity, not the web stack.**

## Recommendation

Lean **Nextflow** to inherit nf-core's vetted pipelines; **WDL** is a defensible
alternative if the team is GATK-heavy and values its readability / clinical
portability. Switching is essentially free until the first real pipeline is
written.
