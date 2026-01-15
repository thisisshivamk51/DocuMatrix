"""
Document Verification Platform - Streamlit Frontend
"""
import streamlit as st
import requests
import os
import time

# API configuration
API_BASE = os.getenv("API_BASE", "http://localhost:8000/api/v1")

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

    /* Glassmorphism Card Style */
    .st-emotion-cache-1r6slb0, .card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        margin-bottom: 1.5rem;
    }

    /* Modern Buttons */
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

    /* Tabs Styling */
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

    /* Custom Status Boxes */
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

    /* HARD FIX: Hide internal Streamlit labels causing overlap */
    [data-testid="stExpander"] button span {
        display: none !important;
    }
    
    .st-emotion-cache-1647y6o, .st-emotion-cache-p5m0v2, .st-emotion-cache-1053lbo {
        overflow: hidden !important;
    }

    /* Sequential List Styling */
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
</style>
""", unsafe_allow_html=True)

# Centered Premium Header
st.markdown("""
    <div style="text-align: center; margin-top: 1rem; margin-bottom: 3rem;">
        <h1 style="font-size: 4rem; font-weight: 900; margin-bottom: 0px; letter-spacing: -0.05em; color: #1e293b; line-height: 1;">
            Docu<span style="background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Matrix</span>
        </h1>
        <div style="height: 5px; width: 60px; background: linear-gradient(90deg, #0ea5e9, #2563eb); margin: 1.5rem auto; border-radius: 10px;"></div>
        <p style="color: #64748b; font-size: 1.25rem; font-weight: 400; max-width: 600px; margin: 0 auto;">
            Professional-grade forensic auditing and structural document intelligence.
        </p>
    </div>
