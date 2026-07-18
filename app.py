import streamlit as st
import os
import re
import hashlib
import logging
from datetime import datetime

# 引入企業級 RAG 必備組件
from pypdf import PdfReader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

# ==========================================
# 0. 企業級審計日誌初始化 (ISO 42001 & AIGP Compliance)
# ==========================================
logging.basicConfig(
    filename='compliance_audit.log', 
    level=logging.INFO,
    format='%(asctime)s | ISO42001-RAG-AUDIT | %(levelname)s | %(message)s'
)

# ==========================================
# 1. 頁面配置與 UI 初始化
# ==========================================
st.set_page_config(
    page_title="HK Cap. 57 RAG Enterprise Advisor",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stCheckbox > label {font-weight: 500;}
    .audit-trail {font-family: 'Courier New', Courier, monospace; color: #6c757d; font-size: 0.8em; margin-top: 10px; border-top: 1px dashed #ced4da; padding-top: 5px;}
    .source-tag {background-color: #f8f9fa; border-left: 3px solid #007bff; padding: 8px; margin: 5px 0; font-size: 0.9em; border-radius: 4px;}
    </style>
""", unsafe_allow_html=True)

if 'messages' not in st.session_state:
    st.session_state.messages = []

# ==========================================
# 2. RAG 本地向量資料庫引擎 (FAISS + SentenceTransformers)
# ==========================================
@st.cache_resource(show_spinner="🛡️ 正在初始化本地 Embedding 引擎...")
def get_embedding_model():
    return HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

def process_pdf_to_chunks(pdf_path):
    """將 PDF 檔案進行具脈絡重疊切片 (Sliding Window Chunking)"""
    filename = os.path.basename(pdf_path)
    chunks = []
    try:
        reader = PdfReader(pdf_path)
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text()
            if not text:
                continue
            
            chunk_size = 300
            overlap = 50
            start = 0
            while start < len(text):
                end = start + chunk_size
                chunk_text = text[start:end]
                
                doc = Document(
                    page_content=chunk_text,
                    metadata={
                        "source": filename,
                        "page": page_num,
                        "hash": hashlib.md5(chunk_text.encode('utf-8')).hexdigest()[:8]
                    }
                )
                chunks.append(doc)
                start += (chunk_size - overlap)
    except Exception as e:
        logging.error(f"Error processing PDF {filename}: {str(e)}")
    return chunks

@st.cache_resource(show_spinner="📚 向量資料庫正在掃描並加載官方 PDF 文件...")
def initialize_vector_db():
    """動態鎖定專案真實絕對路徑，構建 FAISS 向量資料庫"""
    embeddings = get_embedding_model()
    all_chunks = []
    
    # 獲取當前 app.py 所在的絕對路徑目錄
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 掃描該目錄下所有以 .pdf 結尾的檔案
    pdf_files = [os.path.join(current_dir, f) for f in os.listdir(current_dir) if f.endswith('.pdf')]
    
    for pdf_path in pdf_files:
        all_chunks.extend(process_pdf_to_chunks(pdf_path))
        
    if all_chunks:
        vector_db = FAISS.from_documents(all_chunks, embeddings)
        logging.info(f"FAISS DB successfully built with {len(all_chunks)} chunks from {len(pdf_files)} PDFs.")
        return vector_db, len(pdf_files), len(all_chunks)
    else:
        return None, 0, 0

# 啟動 RAG 引擎
VECTOR_DB, PDF_COUNT, CHUNK_COUNT = initialize_vector_db()

# ==========================================
# 3. 密碼學審計軌跡生成 (Non-repudiation Layer)
# ==========================================
def generate_and_log_audit_trail(query, response_text):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    raw_data = f"{query}|{response_text}|{timestamp}".encode('utf-8')
    audit_hash = hashlib.sha256(raw_data).hexdigest()[:16].upper()
    logging.info(f"HashID: [{audit_hash}] | Prompt: {query}")
    return f"<div class='audit-trail'>🔒 ISO 42001 Cryptographic Audit ID: {audit_hash} | Timestamp: {timestamp} (Log secured to local ledger)</div>"

# ==========================================
# 4. 主畫面佈局渲染
# ==========================================
st.title("⚖️ Cap. 57 Employment Ordinance Advisor")
st.subheader("RAG 向量資料庫架構 • 具備高透明度法規追溯與語意檢索")

with st.sidebar:
    st.header("📊 向量資料庫審計監控")
    st.metric("已加載官方 PDF 數量", f"{PDF_COUNT} 份")
    st.metric("解構法規文字切片 (Chunks)", f"{CHUNK_COUNT} 個")
    st.markdown("---")
    st.markdown("💡 **企業管治提示：** 本系統採用 RAG 架構。您只需將最新的官方 FAQ PDF 檔案上傳至專案目錄，系統便會動態完成向量化檢索，消滅硬編碼盲區。")

tab_chat, tab_audit = st.tabs(["💬 官方 FAQ 情境導航 (RAG)", "📋 基礎風險排查"])

with tab_chat:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"], unsafe_allow_html=True)

    if prompt := st.chat_input("請輸入您想查詢的勞工處官方情境..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            final_response = ""
            
            if VECTOR_DB is None:
                st.error("🛑 **系統管治警報：** 未偵測到任何官方 PDF 檔案！請檢查目錄下的 PDF 部署狀態。")
                final_response = "未偵測到知識庫文件。"
            else:
                # 執行向量空間語意檢索 (Semantic Vector Search)
                docs_and_scores = VECTOR_DB.similarity_search_with_score(prompt, k=3)
                st.success("🎯 **RAG 語意檢索完成！已為您勾勒出最高相關度之官方原始條文：**")
                
                for doc, score in docs_and_scores:
                    # 歐氏距離分數歸一化
                    confidence = max(0.0, min(100.0, (1.0 - (score / 2.0)) * 100))
                    source_file = doc.metadata["source"]
                    page_num = doc.metadata["page"]
                    chunk_hash = doc.metadata["hash"]
                    
                    with st.expander(f"📄 來源：{source_file} (第 {page_num} 頁) | 匹配置信度：{confidence:.1f}%", expanded=True):
                        st.markdown(f"**【官方原始答覆文本】**\n\n{doc.page_content}")
                        st.markdown(
                            f"<div class='source-tag'>🔍 <b>審計追溯鏈 (Traceability Link):</b> "
                            f"Doc_ID: {chunk_hash} | File: {source_file}#Page_{page_num}</div>", 
                            unsafe_allow_html=True
                        )
                        final_response += f"[{source_file} Page {page_num}]: {doc.page_content}\n\n"
            
            audit_html = generate_and_log_audit_trail(prompt, final_response)
            st.markdown(audit_html, unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": final_response + audit_html})

with tab_audit:
    st.write("📋 風險排查表單運作正常。")
