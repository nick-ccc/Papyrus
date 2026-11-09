# Document Studio — Project Planning & Technical Architecture

**Status:** Planning / Initial Architecture  
**Platform:** Desktop  
**Architecture:** Rust + Tauri + React + Python  
**Inference:** Hybrid (local + cloud)  
**Document Support:** Mixed / General-purpose  
**Workflow:** Fully automated with human editing afterward

---

# 1. Project Overview

## 1.1 Vision

Document Studio is an AI-powered desktop application that transforms photographs and scanned documents into professionally formatted, editable LaTeX documents.

Users import one or more images, initiate an automated AI processing pipeline, and receive a reconstructed document in LaTeX format. The generated source is then presented in an integrated editor alongside a live PDF preview.

The application should support multiple document types, configurable templates, interchangeable AI providers, and local-first document management.

The primary objective is to provide a complete workflow:

**Photographs → Image Processing → OCR / Vision → Document Reconstruction → Classification → LaTeX Generation → PDF Compilation → Manual Editing**

The application should feel like a dedicated document production environment rather than a generic AI chatbot.

## 1.2 Core Features

- Import photographs and scanned documents.
- Support multiple images representing pages of one document.
- Image preprocessing and correction.
- AI-powered text and mathematical notation extraction.
- Reconstruction of document structure and layout.
- Automatic document classification.
- Template-based LaTeX generation.
- Integrated LaTeX source editor.
- Live compiled PDF preview.
- Pipeline progress monitoring.
- Error detection and automated repair.
- Document version history.
- Project-based organization.
- Export to PDF and LaTeX.
- Hybrid local/cloud inference.

## 1.3 Design Principles

1. **Local-first:** Core functionality should work without internet connectivity.
2. **Provider independence:** AI providers should be interchangeable without modifying agent implementations.
3. **Artifact persistence:** Every processing stage should generate independently persisted outputs.
4. **Reproducibility:** Documents should be regenerable from their original inputs and processing configuration.
5. **Human-editable output:** LaTeX should remain the canonical editable document.
6. **Failure isolation:** Individual agent failures should not destroy previous successful outputs.
7. **Modularity:** The GUI, AI pipeline, and document compiler should remain independently testable.
8. **Extensibility:** New document types, templates, model providers, and agents should be straightforward to introduce.

---

# 2. Technology Stack

## 2.1 Desktop Application

| Technology | Responsibility |
|---|---|
| Tauri 2 | Desktop application framework |
| React | UI framework |
| TypeScript | Frontend language |
| Vite | Frontend build system |
| Tailwind CSS | Styling |
| shadcn/ui | UI components |
| Zustand | Frontend state management |
| Monaco Editor | LaTeX source editor |
| PDF.js | PDF rendering |
| Resizable Panels | Workspace layout |

Tauri provides a relatively lightweight desktop application without requiring a bundled Chromium runtime.

React provides the flexibility needed for a sophisticated document-editing workspace.

## 2.2 Rust Backend

| Technology | Responsibility |
|---|---|
| Rust | Application backend |
| Tokio | Asynchronous runtime |
| SQLx | Database access |
| Serde | Serialization |
| UUID | Entity identifiers |
| Tracing | Logging and diagnostics |
| Tauri Commands | Frontend/backend communication |

Rust is responsible for:

- Application lifecycle.
- Project management.
- Filesystem operations.
- Pipeline orchestration.
- Python worker management.
- LaTeX compiler management.
- SQLite persistence.
- Event delivery to the frontend.

The Rust backend should not contain AI model implementations.

## 2.3 Python AI Worker

| Technology | Responsibility |
|---|---|
| Python 3.12+ | AI pipeline |
| uv | Dependency management |
| Pydantic | Structured schemas |
| OpenCV | Image preprocessing |
| Pillow | Image handling |
| Provider SDKs | Model integration |
| pytest | Testing |

Python is responsible for:

- Image preprocessing.
- OCR and vision inference.
- Document reconstruction.
- Document classification.
- LaTeX generation.
- Semantic validation.
- Agent execution.

## 2.4 Document Engine

| Technology | Responsibility |
|---|---|
| LaTeX | Document representation |
| latexmk | Compilation orchestration |
| Tectonic | Optional alternative compiler |
| Jinja2 | Template rendering |
| PDF.js | Preview rendering |

