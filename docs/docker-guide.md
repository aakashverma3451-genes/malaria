# Docker Guide — Malaria Genomics Platform

## What is Docker and Why This Project Uses It

Your platform has **9 separate services** that all need to run at the same time.
Without Docker you would have to install Postgres 16, Redis 7, MinIO, Keycloak (Java),
Node.js, Python 3.12, and Celery all on your machine — configure each one manually,
manage version conflicts, and start them in the right order every single time.

Docker runs each service in its own isolated container — like 9 mini virtual machines.
You type `make up` and all 9 start correctly. `make down` stops all of them.

---

## Do You Need a Paid Docker Account?

**No. Docker Free (Personal) is enough for this entire project.**

| Feature                  | Free      | Pro ($9/mo) | This project |
|--------------------------|-----------|-------------|--------------|
| Run containers locally   | ✅        | ✅          | ✅ Required  |
| Docker Compose           | ✅        | ✅          | ✅ Required  |
| Pull public images       | ✅        | ✅          | ✅ Required  |
| Build your own images    | ✅        | ✅          | ✅ Required  |
| Private registry         | 1 repo    | Unlimited   | ❌ Not yet   |
| Pull rate limit          | 100/6hr   | Unlimited   | ⚠️ Log in   |
| Team collaboration       | ❌        | ✅          | ❌ Not yet   |

The only thing to do: log in with your free Docker account so the pull
limit goes from 100 to 200 per 6 hours.

```bash
docker login
```

---

## Docker vs BioContainers — What is the Difference?

**BioContainers is not an alternative to Docker. It runs ON Docker.**

BioContainers is a registry of pre-built Docker images for bioinformatics tools —
BWA, GATK, SAMtools, SNPEff, fastp, and hundreds more. You still need Docker to
use them. The question is which images to use for which part:

| Layer                          | What to use              |
|--------------------------------|--------------------------|
| App services (Postgres, Redis) | Standard Docker images   |
| Frontend and backend           | Your own Docker images   |
| Pipeline tools (BWA, GATK...)  | BioContainers images     |

---

## The 9 Services in This Project

```
┌─────────────────────────────────────────────────────────────┐
│                     docker-compose.yml                       │
│                                                             │
│   postgres      ── stores all data (projects, samples,     │
│                    jobs, results)                           │
│                                                             │
│   redis         ── job queue broker. Celery pushes and      │
│                    pops tasks from here                     │
│                                                             │
│   minio         ── object storage for genomic files        │
│                    (FASTQ, BAM, VCF). Like S3 but local    │
│                                                             │
│   keycloak      ── authentication server. Handles login,   │
│                    passwords, JWT tokens                    │
│                                                             │
│   backend       ── your FastAPI application                 │
│                                                             │
│   frontend      ── your Next.js application                 │
│                                                             │
│   celery-worker ── runs bioinformatics pipeline jobs        │
│                                                             │
│   celery-beat   ── schedules cleanup tasks (hourly)        │
│                                                             │
│   flower        ── dashboard to monitor the job queue      │
│                    at localhost:5555                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Complete Workflow — Real Scenario

A lab technician in Nairobi uploads a P. falciparum sample and runs a full analysis.

### Step 1 — Login

```)
        │
        │ opens localhost:3000
        ▼
 ┌─────────────┐   "Sign in"    ┌──────────────────┐
 │  Next.js    │ ─────────────► │    Keycloak       │
 │  :3000      │ ◄───────────── │    :8080          │
 │  (Docker)   │   JWT token    │    (Docker)       │
 └─────────────┘                └──────────────────┘
```

Keycloak handles everything — username, password, brute force
protection, session management. Your code never touches passwords.

---

### Step 2 — Create Project and Sample

```
 ┌─────────────┐  POST /api/v1/projects/   ┌──────────────────┐
 │  Next.js    │ ────────────────────────► │    FastAPI        │
 │             │  POST /api/v1/samples/    │    :8000          │
 └─────────────┘                           │    (Docker)       │
                                           └────────┬─────────┘
                                                    │ writes rows
                                                    ▼
                                           ┌──────────────────┐
                                           │    PostgreSQL     │
                                           │    :5432          │
                                           │    (Docker)       │
                                           └──────────────────┘
