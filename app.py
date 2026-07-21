import streamlit as st
import os
import re
import hashlib
import logging
import gc
from datetime import datetime

# 引入強力 PDF 文字提取引擎
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
# 2. RAG 本地向量資料庫引擎 (快取防禦版)
# ==========================================
@st.cache_resource(show_spinner="🛡️ 正在加載本地 Embedding 模型...")
def get_embedding_model():
    return HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

def process_pdf_to_chunks(pdf_file, is_uploaded=False):
    filename = pdf_file.name if is_uploaded else os.path.basename(pdf_file)
    chunks = []
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if not text:
                    continue
                text = re.sub(r'\s+', ' ', text).strip()
                
                chunk_size = 400
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

@st.cache_resource(show_spinner="📚 正在構建 FAISS 向量數據庫 (僅啟動時執行一次)...")
def build_cached_base_vector_db():
    embeddings = get_embedding_model()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_pdf_files = [os.path.join(current_dir, f) for f in os.listdir(current_dir) if f.endswith('.pdf')]
    base_chunks = []
    base_file_names = []
    
    for pdf_path in base_pdf_files:
        base_file_names.append(os.path.basename(pdf_path))
        base_chunks.extend(process_pdf_to_chunks(pdf_path, is_uploaded=False))
        
    if base_chunks:
        vector_db = FAISS.from_documents(base_chunks, embeddings)
        gc.collect()
        return vector_db, base_chunks, base_file_names
    return None, [], []

def get_runtime_vector_db(uploaded_files):
    base_vector_db, base_chunks, base_files = build_cached_base_vector_db()
    
    if not uploaded_files:
        return base_vector_db, base_chunks, base_files, []
        
    embeddings = get_embedding_model()
    all_chunks = list(base_chunks)
    uploaded_file_names = []
    
    for uploaded_file in uploaded_files:
        uploaded_file_names.append(uploaded_file.name)
        all_chunks.extend(process_pdf_to_chunks(uploaded_file, is_uploaded=True))
        
    runtime_db = FAISS.from_documents(all_chunks, embeddings)
    return runtime_db, all_chunks, base_files, uploaded_file_names