The compiler should run as a restricted subprocess with controlled filesystem access and execution limits.

## 2.5 Persistence

SQLite is the source of truth for project metadata, processing state, and artifact references.

The filesystem stores:

- Original images.
- Processed images.
- Extracted text.
- Intermediate JSON.
- Generated LaTeX.
- Compiled PDFs.
- Logs.
- Document versions.

Large binary files should not be stored as SQLite blobs.

---

# 3. High-Level Architecture

The application consists of three primary processes.

## 3.1 Desktop Process

**Tauri + React**

Responsible for:

- Rendering the interface.
- Handling user interaction.
- Managing project navigation.
- Importing images.
- Editing LaTeX.
- Displaying PDFs.
- Showing pipeline progress.
- Communicating with Rust commands.

## 3.2 Application Core

**Rust**

Responsible for:

- Application state.
- Project lifecycle.
- Database operations.
- Worker process management.
- Job orchestration.
- Artifact management.
- Compilation management.
- Event broadcasting.

Rust acts as the coordinator between the UI, AI worker, and compiler.

## 3.3 AI Worker

**Python**

Responsible for executing specialized processing stages.

The worker should communicate through a structured JSON Lines protocol over stdin/stdout.

This avoids introducing a separate HTTP service for local communication.

Worker logs should be sent to stderr so stdout remains reserved for protocol messages.

## 3.4 Architecture Diagram

```text
┌──────────────────────────────────────────────┐
│             Tauri Desktop Application        │
│                                              │
│  React / TypeScript                          │
│  ├── Project Management                      │
│  ├── Image Upload                            │
│  ├── Pipeline Monitor                        │
│  ├── Monaco Editor                           │
│  └── PDF.js Preview                          │
└──────────────────────┬───────────────────────┘
                       │
                 Tauri Commands
                       │
┌──────────────────────▼───────────────────────┐
│                Rust Application Core         │
│                                              │
│  ├── Domain                                  │
│  ├── Storage                                 │
│  ├── Orchestration                           │
│  ├── Worker Client                           │
│  └── Compiler                                │
└──────────────┬─────────────────┬─────────────┘
               │                 │
         JSONL / IPC        Subprocess
               │                 │
┌──────────────▼───────┐  ┌──────▼─────────────┐
│   Python AI Worker   │  │   LaTeX Compiler   │
│                      │  │                    │
│  Preprocessing       │  │  latexmk           │
│  Extraction          │  │  Template Build    │
│  Reconstruction      │  │  PDF Generation    │
│  Classification      │  │  Diagnostics       │
│  Generation          │  │                    │
│  Validation          │  │                    │
└──────────────┬───────┘  └──────────┬─────────┘
               │                     │
               └──────────┬──────────┘
                          │
              ┌───────────▼────────────┐
              │    Persistent Storage  │
              │                        │
              │  SQLite                │
              │  Original Images       │
              │  Intermediate Artifacts│
              │  LaTeX Sources         │
              │  Compiled PDFs         │
              │  Logs and Versions     │
              └────────────────────────┘
```

---

# 4. Repository Structure

Use a monorepo containing the desktop application, Rust workspace, Python worker, shared schemas, and LaTeX templates.

```text
document-studio/
│
├── apps/
│   └── desktop/
│       ├── src/
│       │   ├── app/
│       │   ├── components/
│       │   │   ├── layout/
│       │   │   ├── upload/
│       │   │   ├── pipeline/
│       │   │   └── common/
│       │   ├── features/
│       │   │   ├── projects/
│       │   │   ├── documents/
│       │   │   ├── editor/
│       │   │   ├── preview/
│       │   │   └── templates/
│       │   ├── hooks/
│       │   ├── stores/
│       │   ├── lib/
│       │   └── types/
│       │
│       └── src-tauri/
│           ├── src/
│           │   ├── commands/
│           │   ├── events/
│           │   ├── state/
│           │   ├── process/
│           │   └── lib.rs
│           └── tauri.conf.json
│
├── crates/
│   ├── domain/
│   ├── storage/
│   ├── orchestration/
│   ├── worker-client/
│   └── compiler/
│
├── workers/
│   └── ai/
│       ├── src/
│       │   └── document_ai/
│       │       ├── agents/
│       │       ├── providers/
│       │       ├── pipelines/
│       │       ├── schemas/
│       │       ├── preprocessing/
│       │       └── worker.py
│       ├── tests/
│       └── pyproject.toml
│
├── templates/
│   ├── academic/
│   ├── notes/
│   ├── technical-report/
│   ├── resume/
│   └── general/
│
├── schemas/
│   ├── worker-protocol/
│   └── artifacts/
│
├── fixtures/
│   └── sample-documents/
│
├── scripts/
│
├── Cargo.toml
├── package.json
└── README.md
```