```

Project: "Kenya Field Study 2024" / Organism: P. falciparum
Sample: KE-2024-001 / Location: Kisumu, Kenya / Date: Jan 2024

---

### Step 3 — Upload FASTQ Files (3.2 GB)

```
 ┌───────────┐  POST /files/init-upload   ┌──────────────────┐
 │  Browser  │ ─────────────────────────► │    FastAPI        │
 │           │ ◄───────────────────────── │                   │
 │           │   presigned URL            └──────────────────┘
 │           │
 │           │  PUT 3.2 GB directly            ┌─────────────┐
 │           │ ──────────────────────────────► │    MinIO    │
 │           │  (browser → MinIO direct)       │    :9000    │
 │           │  FastAPI never buffers the file │   (Docker)  │
 │           │                                 └─────────────┘
 │           │  POST /files/confirm
 │           │ ─────────────────────────► FastAPI checks
 └───────────┘                            file exists ✓
                                          updates status: "completed"
```

Presigned URLs are the key design here. FastAPI generates a
temporary upload link pointing directly to MinIO. The browser
uploads 3GB straight to storage — the API server never touches
the file bytes.

---

### Step 4 — Submit Analysis Job

```
 ┌───────────┐  POST /api/v1/jobs/submit  ┌──────────────────┐
 │  Browser  │ ─────────────────────────► │    FastAPI        │
 │  Wizard:  │                            │                   │
 │  sample ✓ │                            │  creates job row  │
 │  workflow │                            │  status: pending  │
 │  params   │                            └────────┬─────────┘
 │  submit   │                                     │ pushes task
 └───────────┘                                     ▼
                                           ┌──────────────────┐
                                           │     Redis         │
                                           │     :6379         │
                                           │    (Docker)       │
                                           └──────────────────┘
```

---

### Step 5 — Celery Picks Up the Job

```
                                           ┌──────────────────┐
                                           │     Redis         │
                                           └────────┬─────────┘
                                                    │ pop task
                                                    ▼
                                  ┌─────────────────────────────┐
                                  │      Celery Worker           │
                                  │      (Docker)                │
                                  │                              │
                                  │  1. download FASTQ           │
                                  │     from MinIO               │
                                  │     → /staging/abc-123/      │
                                  │                              │
                                  │  2. write params.json        │
                                  │     { ref: "Pf3D7",         │
                                  │       min_qual: 20, ... }    │
                                  │                              │
                                  │  3. nextflow run main.nf     │
                                  │     -params-file params.json │
                                  └──────────────┬──────────────┘
                                                 │
                                                 ▼
                                        Nextflow starts
```

Note on security: user input never appears in shell commands.
Celery writes a params.json file. Nextflow reads the file.
No shell injection is possible.

---

### Step 6 — Nextflow Pipeline (BioContainers)

This is where Docker and BioContainers work together.
Each step runs in its own BioContainers image.

```
┌────────────────────────────────────────────────────────────────┐
│                         NEXTFLOW                                │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  PROCESS 1: Quality Trimming                             │  │
│  │  container: biocontainers/fastp:0.23.4                   │  │
│  │                                                          │  │
│  │  INPUT:   KE-2024-001_R1.fastq.gz  (3.2 GB, raw)       │  │
│  │           KE-2024-001_R2.fastq.gz  (3.1 GB, raw)       │  │
│  │  RUNS:    fastp --quality 20 --length 50 ...            │  │
│  │  OUTPUT:  trimmed FASTQ files + fastp_report.json       │  │
│  └─────────────────────────┬────────────────────────────────┘  │
│                            │                                   │
│                            ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  PROCESS 2: Alignment to Reference Genome                │  │
│  │  container: biocontainers/bwa:0.7.17                     │  │
│  │                                                          │  │
│  │  INPUT:   trimmed FASTQ + Pf3D7.fasta (reference)      │  │
│  │  RUNS:    bwa mem Pf3D7.fasta R1.trimmed R2.trimmed    │  │
│  │  OUTPUT:  KE-2024-001.sam                               │  │
│  └─────────────────────────┬────────────────────────────────┘  │
│                            │                                   │
│                            ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  PROCESS 3: Sort and Index BAM                           │  │
│  │  container: biocontainers/samtools:1.19                  │  │
│  │                                                          │  │
│  │  INPUT:   KE-2024-001.sam                               │  │
│  │  RUNS:    samtools sort → samtools index                │  │
│  │  OUTPUT:  KE-2024-001.sorted.bam + .bai index          │  │
│  └─────────────────────────┬────────────────────────────────┘  │
│                            │                                   │
│                            ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  PROCESS 4: Mark Duplicates + Variant Calling            │  │
│  │  container: broadinstitute/gatk:4.5.0.0                  │  │
│  │                                                          │  │
│  │  INPUT:   KE-2024-001.sorted.bam                        │  │
│  │  RUNS:    gatk MarkDuplicates                           │  │
│  │           gatk HaplotypeCaller -ERC GVCF               │  │
│  │  OUTPUT:  KE-2024-001.dedup.bam                        │  │
│  │           KE-2024-001.g.vcf.gz  (raw variants)         │  │
│  └─────────────────────────┬────────────────────────────────┘  │
│                            │                                   │
│                            ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  PROCESS 5: Variant Annotation                           │  │
│  │  container: biocontainers/snpeff:5.2                     │  │
│  │                                                          │  │
│  │  INPUT:   KE-2024-001.g.vcf.gz                         │  │
│  │  RUNS:    snpEff Pf_3D7 sample.vcf                     │  │
│  │  OUTPUT:  KE-2024-001.annotated.vcf                    │  │
│  │           snpEff_summary.html                           │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