""", unsafe_allow_html=True)

# Check API connection
def check_api():
    try:
        base_url = API_BASE.split('/api')[0]
        resp = requests.get(f"{base_url}/health", timeout=2)
        return resp.status_code == 200
    except:
        return False

# API status indicator (Subtle)
def get_api_status_html(status):
    dot_color = "#10b981" if status else "#ef4444"
    text = "System Online" if status else "System Offline"
    return f"""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 1rem;">
            <div style="width: 8px; height: 8px; background-color: {dot_color}; border-radius: 50%;"></div>
            <span style="font-size: 0.85rem; color: #64748b; font-weight: 500;">{text}</span>
        </div>
    """

api_status = check_api()
st.markdown(get_api_status_html(api_status), unsafe_allow_html=True)

# Create tabs
tabs = st.tabs(["📤 Upload & Verify", "📋 Job Status", "💬 RAG Chat", "ℹ️ Info"])

# ============ Tab 1: Upload & Verify ============
with tabs[0]:
    st.header("Upload Document")
    st.markdown("Upload an image or PDF document for AI-powered verification.")
    
    uploaded = st.file_uploader(
        "Choose a file",
        type=["pdf", "png", "jpg", "jpeg", "tiff"],
        help="Supported formats: PDF, PNG, JPG, JPEG, TIFF (max 50MB)"
    )
    
    if uploaded:
        # Show file info
        col1, col2 = st.columns([2, 1])
        with col1:
            st.info(f"📎 **File:** {uploaded.name} ({uploaded.size / 1024:.1f} KB)")
        
        # Show preview for images
        if uploaded.type and uploaded.type.startswith("image"):
            with st.expander("👁️ Preview", expanded=True):
                st.image(uploaded, caption="Uploaded document", use_column_width=True)
        
        if st.button("🚀 Start Verification", type="primary", use_container_width=True):
            if not api_status:
                st.error("Cannot upload - backend API is not available")
            else:
                files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type)}
                
                with st.spinner("Uploading and starting verification..."):
                    try:
                        resp = requests.post(f"{API_BASE}/upload", files=files, timeout=60)
                        
                        if resp.status_code == 200:
                            data = resp.json()
                            st.success("✅ Verification job created!")
                            st.code(data['job_id'], language=None)
                            st.markdown("**Copy the Job ID above** and go to the **Job Status** tab to monitor progress.")
                            
                            # Store job ID in session
                            if 'job_ids' not in st.session_state:
                                st.session_state.job_ids = []
                            if data['job_id'] not in st.session_state.job_ids:
                                st.session_state.job_ids.insert(0, data['job_id'])
                                st.session_state.job_ids = st.session_state.job_ids[:10]  # Keep last 10
                        else:
                            st.error(f"❌ Upload failed: {resp.text}")
                    except requests.exceptions.Timeout:
                        st.error("❌ Request timed out. The file may be too large.")
                    except requests.exceptions.ConnectionError:
                        st.error("❌ Cannot connect to backend. Make sure the API server is running.")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

# ============ Tab 2: Job Status ============
with tabs[1]:
    st.header("Check Job Status")
    
    # Show recent jobs
    if 'job_ids' in st.session_state and st.session_state.job_ids:
        st.markdown("**Recent Jobs:**")
        selected_job = st.selectbox("Select a job", st.session_state.job_ids, key="job_select")
    else:
        selected_job = None
    
    job_id = st.text_input("Or enter Job ID manually:", value=selected_job or "", key="job_input")
    
    col1, col2 = st.columns(2)
    with col1:
        check_btn = st.button("🔍 Check Status", use_container_width=True)
    with col2:
        auto_refresh = st.checkbox("Auto-refresh (5s)")
    
    if check_btn or (auto_refresh and job_id):
        if job_id:
            try:
                resp = requests.get(f"{API_BASE}/status/{job_id}", timeout=10)
                
                if resp.status_code == 200:
                    data = resp.json()
                    
                    # Status indicator
                    status = data.get("status", "unknown")
                    status_icons = {
                        "done": "✅",
                        "error": "❌", 
                        "processing": "⏳",
                        "queued": "📋"
                    }
                    icon = status_icons.get(status, "❓")
                    
                    st.markdown(f"### {icon} Status: {status.upper()}")
                    
                    # Auto-refresh for processing jobs
                    if status == "processing" and auto_refresh:
                        time.sleep(5)
                        st.rerun()
                    
                    # Show results
                    result = data.get("result")
                    if result:
                        if "error" in result:
                            st.error(f"**Error:** {result['error']}")
                            if "traceback" in result:
                                with st.expander("Error Details"):
                                    st.code(result['traceback'])
                        else:
                            # --- POLISHED CLEAR STRUCTURAL REPORT (V2) ---
                            st.markdown("<br>", unsafe_allow_html=True)
                            
                            # 1. PRIMARY DECISION BANNER
                            v_status = result.get("verification_summary", {}).get("overall_status", "UNKNOWN").upper()
                            status_styles = {
                                "VERIFIED": {"icon": "✅", "color": "#10b981", "bg": "#ecfdf5", "desc": "Verification Successful: All authenticity checks passed."},
                                "REJECTED": {"icon": "❌", "color": "#ef4444", "bg": "#fef2f2", "desc": "Verification Failed: Critical security discrepancies detected."},
                                "NEEDS_REVIEW": {"icon": "⚠️", "color": "#f59e0b", "bg": "#fffbeb", "desc": "Manual Review Required: Some checks were inconclusive."},
                                "APPROVED": {"icon": "✅", "color": "#10b981", "bg": "#ecfdf5", "desc": "Manually Approved by Administrator."}
                            }.get(v_status, {"icon": "❓", "color": "#64748b", "bg": "#f8fafc", "desc": "Processing Complete."})

                            st.markdown(f"""
                                <div style="background-color: {status_styles['bg']}; border: 2px solid {status_styles['color']}; padding: 1.5rem; border-radius: 16px; text-align: center; margin-bottom: 2rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
                                    <div style="font-size: 3rem; margin-bottom: 0.5rem;">{status_styles['icon']}</div>
                                    <div style="font-size: 2rem; font-weight: 800; color: {status_styles['color']}; text-transform: uppercase; letter-spacing: 0.05em;">{v_status}</div>
                                    <div style="font-size: 1.1rem; color: #475569; margin-top: 0.5rem; font-weight: 500;">{status_styles['desc']}</div>
                                </div>
                            """, unsafe_allow_html=True)

                            # 3. DETAILED EVIDENCE
                            tab_data, tab_security = st.tabs(["📄 Extracted Information", "🛡️ Forensic Details"])

                            with tab_data:
                                fields = result.get("fields", {})
                                if fields:
                                    # Presentation-grade table
                                    table_data = []
                                    for name, info in fields.items():
                                        table_data.append({
                                            "Field": name.replace('_', ' ').title(),
                                            "Value": info.get("value", "N/A"),
                                            "Confidence": f"{info.get('confidence', 0)*100:.1f}%"
                                        })
                                    st.table(table_data)
                                else:
                                    st.warning("⚠️ No structured fields were extracted. This usually occurs if the image text is not legible.")

                            with tab_security:
                                scol1, scol2 = st.columns(2)
                                sigs = result.get("signatures", {})
                                
                                with scol1:
                                    st.write("**Human Verification**")
                                    sig_count = len(sigs.get('signatures', []))
                                    if sig_count > 0:
                                        st.success(f"✅ Found {sig_count} Signature(s)")
                                    else:
                                        st.error("❌ No Signatures Detected")
                                
                                with scol2:
                                    st.write("**Institutional Verification**")
                                    seal_count = len(sigs.get('seals', []))
                                    if seal_count > 0:
                                        st.success("✅ Seal/Stamp Verified")
                                    else:
                                        st.info("ℹ️ No Seal/Stamp Detected")

                                # Security Alerts
                                fraud_indicators = result.get("fraud", {}).get("fraud_indicators", [])
                                if fraud_indicators:
                                    st.markdown("#### Security Indicators")
                                    for indicator in list(set(fraud_indicators)):
                                        st.warning(f"🚩 {indicator}")

                            # 4. AI NOTES (SEQUENTIAL & PRESENTABLE)
                            st.markdown("### 🤖 Forensic Intelligence Report")
                            analysis_summary = result.get("analysis_notes") or result.get("verification_summary", {}).get("analysis_summary")
                            if analysis_summary:
                                points = analysis_summary.split("\n")
                                for pt in points:
                                    content = pt.strip()
                                    if content:
                                        # Use a clean, sequential block for each point
                                        st.markdown(f'<div class="analysis-point">{content}</div>', unsafe_allow_html=True)
                            else:
                                st.info("Manual review recommended. Automated analysis could not reach a high confidence conclusion.")

                            # 5. TECHNICAL UTILITIES
                            with st.expander("🛠️ Advanced Inspection Tools"):
                                utab1, utab2 = st.tabs(["OCR Raw Text", "System JSON"])
                                utab1.text(result.get("ocr_text", ""))
                                utab2.json(result)

                            # 6. QUICK CORRECTIONS
                            st.markdown("---")
                            st.markdown("### ✏️ Correction Console")
                            with st.form("corrections_v3"):
                                c_cols = st.columns(2)
                                overrides = {}
                                for i, field_name in enumerate(fields.keys()):
                                    with c_cols[i % 2]:
                                        current = fields[field_name].get("value") or ""
                                        new_val = st.text_input(f"{field_name.replace('_', ' ').title()}", value=current)
                                        if new_val != current:
                                            overrides[field_name] = new_val
                                if st.form_submit_button("Submit Corrections", use_container_width=True, type="primary"):
                                    if overrides:
                                        try:
                                            r = requests.post(f"{API_BASE}/correct/{job_id}", json={"overrides": overrides}, timeout=10)
                                            if r.status_code == 200:
                                                st.success("✅ Updated! Reloding...")
                                                time.sleep(1)
                                                st.rerun()
                                            else:
                                                st.error(f"Save failed: {r.text}")
                                        except Exception as e:
                                            st.error(f"Error: {str(e)}")
                    elif status == "processing":
                        st.info("⏳ Document is being processed... Please wait.")
                    elif status == "queued":
                        st.info("📋 Job is queued and will start processing soon.")
                else:
                    st.error(f"❌ Job not found: {job_id}")
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to backend.")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        else:
            st.warning("Please enter or select a Job ID")

# ============ Tab 3: RAG Chat ============
with tabs[2]:
    st.header("💬 Document Assistant")
    st.markdown("Ask questions about verified documents or document templates.")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about documents..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    resp = requests.post(f"{API_BASE}/chat", json={"query": prompt}, timeout=60)
                    if resp.status_code == 200:
                        answer = resp.json().get("answer", "No response")
                        st.markdown(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                    else:
                        error_msg = f"Error: {resp.text}"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to backend.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    # Clear chat button
    if st.session_state.messages:
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = []
            st.rerun()

# ============ Tab 4: Info ============
with tabs[3]:
    st.header("ℹ️ System Information")
    
    st.markdown("""
    ### About
    This is an AI-powered Document Verification Platform that can:
    - **OCR**: Extract text from document images
    - **Classify**: Identify document types (birth certificate, ID card, etc.)
    - **Extract**: Pull out key fields (name, date, ID numbers)
    - **Verify**: Check for duplicates and potential fraud
    - **Chat**: Answer questions using RAG (Retrieval Augmented Generation)
    
    ### Supported Document Types
    - Birth Certificate
    - ID Card (Aadhaar)
    - Driving License
    - PAN Card
    - Passport
    - Affidavit
    - Income Certificate
    - Residence Certificate
    - Caste Certificate
    
    ### API Endpoints
    | Endpoint | Method | Description |
    |----------|--------|-------------|
    | `/api/upload` | POST | Upload document |
    | `/api/status/{id}` | GET | Check job status |
    | `/api/correct/{id}` | POST | Submit corrections |
    | `/api/chat` | POST | RAG chatbot query |
    """)
    
    st.divider()
    
    st.markdown("### System Status")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("API Status", "🟢 Online" if api_status else "🔴 Offline")
    with col2:
        st.metric("API URL", API_BASE)

# Footer
st.divider()