## 4.1 Rust Workspace Responsibilities

### crates/domain

Contains:

- Project entities.
- Document entities.
- Artifact entities.
- Pipeline stage definitions.
- Job status definitions.
- Domain validation.
- Shared error types.

Should not depend on Tauri, SQLite, or AI providers.

### crates/storage

Contains:

- SQLite connection management.
- Database migrations.
- Project persistence.
- Document persistence.
- Artifact indexing.
- Version history.
- Filesystem storage operations.

### crates/orchestration

Contains:

- Pipeline execution.
- Stage dependencies.
- Job scheduling.
- Retry policies.
- Cancellation.
- Recovery.
- Progress tracking.

### crates/worker-client

Contains:

- Python process lifecycle.
- JSONL communication.
- Request serialization.
- Response deserialization.
- Worker health checks.
- Error handling.

### crates/compiler

Contains:

- LaTeX toolchain detection.
- Compilation.
- Build isolation.
- Diagnostics parsing.
- PDF artifact generation.
- Build cancellation and timeouts.

---

# 5. Frontend Architecture

## 5.1 Primary Workspace

The application should use a resizable three-panel workspace.

```text
┌────────────────────────────────────────────────────────────┐
│ Document Studio        Project       Build       Export     │
├───────────────┬──────────────────────┬─────────────────────┤
│               │                      │                     │
│ Project       │    LaTeX Editor      │    PDF Preview      │
│ Sidebar       │                      │                     │
│               │    main.tex          │    Page 1 / 4       │
│ Documents     │                      │                     │
│               │    Source            │    Rendered         │
│ Source Images │    Editing            │    Document         │
│               │                      │                     │
├───────────────┴──────────────────────┴─────────────────────┤
│ Pipeline: Extraction ✓ Reconstruction ✓ Compilation ✓     │
└────────────────────────────────────────────────────────────┘
```

## 5.2 Components

| Component | Responsibility |
|---|---|
| AppShell | Main application layout |
| ProjectSidebar | Project and document navigation |
| ImageUploader | Image import and ordering |
| ImageInspector | Image inspection, crop, rotation |
| PipelinePanel | Pipeline execution and progress |
| ExtractionReview | Display extracted content |
| TemplateSelector | Select document template |
| LatexEditor | Monaco editor integration |
| PdfPreview | PDF.js rendering |
| ProblemsPanel | Compiler and validation diagnostics |
| ExportDialog | Export generated artifacts |

## 5.3 State Management

Use Zustand for frontend state.

Recommended stores:

```text
stores/
├── project-store.ts
├── document-store.ts
├── editor-store.ts
├── pipeline-store.ts
└── workspace-store.ts
```

The frontend should not be the source of truth for pipeline execution. Rust owns job state; Zustand maintains the current UI representation.

## 5.4 Frontend API Contract

```typescript
export interface DocumentStudioAPI {
  createProject(
    input: CreateProjectInput
  ): Promise<Project>;

  importImages(
    projectId: string,
    files: string[]
  ): Promise<SourceImage[]>;

  startPipeline(
    documentId: string,
    options: PipelineOptions
  ): Promise<Job>;

  getJob(jobId: string): Promise<Job>;

  getDocument(
    documentId: string
  ): Promise<Document>;

  getLatex(
    documentId: string
  ): Promise<string>;

  updateLatex(
    documentId: string,
    source: string
  ): Promise<void>;

  compileDocument(
    documentId: string
  ): Promise<CompilationResult>;

  getTemplates(): Promise<Template[]>;

  exportDocument(
    documentId: string,
    format: "pdf" | "tex"
  ): Promise<string>;
}
```

## 5.5 Pipeline Events

Use Tauri events for asynchronous progress.