Each process runs in complete isolation. No tool installation
needed. No version conflicts. BioContainers guarantees the exact
same tool version runs on your laptop, the lab server, and HPC.

---

### Step 7 — Results Saved

```
                                  ┌─────────────────────────────┐
                                  │      Celery Worker           │
                                  │                              │
                                  │  Nextflow finished ✓         │
                                  │                              │
                                  │  uploads to MinIO:           │
                                  │    results/abc-123/          │
                                  │      fastp_report.json       │
                                  │      KE-2024-001.vcf         │
                                  │      snpEff_summary.html     │
                                  │                              │
                                  │  updates PostgreSQL:         │
                                  │    job.status = completed    │
                                  │    job.progress = 100%       │
                                  │    job.completed_at = now()  │
                                  └─────────────────────────────┘
```

---

### Step 8 — Researcher Sees Results

```
 ┌────────────────────┐
 │  Browser           │
 │  /jobs/abc-123     │   (was auto-refreshing every 15 seconds)
 │                    │
 │  ✅ Completed       │
 │  Progress: 100%    │
 │                    │
 │  Results:          │
 │  📄 QC Report      │──► GET /api/v1/results/xyz/download-url
 │  🧬 Annotated VCF  │         │
 │  📊 SNPEff Summary │         │ FastAPI generates presigned
 │                    │         │ GET URL from MinIO
 │  [Download]        │◄────────┘
 └────────────────────┘    browser downloads direct from MinIO
```

---

## Complete Architecture Map

