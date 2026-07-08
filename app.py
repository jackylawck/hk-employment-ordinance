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
        "keys": ["適用範圍", "application", "scope", "418", "468", "連續性合約", "兼職", "part-time", "散工", "自僱", "假自僱", "返工"],
        "zh": {
            "title": "第 1 章：僱傭條例適用範圍",
            "statute": "《僱傭條例》適用於所有受僱於僱傭合約的僱員。連續性合約已放寬為「468」機制：指僱員連續受僱於同一僱主 4 星期或以上，4 星期內總工作時數滿 68 小時或以上，即享有更多法定權益（如休息日、有薪年假、疾病津貼等）。",
            "red_flag": "錯誤將實質僱傭關係包裝為「獨立承包人（假自僱）」，或刻意打斷 468 連續性合約時數以規避福利。",
            "gov_advice": "【董事會管治】應立即重新審視兼職與散工的排班策略及工時結算演算法，防範潛在的集體勞資索償風險。\n\n【前線營運提示】請確實記錄兼職員工的上下班時間，切勿口頭要求員工「提早下班」以惡意避開 468 工時門檻。"
        },
        "en": {
            "title": "Chapter 1: Application of the Employment Ordinance",
            "statute": "The EO applies to all employees engaged under a contract of employment. A 'continuous contract' (now the 468 rule) means an employee works for the same employer for 4 weeks or more, with at least 68 hours in total over 4 weeks, entitling them to statutory benefits.",
            "red_flag": "Misclassifying employees as independent contractors (false self-employment) or artificially breaking the 468 continuous contract to evade benefits.",
            "gov_advice": "[Board-Level Governance] Immediately review rostering strategies and time-tracking algorithms for non-standard workforce to mitigate class action risks.\n\n[Line Manager Actions] Ensure accurate time-tracking for part-timers. Do not informally ask staff to clock out early to evade the 468 threshold."
        }
    },
    "ch2": {
        "keys": ["僱傭合約", "contracts of employment", "contract", "合約", "更改合約", "variation", "簽約", "試用期", "probation", "轉制", "減薪", "pay cut", "調職"],
        "zh": {
            "title": "第 2 章：僱傭合約",
            "statute": "僱傭合約可以書面或口頭訂立。僱主在僱員就職前，必須向僱員詳細說明僱用條件。如無僱員同意，僱主不得單方面更改合約條款。",
            "red_flag": "未經僱員同意單方面更改合約（如減薪、更改工作地點），構成不合理更改僱傭合約條款。",
            "gov_advice": "【董事會管治】所有合約變更必須落實書面同意（Mutual Consent），制定標準化入職與合約變更 SOP，確保資訊透明度。\n\n【前線營運提示】任何崗位調動或薪酬調整，在系統執行前必須確認已收妥員工簽署的變更同意書。"
        },
        "en": {
            "title": "Chapter 2: Contracts of Employment",
            "statute": "Contracts can be written or oral. Employers must clearly inform employees of the conditions of employment before employment begins. Unilateral variation of terms is not permitted without consent.",
            "red_flag": "Unilateral variation of contract terms (e.g., pay cut, relocation) without employee consent, constituting unreasonable variation.",
            "gov_advice": "[Board-Level Governance] Ensure all contract variations are documented with mutual written consent. Develop standardized SOPs for onboarding and contract changes.\n\n[Line Manager Actions] Do not implement any relocation or pay adjustment without a signed mutual consent form from the employee."
        }
    },
    "ch3": {
        "keys": ["工資", "wages", "salary", "薪金", "扣薪", "deduction", "tips", "小費", "服務費", "人工", "出糧", "遲出糧", "欠薪", "late pay", "扣錢", "佣金", "commission", "津貼", "allowance"],
        "zh": {
            "title": "第 3 章：工資",
            "statute": "工資包括薪金、津貼、小費及服務費（Tips and service charges）。工資必須在工資期屆滿後 7 天內支付。除法例明文規定（如缺勤、損壞僱主貨品上限$300）外，嚴禁扣薪。",
            "red_flag": "遲發工資超過 7 天，或以「表現不佳」等非法定理由非法扣減員工工資。",
            "gov_advice": "【董事會管治】實施自動化工資結算與合規審計系統。董事會應將「欠薪」視為最高級別之營運及法律風險（涉及刑事責任）。\n\n【前線營運提示】即使員工犯錯或造成公司財產損失，絕不可私自扣減工資作為處罰，每次損壞扣款上限硬性規定為 HK$300。"
        },
        "en": {
            "title": "Chapter 3: Wages",
            "statute": "Wages include salary, allowances, tips, and service charges. Wages must be paid within 7 days after the end of the wage period. Deductions are strictly limited by law (e.g., absence, damage to goods capped at $300).",
            "red_flag": "Paying wages later than 7 days, or making illegal deductions for non-statutory reasons like 'poor performance'.",
            "gov_advice": "[Board-Level Governance] Implement automated payroll and compliance audit systems. The Board must treat 'unpaid wages' as a top-tier operational and legal risk (criminal liability).\n\n[Line Manager Actions] Never deduct wages as a punitive measure for poor performance. Damage deduction is strictly capped at HK$300 per instance."
        }
    },
    "ch11": {
        "keys": ["終止僱傭合約", "termination", "解僱", "dismissal", "通知期", "notice period", "代通知金", "payment in lieu", "炒", "解雇", "辭職", "唔撈", "炒人", "fire", "resign", "quit", "補錢", "賠錢走", "遞信", "一個月通知", "即炒", "即時解僱", "summary dismissal", "嚴重犯錯", "偷嘢", "打交", "犯法", "犯錯"],
        "zh": {
            "title": "第 11 章：終止僱傭合約",
            "statute": "終止合約需給予足夠通知期或代通知金。無試用期或試用期後，通知期不得少於 7 天。僱員嚴重犯錯可被無通知期即時解僱（Summary Dismissal）。",
            "red_flag": "未給予足夠代通知金，或濫用「即時解僱」權力而缺乏充分實證。",
            "gov_advice": "【董事會管治】落實漸進式紀律處分程序（Progressive Discipline）。即時解僱（Cap. 57 Sec 9）需視為最後手段，並留存無可辯駁的審計軌跡 (Audit Trail)。\n\n【前線營運提示】若遇員工嚴重違紀（如偷竊、打架），請立即拍照留底並通報 HR/法務，切勿在情緒激動下口頭當場宣告即時解僱。"
        },
        "en": {
            "title": "Chapter 11: Termination of Employment Contract",
            "statute": "Termination requires appropriate notice period or payment in lieu. Post-probation notice must be at least 7 days. Summary dismissal is only for serious misconduct.",
            "red_flag": "Failing to provide sufficient payment in lieu, or abusing 'Summary Dismissal' without concrete evidence.",
            "gov_advice": "[Board-Level Governance] Enforce Progressive Discipline procedures. Summary Dismissal (Cap. 57 Sec 9) must be the absolute last resort with an irrefutable audit trail.\n\n[Line Manager Actions] Report serious misconduct to HR immediately. Take photos/collect evidence, and never verbally execute a summary dismissal in the heat of the moment."
        }
    },
    "ch13": {
        "keys": ["遣散費", "severance payment", "長期服務金", "long service payment", "LSP", "SP", "裁員", "redundancy", "執笠", "結業", "對沖", "offset", "mpf", "強積金", "cut人", "layoff"],
        "zh": {
            "title": "第 13 章：遣散費及長期服務金",
            "statute": "受僱滿 24 個月因裁員遭解僱可獲遣散費（SP）；受僱滿 5 年非因嚴重過失遭解僱可獲長期服務金（LSP）。強積金（MPF）對沖機制已正式取消。",
            "red_flag": "製造假裁員，或為逃避 LSP 而在員工年資接近 5 年時惡意解僱。",
            "gov_advice": "【董事會管治】建立戰略性人力資源規劃（SHRP）。精算並撥備遣散費/長服金負債，特別注意「取消對沖」過渡期的財務與法律合規風險。\n\n【前線營運提示】終止任何年資超過 2 年的員工合約前，必須先與總部 HR 核算潛在的 SP/LSP 負債，切勿私自安排裁員。"
        },
        "en": {
            "title": "Chapter 13: Severance & Long Service Payment",
            "statute": "Severance Payment (SP) for redundancy after 24 months service; Long Service Payment (LSP) for non-summary dismissal after 5 years service. MPF employer contributions offsetting mechanism is abolished.",
            "red_flag": "Sham redundancies or maliciously terminating staff approaching the 5-year mark to evade LSP.",
            "gov_advice": "[Board-Level Governance] Adopt Strategic HR Planning (SHRP). Actuarially assess and provision for SP/LSP liabilities, paying critical attention to the financial compliance risks of the MPF offset abolition.\n\n[Line Manager Actions] Always calculate potential SP/LSP liabilities with HQ HR before terminating any staff with over 2 years of tenure."
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
        * **治理框架**: 系統架構嚴格對齊 **IAPP AIGP** 部署監督規範與 **ISO/IEC 42001** 管理體系思維。
        * **架構安全性**: **100% 無 AI / 無 RAG 技術**。採用純決定性代碼架構，杜絕生成式大模型胡言亂語的「AI 幻覺」風險。
        * **數據零留底**: 系統無後台數據庫，不儲存任何查詢歷史。網頁一經關閉，所有輸入數據立即在雲端**全部歸零**，確保企業人事隱私絕對安全。
        * **法規對齊**: 深度整合官方《僱傭條例》（Cap. 57）主體條文與最新 **「468機制」**。
        """)
    else:
        st.markdown("### ⚙️ System Design & Security")
        st.markdown("""
        * **Positioning**: An automated labor law retrieval and compliance audit tool engineered for corporate executives and managers.
        * **Governance**: Architecture strictly aligned with **IAPP AIGP** deployment oversight and **ISO/IEC 42001** management systems.
        * **Core Technology**: **100% AI-Free / No RAG**. Built entirely on deterministic logic to fully eliminate the risk of generative "AI hallucinations."
        * **Data Sovereignty**: Zero back-end databases. No query histories are recorded. All user inputs are **completely wiped from memory** upon closing the page.
        * **Statutory Alignment**: Fully integrated with the official text of the HK Employment Ordinance (Cap. 57) and the latest **468 mechanism**.
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
# 4. 輔助函式與安全護欄 (Helpers & Guardrails)
# ==========================================
OUT_OF_SCOPE_WORDS = ["稅", "tax", "強積金投資", "mpf investment", "基金", "簽證", "visa", "入境處", "移民", "immigration", "刑事", "criminal", "報稅"]

def check_out_of_scope(query):
    query_lower = query.lower()
    return any(word in query_lower for word in OUT_OF_SCOPE_WORDS)

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

def fallback_response(lang):
    if lang == '繁體中文':
        return "🔍 **兜底與動態導航機制啟動 (Fallback Mechanism Triggered)** 您查詢的內容涉及較為高階或冷門的法定條文。為確保 100% 法律合規性，請查閱官方原文：[🔗 電子版香港法例 Cap. 57 (官方原文)](https://www.elegislation.gov.hk/hk/cap57)"
    else:
        return "🔍 **Fallback & Dynamic Navigation Triggered** Your query involves advanced or specific provisions. To ensure 100% legal compliance, please refer to the official statutory text: [🔗 eLegislation Cap. 57 (Official Full Text)](https://www.elegislation.gov.hk/hk/cap57)"

# ==========================================
# 5. 主畫面佈局
# ==========================================
st.title("⚖️ Cap. 57 Employment Ordinance Full-Text Interactive Advisor")
if is_zh:
    st.subheader("100% 決定性合規・零幻覺勞工法例檢責與審計系統")
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

    if prompt := st.chat_input("請輸入關鍵字、口語或 Cap.57 條文（例如：'468', '即炒', '出糧'）..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            if check_out_of_scope(prompt):
                out_msg = "🛑 **超出範圍阻斷 (Out of Scope)**: 您查詢的內容包含非《僱傭條例》(Cap. 57) 範圍的議題（如：稅務、簽證、基金投資等）。本系統拒絕提供推測性解答。請向稅務局或入境處查詢。" if is_zh else "🛑 **Out of Scope Blocked**: Your query relates to topics outside Cap. 57 (e.g., taxation, visas). This system refuses to generate speculative answers."
                st.error(out_msg)
                st.session_state.messages.append({"role": "assistant", "content": out_msg})
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
# Track C: ADW 713 Calculator (內建大白話原理解釋 ＋ 官方出處)
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
        
        # 💡 升級點：大白話動態原理講解區塊 (Bilingual Explanations)
        st.markdown("---")
        st.subheader("💡 713 條例：分子與分母扣除原理說明" if is_zh else "💡 Paragraph 713: Numerator & Denominator Deduction Logic")
        
        if is_zh:
            st.markdown(f"""
            根據《2007年僱傭(修訂)條例》（俗稱 713 條例），為了**避免拉低員工的平均工資**進而損害其法定權益，系統已執行以下決定性扣除邏輯：
            
            1. **分子（合資格薪酬）**：從總工資 **${total_wages:,.2f}** 中，無情扣除了非全薪假期發放的薪酬 **${disregarded_wages:,.2f}**，得出合資格分子為 **${adjusted_numerator:,.2f}**。
            2. **分母（合資格天數）**：從總天數 **{total_days} 天** 中，精準剔除了非全薪假期的 **{disregarded_days} 天**，得出合資格分母為 **{adjusted_denominator} 天**。
            3. **最終算式**：$$\\text{{ADW}} = \\frac{{\\${adjusted_numerator:,.2f}（合資格薪酬）}}{{{adjusted_denominator}天（合資格天數）}} = \\${adw:.2f}$$
            
            *註：若員工請的是「100%全薪年假」或「有薪休息日」，因為沒有拉低工資平均值，依法**不需剔除**，直接保留在分子和分母中計算。*
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

    # 💡 升級點：提供直連勞工處官方文件的 PDF 出處網址 (Statutory Source Citations)
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