```typescript
type PipelineEvent =
  | {
      type: "stage_started";
      jobId: string;
      stage: string;
    }
  | {
      type: "stage_progress";
      jobId: string;
      stage: string;
      progress?: number;
      message?: string;
    }
  | {
      type: "stage_completed";
      jobId: string;
      stage: string;
      artifactId: string;
    }
  | {
      type: "stage_failed";
      jobId: string;
      stage: string;
      error: string;
    }
  | {
      type: "job_completed";
      jobId: string;
    };
```

The UI subscribes to events and updates the pipeline store.

---

# 6. Rust Backend Interfaces

The Rust backend should coordinate execution without coupling itself to individual AI implementations.

## 6.1 WorkerClient

```rust
pub trait WorkerClient {
    async fn execute(
        &self,
        job: WorkerJob,
    ) -> Result<WorkerResult, WorkerError>;

    async fn cancel(
        &self,
        job_id: &str,
    ) -> Result<(), WorkerError>;
}
```

## 6.2 DocumentCompiler

```rust
pub trait DocumentCompiler {
    async fn compile(
        &self,
        input: CompileInput,
    ) -> Result<CompileResult, CompileError>;
}
```

## 6.3 Orchestration Responsibilities

The orchestration layer should:

1. Validate the requested job.
2. Create a persistent job record.
3. Resolve the next eligible pipeline stage.
4. Execute the worker.
5. Persist returned artifacts.
6. Update job state.
7. Emit frontend events.
8. Continue to the next stage.
9. Recover from failures when possible.
10. Mark the document ready when the pipeline completes.

Pipeline state should survive application restarts.

---

# 7. Python AI Architecture

## 7.1 Agent Interface

Every agent should use strongly typed inputs and outputs.

```python
from typing import Protocol, TypeVar
from pydantic import BaseModel

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class Agent(Protocol[InputT, OutputT]):
    async def execute(
        self,
        input: InputT
    ) -> OutputT:
        ...
```

This ensures that agents can be tested and replaced independently.

## 7.2 Agent Responsibilities

### Image Preprocessing Agent

Input: Original images.

Responsibilities:

- Detect orientation.
- Correct rotation.
- Deskew.
- Perspective correction.
- Crop page boundaries.
- Improve contrast.
- Normalize resolution.

Output: Processed images.

### Vision / Extraction Agent

Input: Processed images.

Responsibilities:

- OCR.
- Handwriting recognition where supported.
- Mathematical notation recognition.
- Table extraction.
- Diagram identification.
- Layout and spatial relationship detection.

Output: Structured extracted blocks.

### Document Reconstruction Agent

Input: Extracted blocks.

Responsibilities:

- Reconstruct paragraphs.
- Identify sections.
- Preserve document ordering.
- Reconstruct lists.
- Associate equations with surrounding text.
- Handle page transitions.
- Identify document hierarchy.

Output: Structured document representation.

### Document Classification Agent

Input: Reconstructed document.

Responsibilities:

- Determine document type.
- Identify likely formatting conventions.
- Select an appropriate template.
- Extract metadata.

Initial document categories:

- Academic papers.
- Lecture notes.
- Handwritten notes.
- Technical reports.
- Mathematical problem sets.
- Resumes.
- Letters.
- General documents.

### LaTeX Generation Agent

Input:

- Reconstructed document.
- Selected template.
- Document metadata.

Responsibilities:

- Generate LaTeX.
- Map content to template sections.
- Select packages.
- Format equations.
- Generate tables.
- Preserve references.
- Generate document metadata.

Output: LaTeX source.

### Validation Agent

Input: Generated LaTeX.

Responsibilities:

- Validate document structure.
- Identify missing content.
- Check equation formatting.
- Detect invalid LaTeX.
- Inspect compiler diagnostics.
- Request targeted repairs.

Output: Validation diagnostics and compilation status.

The validator should not independently rewrite the entire document without preserving existing user edits.

---

# 8. Model Provider Abstraction

The application should support hybrid inference.

Agents should not directly depend on a particular model vendor.

## 8.1 Provider Interfaces

```python
class VisionProvider(Protocol):
    async def analyze_image(
        self,
        image_path: str,
        prompt: str
    ) -> dict:
        ...


class TextProvider(Protocol):
    async def generate_structured(
        self,
        prompt: str,
        schema: type[BaseModel]
    ) -> BaseModel:
        ...
```