```
╔══════════════════════════════════════════════════════════════════╗
║  DOCKER — runs your platform                                      ║
║                                                                  ║
║   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      ║
║   │ postgres │  │  redis   │  │  minio   │  │keycloak  │      ║
║   │  :5432   │  │  :6379   │  │  :9000   │  │  :8080   │      ║
║   │  stores  │  │  queue   │  │  files   │  │  auth    │      ║
║   └──────────┘  └──────────┘  └──────────┘  └──────────┘      ║
║                                                                  ║
║   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      ║
║   │ fastapi  │  │ next.js  │  │  celery  │  │  flower  │      ║
║   │  :8000   │  │  :3000   │  │  worker  │  │  :5555   │      ║
║   │   API    │  │    UI    │  │   jobs   │  │ monitor  │      ║
║   └──────────┘  └──────────┘  └────┬─────┘  └──────────┘      ║
║                                    │                            ║
╚════════════════════════════════════│════════════════════════════╝
                                     │ launches via Nextflow
                                     ▼
╔══════════════════════════════════════════════════════════════════╗
║  BIOCONTAINERS — runs your science                                ║
║                                                                  ║
║   ┌──────────┐  ┌──────────┐  ┌──────────┐                     ║
║   │  fastp   │  │   bwa    │  │samtools  │                     ║
║   │ trimming │→ │ align DNA│→ │ sort BAM │                     ║
║   └──────────┘  └──────────┘  └──────────┘                     ║
║                                    │                            ║
║                                    ▼                            ║
║                    ┌──────────┐  ┌──────────┐                  ║
║                    │   gatk   │→ │  snpeff  │                  ║
║                    │ variants │  │ annotate │                  ║
║                    └──────────┘  └──────────┘                  ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## Quick Reference — Ports

| Service   | Port  | What you open in browser            |
|-----------|-------|-------------------------------------|
| Frontend  | 3000  | http://localhost:3000               |
| Backend   | 8000  | http://localhost:8000/docs (Swagger)|
| Keycloak  | 8080  | http://localhost:8080 (admin)       |
| MinIO     | 9001  | http://localhost:9001 (console)     |
| Flower    | 5555  | http://localhost:5555 (job monitor) |
| Postgres  | 5432  | psql / DBeaver / TablePlus          |
| Redis     | 6379  | redis-cli only                      |

---

## Common Commands

```bash
make up              # start all 9 services
make down            # stop all services
make logs            # stream all logs
make logs-backend    # stream backend logs only
make migrate         # run database migrations
make minio-init      # create the genomics-data bucket
make shell-db        # open postgres shell
docker compose ps    # show status of all services
```

---

## Key Design Decisions

**Why presigned URLs for file upload?**
A 50 GB FASTQ file uploaded through FastAPI means 50 GB in memory
on the API server. With presigned URLs, FastAPI generates a signed
link (a few bytes), the browser uploads directly to MinIO, and the
API only validates metadata. The server never touches the file bytes.

**Why separate Celery from FastAPI?**
Nextflow pipelines run for hours. If they ran inside FastAPI, every
HTTP request would time out. Celery runs pipelines in a separate
process. FastAPI stays responsive. The browser polls for progress.

**Why Keycloak instead of building auth?**
Building login, registration, password hashing, JWT issuance, token
refresh, brute force protection, and account lockout from scratch is
2000+ lines of security-critical code. Keycloak provides all of it
via configuration.

**Why BioContainers instead of installing tools on the server?**
BWA, GATK, SAMtools, SNPEff all have complex dependencies and
conflict with each other when installed on the same machine. Each
BioContainers image is self-contained. Nextflow pulls the exact
version you specify. The same pipeline runs identically on your
laptop, the lab server, and an HPC cluster.

---

## Galaxy Project vs This Platform — Full Comparison

Galaxy (galaxyproject.org) is the most widely used open-source
bioinformatics platform in the world. It solves the same core problem:
making genomic analysis accessible without the command line.
Understanding how Galaxy does it — and why this platform makes
different choices — is important context for every architectural
decision here.

### What Galaxy Is

Galaxy is a general-purpose bioinformatics platform used by
224+ public servers worldwide (UseGalaxy.org, UseGalaxy.eu,
UseGalaxy.org.au and others). It provides a drag-and-drop
workflow builder, a tool library of 8000+ bioinformatics tools,
and a job execution engine that runs tools in Docker or
Singularity containers — drawing from the same BioContainers
registry this platform uses.

It is the gold standard for reproducible bioinformatics and has
been deployed at every major genomics institute on the planet.

---

### How Galaxy Uses Docker and BioContainers

Galaxy's container model works like this:

```
┌─────────────────────────────────────────────────────────────┐
│                    GALAXY ARCHITECTURE                       │
│                                                             │
│  ┌─────────────┐     ┌──────────────┐   ┌───────────────┐ │
│  │  Galaxy UI  │────►│  Galaxy Core │──►│  Job Runner   │ │
│  │  (browser)  │     │  (Python)    │   │  (internal)   │ │
│  └─────────────┘     └──────────────┘   └───────┬───────┘ │
│                                                  │         │
│                              ┌───────────────────┘         │
│                              │  resolves container          │
│                              ▼                             │
│               ┌──────────────────────────┐                 │
│               │   Container Resolver      │                 │
│               │                          │                 │
│               │  1. check explicit tag   │                 │
│               │  2. check mulled hash    │                 │
│               │  3. fallback to conda    │                 │
│               └──────────────┬───────────┘                 │
│                              │                             │
│                              ▼                             │
│               ┌──────────────────────────┐                 │
│               │  quay.io/biocontainers/  │                 │
│               │  (same registry we use)  │                 │
│               └──────────────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

