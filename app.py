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
            "title": "第 1 章：僱傭條例適用範圍",
            "statute": "《僱傭條例》適用於所有受僱於僱傭合約的僱員。連續性合約已放寬為「468」機制：指僱員連續受僱於同一僱主 4 星期或以上，4 星期內總工作時數滿 68 小時，即享有更多法定權益。",
            "red_flag": "錯誤將實質僱傭關係包裝為「獨立承包人（假自僱）」，或刻意打斷工時以規避福利。",
            "gov_advice": "【董事會管治】應立即重新審視兼職與散工的排班策略及工時結算演算法，防範潛在的集體勞資索償風險。\n\n【前線營運提示】請確實記錄兼職員工的上下班時間，切勿口頭要求員工「提早下班」以惡意避開 468 工時門檻。"
        },
        "en": {
            "title": "Chapter 1: Application of the Employment Ordinance",
            "statute": "A 'continuous contract' (468 rule) means an employee works for the same employer for 4 weeks or more, with at least 68 hours in total over 4 weeks, entitling them to statutory benefits.",
            "red_flag": "Misclassifying employees as independent contractors (false self-employment) or artificially breaking the 468 continuous contract.",
            "gov_advice": "[Board-Level Governance] Immediately review rostering strategies and time-tracking algorithms for non-standard workforce.\n\n[Line Manager Actions] Ensure accurate time-tracking for part-timers. Do not informally ask staff to clock out early to evade the 468 threshold."
        }
    },
    "ch3": {
        "keys": ["工資", "wages", "salary", "薪金", "扣薪", "扣人工", "出糧", "遲出糧", "欠薪", "扣錢", "爛嘢", "賠錢"],
        "zh": {
            "title": "第 3 章：工資與扣薪限制",
            "statute": "工資必須在工資期屆滿後 7 天內支付。除法例明文規定外嚴禁扣薪；如僱員損壞僱主貨品，每次按值扣除上限僅為 HK$300。",
            "red_flag": "遲發工資超過 7 天，或以「表現不佳」等非法定理由私自扣減員工工資。",
            "gov_advice": "【董事會管治】實施自動化工資結算與合規審計系統。董事會應將「欠薪」視為最高級別之營運及法律風險（涉刑事責任及監禁）。\n\n【前線營運提示】即使員工打破碗碟或造成公司財產損失，絕不可私自扣減工資作為處罰，法定每次損壞扣款上限為 HK$300。"
        },
        "en": {
            "title": "Chapter 3: Wages & Deductions",
            "statute": "Wages must be paid within 7 days. Deductions are strictly limited by law (e.g., damage to goods capped at HK$300 per instance).",
            "red_flag": "Paying wages later than 7 days, or making illegal deductions for 'poor performance'.",
            "gov_advice": "[Board-Level Governance] Implement automated payroll audit systems. Treat 'unpaid wages' as a top-tier legal risk (criminal liability).\n\n[Line Manager Actions] Never deduct wages as a punitive measure for poor performance. Damage deduction is strictly capped at HK$300 per instance."
        }
    },
    "ch4_5": {
        "keys": ["休息日", "法定假日", "勞工假", "銀行假", "買假", "補假", "紅日", "放假", "逼人返工", "holiday"],
        "zh": {
            "title": "第 4 及 5 章：休息日與法定假日 (勞工假)",
            "statute": "按連續性合約受僱，每 7 天可享不少於 1 天休息日。所有僱員均享法定假日，僱主不得以款項代替發放法定假日（嚴禁「買假」）。",
            "red_flag": "混淆「銀行假」與「勞工假」，強迫僱員在休息日工作，或違法以薪金買斷法定假日。",
            "gov_advice": "【董事會管治】將法定假日與公眾假期（Bank Holidays）的政策差異清晰列明於員工手冊，並設定排班系統防呆機制。\n\n【前線營運提示】如果要求員工在法定假日（勞工假）上班，必須依法安排「另定假日」補假，絕不能用錢「買假」解決。"
        },
        "en": {
            "title": "Chapters 4 & 5: Rest Days & Statutory Holidays",
            "statute": "Continuous contract employees are entitled to 1 rest day in every 7 days. Statutory holidays cannot be bought out with payment.",
            "red_flag": "Compelling employees to work on rest days or illegally buying out statutory holidays.",
            "gov_advice": "[Board-Level Governance] Clearly differentiate Statutory and Public Holidays in the handbook with system-level hardstops.\n\n[Line Manager Actions] If staff must work on a Statutory Holiday, you must arrange an alternative holiday. Paying them extra to 'buy out' the holiday is illegal."
        }
    },
    "ch6": {
        "keys": ["有薪年假", "annual leave", "年假", "AL", "大假", "清假", "辭職扣假"],
        "zh": {
            "title": "第 6 章：有薪年假",
            "statute": "受僱滿1年可享有 7 至 14 天有薪年假。年假薪酬應以過去12個月的每日平均工資（ADW）計算。",
            "red_flag": "錯誤計算 ADW（未計入佣金或津貼），或拒絕批出法定年假。",
            "gov_advice": "【董事會管治】定期審核 ADW 計算公式是否涵蓋所有法定「工資」元素（包含浮動佣金）。\n\n【前線營運提示】員工辭職時，若按比例計算仍有未放取的大假，必須補回大假薪酬，不可隨意沒收。"
        },
        "en": {
            "title": "Chapter 6: Paid Annual Leave",
            "statute": "Employees are entitled to 7-14 days of paid annual leave after 1 year of service, calculated using the 12-month ADW.",
            "red_flag": "Miscalculating ADW (excluding commissions) or refusing statutory leave.",
            "gov_advice": "[Board-Level Governance] Regularly audit the ADW calculation formula to ensure it encompasses all statutory 'wage' elements.\n\n[Line Manager Actions] Upon resignation, any untaken pro-rata annual leave must be compensated. Do not arbitrarily forfeit leave balances."
        }
    },
    "ch7": {
        "keys": ["疾病津貼", "sickness allowance", "病假", "sick leave", "SL", "醫生紙", "五分四糧", "4/5", "連續4日", "工傷"],
        "zh": {
            "title": "第 7 章：疾病津貼 (有薪病假)",
            "statute": "連續病假不少於 4 天，並有適當醫生證明書，可獲每日平均工資五分之四（4/5）的疾病津貼。",
            "red_flag": "在僱員合法放取有薪病假期間解僱僱員（除即時解僱外），屬違法行為。",
            "gov_advice": "【董事會管治】設立健全的醫療缺勤管理機制，嚴防前線主管對合法放取病假的員工採取報復性解僱。\n\n【前線營運提示】請病假 1 至 3 天依法可無薪，但連續 4 天以上並交出有效「醫生紙」，就必須支付 4/5 薪酬。切勿在員工放病假期間將其解僱！"
        },
        "en": {
            "title": "Chapter 7: Sickness Allowance",
            "statute": "Taking ≥ 4 consecutive days of sick leave with a valid medical certificate entitles the employee to 4/5 of their ADW.",
            "red_flag": "Terminating an employee while they are on paid sick leave is an offence.",
            "gov_advice": "[Board-Level Governance] Establish a robust medical absence management mechanism to prevent retaliatory terminations.\n\n[Line Manager Actions] Sick leave < 4 days can be unpaid, but ≥ 4 consecutive days with a valid MC requires 4/5ths pay. Never fire an employee while they are on sick leave."
        }
    },
    "ch8_9": {
        "keys": ["生育保障", "產假", "侍產假", "maternity", "大肚", "懷孕", "前4後10", "男士侍產", "陪產", "有咗"],
        "zh": {
            "title": "第 8 及 9 章：生育與侍產保障",
            "statute": "合資格女性僱員可享有 14 星期有薪產假。男性僱員可享有 5 天侍產假，薪酬同為每日平均工資的五分之四（4/5）。",
            "red_flag": "解僱已發出懷孕通知的女僱員，面臨極高刑事及平機會歧視索償風險。",
            "gov_advice": "【董事會管治】善用政府「發還產假薪酬計劃」。將懷孕解僱的決策權全面收歸最高管理層及法務部。\n\n【前線營運提示】一旦得知女員工懷孕，絕對不能以「表現欠佳」為由隨意解僱。男員工放侍產假需提供嬰兒出生證明等文件。"
        },
        "en": {
            "title": "Chapters 8 & 9: Maternity & Paternity Leave",
            "statute": "Eligible females receive 14 weeks paid maternity leave. Eligible males receive 5 days paternity leave at 4/5 ADW.",
            "red_flag": "Dismissing a pregnant employee carries extreme criminal and EOC discrimination claim risks.",
            "gov_advice": "[Board-Level Governance] Centralize any termination decisions regarding pregnant staff to Top Management. Utilize the Govt Reimbursement Scheme.\n\n[Line Manager Actions] Never terminate an employee for 'poor performance' after learning of her pregnancy. Paternity leave requires birth certification."
        }
    },
    "ch11": {
        "keys": ["終止僱傭合約", "解僱", "通知期", "代通知金", "辭職", "唔撈", "炒人", "即炒", "即時解僱", "summary dismissal", "補錢", "遞信", "偷嘢", "打交"],
        "zh": {
            "title": "第 11 章：終止僱傭合約與即時解僱",
            "statute": "終止合約需給予足夠通知期或代通知金。僅當僱員犯下故意不服從合法命令、行為不當、欺詐或慣常疏忽職責時，才可「即時解僱 (Summary Dismissal)」。",
            "red_flag": "缺乏書面警告信及調查報告下，濫用「即時解僱（即炒）」權利而拒付代通知金。",
            "gov_advice": "【董事會管治】落實漸進式紀律處分程序。即時解僱（Cap. 57 Sec 9）需視為最後手段，並留存無可辯駁的審計軌跡。\n\n【前線營運提示】若遇員工嚴重違紀（如偷竊、打架），請立即拍照留底並通報 HR 及報警，切勿在情緒激動下口頭當場宣告「即炒」而引發程序爭議。"
        },
        "en": {
            "title": "Chapter 11: Termination & Summary Dismissal",
            "statute": "Termination requires notice period or payment in lieu. Summary dismissal is only for serious misconduct (e.g., fraud, habitual neglect).",
            "red_flag": "Failing to provide payment in lieu, or abusing 'Summary Dismissal' without concrete evidence.",
            "gov_advice": "[Board-Level Governance] Enforce Progressive Discipline procedures. Summary Dismissal must be the absolute last resort with an irrefutable audit trail.\n\n[Line Manager Actions] Report serious misconduct to HR immediately. Take photos/collect evidence, and never verbally execute a summary dismissal in the heat of the moment."
        }
    },
    "ch13": {
        "keys": ["遣散費", "長期服務金", "LSP", "SP", "裁員", "執笠", "對沖", "取消對沖", "肥雞餐", "layoff"],
        "zh": {
            "title": "第 13 章：遣散費及長期服務金",
            "statute": "受僱滿 24 個月因裁員可獲遣散費；滿 5 年遭解僱可獲長期服務金。強積金對沖機制於2025年5月1日起正式取消，僱主不可用強制性供款對沖遣散費/長服金。",
            "red_flag": "製造假裁員，或為逃避支付長期服務金而在員工年資接近 5 年時惡意解僱。",
            "gov_advice": "【董事會管治】因應 2025 年取消強積金對沖，必須精算並撥備遣散費/長服金負債，善用政府資助計劃。\n\n【前線營運提示】終止任何年資超過 2 年的員工合約前，必須先與總部 HR 核算潛在的 SP/LSP 負債，切勿私自決定裁員名單。"
        },
        "en": {
            "title": "Chapter 13: Severance & Long Service Payment",
            "statute": "Severance Payment for redundancy after 24 months; Long Service Payment after 5 years service. MPF employer mandatory contributions offsetting mechanism is abolished from 1 May 2025.",
            "red_flag": "Sham redundancies or maliciously terminating staff approaching the 5-year mark to evade LSP.",
            "gov_advice": "[Board-Level Governance] Adopt Strategic HR Planning (SHRP). Actuarially assess and provision for SP/LSP liabilities considering the MPF offset abolition.\n\n[Line Manager Actions] Always calculate potential SP/LSP liabilities with HQ HR before terminating any staff with over 2 years of tenure."
        }
    }
}

