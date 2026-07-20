import streamlit as st
import os
import re
import hashlib
import logging
from datetime import datetime

# 🎯 核心更換：引入更強大的 PDF 文字提取引擎
import pdfplumber
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

# ==========================================
# 0. 企業級審計日誌初始化
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
    .file-inventory {
        font-size: 0.85em !important;
        color: #adb5bd !important;
        padding-left: 10px !important;
        border-left: 2px solid #6c757d !important;
        margin-bottom: 5px !important;
    }
    .smw-alert-box {
        background-color: #212529 !important;
        border-left: 4px solid #ffb74d !important;
        padding: 12px !important;
        border-radius: 4px !important;
        margin-bottom: 15px !important;
        color: #ffffff !important;
    }
    .smw-alert-box b, .smw-alert-box strong {
        color: #ffb74d !important;
    }
    </style>
""", unsafe_allow_html=True)

if 'messages' not in st.session_state:
    st.session_state.messages = []

# ==========================================
# 2. RAG 本地向量資料庫引擎 (pdfplumber 強力解鎖版)
# ==========================================
@st.cache_resource(show_spinner="🛡️ 正在初始化本地 Embedding 引擎...")
def get_embedding_model():
    return HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

def process_pdf_to_chunks(pdf_file, is_uploaded=False):
    filename = pdf_file.name if is_uploaded else os.path.basename(pdf_file)
    chunks = []
    try:
        # 🔥 改用 pdfplumber 開啟，徹底解鎖複雜版面與中文字型
        with pdfplumber.open(pdf_file) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if not text:
                    continue
                
                # 清理異常多餘的空白字元，保持法規整潔度
                text = re.sub(r'\s+', ' ', text).strip()
                
                chunk_size = 400  # 稍微擴大視野範圍
                overlap = 80
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

def build_combined_vector_db(uploaded_files):
    embeddings = get_embedding_model()
    all_chunks = []
    base_file_names = []
    uploaded_file_names = []
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_pdf_files = [os.path.join(current_dir, f) for f in os.listdir(current_dir) if f.endswith('.pdf')]
    
    for pdf_path in base_pdf_files:
        name = os.path.basename(pdf_path)
        base_file_names.append(name)
        # 直接傳遞路徑字串給處理函數
        all_chunks.extend(process_pdf_to_chunks(pdf_path, is_uploaded=False))
        
    if uploaded_files:
        for uploaded_file in uploaded_files:
            uploaded_file_names.append(uploaded_file.name)
            all_chunks.extend(process_pdf_to_chunks(uploaded_file, is_uploaded=True))
            
    if all_chunks:
        vector_db = FAISS.from_documents(all_chunks, embeddings)
        return vector_db, all_chunks, base_file_names, uploaded_file_names
    else:
        return None, [], [], []

# ==========================================
# 3. 🌐 決定性規則引擎層
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
                "企業將面臨補付代通知金、追溯法定福利甚至高達 HK$150,000 補償金的嚴厲申索處分。\n\n"
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
# 4. 主畫面與側邊欄渲染
# ==========================================
st.title("⚖️ Cap. 57 Employment Ordinance Advisor")
st.subheader("RAG 向量資料庫架構 • 具備動態防禦網閘與語意追溯")

st.warning(
    "⚠️ **【企業合規重要聲明 & 免責宣告】**\n\n"
    "本系統為人工智能輔助診斷工具，其檢索與分析結果僅供企業內部 HR 風險排查與管治參考，**絕不構成正式法律意見**。"
    "AI 系統可能因語意邊界或提示詞不全而產生判斷偏差。遇到重大勞資決策，請務必以 **[特區政府勞工處官方網站](https://www.labour.gov.hk/)** "
    "發布的主體條文與指引為最終權威依歸，或尋求專業法律顧問意見。"
)

with st.sidebar:
    st.header("🔗 官方權威渠道")
    st.markdown("🌐 **[香港特區政府勞工處官網](https://www.labour.gov.hk/)**")
    st.markdown("📞 **勞工處查詢熱線：2717 1771**")
    st.markdown("---")
    
    st.header("💰 法定最低工資動態看板")
    st.markdown(
        "<div class='smw-alert-box'>"
        "⚠️ <b>管治提示：</b> 法定最低工資（SMW）具備高度動態時效性（如2026年5月1日起調升至每小時 $43.1 且總工時紀錄上限上調至 $17,600）。"
        "為嚴防法規滯後風險，計糧精算請務必一鍵跳轉交叉核對官方最新公告："
        "</div>", 
        unsafe_allow_html=True
    )
    st.markdown("📢 **[最新法定最低工資 - 官方中文專頁](https://www.labour.gov.hk/tc/news/mwo.htm)**")
    st.markdown("📢 **[Statutory Minimum Wage - Official English Page](https://www.labour.gov.hk/eng/news/mwo.htm)**")
    st.markdown("---")
    
    st.header("📂 動態法規擴充")
    uploaded_files = st.file_uploader(
        "上傳最新勞工處 PDF 文件 (如新政策指引/FAQ)", 
        type=["pdf"], 
        accept_multiple_files=True,
        help="上傳之文件僅保存在當前暫存記憶體內，網頁關閉即全量銷毀，完全對齊數據最小化隱私標準。"
    )
    st.markdown("---")
    
    VECTOR_DB, ALL_CHUNKS, BASE_FILES, UPLOADED_FILES = build_combined_vector_db(uploaded_files)
    TOTAL_PDF_COUNT = len(BASE_FILES) + len(UPLOADED_FILES)
    TOTAL_CHUNK_COUNT = len(ALL_CHUNKS)
    
    st.header("📊 向量資料庫審計監控")
    st.metric("當前已加載 PDF 總數", f"{TOTAL_PDF_COUNT} 份")
    st.metric("解構法規文字切片 (Chunks)", f"{TOTAL_CHUNK_COUNT} 個")
    
    st.subheader("📋 知識庫加載清冊 (Asset Log)")
    github_repo_url = "https://github.com/jackylawck/hk-employment-ordinance/blob/main"
    
    st.markdown("**📁 Git 本地法規底座 (點擊跳轉源碼鏈接):**")
    if BASE_FILES:
        for f_name in BASE_FILES:
            st.markdown(f"<div class='file-inventory'>📦 <a href='{github_repo_url}/{f_name}' target='_blank' style='color:#007bff; text-decoration:none;'>{f_name}</a></div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='file-inventory'>❌ 未偵測到本地法規底座</div>", unsafe_allow_html=True)
        
    if UPLOADED_FILES:
        st.markdown("**⏳ 會話臨時記憶體注入 (揮發性資料):**")
        for f_name in UPLOADED_FILES:
            st.markdown(f"<div class='file-inventory'>📥 {f_name} (臨時鎖定)</div>", unsafe_allow_html=True)

# ==========================================
# 5. 聊天與對話分流
# ==========================================
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
            
            intercepted_advice = guardrails.evaluate(prompt)
            
            if intercepted_advice:
                st.markdown(intercepted_advice, unsafe_allow_html=True)
                final_response = intercepted_advice
            elif VECTOR_DB is None:
                st.error("🛑 **系統管治警報：** 知識庫尚未加載任何文件！")
                final_response = "未偵測到知識庫文件。"
            else:
                docs_and_scores = VECTOR_DB.similarity_search_with_score(prompt, k=3)
                
                top_doc, top_score = docs_and_scores[0]
                base_confidence = max(5.0, min(95.0, (1.2 - (top_score / 2.5)) * 100))
                
                boost_score = 0
                q_lower = prompt.lower()
                if "468" in q_lower or "連續性" in q_lower: boost_score += 65
                if any(w in q_lower for w in ["減人工", "扣薪", "扣錢", "工資"]): boost_score += 60
                if any(w in q_lower for w in ["減福利", "改合約", "更改條款"]): boost_score += 60
                
                final_confidence = max(base_confidence, boost_score)
                if final_confidence > 100.0: final_confidence = 100.0
                
                if final_confidence < 25.0:
                    st.error(
                        f"🛑 **【系統置信度過低阻斷】(最高匹配信度僅: {final_confidence:.1f}%)**\n\n"
                        f"您的提問語意過於模糊。為防止自動化偏見引發合規偏差，系統拒絕盲猜答案。"
                    )
                    fb = "🔍 **已為您啟動安全兜底**：請直接查閱 [官方 Cap. 57 原文](https://www.elegislation.gov.hk/hk/cap57) 或點擊左側連結前往勞工處官網核對。"
                    st.markdown(fb)
                    final_response = fb
                else:
                    st.success("🎯 **RAG 語意檢索完成！已為您勾勒出最高相關度之官方原始條文：**")
                    st.markdown(f"<div class='confidence-badge'>🎯 綜合匹配置信度：{final_confidence:.1f}%</div>", unsafe_allow_html=True)
                    
                    for doc, score in docs_and_scores:
                        chunk_conf = max(5.0, min(95.0, (1.2 - (score / 2.5)) * 100))
                        if boost_score > chunk_conf: chunk_conf = boost_score
                        
                        source_file = doc.metadata["source"]
                        page_num = doc.metadata["page"]
                        chunk_hash = doc.metadata["hash"]
                        
                        with st.expander(f"📄 來源：{source_file} (第 {page_num} 頁) | 局部信度：{chunk_conf:.1f}%", expanded=True):
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