## 8.2 Initial Providers

| Provider | Purpose |
|---|---|
| MLX | Apple Silicon local inference |
| Ollama | Local model serving |
| OpenAI-compatible API | Hosted inference |
| Cloud vision provider | Advanced image interpretation |

## 8.3 Provider Routing

Provider selection should be configuration-driven.

Example:

```yaml
inference:
  routing:
    preprocessing: local
    extraction: local
    reconstruction: cloud
    classification: local
    latex_generation: cloud
    validation: local

  providers:
    local:
      type: openai_compatible
      base_url: http://localhost:1234/v1

    cloud:
      type: openai_compatible
      base_url: https://api.example.com/v1
      api_key_env: DOCUMENT_STUDIO_API_KEY
```

The endpoint is illustrative and should be replaced with the actual provider configuration.

Important requirements:

- Support multiple providers.
- Support per-stage model selection.
- Support local-first routing.
- Support explicitly configured fallbacks.
- Validate model capabilities.
- Support structured outputs.
- Preserve model and provider metadata for reproducibility.
- Never silently transmit private documents to cloud providers.

---

# 9. Data Models

## 9.1 Project

```typescript
interface Project {
  id: string;
  name: string;
  createdAt: string;
  updatedAt: string;
}
```

A project contains multiple documents.

## 9.2 Document

```typescript
interface Document {
  id: string;
  projectId: string;
  title: string;
  status: DocumentStatus;
  templateId?: string;
  activeVersionId?: string;
}
```

## 9.3 SourceImage

```typescript
interface SourceImage {
  id: string;
  documentId: string;
  path: string;
  pageNumber: number;
  checksum: string;
}
```

## 9.4 Artifact

```typescript
interface Artifact {
  id: string;
  documentId: string;
  type: ArtifactType;
  path: string;
  stage: string;
  createdAt: string;
}
```

## 9.5 Job

```typescript
interface Job {
  id: string;
  documentId: string;
  status: JobStatus;
  currentStage?: string;
  createdAt: string;
  completedAt?: string;
}
```

## 9.6 Template

```typescript
interface Template {
  id: string;
  name: string;
  category: string;
  version: string;
  description?: string;
  entrypoint: string;
  requiredPackages: string[];
}
```

## 9.7 Document Version

```typescript
interface DocumentVersion {
  id: string;
  documentId: string;
  versionNumber: number;
  latexArtifactId: string;
  templateId?: string;
  createdAt: string;
}
```

---

# 10. Database Schema

Initial SQLite schema:

```sql
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL,
    template_id TEXT,
    active_version_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id)
        REFERENCES projects(id)
);

CREATE TABLE source_images (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    path TEXT NOT NULL,
    page_number INTEGER NOT NULL,
    checksum TEXT NOT NULL,
    FOREIGN KEY(document_id)
        REFERENCES documents(id)
);

CREATE TABLE jobs (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    status TEXT NOT NULL,
    current_stage TEXT,
    error TEXT,
    created_at TEXT NOT NULL,
    completed_at TEXT
);

CREATE TABLE artifacts (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    job_id TEXT,
    type TEXT NOT NULL,
    stage TEXT NOT NULL,
    path TEXT NOT NULL,
    checksum TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE document_versions (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    version_number INTEGER NOT NULL,
    latex_artifact_id TEXT,
    template_id TEXT,
    created_at TEXT NOT NULL
);
```

Additional implementation requirements:

- Enable SQLite foreign key enforcement.
- Use transactional writes.
- Add database migrations through SQLx.
- Store timestamps in UTC.
- Index frequently queried IDs and statuses.
- Use checksums to detect artifact modifications.
- Preserve old document versions.
- Track pipeline stage execution separately from overall job status.

---

# 11. Filesystem Layout

Each project should be independently organized.

```text
data/
└── projects/
    └── project-uuid/
        └── documents/
            └── document-uuid/
                │
                ├── sources/
                │   ├── page-001.jpg
                │   └── page-002.jpg
                │
                ├── artifacts/
                │   ├── preprocessing/
                │   ├── extraction/
                │   │   └── extracted.json
                │   ├── reconstruction/
                │   │   └── document.json
                │   └── generation/
                │       └── generated.tex
                │
                ├── versions/
                │   ├── v001/
                │   │   ├── main.tex
                │   │   └── document.pdf
                │   └── v002/
                │       ├── main.tex
                │       └── document.pdf
                │
                └── logs/
```

