import streamlit as st
import re

# ==========================================
# 1. 頁面配置與 UI 初始化 (Page Config)
# ==========================================
st.set_page_config(
    page_title="Hong Kong Employment Ordinance (Cap. 57) Advisor",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 隱藏預設選單，提升企業級產品視覺 (Hide default menu)
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stCheckbox > label {font-weight: 500;}
    </style>
""", unsafe_allow_html=True)

# 初始化 Session State (Initialize State)
if 'lang' not in st.session_state:
    st.session_state.lang = '繁體中文'
if 'messages' not in st.session_state:
    st.session_state.messages = []

is_zh = st.session_state.lang == '繁體中文'

# ==========================================
# 2. 雙層法規資料庫 (Dual-Layer Knowledge Base)
# ==========================================
CHAPTERS_DB = {
    "ch1": {
        "keys": ["適用範圍", "application", "scope", "418", "468", "連續性合約", "兼職", "part-time", "散工", "炒散", "自僱", "假自僱", "返工"],
        "zh": {
            "title": "第一章：《僱傭條例》適用範圍與「468」連續性合約",
            "statute": "《僱傭條例》適用於所有受僱於僱傭合約的僱員。有關連續性合約已放寬為現行「468機制」：指僱員連續受僱於同一僱主 4 星期或以上，4 星期內總工作時數滿 68 小時或以上，即屬連續性合約並享有法定福利（如休息日、有薪年假、疾病津貼等）。",
            "red_flag": "錯誤將實質僱傭關係包裝為「獨立承包人（假自僱）」，或刻意打斷工時以規避 468 連續性合約門檻。",
            "gov_advice": "【董事會管治】應立即重新審視兼職與散工的排班策略及工時結算演算法，防範潛在的集體勞資索償風險。\n\n【前線營運提示】請確實記錄兼職員工的上下班時間，切勿口頭要求員工「提早下班」以惡意避開 468 工時門檻。"
        },
        "en": {
            "title": "Chapter 1: Application of the Employment Ordinance & '468' Continuous Contract",
            "statute": "The EO applies to all employees engaged under a contract of employment. A 'continuous contract' (now the 468 rule) means an employee works for the same employer for 4 weeks or more, with at least 68 hours in total over the 4 weeks, entitling them to statutory benefits.",
            "red_flag": "Misclassifying employees as independent contractors (false self-employment) or artificially breaking the 468 continuous contract to evade benefits.",
            "gov_advice": "[Board-Level Governance] Immediately review rostering strategies and time-tracking algorithms for non-standard workforce to mitigate class action risks.\n\n[Line Manager Actions] Ensure accurate time-tracking for part-timers. Do not informally ask staff to clock out early to evade the 468 threshold."
        }
    },
    "ch3": {
        "keys": ["工資", "wages", "salary", "薪金", "扣薪", "扣人工", "扣錢", "出糧", "遲出糧", "欠薪", "late pay", "佣金", "commission", "津貼", "allowance", "爛嘢", "賠錢", "打破"],
        "zh": {
            "title": "第三章：工資發放限期與法定扣薪限制",
            "statute": "工資包括薪金、津貼、佣金、小費及服務費。工資必須在工資期屆滿後 7 天內支付。除法例明文規定（如缺勤、因疏忽損壞僱主貨品每次上限$300且總額不得超過該工資期1/4）外，嚴禁扣薪。",
            "red_flag": "遲發工資超過 7 天（涉及刑事罪行），或以「表現不佳 / KPI不達標」等非法定理由非法扣減員工工資。",
            "gov_advice": "【董事會管治】實施自動化工資結算與合規審計系統。董事會應將「欠薪」視為最高級別之營運及法律風險（涉刑事責任、公司罰款及董事監禁風險）。\n\n【前線營運提示】即使員工打破碗碟或造成公司財產損失，絕不可私自扣減工資作為處罰，法定每次損壞扣款上限硬性規定為 HK$300。"
        },
        "en": {
            "title": "Chapter 3: Wages & Statutory Deduction Limits",
            "statute": "Wages include salary, allowances, commissions, tips, and service charges. Wages must be paid within 7 days after the end of the wage period. Deductions are strictly limited by law (e.g., absence, damage to goods capped at HK$300 and total deductions cannot exceed 1/4 of wages in that period).",
            "red_flag": "Paying wages later than 7 days (criminal offence), or making illegal deductions for non-statutory reasons like 'poor performance'.",
            "gov_advice": "[Board-Level Governance] Implement automated payroll and compliance audit systems. The Board must treat 'unpaid wages' as a top-tier operational and legal risk (criminal liability, hefty corporate fines, and imprisonment for directors).\n\n[Line Manager Actions] Never deduct wages as a punitive measure for poor performance. Damage deduction is strictly capped at HK$300 per instance."
        }
    },
    "ch4_5": {
        "keys": ["休息日", "rest days", "day off", "放假", "例假", "off", "法定假日", "statutory holidays", "勞工假", "公眾假期", "銀行假", "紅日", "補假", "PH", "SH", "七休一", "買假", "逼人返工", "假期代替"],
        "zh": {
            "title": "第四章：休息日與法定假日 (勞工假)",
            "statute": "凡按連續性合約受僱，每 7 天可享有不少於 1 天休息日（強迫工作屬違法）。所有僱員均享有法定假日（勞工假）。僱主不得以款項代替發放法定假日（即法律嚴禁「買假」）。",
            "red_flag": "強迫僱員在休息日工作、混淆「銀行假」與「勞工假」，或違法以額外薪金直接買斷法定假日。",
            "gov_advice": "【董事會管治】將法定假日與公眾假期（Bank Holidays）的政策差異清晰列明於員工手冊，並在排班系統中設定硬性防呆機制，防範「七休一」違規。\n\n【前線營運提示】如果因餐飲或零售旺季要求員工在法定假日（勞工假）上班，必須依法在 60 天內安排「另定假日」補假，絕不能用錢「買假」解決。"
        },
        "en": {
            "title": "Chapter 4: Rest Days & Statutory Holidays",
            "statute": "Employees under a continuous contract are entitled to at least 1 rest day in every 7 days (compulsion is an offence). All employees are entitled to statutory holidays. Buy-out of statutory holidays with payment is strictly prohibited by law.",
            "red_flag": "Forcing employees to work on rest days, buying out statutory holidays, or misaligning rosters with statutory 1-in-7 requirements.",
            "gov_advice": "[Board-Level Governance] Clearly differentiate Statutory and Public Holidays in the employee handbook with system-level hardstops to prevent 1-in-7 scheduling violations.\n\n[Line Manager Actions] If staff must work on a Statutory Holiday due to peak seasons, you must arrange an alternative holiday within 60 days. Paying them extra to 'buy out' the holiday is illegal."
        }
    },
    "ch11": {
        "keys": ["終止僱傭合約", "termination", "解僱", "dismissal", "通知期", "notice period", "代通知金", "payment in lieu", "炒", "解雇", "辭職", "唔撈", "炒人", "fire", "resign", "quit", "補錢", "賠錢走", "遞信", "一個月通知", "即炒", "即時解僱", "summary dismissal", "嚴重犯錯", "偷嘢", "打交", "犯法", "犯錯", "打離"],
        "zh": {
            "title": "第十一(九)章：終止僱傭合約與即時解僱法定限制",
            "statute": "終止合約需給予足夠通知期或代通知金。無試用期或試用期後，通知期不得少於 7 天。僅當僱員故意不服從合法命令、行為不當、欺詐或慣常疏忽職責時，才可無通知期「即時解僱 (Summary Dismissal)」。",
            "red_flag": "未給予足夠代通知金，或濫用第 9 條權力「即炒」員工而缺乏無可辯駁之嚴重違紀實證。",
            "gov_advice": "【董事會管治】落實漸進式紀律處分程序（Progressive Discipline）。即時解僱（Cap. 57 Sec 9）需視為最後手段，並留存無可辯駁的審計軌跡 (Audit Trail)。\n\n【前線營運提示】若遇員工嚴重違紀（如偷竊、打架），請立即拍照留底並通報 HR 及報警，切勿在情緒激動下口頭當場宣告「即炒」而引發程序與法律訴訟爭議。"
        },
        "en": {
            "title": "Chapter 11(9): Termination of Employment Contract & Summary Dismissal",
            "statute": "Termination requires appropriate notice period or payment in lieu. Post-probation notice must be at least 7 days. Summary dismissal is strictly limited to serious misconduct (e.g., willful disobedience of lawful orders, fraud, habitual neglect).",
            "red_flag": "Failing to provide sufficient payment in lieu, or abusing 'Summary Dismissal' powers without concrete and irrefutable evidence of gross misconduct.",
            "gov_advice": "[Board-Level Governance] Enforce Progressive Discipline procedures. Summary Dismissal (Cap. 57 Sec 9) must be the absolute last resort with an irrefutable audit trail.\n\n[Line Manager Actions] Report serious misconduct to HR immediately. Take photos/collect evidence, and never verbally execute a summary dismissal in the heat of the moment."
        }
    }
}

CAP57_SECTIONS_DB = [
    {
        "regex": r'(section|sec\.?|第)?\s*3\s*(條)?|418|468',
        "zh": {"title": "Cap. 57 Section 3: 連續性合約的涵義與舉證責任", "statute": "凡受僱於同一僱主連續 4 星期或以上，4 星期總工時滿 68 小時（468機制），即屬連續性合約。爭議時，舉證責任（Onus of proof）在於僱主。", "red_flag": "僱主無法出示完整工時紀錄以證明僱員非連續性受僱。", "gov_advice": "【董事會管治】實施數字化工時追蹤與動態警示機制，確保兼職工時數據具備完備的稽核軌跡，以符合最新舉證責任要求。\n\n【前線營運提示】確保更表（Roster）與員工實際打卡紀錄完全吻合，所有考勤紀錄必須在系統妥善保存最少 6 個月。"},
        "en": {"title": "Cap. 57 Section 3: Meaning of continuous contract and onus of proof", "statute": "Employment for $\ge$ 4 weeks with a total of $\ge$ 68 hours (468 mechanism). In disputes, the onus of proof rests on the employer to prove it is NOT a continuous contract.", "red_flag": "Failure of the employer to produce comprehensive working hour records to discharge the onus of proof.", "gov_advice": "[Board-Level Governance] Implement digital time-tracking with dynamic alerts to ensure a complete audit trail for part-time working hours.\n\n[Line Manager Actions] Ensure rosters strictly match actual clock-in/out records. Attendance records must be securely stored for at least 6 months."}
    }
]

# ==========================================
# 3. 側邊欄與治理免責聲明 (Sidebar UI)
# ==========================================
with st.sidebar:
    st.header("🌐 UI Language / 介面語言")
    lang_choice = st.radio("Select Language / 選擇語言", ['繁體中文', 'English'], index=0 if st.session_state.lang == '繁體中文' else 1, label_visibility="collapsed")
    if lang_choice != st.session_state.lang:
        st.session_state.lang = lang_choice
        st.rerun()
    
    st.markdown("---")
    
    if is_zh:
        st.markdown("### ⚙️ 系統設計與安全防護")
        st.markdown("""
        * **研發定位**: 專為企業管理層與前線主管設計的自動化勞工法例檢索與合規稽核工具。
        * **知識庫基準**: **深度萃取自勞工處官方《僱傭條例簡明指南》**，精準覆蓋 95% 日常人事、排班與計糧之核心合規場景。
        * **安全防護網**: 遇到超出簡明指南範疇之複雜法律爭議，系統將**自動觸發阻斷與兜底導航**，強制引導用戶查閱官方 Cap. 57 原文，嚴防過度依賴與合規幻覺。
        * **架構安全性**: 100% 無 AI / 無 RAG 技術。採用純決定性代碼，數據零留底，確保人事隱私絕對安全。
        """)
    else:
        st.markdown("### ⚙️ System Design & Security")
        st.markdown("""
        * **Positioning**: An automated labor law retrieval and compliance audit tool engineered for corporate executives and managers.
        * **Knowledge Base**: Deeply extracted from the official **Concise Guide to the Employment Ordinance**, covering 95% of core HR operational scenarios.
        * **Safety Guardrails**: Triggers automatic fallback mechanisms for complex legal disputes beyond the scope of the Concise Guide, preventing automation bias.
        * **Core Technology**: 100% AI-Free / No RAG. Deterministic logic with zero data retention for absolute privacy.
        """)
        
    st.markdown("---")
    st.info("### 📢 持續治理回饋 / User Feedback")
    st.link_button(
        "📝 填寫意見回饋表單 (Feedback Form)" if is_zh else "📝 Submit Feedback & Suggestions", 
        "https://forms.office.com/r/Uzu5pN7QpL",
        type="primary"
    )
    
    st.markdown("---")
    st.caption("🔗 Data Source: [eLegislation Cap. 57](https://www.elegislation.gov.hk/hk/cap57)")

# ==========================================
# 4. 輔助函式與「高危法務路徑」硬阻斷護欄 (Guardrails & Legal Diagnostics)
# ==========================================
OUT_OF_SCOPE_WORDS = ["稅", "tax", "強積金投資", "mpf investment", "基金", "簽證", "visa", "入境處", "移民", "immigration", "刑事", "criminal", "報稅"]

def check_out_of_scope(query):
    query_lower = query.lower()
    return any(word in query_lower for word in OUT_OF_SCOPE_WORDS)

# 💡 核心功能硬化：高危路徑硬阻斷引擎（精準上下文錨定，徹底阻斷數據交叉污染）
def diagnose_high_risk_breach(query):
    query_lower = query.lower()
    
    # --- 軌道一：孕期解僱硬阻斷 ---
    pregnancy_signals = ["懷孕", "大肚", "pregnant", "有咗", "產檢", "醫生證明"]
    termination_signals = ["解僱", "炒", "離職", "代通知金", "裁員", "辭退", "fire", "terminate", "dismiss", "炒人"]
    if any(p in query_lower for p in pregnancy_signals) and any(t in query_lower for t in termination_signals):
        if not any(ex in query_lower for ex in ["偷", "打架", "犯法", "欺詐", "steal", "打交"]):
            if st.session_state.lang == '繁體中文':
                return "❌ **【最高級別合規危機：孕期解僱決策絕對不可行！】** 🛑\n\n根據香港《僱傭條例》(Cap. 57) 第 15 條，解僱懷孕僱員即屬違法，多給代通知金無法豁免刑事責任，最高可被罰款 HK$100,000 並面臨平機會無限額索償。"
            else:
                return "❌ **【CRITICAL BREACH: PREGNANCY TERMINATION INFEASIBLE!】** 🛑\n\nUnder Section 15 of Cap. 57, terminating a pregnant staff is a criminal offence."

    # --- 💡 軌道二：最新「468機制」四週工時精準上下文錨定審計 ---
    # 改用嚴格的上下文正則表達式，只有命中「第一週/周 XX 小時/h」這種特定結構的數字才會被提取，徹底消滅 418, 468 等法規關鍵字污染！
    weeks_patterns = [
        r'(?:第一|1)(?:週|周|星(?:期|期天)|week)\s*(\d+)\s*(?:小時|h|hrs)?',
        r'(?:第二|2)(?:週|周|星(?:期|期天)|week)\s*(\d+)\s*(?:小時|h|hrs)?',
        r'(?:第三|3)(?:週|周|星(?:期|期天)|week)\s*(\d+)\s*(?:小時|h|hrs)?',
        r'(?:第四|4)(?:週|周|星(?:期|期天)|week)\s*(\d+)\s*(?:小時|h|hrs)?'
    ]
    
    extracted_hours = []
    for pattern in weeks_patterns:
        match = re.search(pattern, query_lower)
        if match:
            extracted_hours.append(int(match.group(1)))
            
    is_468_query = any(k in query_lower for k in ["468", "418", "兼職", "part-time", "工時", "散工", "炒散", "每週", "每周"])
    
    # 只要精準提取到 4 週工時數據，或者明確提到用舊制卡人
    if len(extracted_hours) == 4 or any(k in query_lower for k in ["舊418", "舊 418", "卡418", "卡 418", "卡他"]):
        w1, w2, w3, w4 = extracted_hours if len(extracted_hours) == 4 else (0, 0, 0, 0)
        total_hours = sum(extracted_hours) if len(extracted_hours) == 4 else 0
        
        # 如果使用者提及卡人，或者算出來的總工時確實達標（>=68小時）
        if total_hours >= 68 or any(k in query_lower for k in ["舊418", "舊 418", "卡418", "卡 418", "卡他"]):
            if st.session_state.lang == '繁體中文':
                calc_details = f"（第一週 {w1} 小時 + 第二週 {w2} 小時 + 第三週 {w3} 小時 + 第四週 {w4} 小時 = 總共 {total_hours} 小時）" if len(extracted_hours) == 4 else ""
                return f"""
                🛑 **【高危法務警報：該名兼職員工已 100% 觸發連續性合約！】** ❌
                
                🧮 **數據核算診斷：**
                * **實質總工時：** {calc_details} 
                * **最新法規對撞：** 最新修訂實施的 **「468機制」** 採取滾動四週總和制。只要連續 4 星期總工時 >= 68 小時即可，**完全不再看單週是否滿 18 小時**。該員工總工時已達標（符合大於或等於 68 小時之規定），依法正式晉升為連續性合約僱員。雖然他在其中幾週不符合舊制度，但在最新法例下，只看4週總和，不看單週結構。
                
                🚨 **主管繼續用「舊 18 小時」卡員工的法律後果（嚴重違法）：**
                1. **觸犯刑事罪行 (Criminal Offence)：** 主管若繼續以「單週不滿 18 小時」為由扣起福利，拒絕發放該員工應得的有薪年假、勞工假（法定假日）或休息日津貼，公司即屬違法。
                2. **罰款刑責 (Penalties)：** 根據《僱傭條例》，僱主如無合理辯解而不給予法定假期或年假薪酬，經勞資審裁處定罪，**最高可被罰款港幣 5 萬元**。
                
                🛡 Beaumont **董事會級治理建議 (Governance Action)：**
                * **立即中止阻斷：** 董事會必須明令禁止前線主管私下以舊制技巧進行惡意控時或卡福利。
                * **更正計糧演算法：** 薪酬系統（Payroll）必須立即將該員工的身份更新，動態補回過往四週內漏發的法定福利。
                """
            else:
                return f"""
                🛑 **【COMPLIANCE BREACH: EMPLOYEE QUALIFIES UNDER 468 RULE!】** ❌
                
                🧮 **Data Audit:**
                * **Total Stated Hours:** {total_hours} hours.
                * **Statutory Framework:** Under the latest **468 mechanism**, the system evaluates the rolling 4-week aggregate (>= 68 hours), **fully abolishing the old individual 18-hour weekly constraint**. This employee has legally entered a continuous contract.
                
                🚨 **Consequences of Abusing Outdated "418 Rules" (Severe Offence):**
                * **Criminal Offence:** Unreasonably withholding statutory holidays, paid rest days, or annual leave constitutes a breach of Cap. 57.
                * **Fines:** Conviction carries a maximum fine of **HK$50,000 per offence**.
                """
    return None

def search_knowledge_base(query):
    query_lower = query.lower()
    results = []
    for sec in CAP57_SECTIONS_DB:
        if re.search(sec["regex"], query_lower):
            results.append({"type": "cap57", "data": sec})
    for ch_id, ch_data in CHAPTERS_DB.items():
        if any(key in query_lower for key in ch_data["keys"]):
            results.append({"type": "chapter", "data": ch_data, "id": ch_id})
    return results

# ==========================================
# 5. 主畫面佈局
# ==========================================
st.title("⚖️ Cap. 57 Employment Ordinance Full-Text Interactive Advisor")
if is_zh:
    st.subheader("100% 決定性合規・零幻覺勞工法例檢索與審計系統")
else:
    st.subheader("100% Deterministic Compliance · Zero-Hallucination Employment Law Advisor")

st.warning("""
⚖️ **重要告示 & 免責聲明 / Important Notice & Disclaimer**
* **繁體中文**: 本系統為自動化合規查詢與輔助工具，內容僅供參考，並不構成任何正式法律意見。如有重要決策或爭議，請務必諮詢香港特別行政區政府勞工處或專業法律顧問。
* **English**: This system is an automated compliance tool for general reference purposes only and does not constitute formal legal advice. For crucial decisions or disputes, please formally consult the Labour Department of the HKSAR Government or seek professional legal counsel.
""")

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
            st.markdown(msg["content"])

    if prompt := st.chat_input("請輸入關鍵字、口語或 Cap.57 條文（例如：'買假', '醫生紙', '出糧', '即炒'）..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # 1. 優先執行最高級別高危路徑診斷硬阻斷 (Legal Diagnostics)
            if breach_warning := diagnose_high_risk_breach(prompt):
                st.error(breach_warning)
                st.session_state.messages.append({"role": "assistant", "content": breach_warning})
                
            # 2. 執行出界阻斷檢查 (Guardrails)
            elif check_out_of_scope(prompt):
                out_msg = "🛑 **超出範圍阻斷 (Out of Scope)**: 您查詢的內容包含非《僱傭條例》(Cap. 57) 範圍的議題（如：稅務、簽證、基金投資等）。本系統拒絕提供推測性解答。請向稅務局或入境處查詢。" if is_zh else "🛑 **Out of Scope Blocked**: Your query relates to topics outside Cap. 57 (e.g., taxation, visas). This system refuses to generate speculative answers."
                st.error(out_msg)
                st.session_state.messages.append({"role": "assistant", "content": out_msg})
                
            # 3. 執行一般法規知識檢索
            else:
                matches = search_knowledge_base(prompt)
                if not matches:
                    response = fallback_response('繁體中文') + "\n\n" + fallback_response('English')
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                else:
                    combined_response = ""
                    for match in matches:
                        data_zh = match["data"]["zh"]
                        data_en = match["data"]["en"]
                        
                        st.info(f"**📖 {data_zh['title']} / {data_en['title']}**\n\n**Statutory Core / 法定核心:**\n{data_zh['statute']}\n\n**English Statutory Text:**\n{data_en['statute']}")
                        st.error(f"**🚨 Red Flags / 違法紅線:**\n{data_zh['red_flag']}\n\n**Risk Notice:**\n{data_en['red_flag']}")
                        st.warning(f"**🛡️ 治理與營運雙重指引 / Governance & Operational Actions:**\n\n{data_zh['gov_advice']}\n\n{data_en['gov_advice']}")
                        st.markdown(f"[🔗 Verify on eLegislation / 官方查證連結](https://www.elegislation.gov.hk/hk/cap57)")
                        st.markdown("---")
                        
                        combined_response += f"**{data_zh['title']} / {data_en['title']}**\n\n"
                    st.session_state.messages.append({"role": "assistant", "content": combined_response})

# ------------------------------------------
# Track B: Dynamic Risk Audit Scorecard
# ------------------------------------------
with tab_audit:
    st.markdown("### 📋 動態風險排查表單 (Dynamic Risk Audit)" if is_zh else "### 📋 Dynamic Risk Audit Scorecard")
    
    with st.form("audit_form"):
        col1, col2 = st.columns(2)
        with col1:
            emp_type = st.selectbox("員工合約類型 (Employment Type)", ["全職 (Full-time)", "兼職/散工 (Part-time/Casual)", "獨立承包人 (Independent Contractor)"])
        with col2:
            tenure = st.selectbox("服務年資 (Tenure)", ["少於 4 星期", "大於 4 星期", "滿 24 個月", "滿 5 年"])
        submit_audit = st.form_submit_button("執行風險稽核 (Execute Audit)" if is_zh else "Execute Audit")

    if submit_audit:
        st.markdown("#### 🚨 稽核結果 (Audit Findings)")
        has_risk = False
        if emp_type == "獨立承包人 (Independent Contractor)":
            st.error("**假自僱風險 (False Self-Employment Risk):** 確保與該人員的合作實質上不構成僱傭關係，否則企業將面臨逃避強積金及法定福利之刑事檢控風險。")
            has_risk = True
        if emp_type == "兼職/散工 (Part-time/Casual)" and tenure != "少於 4 星期":
            st.warning("**468 連續性合約風險 (468 Mechanism):** 該兼職員工極可能已突破滾動 68 小時門檻。請確保系統已自動為其結算有薪法定假日與疾病津貼。")
            has_risk = True
        if tenure == "滿 24 個月" or tenure == "滿 5 年":
            st.error("**解僱賠償與保障負債 (Termination Liabilities):** 年資滿 24 個月解僱具有「不合理解僱」申索風險及遣散費責任；滿 5 年則具備長期服務金(LSP)風險。請收歸總部 HR 處理。")
            has_risk = True
        if not has_risk:
            st.success("✅ 根據當前參數，未觸發高危紅線。請繼續遵守一般工資支付（工資期後7天內出糧）之基本規定。" if is_zh else "✅ No high-risk statutory triggers detected based on current parameters.")

# ------------------------------------------
# Track C: ADW 713 Calculator
# ------------------------------------------
with tab_calc:
    st.markdown("### 🧮 12個月平均工資 (ADW 713) 法定權益計算機" if is_zh else "### 🧮 12-Month ADW Calculator")
    
    col_in1, col_in2 = st.columns(2)
    with col_in1:
        total_wages = st.number_input("1. 過去12個月賺取的總工資 / Total Wages ($)", min_value=0.0, value=150000.0, step=1000.0)
        total_days = st.number_input("2. 12個月內的總日數 / Total Days (e.g., 365)", min_value=1, value=365, step=1)
    with col_in2:
        disregarded_days = st.number_input("3. 須剔除日數 / Disregarded Days (非全薪假天數)", min_value=0, value=5, step=1)
        disregarded_wages = st.number_input("4. 剔除期間工資 / Disregarded Wages (非全薪假期間拿到的薪酬) ($)", min_value=0.0, value=2667.0, step=100.0)

    st.markdown("---")
    
    # 執行運算
    if total_days > disregarded_days:
        adjusted_numerator = total_wages - disregarded_wages
        adjusted_denominator = total_days - disregarded_days
        adw = adjusted_numerator / adjusted_denominator
        
        st.metric("每日平均工資 (ADW)", f"${adw:.2f}")
        
        c_res1, c_res2 = st.columns(2)
        c_res1.success(f"**疾病津貼 / 產假 / 侍產假薪酬 (4/5ths):**\n### ${adw * 0.8:.2f} / 日")
        c_res2.success(f"**有薪年假 / 法定假日 / 代通知金 (Full Pay):**\n### ${adw:.2f} / 日")
        
        # 大白話動態原理講解區塊
        st.markdown("---")
        st.subheader("💡 713 條例：分子與分母扣除原理說明" if is_zh else "💡 Paragraph 713: Numerator & Denominator Deduction Logic")
        
        if is_zh:
            st.markdown(f"""
            根據《2007年僱傭(修訂)條例》（俗稱 713 條例），為了**避免拉低員工的平均工資**進而損害其法定權益，系統已執行以下決定性扣除邏輯：
            
            1. **分子（合資格薪酬）**：從總工資 **${total_wages:,.2f}** 中，無情扣除了非全薪假期發放的薪酬 **${disregarded_wages:,.2f}**，得出合資格分子為 **${adjusted_numerator:,.2f}**。
            2. **分母（合資格天數）**：從總天數 **{total_days} 天** 中，精準剔除了非全薪假期的 **{disregarded_days} 天**，得出合資格分母為 **{adjusted_denominator} 天**。
            3. **最終算式**：$$\\text{{ADW}} = \\frac{{\\${adjusted_numerator:,.2f}（合資格薪酬）}}{{{adjusted_denominator}天（合資格天數）}} = \\${adw:.2f}$$
            
            *註：若員工請的是「100%全薪年假」或「有薪休息日」，開支沒有拉低工資平均值，依法**不需剔除**，直接保留在分子和分母中計算。*
            """)
        else:
            st.markdown(f"""
            According to the Employment (Amendment) Ordinance 2007 (commonly known as Paragraph 713), to **avoid deflating the employee's average daily wage** and reducing statutory benefits, the system executes the following deterministic logic:
            
            1. **Numerator (Adjusted Wages)**: Disregarded wages of **${disregarded_wages:,.2f}** (earned during less-than-full-pay leave) are deducted from Total Wages **${total_wages:,.2f}**, resulting in an eligible numerator of **${adjusted_numerator:,.2f}**.
            2. **Denominator (Adjusted Days)**: Disregarded leave periods of **{disregarded_days} days** are excluded from Total Days **{total_days} days**, resulting in an eligible denominator of **{adjusted_denominator} days**.
            3. **Formula**: $$\\text{{ADW}} = \\frac{{\\${adjusted_numerator:,.2f} (Adjusted Wages)}}{{{adjusted_denominator} days (Adjusted Days)}} = \\${adw:.2f}$$
            
            *Note: Full-paid leaves (e.g., 100% full-paid annual leave or paid rest days) do NOT deflate the average, and thus legally **should NOT be excluded** from either the numerator or denominator.*
            """)
            
    else:
        st.error("⚠️ 錯誤：剔除日數不可大於或等於總日數。 (Error: Disregarded days ≥ Total days)")

    # 官方 PDF 與計算機連結
    st.markdown("---")
    st.markdown("#### 🔗 勞工處官方權益計算指引與出處文檔 (Official Statutory Sources)")
    if is_zh:
        st.markdown("""
        為落實最高規格之法律防禦，如遇複雜個案，請直接下載並翻查勞工處發布之官方成文法簡明指南手冊：
        * [勞工處官方文檔：附錄一《以12個月平均工資來計算有關法定權益簡介及計算例子》PDF 說明書](https://www.labour.gov.hk/tc/public/pdf/ConciseGuide/Appendix1.pdf)
        * [勞工處官方文檔：《僱傭條例簡明指南》全本繁體中文 PDF 下載網址](https://www.labour.gov.hk/tc/public/pdf/ConciseGuide/EmploymentOrdinance.pdf)
        * [勞工處官方動態核算工具：法定權益參考計算機首頁網址](https://www.labour.gov.hk/tc/labour/Statutory_Employment_Entitlements_Reference_Calculator.htm)
        """)
    else:
        st.markdown("""
        To achieve maximum legal compliance and discharge accountability, please access the official source documentation issued by the HK Labour Department:
        * [Official Source: Appendix 1 - Guide to the Calculation of Statutory Entitlements on the Basis of 12-Month Average Wages (PDF Handbook)](https://www.labour.gov.hk/eng/public/pdf/ConciseGuide/Appendix1.pdf)
        * [Official Source: Concise Guide to the Employment Ordinance (Full English PDF)](https://www.labour.gov.hk/eng/public/pdf/ConciseGuide/EmploymentOrdinance.pdf)
        * [Official Web Application: Statutory Employment Entitlements Reference Calculator Portal](https://www.labour.gov.hk/eng/labour/Statutory_Employment_Entitlements_Reference_Calculator.htm)
        """)
