"""
Document Verification Platform - Fully Standalone Streamlit App
No backend required - everything runs in the browser
"""
import streamlit as st
import sqlite3
import hashlib
import uuid
import json
import re
from datetime import datetime
from pathlib import Path
import base64
from io import BytesIO

# Optional imports with fallbacks
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    import easyocr
    EASYOCR_AVAILABLE = True
    # Initialize once
    @st.cache_resource
    def get_easyocr_reader():
        return easyocr.Reader(['en', 'hi'], gpu=False)
except ImportError:
    EASYOCR_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="DocuMatrix - Document Intelligence",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Premium Look
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif;
    }

    .main {
        padding: 2rem;
        background: #f8fafc;
    }

    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
        height: 3rem;
        text-transform: uppercase;
        letter-spacing: 0.025em;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f1f5f9;
        padding: 4px;
        border-radius: 12px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 16px;
        background-color: transparent;
        border: none;
        color: #64748b;
        font-weight: 500;
    }

    .stTabs [aria-selected="true"] {
        background-color: white !important;
        color: #0f172a !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
    }

    .status-done { 
        background: #ecfdf5; border-left: 4px solid #10b981; padding: 1rem; border-radius: 8px; color: #065f46; 
    }
    .status-processing { 
        background: #eff6ff; border-left: 4px solid #3b82f6; padding: 1rem; border-radius: 8px; color: #1e40af; 
    }
    .status-error { 
        background: #fef2f2; border-left: 4px solid #ef4444; padding: 1rem; border-radius: 8px; color: #991b1b; 
    }
    
    h1, h2, h3 {
        color: #0f172a;
        font-weight: 700 !important;
    }

    .analysis-point {
        padding: 0.85rem 1.25rem;
        margin-bottom: 0.75rem;
        border-radius: 10px;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-left: 5px solid #4f46e5;
        font-weight: 500;
        color: #1e293b;
        line-height: 1.5;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }

    hr {
        margin: 1.5rem 0;
        border: none;
        border-top: 1px solid #e2e8f0;
    }
    
    .info-box {
        background: #f0f9ff;
        border: 1px solid #0ea5e9;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ============ DATABASE SETUP ============
DB_PATH = "documents.db"

def init_database():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            filename TEXT,
            file_hash TEXT,
            document_type TEXT,
            ocr_text TEXT,
            extracted_fields TEXT,
            verification_status TEXT,
            fraud_indicators TEXT,
            confidence_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS verification_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id TEXT,
            action TEXT,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(id)
        )
    ''')
    
    # Create index for duplicate detection
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_file_hash ON documents(file_hash)
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get database connection"""
    return sqlite3.connect(DB_PATH)

def compute_file_hash(file_bytes):
    """Compute SHA256 hash of file"""
    return hashlib.sha256(file_bytes).hexdigest()

def check_duplicate(file_hash):
    """Check if document already exists"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, filename, document_type, created_at FROM documents WHERE file_hash = ?", (file_hash,))
    result = cursor.fetchone()
    conn.close()
    return result

def save_document(doc_id, filename, file_hash, doc_type, ocr_text, fields, status, fraud_indicators, confidence):
    """Save document to database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO documents 
        (id, filename, file_hash, document_type, ocr_text, extracted_fields, 
         verification_status, fraud_indicators, confidence_score, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (doc_id, filename, file_hash, doc_type, ocr_text, 
          json.dumps(fields), status, json.dumps(fraud_indicators), 
          confidence, datetime.now()))
    conn.commit()
    conn.close()

def get_document(doc_id):
    """Retrieve document by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            "id": result[0],
            "filename": result[1],
            "file_hash": result[2],
            "document_type": result[3],
            "ocr_text": result[4],
            "extracted_fields": json.loads(result[5]) if result[5] else {},
            "verification_status": result[6],
            "fraud_indicators": json.loads(result[7]) if result[7] else [],
            "confidence_score": result[8],
            "created_at": result[9],
            "updated_at": result[10]
        }
    return None

def get_all_documents():
    """Get all documents"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, filename, document_type, verification_status, created_at FROM documents ORDER BY created_at DESC")
    results = cursor.fetchall()
    conn.close()
    return results

def update_document_fields(doc_id, fields):
    """Update document fields"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE documents SET extracted_fields = ?, updated_at = ? WHERE id = ?
    ''', (json.dumps(fields), datetime.now(), doc_id))
    conn.commit()
    conn.close()