The distinction between `artifacts` and `versions` is important.

- Artifacts are outputs from automated pipeline stages.
- Versions are user-facing document revisions.

The original images should never be overwritten by preprocessing.

---

# 12. Pipeline Execution

## 12.1 Deterministic Pipeline

Use a deterministic DAG instead of allowing a free-form autonomous agent to control the entire workflow.

```text
Images Uploaded
      |
      v
Image Preprocessing
      |
      v
Vision / OCR Extraction
      |
      v
Document Reconstruction
      |
      v
Document Classification
      |
      v
Template Resolution
      |
      v
LaTeX Generation
      |
      v
Compilation
      |
      v
Validation
      |
      v
Document Ready
```

## 12.2 Pipeline State

Suggested statuses:

```typescript
type JobStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

type StageStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "skipped";
```

Every stage should:

1. Validate its input.
2. Execute its operation.
3. Validate its output.
4. Persist its artifact.
5. Record execution metadata.
6. Report completion or failure.

## 12.3 Recovery

If LaTeX generation fails, extraction should not run again.

If compilation fails, the system should preserve the generated source and previous successful PDF.

If the application closes during processing, the job should be recoverable on the next startup.

## 12.4 Source Traceability

Every reconstructed content block should retain its original source reference.

Example:

```json
{
  "block_id": "block-104",
  "type": "equation",
  "content": "E = mc^2",
  "source": {
    "image_id": "image-001",
    "page": 1,
    "bounding_box": [0.12, 0.34, 0.82, 0.41]
  },
  "confidence": 0.97
}
```

This enables future functionality such as selecting an equation in the generated PDF and locating its original position in the photograph.

---

# 13. LaTeX Template System

Templates should be independent of the AI agents.

The AI should provide structured content; the template engine should control presentation.

## 13.1 Initial Templates

- General-purpose article.
- Academic paper.
- Lecture notes.
- Technical report.
- Resume.
- Letter.

## 13.2 Template Structure

Example:

```text
templates/
└── academic/
    ├── manifest.yaml
    ├── main.tex.j2
    ├── preamble.tex.j2
    └── assets/
```

Example manifest:

```yaml
id: academic-article
name: Academic Article
version: "1.0.0"
category: academic

entrypoint: main.tex.j2

required_packages:
  - amsmath
  - amssymb
  - graphicx
  - geometry

metadata:
  title: true
  author: true
  date: true
```

## 13.3 Template Resolution

The classification agent recommends a template.

The template resolver validates that the template exists and that all required metadata is available.

The generation agent then populates the template.

This keeps document content separate from formatting.

---

# 14. Editor and PDF Preview

## 14.1 Monaco Editor

Requirements:

- LaTeX syntax highlighting.
- Line numbers.
- Editing and autosaving.
- Search and replace.
- Keyboard shortcuts.
- Compiler diagnostic markers.
- Document version history.

## 14.2 PDF.js

Requirements:

- Render compiled PDF.
- Page navigation.
- Zoom controls.
- Search.
- Text selection.
- Refresh after successful compilation.

## 14.3 Compilation Workflow

The PDF preview should not recompile on every keystroke.

Recommended workflow:

1. Monaco detects edits.
2. Changes are debounced for autosaving.
3. User presses `Ctrl+S` or Build.
4. Rust creates a compilation job.
5. latexmk compiles into a temporary directory.
6. Diagnostics are collected.
7. On success, the new PDF is atomically promoted to the active preview.
8. On failure, the last successful PDF remains visible.
9. Errors appear in the Problems panel.

The compiler should monitor dependencies such as:

- `.tex`
- `.bib`
- `.sty`
- Included figures and other document assets.

## 14.4 Version Management

The system should distinguish between:

- AI-generated versions.
- User-edited versions.
- Automatically repaired versions.

Never overwrite a user's manually edited LaTeX when regenerating the document.

---

# 15. Security and Reliability

Security is especially important because generated LaTeX can execute commands under certain compiler configurations.

