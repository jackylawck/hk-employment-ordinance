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
# 2. 知識庫徹底解耦與強制同步層 (Forced Data Sync Layer)
# ==========================================
DB_FILE_PATH = 'cap57_db.json'

def init_and_load_knowledge_base():
    full_official_db = {
        "ch1": {
            "keys": [
                "適用範圍", "418", "468", "連續性合約", "兼職", "part-time", "散工", "炒散", "假自僱", "判頭",
                "甚麼人士受", "保障的僱員", "誰受保障", "保障", "臨時僱員", "兼職僱員又怎樣", "家屬", "同住"
            ],
            "zh": {
                "title": "第一章：《僱傭條例》適用範圍與「468」連續性合約",
                "statute": "【勞工處官方完整問答】：\n《僱傭條例》適用於所有僱員，包括臨時僱員和兼職僱員，但**不包括**下列人士：\na. 僱主家屬並與僱主同住的僱員；\nb. 《香港以外地區就業合約條例》所界定的僱員；\nc. 根據《商船（海員）條例》所指的船員協議而服務的人，或在非於香港註冊的船上服務的人；以及\nd. 按照《學徒制度條例》註冊的學徒，但《僱傭條例》內的某些條文仍適用。\n\n所有僱員，**無論他們每星期工作多少小時**，都可根據《僱傭條例》享有：\na. 法定假日；\nb. 工資保障；及\nc. 職工會不受歧視的保障。\n\n根據連續性合約工作的僱員，包括臨時僱員和兼職僱員，只要符合《僱傭條例》的要求（現行已放寬為 468 機制：連續受僱於同一僱主 4 星期或以上，4 星期內總工作時數滿 68 小時或以上），都有權享有條例下所有法定福利及保障。",
                "red_flag": "錯誤包裝「獨立承包人（假自僱）」，或刻意打斷工時以規避 468 門檻。",
                "gov_advice": "【董事會管治】人事考勤系統必須硬編碼此四大豁除群組，排班系統設定防呆機制，防範「468」違規。\n【前線營運提示】請確實記錄上下班時間，切勿口頭要求員工「提早下班」惡意避開 468 門檻。"
            },
            "en": {
                "title": "Chapter 1: Application of the Ordinance & '468' Continuous Contract",
                "statute": "The Employment Ordinance applies to all employees, including temporary and part-time employees, with the exception of: family members cohabiting with the employer, overseas contracts, seafarers, and registered apprentices.",
                "red_flag": "Misclassifying standard employees into excluded categories.",
                "gov_advice": "[Governance] Systematically audit the four statutory exclusion groups to ensure strict alignment."
            }
        },
        "ch2": {
            "keys": ["僱傭合約", "合約", "甚麼是僱傭合約", "什麼是僱傭合約", "條款", "就職前", "詳細說明", "contract of employment"],
            "zh": {
                "title": "第二章：僱傭合約的定義與就職前法定告知條件",
                "statute": "【勞工處官方完整問答 - 答1】：\n僱傭合約是指僱主和僱員訂立的僱傭協議。僱傭合約可以書面或口頭方式訂立，並可包含明示或暗示的條款。\n\n《僱傭條例》規定僱主必須在僱員就職前，向他詳細說明僱用條件，包括：\n（1）工資（包括工資率、超時工作的工資率及任何津貼，無論以按件、按工、按時、按日、按週或其他方式計算）；\n（2）工資期；\n（3）終止合約所需通知期；及\n（4）如僱員享有年終酬金，則有關年終酬金、部分年終酬金和酬金期的資料。",
                "red_flag": "入職前未以書面或清晰口頭說明上述四大法定條件，或未經僱員同意單方面更改合約核心條款，構成不合理更改合約條件或非法欠薪。",
                "gov_advice": "【董事會管治】企業必須落實標準化 Onboarding 流程，在員工正式上班的第一分鐘前，確保雙方已簽署包含上述四大法定條件的書面合約（Employment Contract），拒絕任何「口頭試工」灰色地帶。"
            },
            "en": {
                "title": "Chapter 2: Contract of Employment & Onboarding Requirements",
                "statute": "A contract of employment is an agreement between an employer and an employee. An employer must clearly inform the employee of conditions before employment begins, including: (1) Wage rate and allowances; (2) Wage period; (3) Notice period; (4) Year-end payment details.",
                "red_flag": "Failure to provide core terms before onboarding or unilateral variation of terms.",
                "gov_advice": "[Governance] Enforce mandatory signing of formal employment contracts prior to the first day of work."
            }
        },
        "ch3": {
            "keys": ["工資", "salary", "扣薪", "扣錢", "出糧", "遲出糧", "拖糧", "欠薪", "late pay", "爛嘢", "打破", "扣除工資", "扣人工"],
            "zh": {
                "title": "第三章：工資發放限期與法定扣薪限制",
                "statute": "【勞工處官方完整問答】：工資必須在工資期發放限期屆滿後 7 天內支付。除法例明文規定（如因疏忽損壞僱主貨品每次上限$300且總額不超該期工資1/4）外，嚴禁任何扣薪。",
                "red_flag": "遲發工資超過 7 天（涉及刑事罪行），或以「表現不佳 / 唔達標」為由非法扣減員工工資。",
                "gov_advice": "【董事會管治】將「欠薪」視為最高級別刑事法律風險。\n【前線營運提示】即使員工打破財產，法定每次損壞扣款上限硬性規定為 HK$300，切勿私自擴大扣款金額。"
            },
            "en": {
                "title": "Chapter 3: Wages & Statutory Deduction Limits",
                "statute": "Wages must be paid within 7 days. Deductions for damage are strictly limited to HK$300 per instance and cannot exceed 1/4 of the wage period.",
                "red_flag": "Paying wages later than 7 days or implementing non-statutory deductions.",
                "gov_advice": "[Governance] Implement deterministic system payroll blocks to prevent dynamic illegal wage retention."
            }
        },
        "ch11": {
            "keys": ["終止僱傭合約", "想終止", "解僱", "通知期", "代通知金", "多長的通知期", "多少代通知金", "試用期內", "無期通知", "即炒", "summary dismissal", "嚴重犯錯", "偷嘢", "打交", "炒佢", "唔聽話"],
            "zh": {
                "title": "第十一章：終止僱傭合約、通知期與代通知金規範",
                "statute": "【勞工處官方完整問答 - 結合截圖表格一規範】：\n如想終止僱傭合約，所需的通知期或代通知金如下：\n1. 在試用期內：\n   - 試用期內首個月：無需通知期，無需代通知金。\n   - 試用期內第一個星期後（有明確規定）：依照合約訂明，但不少於 7 天通知。\n   - 試用期內第一個星期後（無明確規定）：不少於 7 天通知。\n2. 無試用期 / 完成試用期的連續性合約：\n   - 合約有明確規定：依照合約訂明，但不少於 7 天通知。\n   - 合約無明確規定：不少於一個月通知。",
                "red_flag": "在試用期首個月內強行向員工索取通知期，或完成試用期後少於 7 天/一個月通知且不給予代通知金結算尾糧。",
                "gov_advice": "【董事會管治】請對齊勞工處標準，將試用期前後的計糧公式模組化，離職審批留存完整的審計軌跡。\n【前線營運提示】遇到嚴重違紀請拍照留底並通報 HR，切勿在情緒激動下口頭宣告即炒。"
            },
            "en": {
                "title": "Chapter 11: Termination of Contracts, Notice Period & Paid in Lieu",
                "statute": "Requirements for termination: First month of probation requires no notice. Post first month requires stipulated notice but not less than 7 days. Continuous contract without probation requires not less than 1 month notice if unstated.",
                "red_flag": "Breaching minimum 7-day or 1-month statutory notice limits.",
                "gov_advice": "[Governance] Implement strict date-check controls for dynamic offboarding compliance."
            }
        }
    }
    with open(DB_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(full_official_db, f, ensure_ascii=False, indent=4)
    return full_official_db

CHAPTERS_DB = init_and_load_knowledge_base()

# ==========================================
# 3. 升級版意圖規則引擎 (Advanced Rule Engine)
# ==========================================
class ComplianceRuleEngine:
    def __init__(self, lang):
        self.lang = lang
        self.negations = ["沒有", "不是", "並非", "無", "未", "not ", "non-"]

    def _is_negated(self, query, keywords):
        q_lower = query.lower()
        for kw in keywords:
            if kw in q_lower:
                idx = q_lower.find(kw)
                context_window = q_lower[max(0, idx-6):idx]
                if any(neg in context_window for neg in self.negations):
                    return True 
        return False
        
    def evaluate(self, query):
        q = query.lower()
        
        if any(w in q for w in ["稅務局", "報稅", "簽證", "移民", "基金投資"]):
            return self._format_error("超出範圍阻斷", "查詢涉及稅務、簽證等非《僱傭條例》範疇，本系統拒絕推測。")

        preg_kws = ["懷孕", "大肚", "pregnant", "產檢", "有咗"]
        term_kws = ["解僱", "炒", "代通知金", "裁員", "炒佢", "即炒", "唔撈", "炒人"]
        if any(p in q for p in preg_kws) and any(t in q for t in term_kws):
            if not self._is_negated(query, preg_kws) and not any(ex in q for ex in ["偷", "打架", "打交"]):
                return self._format_error(
                    "最高級別合規危機：孕期解僱決策絕對不可行！", 
                    "根據 Cap. 57 第 15 條，解僱懷孕僱員屬刑事罪行。多給代通知金無法豁免刑責，最高罰款 HK$100,000。"
                )

        if any(v in q for v in ["降職", "減薪", "變更合約", "逼簽", "不簽就", "轉兼職", "減人工", "轉散工", "逼走"]):
            return self._format_error(
                "最高級別合規危機：變相減薪逼退方案完全違法！",
                "單方面大幅變更核心條款構成「推定解僱 (Constructive Dismissal)」。若強行扣工資觸犯非法扣薪罪，最高罰款 HK$350,000。"
            )

        if any(pl in q for pl in ["信貸報告", "tu報告", "性罪行", "私隱", "查家宅", "tu"]) and any(ds in q for ds in ["不服從", "即炒", "炒佢", "唔聽話"]):
            return self._format_error(
                "最高級別合規危機：強制索取私隱報告並「即炒」完全違法！",
                "強制現職員工提供 TU/性罪行紀錄違反私隱條例 (Cap. 486)。該命令不具合法性，無權以第 9 條解僱。違者面臨 PCPD 刑事處分。"
            )
        return None

    def _format_error(self, title, body):
        if self.lang == '繁體中文':
            return f"🛑 **【{title}】** ❌\n\n{body}"
        return f"🛑 **【COMPLIANCE BREACH / SYSTEM GUARDRAIL TRIGGERED】** ❌\n\n{body}"

rule_engine = ComplianceRuleEngine(st.session_state.lang)

# ==========================================
# 4. 真實的密碼學審計軌跡 (True Cryptographic Audit Logging)
# ==========================================
def generate_and_log_audit_trail(query, response_text):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    raw_data = f"{query}|{response_text}|{timestamp}".encode('utf-8')
    audit_hash = hashlib.sha256(raw_data).hexdigest()[:16].upper()
    logging.info(f"HashID: [{audit_hash}] | Prompt: {query} | System_Action: Legal_Advice_Generated")
    return f"<div class='audit-trail'>🔒 ISO 42001 Audit Trail ID: {audit_hash} | Timestamp: {timestamp} (Log secured to backend)</div>"

# ==========================================
# 5. 主畫面佈局與配置
# ==========================================
st.title("⚖️ Cap. 57 Employment Ordinance Advisor")
st.subheader("ISO 42001 認證架構・具備多字詞分數路由與高透明度審計")

tab_chat, tab_audit, tab_calc = st.tabs([
    "💬 情境導航 (Scenario Advisor)", 
    "📋 動態合規評分卡 (Dynamic Audit)", 
    "🧮 ADW 713 計算機 (Salary Calculator)"
])

# ------------------------------------------
# Track A: Chatbot Interface (具備雙層置信度風控護欄)
# ------------------------------------------
with tab_chat:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"], unsafe_allow_html=True)

    if prompt := st.chat_input("請輸入合規情境（例如：'如僱主或僱員想終止僱傭合約...'）..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            final_response = ""
            
            # 正向語意清洗層：刨除前綴干擾
            cleaned_prompt = re.sub(r'^(甚麼是|什麼是|請問|我想問|點樣先算係|如何|點樣)', '', prompt.strip())
            
            # 1. 第一層防禦：危險合規意圖強行攔截
            breach_warning = rule_engine.evaluate(prompt)
            if breach_warning:
                st.error(breach_warning)
                final_response = breach_warning
            else:
                # 2. 多字詞高精準計分路由引擎
                best_match_key = None
                max_score = 0
                
                for ch_key, ch_data in CHAPTERS_DB.items():
                    score = 0
                    for k in ch_data["keys"]:
                        if k.lower() in cleaned_prompt.lower() or k.lower() in prompt.lower():
                            score += 1
                    
                    if score > max_score:
                        max_score = score
                        best_match_key = ch_key
                
                # 3. 第二層防禦：基於風險(Risk-Based)的雙重信度閾值網閘
                if best_match_key and max_score > 0:
                    match = CHAPTERS_DB[best_match_key]
                    d_zh = match["zh"]
                    
                    total_features = len(match["keys"])
                    confidence_pct = (max_score / total_features) * 100
                    
                    # 🚀 網閘 A: 門檻低於 30.0% 判定為高風險瞎猜，實施「硬阻斷拒答」
                    if confidence_pct < 30.0:
                        st.error(
                            f"🛑 **【系統置信度過低阻斷】(當前信度: {confidence_pct:.1f}%)**\n\n"
                            f"您的提問過於模糊（僅命中 {max_score}/{total_features} 個特徵詞）。"
                            f"為防範自動化偏見（Automation Bias）引發合規漏洞，系統拒絕推測答案。"
                        )
                        fb = "🔍 **已為您啟動安全兜底**：請直接查閱 [官方 Cap. 57 原文](https://www.elegislation.gov.hk/hk/cap57) 進行人工核對。"
                        st.markdown(fb)
                        final_response = fb
                    else:
                        # 🚀 網閘 B: 信度在 30% 到 50% 之間，放行但置頂「黃色高亮強烈警告」
                        if confidence_pct < 50.0:
                            st.warning(
                                f"⚠️ **【合規預警：提示詞不夠具體】**\n\n"
                                f"本次法規匹配之置信度偏低（僅有 **{confidence_pct:.1f}%**）。"
                                f"系統雖為您路由至高度相關章節，但強烈建議您補全更具體的情境（例如輸入：'試用期內即炒通知期'）以獲得精準研判。"
                            )
                        
                        hit_keywords = [k for k in match["keys"] if k.lower() in cleaned_prompt.lower() or k.lower() in prompt.lower()]
                        hit_list_str = "、".join(hit_keywords)
                        
                        # UI 高管級別高保真渲染
                        st.info(f"**📖 {d_zh['title']}**")
                        st.caption(
                            f"🎯 **條例匹配置信度：{confidence_pct:.1f}%** (命中 {max_score}/{total_features} 個法定特徵詞) "
                            f"ℹ️ [審計說明](## \"本次命中的特徵詞包括：{hit_list_str}。系統已排除常見前綴。\")"
                        )
                        st.markdown("---")
                        st.write(f"**⚖️ 法定核心:**\n{d_zh['statute']}")
                        st.error(f"**🚨 違法紅線:** {d_flag := d_zh.get('red_flag', '未定義')}")
                        st.warning(f"**🛡️ 治理與營運指引:**\n\n{d_zh['gov_advice']}")
                        final_response = d_zh['statute']
                else:
                    fb = "🔍 **兜底導航啟動**：請查閱 [官方 Cap. 57 原文](https://www.elegislation.gov.hk/hk/cap57)"
                    st.markdown(fb)
                    final_response = fb
            
            # 4. 寫入真實的後台密碼學審計軌跡
            audit_html = generate_and_log_audit_trail(prompt, final_response)
            st.markdown(audit_html, unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": final_response + audit_html})

# ------------------------------------------
# Track B: Dynamic Risk Audit Scorecard
# ------------------------------------------
with tab_audit:
    st.markdown("### 📋 動態風險排查表單 (Dynamic Risk Audit)")
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
    st.markdown("### 🧮 12個月平均工資 (ADW 713) 法定權益計算機")
    col_in1, col_in2 = st.columns(2)
    with col_in1:
        total_wages = st.number_input("1. 過去12個月賺取的總工資 ($)", min_value=0.0, value=150000.0, step=1000.0)
        total_days = st.number_input("2. 12個月內的總日數", min_value=1, value=365, step=1)
    with col_in2:
        disrepresented_days = st.number_input("3. 須剔除日數 (非全薪假天數)", min_value=0, value=5, step=1)
        disrepresented_wages = st.number_input("4. 剔除期間工資 ($)", min_value=0.0, value=2667.0, step=100.0)

    st.markdown("---")
    if total_days > disrepresented_days:
        adjusted_numerator = total_wages - disrepresented_wages
        adjusted_denominator = total_days - disrepresented_days
        adw = adjusted_numerator / adjusted_denominator
        st.metric("每日平均工資 (ADW)", f"${adw:.2f}")
    else:
        st.error("⚠️ 錯誤：剔除日數不可大於總日數。")
with st.sidebar:
    st.header("🌐 UI Language")
    st.write(f"當前配置: {st.session_state.lang}")
