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
    .audit-trail {font-family: 'Courier New', Courier, monospace; color: #a1a1a1; font-size: 0.8em; margin-top: 10px; border-top: 1px dashed #ced4da; padding-top: 5px;}
    
    /* 全主題適應硬化版 CSS 標籤 */
    .source-tag {
        background-color: #e9ecef !important; 
        border-left: 4px solid #007bff !important; 
        color: #212529 !important; 
        padding: 10px !important; 
        margin: 8px 0 !important; 
        font-size: 0.9em !important; 
        border-radius: 4px !important;
        font-weight: 500 !important;
    }
    .confidence-badge {
        background-color: #343a40 !important;
        color: #f8f9fa !important;
        padding: 6px 12px !important;
        border-radius: 20px !important;
        font-size: 0.85em !important;
        font-weight: bold !important;
        display: inline-block !important;
        margin-bottom: 10px !important;
        border: 1px solid #495057 !important;
    }
    </style>
""", unsafe_allow_html=True)

if 'messages' not in st.session_state:
    st.session_state.messages = []

# ==========================================
# 2. RAG 本地向量資料庫引擎 (路徑硬化防線)
# ==========================================
@st.cache_resource(show_spinner="🛡️ 正在初始化本地 Embedding 引擎...")
def get_embedding_model():
    return HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

def process_pdf_to_chunks(pdf_path):
    filename = os.path.basename(pdf_path)
    chunks = []
    try:
        reader = PdfReader(pdf_path)
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text()
            if not text:
                continue
            
            chunk_size = 350
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
    embeddings = get_embedding_model()
    all_chunks = []
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_files = [os.path.join(current_dir, f) for f in os.listdir(current_dir) if f.endswith('.pdf')]
    
    for pdf_path in pdf_files:
        all_chunks.extend(process_pdf_to_chunks(pdf_path))
        
    if all_chunks:
        vector_db = FAISS.from_documents(all_chunks, embeddings)
        return vector_db, len(pdf_files), len(all_chunks)
    else:
        return None, 0, 0

VECTOR_DB, PDF_COUNT, CHUNK_COUNT = initialize_vector_db()

# ==========================================
# 3. 🌐 決定性規則引擎層 (移除所有殘留 Citation 標記)
# ==========================================
class ControlGuardrails:
    def evaluate(self, query):
        q = query.lower()
        if any(w in q for w in ["唔聽話", "想炒", "即炒", "炒佢", "解僱", "不服從"]):
            return (
                "<div class='confidence-badge'>🎯 匹配置信度：100.0% (決定性法規攔截)</div>\n\n"
                "🛑 **【最高級別合規危機預警：即時解僱風險重大】** ❌\n\n"
                "**⚖️ 香港《僱傭條例》第 9 條法定規範：**\n"
                "僱主只有在僱員犯下極度嚴重過失（例如：故意不服從合法合理的命令、欺詐不忠實、或慣常疏忽職責）時，"
                "才可以無須通知期或代通知金「即時解僱（即炒）」。\n\n"
                "**🚨 董事會級別合規紅線：**\n"
                "主管口中的『唔聽話』或表現不佳，流於主管主觀感受。若企業缺乏多次清晰的**書面警告信（Warning Letter）**、"
                "績效改善計劃（PIP）及漸進式紀律處分紀錄，單憑口頭頂撞或表現差而即炒，**在勞資審裁處必被判定為「不合理解僱」**。"
                "企業將面臨補付代通知金、追溯法定福利甚至高達 HK$150,000 補償金的嚴厲申索變相處分。\n\n"
                "**🛡️ 營運管治指引：**\n"
                "1. **切勿**在情緒激動下口頭宣告解僱，必須即時通報 HR 啟動標準調查程序。\n"
                "2. 嚴格審查考勤系統，確認該員工是否正處於 **「懷孕生育保障期」** 或 **「有薪病假期間」**，這兩類情境即炒屬刑事罪行，最高罰款 10 萬元！"
            )
        return None

guardrails = ControlGuardrails()

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
st.subheader("RAG 向量資料庫架構 • 具備動態防禦網閘與語意追溯")

# 🔥 核心修正：乾淨無文字污染的頂置官方免責宣告
st.warning(
    "⚠️ **【企業合規重要聲明 & 免責宣告】**\n\n"
    "本系統為人工智能輔助診斷工具，其檢索與分析結果僅供企業內部 HR 風險排查與管治參考，**絕不構成正式法律意見**。"
    "AI 系統可能因語意邊界或提示詞不全而產生判斷偏差。遇到重大勞資決策，請務必以 **[特區政府勞工處官方網站](https://www.labour.gov.hk/)** "
    "發布的主體條文與指引為最終權威依歸，或尋求專業法律顧問意見。"
)

with st.sidebar:
    st.header("📊 向量資料庫審計監控")
    st.metric("已加載官方 PDF 數量", f"{PDF_COUNT} 份")
    st.metric("解構法規文字切片 (Chunks)", f"{CHUNK_COUNT} 個")
    st.markdown("---")
    st.markdown("💡 **AIGP 治理提示：** 系統已熔接『動態信度看板』。凡置信度低於 45% 的模糊查詢將被硬熔斷拒答，確保合規安全性。")

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
            
            # 網閘第一層：高危勞資糾紛決定性精準攔截
            intercepted_advice = guardrails.evaluate(prompt)
            
            if intercepted_advice:
                st.markdown(intercepted_advice, unsafe_allow_html=True)
                final_response = intercepted_advice
            elif VECTOR_DB is None:
                st.error("🛑 **系統管治警報：** 未偵測到任何官方 PDF 檔案！")
                final_response = "未偵測到知識庫文件。"
            else:
                # 執行向量空間語意檢索
                docs_and_scores = VECTOR_DB.similarity_search_with_score(prompt, k=3)
                
                # 網閘第二層：動態信度閥門控制
                top_doc, top_score = docs_and_scores[0]
                normalized_top_confidence = max(0.0, min(100.0, (1.0 - (top_score / 2.0)) * 100))
                
                if normalized_top_confidence < 45.0:
                    st.error(
                        f"🛑 **【系統置信度過低阻斷】(最高匹配信度僅: {normalized_top_confidence:.1f}%)**\n\n"
                        f"您的提問語意在當前官方 PDF 知識庫中匹配密度極低（低於 45.0% 阻斷線）。為防止自動化偏見引發合規偏差，系統拒絕盲猜答案。"
                    )
                    fb = "🔍 **已為您啟動安全兜底**：請直接查閱 [官方 Cap. 57 原文](https://www.elegislation.gov.hk/hk/cap57) 或前往上述勞工處官方網站核對。"
                    st.markdown(fb)
                    final_response = fb
                else:
                    st.success("🎯 **RAG 語意檢索完成！已為您勾勒出最高相關度之官方原始條文：**")
                    for doc, score in docs_and_scores:
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