Initial requirements:

- Run compilation with `-no-shell-escape`.
- Use restricted filesystem access.
- Apply CPU and memory limits.
- Enforce compilation timeouts.
- Never interpolate user input into shell commands.
- Validate worker messages.
- Restrict worker access to project directories.
- Preserve original source files.
- Secure API keys using operating-system credential storage.
- Require explicit permission for cloud processing.
- Keep sensitive document data out of application logs.

Compilation should eventually use a sandboxed environment with an explicit allowlist of packages and dependencies.

---

# 16. Implementation Roadmap

Development should proceed through vertical slices, ensuring the application remains runnable throughout development.

## Milestone 1 — End-to-End MVP

**Objective:** Upload photographs, process them, generate LaTeX, compile a PDF, and edit the document.

### Tasks

| Task | Deliverable |
|---|---|
| Desktop bootstrap | Working Tauri + React application |
| Rust workspace | Five initial crates |
| Python worker | Independently executable package |
| Shared protocol | JSONL worker contracts |
| Project management | Create and open projects |
| Image ingestion | Import multiple photographs |
| Worker integration | Rust launches Python worker |
| Extraction | Structured text and equations |
| Reconstruction | Structured document JSON |
| Template engine | General and academic templates |
| LaTeX generation | Generated source |
| Compiler integration | PDF compilation |
| Editor | Monaco integration |
| Preview | PDF.js integration |
| Persistence | SQLite and artifact storage |

### Acceptance Criteria

- [ ] User can create a project.
- [ ] User can create a document.
- [ ] User can import multiple photographs.
- [ ] User can initiate the pipeline with one click.
- [ ] Pipeline progress appears in the GUI.
- [ ] Extracted text is persisted.
- [ ] Structured document representation is persisted.
- [ ] Template selection works.
- [ ] LaTeX is generated.
- [ ] PDF compiles successfully.
- [ ] LaTeX can be manually edited.
- [ ] PDF preview refreshes after compilation.
- [ ] Closing and reopening the application preserves the project.
- [ ] Failed stages can be retried without rerunning successful stages.

### Explicitly Deferred

- Autonomous multi-agent planning.
- Multiple simultaneous pipelines.
- Cloud synchronization.
- Collaborative editing.
- Advanced equation correction interface.
- Custom template authoring GUI.
- Sophisticated layout reconstruction.
- Complex document comparison.

## Milestone 2 — Document Intelligence

**Objective:** Improve extraction accuracy and document reconstruction.

Features:

- Better handwritten text support.
- Improved mathematical notation extraction.
- Table reconstruction.
- Diagram handling.
- Confidence-based highlighting.
- Multi-page continuity.
- Source image navigation.
- Selective section regeneration.
- Automated LaTeX repair.

## Milestone 3 — Advanced Editing

**Objective:** Turn the MVP into a polished document production environment.

Features:

- Source-to-image traceability.
- PDF-to-LaTeX navigation.
- Advanced editor diagnostics.
- Template management interface.
- Version comparison.
- Undo and redo.
- Document metadata editor.
- Custom document packages.
- Export configuration.

## Milestone 4 — AI and Infrastructure Expansion

**Objective:** Expand inference and automation capabilities.

Features:

- Multiple local inference providers.
- Multiple cloud providers.
- Per-agent model routing.
- Configurable fallback.
- Model benchmarking.
- Batch document processing.
- Pipeline configuration.
- Plugin architecture.
- Advanced agent collaboration.

---

# 17. Testing Strategy

Testing should be implemented alongside each subsystem.

| Layer | Framework | Tests |
|---|---|---|
| Rust domain | cargo test | Entity validation |
| Rust storage | cargo test | CRUD, migrations, transactions |
| Worker client | cargo test | Process lifecycle and IPC |
| Compiler | cargo test | Successful and failed builds |
| Python | pytest | Agent inputs and outputs |
| Frontend | Vitest | Components and state |
| Integration | pytest / Rust | Complete pipeline |
| Desktop | Manual / E2E | User workflows |

## Golden Dataset

Create a small collection of representative documents:

1. Printed academic paper.
2. Handwritten lecture notes.
3. Mathematical equations.
4. Technical report.
5. Multi-page document.
6. Table-heavy document.
7. Mixed text and diagrams.