Galaxy auto-resolves which BioContainers image to pull based
on the tool's Conda package requirements. It can also use
"mulled containers" — auto-generated images that bundle
multiple tools into one container using a hash-based naming
scheme (e.g. mulled-v2-a9d250a....).

This is sophisticated and production-proven. It is also one of
the reasons Galaxy is complex to self-host.

---

### Architecture Comparison

```
╔══════════════════════════════════════════════════════════════════╗
║              GALAXY                vs      THIS PLATFORM         ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  PURPOSE                                                         ║
║  General-purpose bioinformatics    Malaria / mosquito            ║
║  for any organism, any tool        genomic surveillance only     ║
║                                                                  ║
║  ARCHITECTURE                                                     ║
║  Monolithic                        Microservices                 ║
║  (one big Galaxy Python app)       (9 separate services)         ║
║                                                                  ║
║  WEB FRAMEWORK                                                    ║
║  Gunicorn + FastAPI (recent)       FastAPI (native async)        ║
║  Previously uWSGI (legacy)                                       ║
║                                                                  ║
║  DATABASE                                                         ║
║  SQLite (default)                  PostgreSQL 16 (required)      ║
║  PostgreSQL (production)           No SQLite ever                ║
║                                                                  ║
║  JOB QUEUE                                                        ║
║  Internal Galaxy job runner        Celery + Redis                ║
║  + Pulsar (for HPC remoting)       + Nextflow (for HPC)          ║
║                                                                  ║
║  WORKFLOW LANGUAGE                                                ║
║  Galaxy Workflow Format (.ga)      Nextflow DSL2                 ║
║  drag-and-drop GUI builder         code-first pipelines          ║
║                                                                  ║
║  CONTAINER STRATEGY                                               ║
║  Auto-resolves BioContainers       Explicit BioContainers        ║
║  via mulled hashes                 tags in Nextflow configs      ║
║                                                                  ║
║  AUTH                                                             ║
║  Built-in user accounts            Keycloak (OIDC/SSO)          ║
║  + OIDC support                                                  ║
║                                                                  ║
║  FILE STORAGE                                                     ║
║  Local filesystem (default)        MinIO (S3-compatible)         ║
║  Object store plugins available    Presigned URL uploads         ║
║                                                                  ║
║  VISUALIZATION                                                    ║
║  Generic chart plugins             Plotly, ECharts, IGV.js,      ║
║                                    Phylocanvas (malaria-specific) ║
║                                                                  ║
║  TOOL LIBRARY                                                     ║
║  8000+ tools (any field)           7 curated workflows           ║
║                                    (malaria-specific only)       ║
║                                                                  ║
║  SETUP COMPLEXITY                                                 ║
║  High (Galaxy has ~200 config      Moderate (docker compose up)  ║
║  options, requires expertise)                                    ║
║                                                                  ║
║  SELF-HOSTING                                                     ║
║  Complex (Ansible playbooks        Simple (make up)              ║
║  recommended for production)                                     ║
║                                                                  ║
║  COMMUNITY                                                        ║
║  Massive (20 years, global)        Yours (purpose-built)         ║
╚══════════════════════════════════════════════════════════════════╝
```

---

### Where Galaxy Wins

**Tool library depth.**
Galaxy has 8000+ tools integrated, tested, and containerized.
If a researcher wants to try a new variant caller tomorrow,
it is probably already in Galaxy. In this platform, adding a
new tool means writing a new Nextflow module.

**No-code workflow builder.**
Galaxy's drag-and-drop workflow editor means epidemiologists
with no programming background can chain tools together.
This platform requires understanding Nextflow DSL2 to modify
pipelines.

**Community and support.**
Galaxy has been in production at the world's largest genomics
institutes since 2005. Every edge case has been hit and
documented. UseGalaxy.org handles millions of jobs per year.

**Training ecosystem.**
Galaxy Training Network (GTN) has 300+ tutorials for
bioinformatics workflows including malaria-specific ones.
Researchers already know it.