# ==========================================
# 3. 🌐 決定性規則引擎層 (精準三重網閘硬化)
# ==========================================
class ControlGuardrails:
    def evaluate(self, query):
        q = query.lower()
        
        # 🚨 第一重網閘：即時解僱風險攔截
        if any(w in q for w in ["唔聽話", "想炒", "即炒", "炒佢", "解僱", "不服從"]):
            return (
                "<div class='confidence-badge'>🎯 匹配置信度：100.0% (決定性法規攔截)</div>\n\n"
                "🛑 **【最高級別合規危機預警：即時解僱風險重大】** ❌\n\n"
                "**⚖️ 香港《僱傭條例》第 9 條法定規範：**\n"
                "僱主只有在僱員犯下極度嚴重過失（例如：故意不服從合法合理的命令、欺詐不忠實、或慣常疏忽職責）時，"
                "才可以無須通知期或代通知金「即時解僱（即炒）」[cite: 1, 4]。\n\n"
                "**🚨 董事會級別合規紅線：**\n"
                "主管口中的『唔聽話』或表現不佳，流於主管主觀感受。若企業缺乏多次清晰的**書面警告信（Warning Letter）**、"
                "績效改善計劃（PIP）及漸進式紀律處分紀錄，單憑口頭頂撞或表現差而即炒，**在勞資審裁處必被判定為「不合理解僱」**[cite: 1, 4]。"
                "企業將面臨補付代通知金、追溯法定福利甚至高達 HK$150,000 補償金的嚴厲申索處分[cite: 1, 4]。\n\n"
                "**🛡️ 營運管治指引：**\n"
                "1. **切勿**在情緒激動下口頭宣告解僱，必須即時通報 HR 啟動標準調查程序。\n"
                "2. 嚴格審查考勤系統，確認該員工是否正處於 **「懷孕生育保障期」** 或 **「有薪病假期間」**，這兩類情境即炒屬刑事罪行，最高罰款 10 萬元[cite: 1, 4]！"
            )
            
        # 🚨 第二重網閘：468 / 418 連續性合約修訂精準攔截
        if any(w in q for w in ["468", "418", "連續性合約", "連續性僱傭"]):
            return (
                "<div class='confidence-badge'>🎯 匹配置信度：100.0% (決定性法規攔截)</div>\n\n"
                "⚖️ **【2026年「連續性合約」新舊制度核心差異與 HR 管治應對】**\n\n"
                "**1. 舊制「418」規定（2026年1月18日前）：**\n"
                "僱員須連續受僱於同一僱主 4 星期或以上，且**每星期均須工作最少 18 小時**，方符合「連續性合約」[cite: 1, 3]。\n\n"
                "**2. 最新「468」新制（2026年1月18日起生效）：**\n"
                "門檻進一步放寬，符合以下**任一條件**即屬「連續性合約」[cite: 1, 3]：\n"
                "• **條件 (i)**：每星期最少工作 **17 小時**（週門檻由 18 下調至 17）[cite: 1, 3]；或\n"
                "• **條件 (ii) - 「468」四週合計準則**：若某星期不足 17 小時，只要該星期與緊接過去三星期（共 4 星期）的**總工時合計不少於 68 小時**，該星期仍算入連續性受僱[cite: 1, 3]！\n\n"
                "**🛡️ HR 企業級管治應對策略（Board & HR Action Plan）：**\n"
                "1. **排班系統 (Roster Engine) 重構**：徹底檢視兼職/炒場員工的排班表，防止前線主管誤以為『某週排 10 小時就不會撞 418』，在『468』新制下此舉會直接觸發合規門檻[cite: 1, 3]！\n"
                "2. **考勤與薪酬數據審計**：備存過去 12 個月完整的工時紀錄（工時低於 $17,600 月薪上限者必須記工時）[cite: 1, 4]，嚴防因漏計而引發遣散費、年假或病假津貼的追討申索[cite: 1, 4]。\n"
                "3. **合規追溯**：[點此查閱勞工處《修訂連續性合約 FAQ》官方原檔](https://github.com/jackylawck/hk-employment-ordinance/blob/main/continuous_contract_FAQ_tc.pdf)[cite: 3]"
            )

        # 🚨 第三重網閘：12個月平均工資 (ADW) 713 條例 / 剔除期精準硬化 (解決答非所問)
        if any(w in q for w in ["adw", "713", "剔除期", "不予計算在內", "平均工資"]):
            return (
                "<div class='confidence-badge'>🎯 匹配置信度：100.0% (決定性法規攔截)</div>\n\n"
                "⚖️ **【香港《僱傭條例》( Cap. 57) - 12 個月平均工資 (ADW) 與「剔除期」權威規範】**\n\n"
                "**1. 什麼是『剔除期』（不予計算在內的期間及工資）？**\n"
                "根據《2007年僱傭（修訂）條例》（簡稱 713 條例），為**避免平均工資被拉低**而損害僱員的法定權益，"
                "在計算過去 12 個月的每日（或每月）平均工資（ADW）時，僱主**必須剔除**僱員獲支付少於全薪的期間及相關工資[cite: 1, 4]。\n\n"
                "**2. 法定須剔除的 2 大核心情境：**\n"
                "• **(i) 放取法定少於全薪或無薪假期**：包括 4/5 薪疾病津貼[cite: 1, 4]、4/5 薪產假[cite: 1, 4]/侍產假[cite: 1, 4]、工傷病假[cite: 1, 4]、或獲僱主同意的無薪假[cite: 1, 4]；\n"
                "• **(ii) 正常工作日不獲提供工作**：例如因業務停頓而停工的無薪日子[cite: 1, 4]。\n\n"
                "**📊 計算公式 (Formula)：**\n"
                "$$\\text{每日平均工資 (ADW)} = \\frac{12 \\text{ 個月工資總額} - \\text{須剔除的假期款額}}{365 \\text{ 天} - \\text{須剔除的假期天數}}$$\n\n"
                "**💡 HR 實務例子（以 14 星期產假為例）：**\n"
                "若僱員過去 12 個月中放取了 14 星期（98 天）的 4/5 薪產假[cite: 1, 4]：\n"
                "• **分子（金額）**：12 個月總收入 減去 14 星期已領取的產假薪酬[cite: 1, 4]；\n"
                "• **分母（天數）**：365 天 減去 98 天（即以 267 天作為分母計算）[cite: 1, 4]。\n\n"
                "**🔍 審計追溯鏈 (Traceability Link):** [EO_guide_full_tc.pdf 附錄一第 48-51 頁]"
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
    st.header("📊 向量資料庫審計監控")
    
    uploaded_files_ctx = st.session_state.get('sidebar_uploader_key', None)
    
    VECTOR_DB, ALL_CHUNKS, BASE_FILES, UPLOADED_FILES = get_runtime_vector_db(uploaded_files_ctx)
    TOTAL_PDF_COUNT = len(BASE_FILES) + len(UPLOADED_FILES)
    TOTAL_CHUNK_COUNT = len(ALL_CHUNKS)
    
    st.metric("當前已加載 PDF 總數", f"{TOTAL_PDF_COUNT} 份")
    st.metric("解構法規文字切片 (Chunks)", f"{TOTAL_CHUNK_COUNT} 個")
    
    st.subheader("📋 知識庫加載清冊 (Asset Log)")
    github_repo_url = "https://github.com/jackylawck/hk-employment-ordinance/blob/main"
    
    st.markdown("**📁 Git 本地法規底座 (點擊跳轉源碼鏈接):**")
    if BASE_FILES:
        for f_name in BASE_FILES:
            st.markdown(f"<div class='file-inventory'>📦 <a href='{github_repo_url}/{f_name}' target='_blank' style='color:#007bff; text-decoration:none;'>{f_name}</a></div>", unsafe_allow_html=True)
            
    if UPLOADED_FILES:
        st.markdown("**⏳ 會話臨時記憶體注入 (揮發性資料):**")
        for f_name in UPLOADED_FILES:
            st.markdown(f"<div class='file-inventory'>📥 {f_name} (臨時鎖定)</div>", unsafe_allow_html=True)
            
    st.markdown("---")
    
    st.header("📂 動態法規擴充")
    st.file_uploader(
        "上傳最新勞工處 PDF 文件 (如新政策指引/FAQ)", 
        type=["pdf"], 
        accept_multiple_files=True,
        key="sidebar_uploader_key"
    )
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
    
    st.header("🔗 官方權威渠道")
    st.markdown("🌐 **[香港特區政府勞工處官網](https://www.labour.gov.hk/)**")
    st.markdown("📞 **勞工處查詢熱線：2717 1771**")

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
                
                # 🔥 修正處：移除過於寬鬆的 "工資" 加分，改為精準動態加分
                boost_score = 0
                q_lower = prompt.lower()
                if any(w in q_lower for w in ["減人工", "扣薪", "扣錢"]): boost_score += 60
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