# Initialize database
init_database()

# ============ OCR FUNCTIONS ============

def perform_ocr(image_bytes):
    """Perform OCR on image"""
    if not PIL_AVAILABLE:
        return "Error: PIL/Pillow not installed. Install with: pip install Pillow"
    
    try:
        image = Image.open(BytesIO(image_bytes))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Try EasyOCR first (better for Indian documents)
        if EASYOCR_AVAILABLE:
            try:
                reader = get_easyocr_reader()
                results = reader.readtext(image_bytes)
                text = "\n".join([result[1] for result in results])
                if text.strip():
                    return text
            except Exception as e:
                st.warning(f"EasyOCR failed: {e}, trying Tesseract...")
        
        # Fall back to Tesseract
        if TESSERACT_AVAILABLE:
            try:
                text = pytesseract.image_to_string(image, lang='eng+hin')
                if text.strip():
                    return text
            except Exception as e:
                st.warning(f"Tesseract failed: {e}")
        
        # If no OCR engine available, return placeholder
        return """[OCR Engine Not Available]

To enable OCR, install one of:
1. EasyOCR: pip install easyocr
2. Tesseract: pip install pytesseract (and install Tesseract OCR)

For Streamlit Cloud, add to requirements.txt:
easyocr
pytesseract

Sample extracted text for demo:
Name: JOHN DOE
Date of Birth: 01/01/1990
Document Number: ABCD1234567
Address: 123 Main Street, City, State
"""
    except Exception as e:
        return f"OCR Error: {str(e)}"

# ============ DOCUMENT CLASSIFICATION ============

DOCUMENT_PATTERNS = {
    "pan_card": {
        "keywords": ["permanent account number", "income tax department", "pan", "govt. of india"],
        "patterns": [r"[A-Z]{5}[0-9]{4}[A-Z]"],  # PAN format
        "fields": ["pan_number", "name", "father_name", "date_of_birth"]
    },
    "aadhaar_card": {
        "keywords": ["aadhaar", "unique identification", "uidai", "आधार"],
        "patterns": [r"\d{4}\s?\d{4}\s?\d{4}"],  # Aadhaar format
        "fields": ["aadhaar_number", "name", "date_of_birth", "gender", "address"]
    },
    "driving_license": {
        "keywords": ["driving", "license", "licence", "motor vehicle", "transport"],
        "patterns": [r"[A-Z]{2}\d{2}\s?\d{11}"],  # DL format
        "fields": ["license_number", "name", "date_of_birth", "validity", "address"]
    },
    "birth_certificate": {
        "keywords": ["birth", "certificate", "registration", "born", "child"],
        "patterns": [],
        "fields": ["name", "date_of_birth", "place_of_birth", "father_name", "mother_name", "registration_number"]
    },
    "passport": {
        "keywords": ["passport", "republic of india", "nationality", "travel document"],
        "patterns": [r"[A-Z]\d{7}"],  # Passport format
        "fields": ["passport_number", "name", "date_of_birth", "place_of_birth", "nationality", "expiry_date"]
    },
    "income_certificate": {
        "keywords": ["income", "certificate", "annual income", "earnings"],
        "patterns": [],
        "fields": ["name", "income_amount", "financial_year", "issuing_authority"]
    },
    "caste_certificate": {
        "keywords": ["caste", "certificate", "community", "sc", "st", "obc"],
        "patterns": [],
        "fields": ["name", "caste", "father_name", "address", "issuing_authority"]
    },
    "residence_certificate": {
        "keywords": ["residence", "domicile", "residential", "proof of residence"],
        "patterns": [],
        "fields": ["name", "address", "duration", "issuing_authority"]
    }
}

def classify_document(ocr_text):
    """Classify document type based on OCR text"""
    text_lower = ocr_text.lower()
    scores = {}
    
    for doc_type, config in DOCUMENT_PATTERNS.items():
        score = 0
        
        # Check keywords
        for keyword in config["keywords"]:
            if keyword in text_lower:
                score += 10
        
        # Check patterns
        for pattern in config["patterns"]:
            if re.search(pattern, ocr_text, re.IGNORECASE):
                score += 20
        
        scores[doc_type] = score
    
    # Get best match
    if scores:
        best_type = max(scores, key=scores.get)
        if scores[best_type] > 0:
            return best_type, scores[best_type] / 100
    
    return "unknown", 0.0