For each, preserve:

- Original photographs.
- Expected extracted text.
- Expected structured document.
- Expected LaTeX output.
- Reference PDF.

This dataset will be useful for regression testing model and prompt changes.

---

# 18. Development Priorities

The recommended development sequence is:

### Phase 1: Foundation

- Initialize repository.
- Bootstrap Tauri.
- Set up React and TypeScript.
- Create Cargo workspace.
- Initialize Python package.
- Define shared schemas.

### Phase 2: Project Management

- SQLite migrations.
- Project creation.
- Document creation.
- Filesystem organization.
- Image import.

### Phase 3: Worker Integration

- JSONL protocol.
- Python process lifecycle.
- Mock worker.
- Progress events.
- Error handling.
- Cancellation.

### Phase 4: AI Pipeline

- Image preprocessing.
- Vision extraction.
- Document reconstruction.
- Classification.
- LaTeX generation.

### Phase 5: Document Engine

- Template resolution.
- LaTeX compilation.
- Diagnostic parsing.
- PDF artifact storage.

### Phase 6: GUI Integration

- Three-panel workspace.
- Pipeline monitor.
- Monaco editor.
- PDF.js viewer.
- Autosave.
- Build workflow.

### Phase 7: Real Inference

- Connect local models.
- Connect cloud models.
- Configure routing.
- Test representative documents.
- Tune prompts and validation.

---

# 19. Engineering Decisions and Constraints

These decisions should remain consistent throughout the initial implementation.

| Area | Decision |
|---|---|
| Application framework | Tauri 2 |
| Frontend | React + TypeScript |
| Backend | Rust |
| Async runtime | Tokio |
| Database | SQLite |
| Database access | SQLx |
| AI worker | Python |
| Python management | uv |
| AI schemas | Pydantic |
| Worker communication | JSONL over stdio |
| Editor | Monaco |
| PDF rendering | PDF.js |
| Compiler | latexmk |
| Templates | Jinja2 |
| Frontend state | Zustand |
| Local inference | MLX / Ollama |
| Cloud inference | Provider abstraction |
| Testing | cargo test / pytest / Vitest |

## Explicit Architectural Constraints

- No Kubernetes requirement.
- No Redis requirement.
- No message broker requirement.
- No mandatory HTTP backend.
- No coupling between agents and model vendors.
- No coupling between document content and templates.
- No direct AI worker access to the frontend.
- No overwriting original images.
- No destructive replacement of user-edited LaTeX.
- No mandatory cloud inference.

The initial system should remain lightweight and self-contained.

---

# 20. Immediate Implementation Target

The first engineering deliverable should be a compilable repository scaffold.

It should contain:

1. Initialized Tauri desktop application.
2. React/TypeScript workspace.
3. Cargo workspace with five Rust crates.
4. Python worker package managed by uv.
5. Shared JSON schemas.
6. JSONL worker protocol.
7. Rust worker process manager.
8. Mock Python worker.
9. Basic SQLite project persistence.
10. Three-panel application interface.
11. Image import.
12. Pipeline progress display.

The first demo should work as follows:

```text
1. Launch Document Studio.

2. Create a new project.

3. Create a document.

4. Import three photographs.

5. Press "Process Document".

6. Rust launches the Python worker.

7. Python executes mock extraction.

8. Worker returns structured JSON.

9. Rust persists the result.

10. UI displays pipeline completion.

11. LaTeX generation produces a sample document.

12. latexmk compiles the PDF.

13. Monaco displays the source.

14. PDF.js displays the compiled document.
```

Initially, the AI worker can return deterministic mock extraction results. This allows the entire desktop application to be developed and tested before introducing model dependencies.

The mock implementation should follow exactly the same schemas and interfaces as the eventual real agents.

---

# 21. Definition of Success

Document Studio will have achieved its initial objective when a user can import photographs and receive a compiled, editable LaTeX document without leaving the desktop application.

The architecture should make it possible to replace an OCR model, introduce a new document classification agent, add a template, or switch inference providers without restructuring the application.

**The core product is not the agent pipeline alone. It is the integrated document production workflow: image ingestion, intelligent reconstruction, editable source, and synchronized rendered output.**

The first priority is therefore a working vertical slice, followed by progressively more sophisticated document intelligence.