**Proven container resolution.**
Galaxy's auto-resolution of BioContainers via mulled hashes
means tool authors never have to specify a container — it
is derived automatically from the Conda package name and
version. This is more maintainable at scale.

---

### Where This Platform Wins

**Malaria-specific depth.**
Galaxy is general-purpose. It has no concept of FWS scores,
hmmIBD matrices, Pf3k identifiers, drug resistance markers
(pfkelch13, pfcrt, pfmdr1), or MalariaGEN data formats.
This platform is built around these from the ground up.

**Modern API-first architecture.**
Galaxy was built before REST APIs and async Python were standard.
This platform uses FastAPI with native async from day one —
better for WebSocket job monitoring, presigned file URLs,
and building mobile or desktop clients later.

**Object storage built-in.**
Galaxy defaults to local filesystem storage. For 50 GB FASTQ
files across hundreds of samples this creates disk management
problems. MinIO with presigned URLs means the API server never
buffers genomic files, and storage scales independently.

**Simpler self-hosting.**
Running Galaxy in production requires Ansible playbooks,
careful uWSGI/Gunicorn tuning, and Galaxy-specific expertise.
This platform runs with `make up`. The entire stack is defined
in one docker-compose.yml that any developer can read.

**Real-time job monitoring.**
Galaxy's job monitoring is page-refresh based. This platform
is built for WebSocket streaming (Stage 9) — researchers see
live log output from Nextflow as it runs, step by step.

**Custom visualizations.**
Galaxy has generic chart plugins. This platform integrates
IGV.js for genome browsing, Phylocanvas.gl for phylogenetic
trees, and Plotly for Manhattan plots and selection scans —
all rendering malaria-specific output formats natively.

**Keycloak SSO.**
Galaxy has its own user database with OIDC support as an
add-on. This platform uses Keycloak natively — meaning it
can integrate with a hospital's Active Directory, a
university's LDAP, or MalariaGEN's identity provider out
of the box.

---

### Why Not Just Use Galaxy Then?

The honest answer: Galaxy is a better choice for a general-
purpose genomics institute that needs to run thousands of
different analyses.

This platform is the better choice when:

```
1. Your organism is P. falciparum, P. vivax, or A. gambiae
   and you need surveillance-specific outputs (FWS, IBD,
   drug resistance markers, population structure)

2. Your users are epidemiologists and public health officers
   who need a dashboard built around their data model —
   not a general bioinformatics tool explorer

3. You need to integrate with national disease surveillance
   systems via API (REST endpoints Galaxy does not expose
   cleanly)

4. You are deploying in a resource-limited setting where
   Galaxy's operational complexity is a barrier

5. You want full control over the data model, access
   control, and report format for regulatory or
   publication purposes
```

---

### How the Same BioContainers Work in Both

Both platforms pull from the same registry — quay.io/biocontainers.
The difference is how they specify which image to use:

```
GALAXY (auto-resolved):
  Tool XML declares:    <requirement type="package" version="0.7.17">bwa</requirement>
  Galaxy resolves to:   quay.io/biocontainers/bwa:0.7.17--h5bf99c6_8
  No container tag needed in the tool definition

THIS PLATFORM (explicit):
  Nextflow module:      container 'biocontainers/bwa:0.7.17'
  You pin the tag.      You know exactly what runs.
  You update manually.  You control when it changes.
```

Galaxy's approach is more scalable for 8000 tools.
This platform's approach is more auditable for regulated
genomic surveillance — you can prove exactly which version
of every tool ran on every sample.

---

### Summary

```
┌─────────────────────────────────────────────────────────────┐
│  USE GALAXY IF:              USE THIS PLATFORM IF:          │
│                                                             │
│  • general genomics          • malaria surveillance only    │
│  • no-code users             • API-driven workflows         │
│  • 8000+ tool library        • custom dashboards            │
│  • large public server       • lightweight self-hosting     │
│  • community support         • SSO / institutional auth     │
│  • existing Galaxy users     • real-time monitoring         │
│                              • MinIO object storage         │
│                              • regulatory auditability      │
└─────────────────────────────────────────────────────────────┘

Both use Docker. Both use BioContainers. Different problems,
different trade-offs. Galaxy solved the general case in 2005.
This platform solves the malaria surveillance case in 2024.
```