# ============ FIELD EXTRACTION ============

def extract_fields(ocr_text, document_type):
    """Extract fields based on document type"""
    fields = {}
    
    # Common patterns
    patterns = {
        "name": [
            r"name[:\s]+([A-Z][a-zA-Z\s]+)",
            r"नाम[:\s]+(.+)",
        ],
        "date_of_birth": [
            r"(?:dob|date of birth|birth date|d\.o\.b)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"(\d{1,2}[/-]\d{1,2}[/-]\d{4})",
        ],
        "father_name": [
            r"(?:father|father's name|s/o|d/o)[:\s]+([A-Z][a-zA-Z\s]+)",
            r"पिता[:\s]+(.+)",
        ],
        "mother_name": [
            r"(?:mother|mother's name)[:\s]+([A-Z][a-zA-Z\s]+)",
            r"माता[:\s]+(.+)",
        ],
        "address": [
            r"(?:address|addr)[:\s]+(.+?)(?:\n|$)",
            r"पता[:\s]+(.+)",
        ],
        "pan_number": [
            r"([A-Z]{5}[0-9]{4}[A-Z])",
        ],
        "aadhaar_number": [
            r"(\d{4}\s?\d{4}\s?\d{4})",
        ],
        "license_number": [
            r"([A-Z]{2}\d{2}\s?\d{11})",
            r"(?:dl no|license no)[:\s]*([A-Z0-9]+)",
        ],
        "passport_number": [
            r"([A-Z]\d{7})",
        ],
        "registration_number": [
            r"(?:registration|reg\.? no)[:\s]*([A-Z0-9/-]+)",
        ],
        "gender": [
            r"(?:gender|sex)[:\s]*(male|female|m|f)",
            r"(पुरुष|महिला)",
        ],
        "validity": [
            r"(?:valid|validity|expiry)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        ],
    }
    
    # Get expected fields for document type
    expected_fields = DOCUMENT_PATTERNS.get(document_type, {}).get("fields", [])
    
    for field_name in expected_fields:
        if field_name in patterns:
            for pattern in patterns[field_name]:
                match = re.search(pattern, ocr_text, re.IGNORECASE | re.MULTILINE)
                if match:
                    value = match.group(1).strip()
                    fields[field_name] = {
                        "value": value,
                        "confidence": 0.8
                    }
                    break
            
            # If not found, add empty
            if field_name not in fields:
                fields[field_name] = {"value": "", "confidence": 0.0}
    
    return fields

# ============ FRAUD DETECTION ============

def detect_fraud_indicators(ocr_text, fields, image_bytes=None):
    """Detect potential fraud indicators"""
    indicators = []
    confidence_score = 1.0
    
    # Check for suspicious patterns
    suspicious_patterns = [
        (r"sample|specimen|demo|test", "Contains sample/demo text"),
        (r"photocopy|xerox|copy", "Appears to be a photocopy"),
        (r"draft|provisional", "Document marked as draft/provisional"),
    ]
    
    text_lower = ocr_text.lower()
    
    for pattern, message in suspicious_patterns:
        if re.search(pattern, text_lower):
            indicators.append(message)
            confidence_score -= 0.1
    
    # Check field completeness
    empty_fields = sum(1 for f in fields.values() if not f.get("value"))
    total_fields = len(fields)
    if total_fields > 0:
        completeness = (total_fields - empty_fields) / total_fields
        if completeness < 0.5:
            indicators.append(f"Low field completeness: {completeness*100:.0f}%")
            confidence_score -= 0.2
    
    # Check for low-quality OCR
    if len(ocr_text) < 50:
        indicators.append("Very little text extracted - possible low quality image")
        confidence_score -= 0.3
    
    # Check for mixed scripts (potential tampering)
    has_english = bool(re.search(r"[a-zA-Z]", ocr_text))
    has_hindi = bool(re.search(r"[\u0900-\u097F]", ocr_text))
    if has_english and has_hindi:
        # This is normal for Indian documents, but flag excessive mixing
        pass
    
    confidence_score = max(0.0, min(1.0, confidence_score))
    
    return indicators, confidence_score

def determine_verification_status(confidence_score, fraud_indicators):
    """Determine overall verification status"""
    if confidence_score >= 0.8 and len(fraud_indicators) == 0:
        return "VERIFIED"
    elif confidence_score < 0.4 or len(fraud_indicators) >= 3:
        return "REJECTED"
    else:
        return "NEEDS_REVIEW"

# ============ SIGNATURE/SEAL DETECTION ============

def detect_signatures_seals(image_bytes):
    """Simple signature/seal detection"""
    # This is a simplified version - real implementation would use CV
    signatures = []
    seals = []
    
    if PIL_AVAILABLE:
        try:
            image = Image.open(BytesIO(image_bytes))
            width, height = image.size
            
            # Check bottom portion of document (common signature location)
            # This is a heuristic - real detection would use ML
            bottom_region = image.crop((0, int(height * 0.7), width, height))
            
            # Simple check: if bottom region has dark pixels, might have signature
            if image.mode != 'L':
                bottom_gray = bottom_region.convert('L')
            else:
                bottom_gray = bottom_region
            
            pixels = list(bottom_gray.getdata())
            dark_pixels = sum(1 for p in pixels if p < 100)
            total_pixels = len(pixels)
            
            if dark_pixels / total_pixels > 0.05:
                signatures.append({"location": "bottom", "confidence": 0.6})
            
            # Check for circular patterns (seals)
            # This is placeholder - real implementation would use Hough circles
            
        except Exception:
            pass
    
    return {"signatures": signatures, "seals": seals}

# ============ MAIN VERIFICATION FUNCTION ============

def verify_document(image_bytes, filename):
    """Main verification pipeline"""
    doc_id = str(uuid.uuid4())
    file_hash = compute_file_hash(image_bytes)
    
    # Check for duplicates
    duplicate = check_duplicate(file_hash)
    if duplicate:
        return {
            "status": "DUPLICATE",
            "original_id": duplicate[0],
            "original_filename": duplicate[1],
            "original_type": duplicate[2],
            "original_date": duplicate[3],
            "message": "This document has already been verified"
        }
    
    # Perform OCR
    ocr_text = perform_ocr(image_bytes)
    
    # Classify document
    doc_type, type_confidence = classify_document(ocr_text)
    
    # Extract fields
    fields = extract_fields(ocr_text, doc_type)
    
    # Detect fraud indicators
    fraud_indicators, confidence_score = detect_fraud_indicators(ocr_text, fields, image_bytes)
    
    # Determine status
    verification_status = determine_verification_status(confidence_score, fraud_indicators)
    
    # Detect signatures/seals
    sig_seal = detect_signatures_seals(image_bytes)
    
    # Save to database
    save_document(
        doc_id, filename, file_hash, doc_type, ocr_text,
        fields, verification_status, fraud_indicators, confidence_score
    )
    
    return {
        "id": doc_id,
        "status": "PROCESSED",
        "document_type": doc_type,
        "type_confidence": type_confidence,
        "ocr_text": ocr_text,
        "fields": fields,
        "verification_status": verification_status,
        "fraud_indicators": fraud_indicators,
        "confidence_score": confidence_score,
        "signatures": sig_seal
    }

# ============ UI COMPONENTS ============

# Header
st.markdown("""
    <div style="text-align: center; margin-top: 1rem; margin-bottom: 3rem;">
        <h1 style="font-size: 4rem; font-weight: 900; margin-bottom: 0px; letter-spacing: -0.05em; color: #1e293b; line-height: 1;">
            Docu<span style="background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Matrix</span>
        </h1>
        <div style="height: 5px; width: 60px; background: linear-gradient(90deg, #0ea5e9, #2563eb); margin: 1.5rem auto; border-radius: 10px;"></div>
        <p style="color: #64748b; font-size: 1.25rem; font-weight: 400; max-width: 600px; margin: 0 auto;">
            Standalone Document Verification • No Backend Required
        </p>
    </div>
""", unsafe_allow_html=True)

# System status
ocr_status = "🟢 Available" if (EASYOCR_AVAILABLE or TESSERACT_AVAILABLE) else "🟡 Demo Mode"
st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 1rem;">
        <span style="font-size: 0.85rem; color: #64748b; font-weight: 500;">OCR: {ocr_status}</span>
    </div>
""", unsafe_allow_html=True)

# Create tabs
tabs = st.tabs(["📤 Upload & Verify", "📋 Verification History", "🔍 Document Lookup", "ℹ️ Info"])

# ============ Tab 1: Upload & Verify ============
with tabs[0]:
    st.header("Upload Document")
    st.markdown("Upload an image document for AI-powered verification.")
    
    uploaded = st.file_uploader(
        "Choose a file",
        type=["png", "jpg", "jpeg", "tiff", "bmp"],
        help="Supported formats: PNG, JPG, JPEG, TIFF, BMP (max 10MB)"
    )
    
    if uploaded:
        image_bytes = uploaded.read()
        
        # Show file info
        col1, col2 = st.columns([2, 1])
        with col1:
            st.info(f"📎 **File:** {uploaded.name} ({len(image_bytes) / 1024:.1f} KB)")
        
        # Show preview
        with st.expander("👁️ Preview", expanded=True):
            st.image(image_bytes, caption="Uploaded document", use_column_width=True)
        
        if st.button("🚀 Start Verification", type="primary", use_container_width=True):
            with st.spinner("Processing document..."):
                result = verify_document(image_bytes, uploaded.name)
            
            if result["status"] == "DUPLICATE":
                st.warning(f"""
                    ⚠️ **Duplicate Document Detected!**
                    
                    This document was already verified:
                    - **Original ID:** `{result['original_id']}`
                    - **Filename:** {result['original_filename']}
                    - **Type:** {result['original_type']}
                    - **Date:** {result['original_date']}
                """)
            else:
                # Store result in session for display
                st.session_state.last_result = result
                st.success(f"✅ Document processed! ID: `{result['id']}`")
                st.rerun()
    
    # Display last result
    if 'last_result' in st.session_state:
        result = st.session_state.last_result
        
        # Status banner
        v_status = result.get("verification_status", "UNKNOWN").upper()
        status_styles = {
            "VERIFIED": {"icon": "✅", "color": "#10b981", "bg": "#ecfdf5", "desc": "All authenticity checks passed."},
            "REJECTED": {"icon": "❌", "color": "#ef4444", "bg": "#fef2f2", "desc": "Critical issues detected."},
            "NEEDS_REVIEW": {"icon": "⚠️", "color": "#f59e0b", "bg": "#fffbeb", "desc": "Manual review required."},
        }.get(v_status, {"icon": "❓", "color": "#64748b", "bg": "#f8fafc", "desc": "Processing complete."})

        st.markdown(f"""
            <div style="background-color: {status_styles['bg']}; border: 2px solid {status_styles['color']}; padding: 1.5rem; border-radius: 16px; text-align: center; margin: 2rem 0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
                <div style="font-size: 3rem; margin-bottom: 0.5rem;">{status_styles['icon']}</div>
                <div style="font-size: 2rem; font-weight: 800; color: {status_styles['color']}; text-transform: uppercase;">{v_status}</div>
                <div style="font-size: 1rem; color: #475569; margin-top: 0.5rem;">{status_styles['desc']}</div>
                <div style="font-size: 0.9rem; color: #64748b; margin-top: 0.5rem;">Document Type: <strong>{result.get('document_type', 'Unknown').replace('_', ' ').title()}</strong></div>
                <div style="font-size: 0.9rem; color: #64748b;">Confidence: <strong>{result.get('confidence_score', 0)*100:.1f}%</strong></div>
            </div>
        """, unsafe_allow_html=True)
        
        # Tabs for details
        detail_tabs = st.tabs(["📄 Extracted Fields", "🛡️ Security Analysis", "📝 Raw OCR"])
        
        with detail_tabs[0]:
            fields = result.get("fields", {})
            if fields:
                for name, info in fields.items():
                    value = info.get("value", "Not detected")
                    conf = info.get("confidence", 0) * 100
                    st.markdown(f"**{name.replace('_', ' ').title()}:** {value or 'Not detected'} ({conf:.0f}% confidence)")
            else:
                st.info("No fields extracted")
        
        with detail_tabs[1]:
            col1, col2 = st.columns(2)
            
            with col1:
                sigs = result.get("signatures", {})
                sig_count = len(sigs.get("signatures", []))
                if sig_count > 0:
                    st.success(f"✅ {sig_count} Signature(s) detected")
                else:
                    st.warning("⚠️ No signature detected")
            
            with col2:
                seal_count = len(sigs.get("seals", []))
                if seal_count > 0:
                    st.success(f"✅ {seal_count} Seal(s) detected")
                else:
                    st.info("ℹ️ No seal detected")
            
            # Fraud indicators
            fraud = result.get("fraud_indicators", [])
            if fraud:
                st.markdown("#### ⚠️ Security Alerts")
                for indicator in fraud:
                    st.warning(f"🚩 {indicator}")
            else:
                st.success("✅ No security concerns detected")
        
        with detail_tabs[2]:
            st.text_area("OCR Output", result.get("ocr_text", ""), height=300)
        
        # Clear result button
        if st.button("🗑️ Clear Results"):
            del st.session_state.last_result
            st.rerun()

# ============ Tab 2: History ============
with tabs[1]:
    st.header("Verification History")
    
    documents = get_all_documents()
    
    if documents:
        for doc in documents:
            doc_id, filename, doc_type, status, created_at = doc
            
            status_icon = {"VERIFIED": "✅", "REJECTED": "❌", "NEEDS_REVIEW": "⚠️"}.get(status, "❓")
            
            with st.expander(f"{status_icon} {filename} - {doc_type or 'Unknown'}", expanded=False):
                st.markdown(f"**ID:** `{doc_id}`")
                st.markdown(f"**Type:** {doc_type or 'Unknown'}")
                st.markdown(f"**Status:** {status}")
                st.markdown(f"**Date:** {created_at}")
                
                if st.button("View Details", key=f"view_{doc_id}"):
                    st.session_state.view_doc_id = doc_id
    else:
        st.info("No documents verified yet. Upload a document to get started!")

# ============ Tab 3: Document Lookup ============
with tabs[2]:
    st.header("Document Lookup")
    
    doc_id = st.text_input("Enter Document ID:")
    
    if st.button("🔍 Lookup", use_container_width=True):
        if doc_id:
            doc = get_document(doc_id)
            if doc:
                st.success("Document found!")
                
                st.json({
                    "id": doc["id"],
                    "filename": doc["filename"],
                    "document_type": doc["document_type"],
                    "verification_status": doc["verification_status"],
                    "confidence_score": doc["confidence_score"],
                    "extracted_fields": doc["extracted_fields"],
                    "fraud_indicators": doc["fraud_indicators"],
                    "created_at": doc["created_at"]
                })
                
                # Field correction form
                st.markdown("### ✏️ Update Fields")
                with st.form("update_fields"):
                    updated_fields = {}
                    for name, info in doc["extracted_fields"].items():
                        new_val = st.text_input(
                            name.replace('_', ' ').title(),
                            value=info.get("value", ""),
                            key=f"field_{name}"
                        )
                        updated_fields[name] = {"value": new_val, "confidence": 1.0}
                    
                    if st.form_submit_button("Save Changes"):
                        update_document_fields(doc_id, updated_fields)
                        st.success("✅ Fields updated!")
                        st.rerun()
            else:
                st.error("Document not found")
        else:
            st.warning("Please enter a document ID")

# ============ Tab 4: Info ============
with tabs[3]:
    st.header("ℹ️ System Information")
    
    st.markdown("""
    ### About
    This is a **fully standalone** document verification platform that runs entirely in your browser.
    
    **No backend server required!** Everything runs locally:
    - ✅ OCR processing
    - ✅ Document classification
    - ✅ Field extraction
    - ✅ Fraud detection
    - ✅ SQLite database
    
    ### Supported Document Types
    - PAN Card
    - Aadhaar Card
    - Driving License
    - Birth Certificate
    - Passport
    - Income Certificate
    - Caste Certificate
    - Residence Certificate
    
    ### OCR Engines
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("EasyOCR", "✅ Available" if EASYOCR_AVAILABLE else "❌ Not Installed")
    with col2:
        st.metric("Tesseract", "✅ Available" if TESSERACT_AVAILABLE else "❌ Not Installed")
    
    st.markdown("""
    ### Installation (for full OCR support)
    
    ```bash
    pip install easyocr pillow
    # or
    pip install pytesseract pillow
    ```
    
    For Streamlit Cloud, add to `requirements.txt`:
    ```
    streamlit
    pillow
    easyocr
    ```
    """)
    
    st.divider()
    
    # Database stats
    st.markdown("### Database Statistics")
    docs = get_all_documents()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Documents", len(docs))
    with col2:
        verified = sum(1 for d in docs if d[3] == "VERIFIED")
        st.metric("Verified", verified)
    with col3:
        rejected = sum(1 for d in docs if d[3] == "REJECTED")
        st.metric("Rejected", rejected)

# Footer
st.divider()
st.markdown("""
    <div style="text-align: center; color: #64748b; font-size: 0.85rem;">
        DocuMatrix • Standalone Document Verification • No Backend Required
    </div>
""", unsafe_allow_html=True)
