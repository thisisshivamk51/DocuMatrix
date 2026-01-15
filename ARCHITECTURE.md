# Document Verification Platform - Comprehensive System Architecture

This document provides an exhaustive technical specification of the Document Verification Platform, covering algorithmic details, logic weighting, service interactions, and data schemas.

---

## 1. System Architecture Overview
The platform utilizes a **Decoupled Service-Oriented Architecture (SOA)** built with Python. It is designed to process unstructured document images into structured, verified data points using a composite AI pipeline.

### Core Architecture Components:
1.  **Orchestrator (FastAPI)**: Manages the lifecycle of a verification request.
2.  **Vision Suite (OpenCV/Pillow)**: Handles image normalization and forensic analysis.
3.  **Extraction Engine (PaddleOCR/Regex)**: Converts pixels to text and text to entities.
4.  **Intelligence Layer (RAG/FAISS)**: Provides context-aware search and similarity detection.
5.  **Risk Engine (The Analyzer)**: Aggregates all signals into a finalized risk profile.

---

## 2. Technical Deep-Dive: Service Logic

### A. The Risk Engine (`analyser.py`)
The Analyzer uses a weighted heuristic model to determine document validity.

| Category | Indicator | Risk Penalty | Rationale |
| :--- | :--- | :--- | :--- |
| **Integrity** | ELA Tampering | +8.0 | High probability of digital alteration. |
| **Logic** | Missing Signature | +2.0 to +4.0 | Critical for legal/invoice documents. |
| **OCR Quality** | Text Length < 30 | +4.0 | Insufficient data for reliable verification. |
| **Consistency** | Duplicate pHash | +5.0 | Potential multi-submission fraud. |
| **Metadata** | Low Resolution | +1.0 | Higher chance of extraction errors. |

**Final Risk Levels:**
*   **CLEAN (Score 0-3)**: Document matches all requirements.
*   **MEDIUM (Score 4-7)**: Minor discrepancies or quality issues. Needs human review.
*   **HIGH (Score 8+)**: Critical failure (Tampering, no text, or major fraud flags).

---

### B. Forensic Pipeline (`fraud.py` & `signatures.py`)

#### 1. Error Level Analysis (ELA)
*   **Step 1**: Open original image $I_{orig}$.
*   **Step 2**: Re-compress $I_{orig}$ at 90% JPEG quality to create $I_{resave}$.
*   **Step 3**: Calculate the absolute difference $D = |I_{orig} - I_{resave}|$.
*   **Step 4**: Compute the average variance across $D$. Since tampered regions often have different compression statistics than the original capture, they appear as bright "hotspots" in the ELA map.
*   **Threshold**: If variance $> 10.0$, the document is flagged for manual tampering review.

#### 2. Color-Agnostic Signature Detection
Instead of simple color filtering, we use a **Chrominance-Luminance Deviation** method:
*   **Luminance Map**: Adaptive Gaussian thresholding ($31 \times 31$ block) to isolate dark strokes against paper.
*   **Chrominance Map**: Calculated as $max(R,G,B) - min(R,G,B)$. This isolates colored ink (Blue, Red) even if it's very light.
*   **Heuristic Overlays**: Entities are classified as **Signatures** if:
    *   Horizontal Bias (Aspect Ratio $> 1.2$).
    *   Density Range between $5\%$ and $50\%$ (Handwriting is "airier" than printed blocks).
    *   Position typically in the bottom $55\%$ of the document.

---

### C. Information Extraction Engine (`extractor.py`)
Utilizes structured regex patterns with spatial anchoring:

*   **Aadhaar**: `\d{4}\s\d{4}\s\d{4}` (12 digits, optional spacing).
*   **PAN Card**: `[A-Z]{5}\d{4}[A-Z]` (Standardized 5-4-1 format).
*   **Name Detection**: Multi-language labels (e.g., "नाम", "Name") followed by title-cased string capture. Noise filters exclude common words like "Government", "Father", "Address".

---

### D. RAG & Semantic Memory (`rag.py`)
*   **Encoder**: `all-MiniLM-L6-v2` (384-dimensional dense vectors).
*   **Vector DB**: FAISS (IndexFlatL2) for sub-millisecond similarity lookups.
*   **Mechanism**: Every verified document text is indexed. When a new document arrives, a similarity search is performed. If the distance is too low (Similarity $> 95\%$), it triggers a **Duplicate Fraud Alert**.

---

## 3. Data Flow Specification

### 1. Ingestion Phase
*   **File Handling**: Supports JPG, PNG, and PDF (via `pdf2image` @ 300 DPI).
*   **Normalization**: Images are deskewed and resized to a max dimension of 2000px to balance speed and accuracy.

### 2. Execution Pipeline (Concurrent)
*   **Branch A (Vision)**: ELA Analysis $\rightarrow$ Signature/Seal Detection $\rightarrow$ Blur Detection.
*   **Branch B (Text)**: PaddleOCR $\rightarrow$ Text Sanitization $\rightarrow$ Field Extraction.
*   **Branch C (Identity)**: pHash generation $\rightarrow$ FAISS Hash Lookup.

### 3. Aggregation Phase
The results from all branches are piped into the `DocumentAnalyzer` which compiles the `VerificationReport` object returned to the Streamlit UI.

---

## 4. Directory Structure Topology
```text
/
├── backend/
│   ├── app/
│   │   ├── api/            # Route controllers (FastAPI)
│   │   ├── core/           # Security & Configuration
│   │   ├── services/       # Algorithmic Logic
│   │   │   ├── ocr.py      # PaddleOCR/Tesseract orchestration
│   │   │   ├── fraud.py    # ELA and pHash logic
│   │   │   ├── signatures.py # CV-based ink detection
│   │   │   ├── analyser.py # Weighted risk engine
│   │   │   └── rag.py      # FAISS & Embeddings
│   │   └── models/         # Pydantic Schemas
├── frontend/               # Streamlit UI & Visuals
├── uploads/                # Volatile file storage
└── docker-compose.yml      # Orchestration config
```

## 5. Deployment & Performance
*   **Concurrency**: Managed via FastAPI's async loops.
*   **Caching**: FAISS indices are persisted to disk in `.bin` format for instant restarts.
*   **Scaling**: The service is container-ready; the `backend` and `frontend` can be scaled horizontally behind a load balancer.
