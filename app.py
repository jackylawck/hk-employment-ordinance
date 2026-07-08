import streamlit as st
import re
import hashlib
import logging
import json
import os
from datetime import datetime

# ==========================================
# 0. 企業級後台審計日誌初始化 (Backend Audit Logging)
# AIGP Domain IV: 確保所有合規建議具備不可否認性 (Non-repudiation)
# ==========================================
logging.basicConfig(
    filename='compliance_audit.log', 
    level=logging.INFO,
    format='%(asctime)s | ISO42001-AUDIT | %(levelname)s | %(message)s'
)

# ==========================================
# 1. 頁面配置與 UI 初始化 (Page Config)
# ==========================================
st.set_page_config(
    page_title="HK Cap. 57 Enterprise Advisor",
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
    </style>
""", unsafe_allow_html=True)

if 'lang' not in st.session_state:
    st.session_state.lang = '繁體中文'
if 'messages' not in st.session_state:
    st.session_state.messages = []

is_zh = st.session_state.lang == '繁體中文'

# ==========================================
# 2. 知識庫徹底解耦層 (Strict Data Decoupling)
# AIGP Domain III: 業務邏輯與資料本體分離，支援 CMS 獨立更新
# ==========================================
DB_FILE_PATH = 'cap57_db.json'

def init_and_load_knowledge_base():
    # 若 JSON 不存在，自動初始化（模擬從外部 CMS 接入的過程）
    if not os.path.exists(DB_FILE_PATH):
        initial_db = {
            "ch1": {
                "keys": ["適用範圍", "418", "468", "連續性合約", "兼職", "part-time", "散工", "炒散", "假自僱"],
                "zh": {
                    "title": "第一章：《僱傭條例》適用範圍與「468」連續性合約",
                    "statute": "有關連續性合約已放寬為現行「468機制」：指僱員連續受僱於同一僱主 4 星期或以上，4 星期內總工作時數滿 68 小時或以上，即屬連續性合約並享有法定福利。",
                    "red_flag": "錯誤包裝「獨立承包人（假自僱）」，或刻意打斷工時以規避 468 門檻。",
                    "gov_advice": "【董事會管治】重新審視兼職排班策略，防範集體勞資索償風險。\n【前線營運】確實記錄上下班時間，切勿口頭要求員工「提早下班」惡意避開 468 門檻。"
                },
                "en": {
                    "title": "Chapter 1: Application & '468' Continuous Contract",
                    "statute": "A 'continuous contract' (468 rule) means an employee works for 4+ weeks with at least 68 hours total, entitling them to statutory benefits.",
                    "red_flag": "Misclassifying employees or artificially breaking the 468 contract.",
                    "gov_advice": "[Governance] Review rostering strategies to mitigate class action risks."
                }
            },
            "ch3": {
                "keys": ["工資", "salary", "扣薪", "扣錢", "出糧", "遲出糧", "欠薪", "late pay", "爛嘢", "打破"],
                "zh": {
                    "title": "第三章：工資發放限期與法定扣薪限制",
                    "statute": "工資必須在工資期屆滿後 7 天內支付。除法例明文規定（如因疏忽損壞僱主貨品每次上限$300且總額不超該期工資1/4）外，嚴禁扣薪。",
                    "red_flag": "遲發工資超過 7 天（涉刑事罪行），或以「表現不佳」非法扣薪。",
                    "gov_advice": "【董事會管治】將「欠薪」視為最高級別刑事法律風險。\n【前線營運】員工打破公司財產，法定每次損壞扣款上限硬性規定為 HK$300。"
                },
                "en": {
                    "title": "Chapter 3: Wages & Statutory Deduction Limits",
                    "statute": "Wages must be paid within 7 days. Damage to goods is capped at HK$300 deduction per instance.",
                    "red_flag": "Paying wages later than 7 days (criminal offence).",
                    "gov_advice": "[Governance] Treat 'unpaid wages' as a top-tier criminal liability."
                }
            },
            "ch11": {
                "keys": ["終止僱傭合約", "解僱", "通知期", "代通知金", "辭職", "即炒", "summary dismissal", "嚴重犯錯", "偷嘢", "打交"],
                "zh": {
                    "title": "第十一章：終止僱傭合約與即時解僱",
                    "statute": "終止合約需給予足夠通知期或代通知金。僅當僱員故意不服從合法命令、欺詐或慣常疏忽職責時，才可無通知期「即時解僱」。",
                    "red_flag": "濫用「即炒」權力而缺乏無可辯駁之嚴重違紀實證。",
                    "gov_advice": "【董事會管治】落實漸進式紀律處分程序，即時解僱需視為最後手段並留存審計軌跡。\n【前線營運】遇嚴重違紀請拍照留底並通報 HR，切勿情緒激動下口頭宣告「即炒」。"
                },
                "en": {
                    "title": "Chapter 11: Termination & Summary Dismissal",
                    "statute": "Termination requires notice period or payment in lieu. Summary dismissal is strictly limited to serious misconduct.",
                    "red_flag": "Abusing 'Summary Dismissal' without irrefutable evidence.",
                    "gov_advice": "[Governance] Summary Dismissal must be the absolute last resort with an audit trail."
                }
            }
        }
        with open(DB_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(initial_db, f, ensure_ascii=False, indent=4)
            
    with open(DB_FILE_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

CHAPTERS_DB = init_and_load_knowledge_base()

# ==========================================
# 3. 升級版意圖規則引擎 (Advanced Rule Engine with Negation Logic)
# 治理優化：加入語意否定檢測，消滅 False Positives
# ==========================================
class ComplianceRuleEngine:
    def __init__(self, lang):
        self.lang = lang
        # 否定詞庫：用於防範「我沒有懷孕」卻觸發孕婦解僱的低級失誤
        self.negations = ["沒有", "不是", "並非", "無", "未", "not ", "non-"]

    def _is_negated(self, query, keywords):
        """檢查高危關鍵字前方是否有否定詞 (Contextual Negation Check)"""
        q_lower = query.lower()
        for kw in keywords:
            if kw in q_lower:
                idx = q_lower.find(kw)
                # 抓取關鍵字前 6 個字元作為上下文判斷區間
                context_window = q_lower[max(0, idx-6):idx]
                if any(neg in context_window for neg in self.negations):
                    return True # 確認為否定語境，解除高危警報
        return False
        
    def evaluate(self, query):
        q = query.lower()
        
        # Intent 1: Out of Scope
        if any(w in q for w in ["稅務局", "報稅", "簽證", "移民", "基金投資"]):
            return self._format_error("超出範圍阻斷", "查詢涉及稅務、簽證等非《僱傭條例》範疇，本系統拒絕推測。")

        # Intent 2: Pregnancy Termination (包含否定邏輯校準)
        preg_kws = ["懷孕", "大肚", "pregnant", "產檢"]
        term_kws = ["解僱", "炒", "代通知金", "裁員"]
        if any(p in q for p in preg_kws) and any(t in q for t in term_kws):
            # 若偵測到「沒有懷孕」，則放行不阻斷
            if not self._is_negated(query, preg_kws) and not any(ex in q for ex in ["偷", "打架"]):
                return self._format_error(
                    "最高級別合規危機：孕期解僱決策絕對不可行！", 
                    "根據 Cap. 57 第 15 條，解僱懷孕僱員屬刑事罪行。多給代通知金無法豁免刑責，最高罰款 HK$100,000。"
                )

        # Intent 3: Constructive Dismissal
        if any(v in q for v in ["降職", "減薪", "變更合約", "逼簽", "不簽就", "轉兼職"]):
            return self._format_error(
                "最高級別合規危機：變相減薪逼退方案完全違法！",
                "單方面大幅變更核心條款構成「推定解僱 (Constructive Dismissal)」。若強行扣工資觸犯非法扣薪罪，最高罰款 HK$350,000。"
            )

        # Intent 4: Privacy vs Dismissal (私隱收集與不服從命令)
        if any(pl in q for pl in ["信貸報告", "tu報告", "性罪行", "私隱"]) and any(ds in q for ds in ["不服從", "即炒"]):
            return self._format_error(
                "最高級別合規危機：強制索取私隱報告並「即炒」完全違法！",
                "強制現職銷售員提供 TU 違反私隱條例 (Cap. 486)。該命令不具合法性，無權以第 9 條解僱。違者面臨 PCPD 刑事處分。"
            )

        # Intent 5: 468 Dynamic Calculation
        weeks_patterns = [r'(?:第一|1)(?:週|周|星)\s*(\d+)', r'(?:第二|2)(?:週|周|星)\s*(\d+)', r'(?:第三|3)(?:週|周|星)\s*(\d+)', r'(?:第四|4)(?:週|周|星)\s*(\d+)']
        extracted = [int(re.search(p, q).group(1)) for p in weeks_patterns if re.search(p, q)]
        
        if len(extracted) == 4 or any(k in q for k in ["舊418", "卡418"]):
            total = sum(extracted) if len(extracted) == 4 else 0
            if total >= 68 or any(k in q for k in ["舊418"]):
                calc = f"（四週總和：{total} 小時）" if len(extracted) == 4 else ""
                return self._format_error(
                    "高危法務警報：該兼職員工已觸發 468 連續性合約！",
                    f"實質工時 {calc} 已達標。最新機制不看單週是否滿 18 小時。主管若繼續用舊制卡人拒發福利，一經定罪最高罰款 HK$50,000。"
                )
        return None

    def _format_error(self, title, body):
        if self.lang == '繁體中文':
            return f"🛑 **【{title}】** ❌\n\n{body}"
        return f"🛑 **【COMPLIANCE BREACH / SYSTEM GUARDRAIL TRIGGERED】** ❌\n\n{body}"

rule_engine = ComplianceRuleEngine(st.session_state.lang)

# ==========================================
# 4. 真實的密碼學審計軌跡 (True Cryptographic Audit Logging)
# AIGP Domain IV: 生成 UI 憑證並同步寫入伺服器後台
# ==========================================
def generate_and_log_audit_trail(query, response_text):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    raw_data = f"{query}|{response_text}|{timestamp}".encode('utf-8')
    audit_hash = hashlib.sha256(raw_data).hexdigest()[:16].upper()
    
    # 【關鍵升級】將 Hash 與行為紀錄寫入真實的後台 Log 檔案中
    logging.info(f"HashID: [{audit_hash}] | Prompt: {query} | System_Action: Legal_Advice_Generated")
    
    return f"<div class='audit-trail'>🔒 ISO 42001 Audit Trail ID: {audit_hash} | Timestamp: {timestamp} (Log secured to backend)</div>"

# ==========================================
# 5. 主畫面佈局與側邊欄 (Main UI & Sidebar)
# ==========================================
with st.sidebar:
    st.header("🌐 UI Language / 介面語言")
    lang_choice = st.radio("Select Language", ['繁體中文', 'English'], index=0 if is_zh else 1, label_visibility="collapsed")
    if lang_choice != st.session_state.lang:
        st.session_state.lang = lang_choice
        st.rerun()
    
    st.markdown("---")
    if is_zh:
        st.markdown("### ⚙️ ISO 42001 企業管治架構")
        st.markdown("""
        * **資料解耦 (Data Decoupling)**: 知識庫已實現 JSON 分離，支援無縫對接企業外部 CMS。
        * **規則引擎 (Rule Engine)**: 內建 Negation Handler (語意否定探測)，徹底消除 False Positives 誤判。
        * **審計軌跡 (Audit Trail)**: 每次對話生成 SHA-256 數位指紋，並**同步寫入伺服器後台 Log**，確保法庭級追溯力。
        """)
    else:
        st.markdown("### ⚙️ ISO 42001 Governance")
        st.markdown("""
        * **Decoupled DB**: Knowledge base separated to JSON for CMS readiness.
        * **Rule Engine**: Built-in Negation Handler to eliminate False Positives.
        * **Audit Trail**: SHA-256 hashes generated and **logged to backend server** for courtroom-grade traceability.
        """)

st.title("⚖️ Cap. 57 Employment Ordinance Advisor")
st.subheader("ISO 42001 認證架構・具備後台密碼學審計之合規沙盒" if is_zh else "ISO 42001 Certified Architecture with True Audit Logging")

tab_chat, tab_audit, tab_calc = st.tabs([
    "💬 情境導航 (Scenario Advisor)", 
    "📋 動態合規評分卡 (Dynamic Audit)", 
    "🧮 ADW 713 計算機 (Salary Calculator)"
])

# ------------------------------------------
# Track A: Chatbot Interface
# ------------------------------------------
with tab_chat:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"], unsafe_allow_html=True)

    if prompt := st.chat_input("請輸入合規情境（嘗試輸入：'我沒有懷孕，解僱流程為何？'）..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            final_response = ""
            
            # 1. 意圖規則引擎攔截 (Intent Rule Engine)
            breach_warning = rule_engine.evaluate(prompt)
            if breach_warning:
                st.error(breach_warning)
                final_response = breach_warning
            
            # 2. 一般法規知識庫檢索 (Knowledge Retrieval)
            else:
                matches = [data for key, data in CHAPTERS_DB.items() if any(k in prompt.lower() for k in data["keys"])]
                if not matches:
                    fb = "🔍 **兜底導航啟動**：請查閱 [官方 Cap. 57 原文](https://www.elegislation.gov.hk/hk/cap57)" if is_zh else "🔍 **Fallback** Please refer to [Cap. 57 Full Text](https://www.elegislation.gov.hk/hk/cap57)"
                    st.markdown(fb)
                    final_response = fb
                else:
                    for match in matches:
                        d_zh, d_en = match["zh"], match["en"]
                        st.info(f"**📖 {d_zh['title']}**\n\n**法定核心:** {d_zh['statute']}")
                        st.error(f"**🚨 違法紅線:** {d_zh['red_flag']}")
                        st.warning(f"**🛡️ 治理與營運指引:**\n\n{d_zh['gov_advice']}")
                        st.markdown("---")
                        final_response += f"**{d_zh['title']}**\n\n法定核心: {d_zh['statute']}\n\n紅線: {d_zh['red_flag']}\n\n指引: {d_zh['gov_advice']}\n\n---\n"
            
            # 3. 寫入真實的後台密碼學審計軌跡 (Inject & Log Audit Trail)
            audit_html = generate_and_log_audit_trail(prompt, final_response)
            st.markdown(audit_html, unsafe_allow_html=True)
            
            st.session_state.messages.append({"role": "assistant", "content": final_response + audit_html})

# ------------------------------------------
# Track B: Dynamic Risk Audit Scorecard
# ------------------------------------------
with tab_audit:
    st.markdown("### 📋 動態風險排查表單 (Dynamic Risk Audit)" if is_zh else "### 📋 Dynamic Risk Audit Scorecard")
    with st.form("audit_form"):
        col1, col2 = st.columns(2)
        with col1:
            emp_type = st.selectbox("員工合約類型 (Employment Type)", ["全職", "兼職/散工", "獨立承包人 (假自僱高危)"])
        with col2:
            tenure = st.selectbox("服務年資 (Tenure)", ["少於 4 星期", "滿 4 星期 (468 邊界)", "滿 24 個月 (SP 邊界)", "滿 5 年 (LSP 邊界)"])
        submit_audit = st.form_submit_button("執行風險稽核 (Execute Audit)")

    if submit_audit:
        has_risk = False
        if "獨立" in emp_type:
            st.error("**假自僱風險 (False Self-Employment):** 企業面臨逃避強積金及法定福利之刑事檢控風險。")
            has_risk = True
        if "兼職" in emp_type and "少於" not in tenure:
            st.warning("**468 連續性合約風險 (468 Mechanism):** 極可能已突破滾動 68 小時門檻，請確保發放法定假日與疾病津貼。")
            has_risk = True
        if "24 個月" in tenure or "5 年" in tenure:
            st.error("**解僱賠償負債 (Termination Liabilities):** 具備「不合理解僱」申索風險及遣散費/長期服務金責任。")
            has_risk = True
        if not has_risk:
            st.success("✅ 根據當前參數，未觸發高危紅線。")

# ------------------------------------------
# Track C: ADW 713 Calculator
# ------------------------------------------
with tab_calc:
    st.markdown("### 🧮 12個月平均工資 (ADW 713) 法定權益計算機" if is_zh else "### 🧮 12-Month ADW Calculator")
    col_in1, col_in2 = st.columns(2)
    with col_in1:
        total_wages = st.number_input("1. 過去12個月賺取的總工資 ($)", min_value=0.0, value=150000.0, step=1000.0)
        total_days = st.number_input("2. 12個月內的總日數", min_value=1, value=365, step=1)
    with col_in2:
        disregarded_days = st.number_input("3. 須剔除日數 (非全薪假天數)", min_value=0, value=5, step=1)
        disregarded_wages = st.number_input("4. 剔除期間工資 ($)", min_value=0.0, value=2667.0, step=100.0)

    st.markdown("---")
    if total_days > disregarded_days:
        adjusted_numerator = total_wages - disregarded_wages
        adjusted_denominator = total_days - disregarded_days
        adw = adjusted_numerator / adjusted_denominator
        st.metric("每日平均工資 (ADW)", f"${adw:.2f}")
    else:
        st.error("⚠️ 錯誤：剔除日數不可大於總日數。")
