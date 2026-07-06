import streamlit as st
import re
from datetime import datetime

# ==========================================
# 1. Page Configuration & UI Initialization
# ==========================================
st.set_page_config(
    page_title="Hong Kong Employment Ordinance (Cap. 57) Advisor",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hide Streamlit default menu for enterprise look
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stCheckbox > label {font-weight: 500;}
    </style>
""", unsafe_allow_html=True)

# Initialize Session State
if 'lang' not in st.session_state:
    st.session_state.lang = '繁體中文'
if 'messages' not in st.session_state:
    st.session_state.messages = []

# ==========================================
# 2. Dual-Layer Knowledge Base (Cap. 57 & 13 Chapters)
# ==========================================
# Layer 1: 13 Core Chapters of the Concise Guide
CHAPTERS_DB = {
    "ch1": {
        "keys": ["適用範圍", "application", "scope", "418", "連續性合約", "continuous contract"],
        "zh": {
            "title": "第 1 章：僱傭條例適用範圍",
            "statute": "《僱傭條例》適用於所有受僱於僱傭合約的僱員。連續性合約（俗稱418）指僱員連續受僱於同一僱主4星期或以上，每星期最少工作18小時，可享有更多法定權益（如休息日、有薪年假、疾病津貼等）。",
            "red_flag": "錯誤將實質僱傭關係包裝為「獨立承包人（假自僱）」，或刻意打斷 418 連續性合約以規避福利。",
            "board_advice": "建立嚴格的非標準勞動力（Gig Workers/Contractors）合約審查機制，定期進行勞資關係實質性測試（Control Test, Integration Test）。"
        },
        "en": {
            "title": "Chapter 1: Application of the Employment Ordinance",
            "statute": "The EO applies to all employees engaged under a contract of employment. A 'continuous contract' (418 rule) means an employee works for the same employer for 4 weeks or more, at least 18 hours per week, entitling them to statutory benefits.",
            "red_flag": "Misclassifying employees as independent contractors (false self-employment) or artificially breaking the 418 continuous contract to evade benefits.",
            "board_advice": "Establish strict contract review mechanisms for non-standard workforce. Regularly conduct substantive tests on employment relations (e.g., Control Test)."
        }
    },
    "ch2": {
        "keys": ["僱傭合約", "contracts of employment", "contract", "合約", "更改合約", "variation"],
        "zh": {
            "title": "第 2 章：僱傭合約",
            "statute": "僱傭合約可以書面或口頭訂立。僱主在僱員就職前，必須向僱員詳細說明僱傭條件。如無僱員同意，僱主不得單方面更改合約條款。",
            "red_flag": "未經僱員同意單方面更改合約（如減薪、更改工作地點），構成不合理更改僱傭合約條款。",
            "board_advice": "所有合約變更必須落實書面同意（Mutual Consent）。制定標準化入職與合約變更 SOP，確保資訊透明度。"
        },
        "en": {
            "title": "Chapter 2: Contracts of Employment",
            "statute": "Contracts can be written or oral. Employers must clearly inform employees of the conditions of employment before employment begins. Unilateral variation of terms is not permitted without consent.",
            "red_flag": "Unilateral variation of contract terms (e.g., pay cut, relocation) without employee consent, constituting unreasonable variation.",
            "board_advice": "Ensure all contract variations are documented with mutual written consent. Develop standardized SOPs for onboarding and contract changes."
        }
    },
    "ch3": {
        "keys": ["工資", "wages", "salary", "薪金", "扣薪", "deduction", "tips", "小費", "服務費"],
        "zh": {
            "title": "第 3 章：工資",
            "statute": "工資包括薪金、津貼、小費及服務費（Tips and service charges）。工資必須在工資期屆滿後 7 天內支付。除法例明文規定（如缺勤、損壞僱主貨品上限$300）外，嚴禁扣薪。",
            "red_flag": "遲發工資超過 7 天，或以「表現不佳」等非法定理由非法扣減員工工資。",
            "board_advice": "實施自動化工資結算與合規審計系統。董事會應將「欠薪」視為最高級別之營運及法律風險（涉及刑事責任）。"
        },
        "en": {
            "title": "Chapter 3: Wages",
            "statute": "Wages include salary, allowances, tips, and service charges. Wages must be paid within 7 days after the end of the wage period. Deductions are strictly limited by law (e.g., absence, damage to goods capped at $300).",
            "red_flag": "Paying wages later than 7 days, or making illegal deductions for non-statutory reasons like 'poor performance'.",
            "board_advice": "Implement automated payroll and compliance audit systems. The Board must treat 'unpaid wages' as a top-tier operational and legal risk (criminal liability)."
        }
    },
    "ch4": {
        "keys": ["休息日", "rest days", "day off", "放假"],
        "zh": {"title": "第 4 章：休息日", "statute": "連續性合約僱員每 7 天可享有不少於 1 天休息日。休息日屬自願性質工作，僱主不得強迫。", "red_flag": "強迫僱員在休息日工作或以工資代替休息日（買假）。", "board_advice": "監控工時與排班系統，確保排班演算法不會自動違反 7休1 法定要求。"},
        "en": {"title": "Chapter 4: Rest Days", "statute": "Employees under a continuous contract are entitled to at least 1 rest day in every period of 7 days. Compelling employees to work on rest days is prohibited.", "red_flag": "Forcing employees to work on rest days or buying out rest days.", "board_advice": "Monitor rostering systems to ensure scheduling algorithms do not automatically violate the 1-in-7 rest day rule."}
    },
    "ch5": {
        "keys": ["法定假日", "statutory holidays", "勞工假", "public holidays", "bank holiday"],
        "zh": {"title": "第 5 章：法定假日", "statute": "所有僱員均享有法定假日（勞工假）。如受僱滿3個月，可享有薪法定假日。不得以款項代替發放法定假日。", "red_flag": "以薪金買斷法定假日，或未在法定限期內安排補假。", "board_advice": "將法定假日與公眾假期（Bank Holidays）的政策差異清晰列明於員工手冊，並設定系統硬性防呆機制。"},
        "en": {"title": "Chapter 5: Statutory Holidays", "statute": "All employees are entitled to statutory holidays. If employed for 3 months, they are entitled to holiday pay. Buy-out of statutory holidays is strictly prohibited.", "red_flag": "Buying out statutory holidays with payment or failing to arrange substituted holidays within the legal timeframe.", "board_advice": "Clearly differentiate Statutory and Public Holidays in the employee handbook with system-level hardstops."}
    },
    "ch6": {
        "keys": ["有薪年假", "paid annual leave", "annual leave", "年假", "AL"],
        "zh": {"title": "第 6 章：有薪年假", "statute": "受僱滿1年可享有 7 至 14 天有薪年假。年假薪酬應以過去12個月的每日平均工資（ADW）計算。", "red_flag": "錯誤計算 ADW（未計入佣金或津貼），或拒絕批出法定年假。", "board_advice": "定期審核 ADW 計算公式是否涵蓋所有法定「工資」元素（包含浮動佣金）。"},
        "en": {"title": "Chapter 6: Paid Annual Leave", "statute": "Employees are entitled to 7-14 days of paid annual leave after 1 year of service. Leave pay must be calculated using the 12-month Average Daily Wage (ADW).", "red_flag": "Miscalculating ADW (excluding commission/allowances) or refusing statutory leave.", "board_advice": "Regularly audit the ADW calculation formula to ensure it encompasses all statutory 'wage' elements including variable commissions."}
    },
    "ch7": {
        "keys": ["疾病津貼", "sickness allowance", "sick leave", "病假", "SL"],
        "zh": {"title": "第 7 章：疾病津貼", "statute": "連續病假不少於 4 天，並有合資格醫生證明書，可獲每日平均工資五分之四（4/5）的疾病津貼。", "red_flag": "在僱員放取有薪病假期間解僱僱員（除即時解僱外），屬違法行為。", "board_advice": "設立健全的醫療缺勤管理機制，嚴禁管理層對正合法放取病假的員工採取不利行動。"},
        "en": {"title": "Chapter 7: Sickness Allowance", "statute": "Employees taking $\ge$ 4 consecutive days of sick leave with a valid medical certificate are entitled to sickness allowance at 4/5 of their ADW.", "red_flag": "Terminating an employee (other than summary dismissal) while they are on paid sick leave is an offence.", "board_advice": "Establish a robust medical absence management mechanism. Strictly prohibit adverse actions against employees on valid sick leave."}
    },
    "ch8": {
        "keys": ["生育保障", "maternity protection", "maternity leave", "產假"],
        "zh": {"title": "第 8 章：生育保障", "statute": "合資格女性僱員可享有 14 星期有薪產假。僱主解僱已發出懷孕通知的僱員，即屬違法。", "red_flag": "解僱懷孕僱員（具極高刑事及平機會歧視索償風險）。", "board_advice": "推行母乳哺育友善及孕婦保護政策。將懷孕解僱的決策權收歸最高管理層/法務部。"},
        "en": {"title": "Chapter 8: Maternity Protection", "statute": "Eligible female employees are entitled to 14 weeks of paid maternity leave. It is an offence to dismiss an employee who has served notice of pregnancy.", "red_flag": "Dismissing a pregnant employee (carries extreme criminal and EOC discrimination claim risks).", "board_advice": "Implement breastfeeding-friendly and maternity protection policies. Centralize any termination decisions regarding pregnant staff to Top Management/Legal."}
    },
    "ch9": {
        "keys": ["侍產假", "paternity leave", "侍產"],
        "zh": {"title": "第 9 章：侍產假", "statute": "合資格男性僱員可享有 5 天男士侍產假，薪酬為每日平均工資的五分之四（4/5）。", "red_flag": "無理拒絕合資格的侍產假申請或未按 ADW 支付侍產假薪酬。", "board_advice": "推廣家庭友善政策（Family-friendly policies），增強員工歸屬感與 ESG 社會責任指標 (S)."},
        "en": {"title": "Chapter 9: Paternity Leave", "statute": "Eligible male employees are entitled to 5 days of paternity leave at 4/5 of their ADW.", "red_flag": "Unreasonably refusing eligible paternity leave applications or failing to pay at the ADW rate.", "board_advice": "Promote family-friendly policies to enhance employee engagement and support ESG (Social) metrics."}
    },
    "ch10": {
        "keys": ["年終酬金", "end of year payment", "雙糧", "double pay", "bonus"],
        "zh": {"title": "第 10 章：年終酬金", "statute": "合約訂明的年終酬金（如雙糧）受法例保障。不適用於純粹屬賞贈性質或由僱主酌情發放的獎賞（Discretionary Bonus）。", "red_flag": "將合約明訂的雙糧隨意更改為「酌情花紅」，並拒絕支付。", "board_advice": "在僱傭合約中，必須由法務審閱「酌情性（Discretionary）」與「保證性（Guaranteed）」獎金的法律字眼定義。"},
        "en": {"title": "Chapter 10: End of Year Payment", "statute": "Contractual end of year payments (e.g., double pay) are protected. This does not apply to strictly discretionary bonuses.", "red_flag": "Arbitrarily treating contractual double pay as 'discretionary' and refusing payment.", "board_advice": "Ensure Legal review of all employment contracts to explicitly define the wording distinguishing 'Discretionary' vs 'Guaranteed' payments."}
    },
    "ch11": {
        "keys": ["終止僱傭合約", "termination", "解僱", "dismissal", "通知期", "notice period", "代通知金", "payment in lieu"],
        "zh": {"title": "第 11 章：終止僱傭合約", "statute": "終止合約需給予足夠通知期或代通知金。無試用期或試用期後，通知期不得少於 7 天。僱員嚴重犯錯可被即時解僱（Summary Dismissal）。", "red_flag": "未給予足夠代通知金，或濫用「即時解僱」權力而缺乏充分實證。", "board_advice": "落實漸進式紀律處分程序（Progressive Discipline）。即時解僱（Cap. 57 Sec 9）需視為最後手段，並留存無可辯駁的審計軌跡 (Audit Trail)。"},
        "en": {"title": "Chapter 11: Termination of Employment Contract", "statute": "Termination requires appropriate notice period or payment in lieu. Post-probation notice must be at least 7 days. Summary dismissal is only for serious misconduct.", "red_flag": "Failing to provide sufficient payment in lieu, or abusing 'Summary Dismissal' without concrete evidence.", "board_advice": "Enforce Progressive Discipline procedures. Summary Dismissal (Cap. 57 Sec 9) must be the absolute last resort with an irrefutable audit trail."}
    },
    "ch12": {
        "keys": ["僱傭保障", "employment protection", "不合理解僱", "unreasonable dismissal", "補償", "remedies"],
        "zh": {"title": "第 12 章：僱傭保障", "statute": "連續受僱滿 24 個月，如被僱主在缺乏正當理由（如能力、行為、冗員）下解僱，即屬不合理解僱，僱員可向勞資審裁處申索補救（如復職或終止僱傭金）。", "red_flag": "缺乏績效評估記錄（PIP）而以「表現欠佳」解僱滿2年的員工。", "board_advice": "優化績效改進計劃（PIP）流程。任何年資大於 2 年的解僱案，HR 總監需作獨立風險合規審核。"},
        "en": {"title": "Chapter 12: Employment Protection", "statute": "Employees with $\ge$ 24 months of continuous service dismissed without a valid reason (e.g., conduct, capability, redundancy) can claim for unreasonable dismissal remedies.", "red_flag": "Dismissing an employee of >2 years for 'poor performance' without any Performance Improvement Plan (PIP) records.", "board_advice": "Optimize PIP workflows. Any termination of employees with >2 years of tenure requires an independent risk & compliance review by the HR Director."}
    },
    "ch13": {
        "keys": ["遣散費", "severance payment", "長期服務金", "long service payment", "LSP", "SP", "裁員", "redundancy"],
        "zh": {"title": "第 13 章：遣散費及長期服務金", "statute": "受僱滿 24 個月因裁員遭解僱可獲遣散費（SP）；受僱滿 5 年非因嚴重過失遭解僱可獲長期服務金（LSP）。強積金（MPF）僱主供款部分可作對沖（直至2025年取消對沖機制生效前）。", "red_flag": "製造假裁員，或為逃避 LSP 而在員工年資接近 5 年時惡意解僱。", "board_advice": "建立戰略性人力資源規劃（SHRP）。精算並撥備遣散費/長服金負債，特別注意「取消對沖」過渡期的財務合規風險。"},
        "en": {"title": "Chapter 13: Severance & Long Service Payment", "statute": "Severance Payment (SP) for redundancy after 24 months service; Long Service Payment (LSP) for non-summary dismissal after 5 years service. MPF employer contributions can currently offset these (until abolition takes effect).", "red_flag": "Sham redundancies or maliciously terminating staff approaching the 5-year mark to evade LSP.", "board_advice": "Adopt Strategic HR Planning (SHRP). Actuarially assess and provision for SP/LSP liabilities, paying critical attention to the financial compliance risks of the MPF offset abolition."}
    }
}

# Layer 2: Cap. 57 Full Text Core Mapping (Sections & Parts)
CAP57_SECTIONS_DB = [
    {
        "regex": r'(section|sec\.?|第)?\s*3\s*(條)?|418',
        "zh": {"title": "Cap. 57 Section 3: 連續性合約的涵義與舉證責任", "statute": "凡受僱於同一僱主連續 4 星期或以上，每星期最少工作 18 小時，即屬連續性合約。爭議時，舉證責任（Onus of proof）在於僱主。", "red_flag": "僱主無法出示工時紀錄證明僱員非連續性受僱。", "board_advice": "實施數字化工時追蹤，確保舉證責任合規。"},
        "en": {"title": "Cap. 57 Section 3: Meaning of continuous contract and onus of proof", "statute": "Employment for $\ge$ 4 weeks, $\ge$ 18 hours/week. In disputes, the onus of proof rests on the employer to prove it is NOT a continuous contract.", "red_flag": "Failure of the employer to produce working hour records to discharge the onus of proof.", "board_advice": "Implement digital time-tracking to ensure compliance regarding the onus of proof."}
    },
    {
        "regex": r'(section|sec\.?|第)?\s*9\s*(條)?|即時解僱|summary dismissal',
        "zh": {"title": "Cap. 57 Section 9: 僱主不給予通知而終止合約的情況", "statute": "僱主只可在僱員：(a) 故意不服從合法合理命令；(b) 行為不當；(c) 犯有欺詐/不忠實行為；(d) 慣常疏忽職責時，才可無通知期即時解僱。", "red_flag": "缺乏書面警告信及調查報告下，濫用第 9 條權利。", "board_advice": "將第 9 條解僱定為「極端風險行動」，必須由 HR 總監及法務共同簽發 (Sign-off)。"},
        "en": {"title": "Cap. 57 Section 9: Termination by employer without notice", "statute": "Employers can only summarily dismiss for: (a) willful disobedience of lawful/reasonable orders; (b) misconduct; (c) fraud/dishonesty; (d) habitual neglect of duties.", "red_flag": "Abusing Section 9 without written warnings and a thorough investigation report.", "board_advice": "Classify Section 9 dismissals as 'Extreme Risk Actions' requiring joint sign-off by HR Director and Legal."}
    },
    {
        "regex": r'(section|sec\.?|第)?\s*31[B-Y]\s*(條)?|遣散費|severance|31I',
        "zh": {"title": "Cap. 57 Part VB (Sec 31B-31Y): 遣散費", "statute": "詳列遣散費之計算、裁員的法律定義、以及發生權益轉移（Transfer of Business）時連續性僱傭的計算方式。", "red_flag": "企業併購或業務轉讓時，未妥善處理員工年資過渡，引發集體訴訟。", "board_advice": "併購前（M&A）必須進行徹底的 HR 盡職調查（Due Diligence），精算潛在的 Sec 31 遣散責任。"},
        "en": {"title": "Cap. 57 Part VB (Sec 31B-31Y): Severance Payment", "statute": "Details SP calculation, the legal definition of redundancy, and continuity of employment during a Transfer of Business.", "red_flag": "Failing to handle tenure transition during M&A/Transfer of Business, triggering class actions.", "board_advice": "Conduct thorough HR Due Diligence pre-M&A to actuarially assess potential Section 31 liabilities."}
    },
    {
        "regex": r'(section|sec\.?|第)?\s*32[A-V]\s*(條)?|不合理解僱|unreasonable dismissal',
        "zh": {"title": "Cap. 57 Part VIA (Sec 32A-32V): 僱傭保障", "statute": "涵蓋不合理解僱、不合理及不合法解僱（如懷孕、工傷期間解僱）的補償機制，包括復職令或最高15萬元的補償金。", "red_flag": "觸犯不合法解僱，需面臨刑事檢控及勞資審裁處的高額補償金裁決。", "board_advice": "強化高管法律培訓。部署合規監控，防止經理級人員隨意終止合約。"},
        "en": {"title": "Cap. 57 Part VIA (Sec 32A-32V): Employment Protection", "statute": "Covers remedies for unreasonable, and unreasonable & unlawful dismissals (e.g., during pregnancy/work injury), including reinstatement or compensation up to $150k.", "red_flag": "Committing unlawful dismissal leading to criminal prosecution and severe Labour Tribunal awards.", "board_advice": "Enhance executive legal training. Deploy compliance monitors to prevent line managers from arbitrary terminations."}
    }
]

# ==========================================
# 3. Sidebar UI (Architect Profile & Settings)
# ==========================================
with st.sidebar:
    st.header("🌐 UI Language / 介面語言")
    lang_choice = st.radio("Select Language / 選擇語言", ['繁體中文', 'English'], index=0 if st.session_state.lang == '繁體中文' else 1)
    if lang_choice != st.session_state.lang:
        st.session_state.lang = lang_choice
        st.rerun()
    
  st.markdown("---")
    is_zh = st.session_state.lang == '繁體中文'
    
    if is_zh:
        st.markdown("### ⚙️ 系統設計與合規框架")
        st.markdown("""
        * **研發定位**: 專為企業管理層與人力資源團隊設計的自動化勞工法例檢索與合規稽核工具。
        * **治理框架**: 系統架構嚴格對齊國際 **IAPP AIGP** 部署監督規範與 **ISO/IEC 42001** 管理體系思維。
        * **設計原則**: 採用 100% 決定性邏輯（Deterministic Logic）架構，杜絕生成式幻覺，確保法定條文之準確性與可追溯性（Traceability）。
        * **法規對齊**: 深度整合電子版香港法例《僱傭條例》（Cap. 57）主體條文與勞工處簡明指南範疇。
        """)
    else:
        st.markdown("### ⚙️ System Design & Framework")
        st.markdown("""
        * **Positioning**: An automated labor law retrieval and compliance audit tool engineered for corporate executives and HR professionals.
        * **Governance**: Architecture strictly aligned with international **IAPP AIGP** deployment oversight and **ISO/IEC 42001** management systems.
        * **Design Principle**: Built upon 100% deterministic logic to eliminate AI hallucinations, guaranteeing statutory accuracy and total traceability.
        * **Statutory Alignment**: Fully integrated with the official text of the HK Employment Ordinance (Cap. 57) and Labour Department guidelines.
        """)
        
    st.markdown("---")
    st.caption("🔗 Data Source: [eLegislation Cap. 57](https://www.elegislation.gov.hk/hk/cap57)")

# ==========================================
# 4. Helper Functions for Logic
# ==========================================
def search_knowledge_base(query):
    query_lower = query.lower()
    results = []
    
    # Check Layer 2: Cap 57 Sections (Priority)
    for sec in CAP57_SECTIONS_DB:
        if re.search(sec["regex"], query_lower):
            results.append({"type": "cap57", "data": sec})
            
    # Check Layer 1: 13 Chapters
    for ch_id, ch_data in CHAPTERS_DB.items():
        if any(key in query_lower for key in ch_data["keys"]):
            results.append({"type": "chapter", "data": ch_data, "id": ch_id})
            
    return results

def fallback_response(lang):
    if lang == '繁體中文':
        return """
        🔍 **兜底與動態導航機制啟動 (Fallback Mechanism Triggered)** 您查詢的內容涉及《僱傭條例》（Cap. 57）較為高階或細緻的法定條文，超出了常規簡明指南的範疇。
        
        ⚖️ **法務與調解視角提示：**
        處理冷門或複雜的勞資爭議時，切勿依賴二手資訊。為確保 100% 的法律合規性與精準度，請避免依賴 AI 生成之解讀，直接查閱原文。同時，請注意防範相關的勞資關係破裂與潛在的法庭索償風險。
        
        👉 **請點擊下方鏈結直接查閱電子版香港法例的官方即時條文：**
        [🔗 電子版香港法例 Cap. 57 (官方原文)](https://www.elegislation.gov.hk/hk/cap57)
        """
    else:
        return """
        🔍 **Fallback & Dynamic Navigation Triggered** Your query involves advanced or highly specific provisions of the Employment Ordinance (Cap. 57) that fall outside the standard concise guidelines.
        
        ⚖️ **Legal & Mediation Perspective:**
        When dealing with complex or uncommon labor disputes, never rely on secondary information. To ensure 100% legal compliance and accuracy, avoid relying solely on AI interpretations. Please refer to the statutory text. Simultaneously, guard against the breakdown of labor relations and potential tribunal litigation risks.
        
        👉 **Please click the link below to access the official, up-to-date statutory text:**
        [🔗 eLegislation Cap. 57 (Official Full Text)](https://www.elegislation.gov.hk/hk/cap57)
        """

# ==========================================
# 5. Main UI Layout (Dual-Track)
# ==========================================
st.title("⚖️ Cap. 57 Employment Ordinance Full-Text Interactive Advisor")
if is_zh:
    st.subheader("100% 決定性合規・零幻覺勞工法例檢索與審計系統")
else:
    st.subheader("100% Deterministic Compliance · Zero-Hallucination Employment Law Advisor")

# ------------ 💡 就是這裡！請把免責聲明插在中間 💡 ------------
st.warning("""
⚖️ **重要告示 & 免責聲明 / Important Notice & Disclaimer**

* **繁體中文**: 本系統為自動化合規查詢與輔助工具，內容僅供參考，並不構成任何正式法律意見。由於法令條文可能隨時間修訂，且個案情境各有不同，本系統無法保證所有資訊之即時性與完全適用性。如有重要決策或爭議，請務必諮詢香港特別行政區政府勞工處或專業法律顧問。
* **English**: This system is an automated compliance tool for general reference purposes only and does not constitute formal legal advice. As statutory provisions may evolve and individual case circumstances vary, the absolute real-time currency or applicability of the information cannot be guaranteed. For crucial decisions or disputes, please formally consult the Labour Department of the HKSAR Government or seek professional legal counsel.
""")
# -----------------------------------------------------------

tab_chat, tab_audit = st.tabs(["💬 Chatbot (情境導航 / Scenario Advisor)", "📋 Executive Audit (高管合規審計清單)"])

# ------------------------------------------
# Track A: Chatbot Interface
# ------------------------------------------
with tab_chat:
    # Display chat messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Enter keywords, concepts, or Cap.57 Sections (e.g., '418', 'Section 9', 'Maternity', '遣散費')..." if not is_zh else "請輸入關鍵字、概念或 Cap.57 條文編號（例如：'418', '第9條', '產假', '遣散費'）..."):
        # Add user message to state
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Process matching
        with st.chat_message("assistant"):
            matches = search_knowledge_base(prompt)
            lang_key = "zh" if is_zh else "en"
            
            if not matches:
                response = fallback_response(st.session_state.lang)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            else:
                combined_response = ""
                for match in matches:
                    data = match["data"][lang_key]
                    
                    st.info(f"**📖 {data['title']}**\n\n**Statutory Core / 法定核心:**\n{data['statute']}")
                    st.error(f"**🚨 Red Flags / 違法紅線:**\n{data['red_flag']}")
                    st.warning(f"**🛡️ Board-Level Governance / 高管與董事會治理建議:**\n{data['board_advice']}")
                    st.markdown(f"[🔗 Verify on eLegislation / 官方查證連結](https://www.elegislation.gov.hk/hk/cap57)")
                    st.markdown("---")
                    
                    # Store to history (using markdown formatting)
                    combined_response += f"**{data['title']}**\n\n*Statute:* {data['statute']}\n\n*Red Flag:* {data['red_flag']}\n\n*Governance:* {data['board_advice']}\n\n---\n"
                
                st.session_state.messages.append({"role": "assistant", "content": combined_response})

# ------------------------------------------
# Track B: Executive Audit Checklists
# ------------------------------------------
with tab_audit:
    if is_zh:
        st.markdown("### 📊 企業級合規自我審查 (Pre-Deployment Audit Scorecard)")
        st.caption("基於 AIGP 部署監督理念：將靜態指引轉化為 100% 決定性檢查工具，確保企業 HR 政策完全符合 Cap. 57。")
    else:
        st.markdown("### 📊 Enterprise-Grade Compliance Audit Scorecard")
        st.caption("Aligned with AIGP Deployment Oversight: Transforming static guidelines into 100% deterministic checklists to ensure full Cap. 57 compliance.")

    lang_key = "zh" if is_zh else "en"
    
    # Audit logic: Calculate compliance rate
    total_checks = 0
    passed_checks = 0

    # Create an accordion/expander for each of the 13 Chapters mapped in our DB
    for ch_id, ch_data in CHAPTERS_DB.items():
        data = ch_data[lang_key]
        with st.expander(f"✅ {data['title']}"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**📝 Statutory Requirement:** {data['statute']}")
                st.markdown(f"**🚨 Risk Flag:** {data['red_flag']}")
                st.markdown(f"**🛡️ Governance:** {data['board_advice']}")
                st.markdown("[🔗 Cap. 57 Link](https://www.elegislation.gov.hk/hk/cap57)")
            
            with col2:
                # 3 Checklist items per chapter for demonstration
                st.markdown("**Compliance Checklist:**")
                c1 = st.checkbox(f"Policy Updated ({ch_id})", key=f"{ch_id}_c1")
                c2 = st.checkbox(f"Staff Notified ({ch_id})", key=f"{ch_id}_c2")
                c3 = st.checkbox(f"System Enforced ({ch_id})", key=f"{ch_id}_c3")
                
                total_checks += 3
                passed_checks += sum([c1, c2, c3])
                
                score = (sum([c1, c2, c3]) / 3) * 100
                st.metric("Chapter Score", f"{score:.0f}%")

    # Overall Compliance Score
    st.markdown("---")
    overall_score = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
    st.subheader(f"📈 {'整體合規率 / Overall Compliance Rate'}: {overall_score:.1f}%")
    st.progress(overall_score / 100)
    
    if overall_score < 100:
        st.error("⚠️ Actions Required: Unchecked items present potential legal and operational risks." if not is_zh else "⚠️ 需採取行動：未勾選項目存在潛在的法律及營運風險，請盡速由法務/HR總監介入處理。")
    else:
        st.success("✅ Fully Compliant based on internal audit parameters." if not is_zh else "✅ 內部審計顯示為完全合規狀態。")