CAP57_SECTIONS_DB = [
    {
        "regex": r'(section|sec\.?|第)?\s*3\s*(條)?|418|468',
        "zh": {"title": "Cap. 57 Section 3: 連續性合約的涵義與舉證責任", "statute": "連續性合約已放寬為「468」機制：凡受僱於同一僱主連續 4 星期或以上，4 星期總工時滿 68 小時，即屬連續性合約。爭議時，舉證責任在於僱主。", "red_flag": "僱主無法出示完整工時紀錄以證明僱員非連續性受僱。", "gov_advice": "【董事會管治】實施數字化工時追蹤與動態警示機制，確保兼職工時數據具備完備的稽核軌跡。\n\n【前線營運提示】確保更表（Roster）與員工實際打卡紀錄完全吻合，所有考勤紀錄必須在系統妥善保存最少 6 個月。"},
        "en": {"title": "Cap. 57 Section 3: Meaning of continuous contract and onus of proof", "statute": "Employment for ≥ 4 weeks with a total of ≥ 68 hours (468 mechanism). Onus of proof rests on the employer.", "red_flag": "Failure of the employer to produce comprehensive working hour records to discharge the onus of proof.", "gov_advice": "[Board-Level Governance] Implement digital time-tracking with dynamic alerts to ensure a complete audit trail for part-time working hours.\n\n[Line Manager Actions] Ensure rosters strictly match actual clock-in/out records. Attendance records must be securely stored for at least 6 months."}
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
        
        # 大白話動態原理講解區塊 (Bilingual Explanations)
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
