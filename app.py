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
# 嚴格依據勞工處官方《僱傭條例簡明指南》主體架構與香港本地職場實務編碼
CHAPTERS_DB = {
    "ch1": {
        "keys": ["適用範圍", "application", "scope", "418", "468", "連續性合約", "兼職", "part-time", "散工", "炒散", "自僱", "假自僱", "返工"],
        "zh": {
            "title": "第一章：《僱傭條例》適用範圍與「468」連續性合約",
            "statute": "《僱傭條例》適用於所有受僱於僱傭合約的僱員。有關連續性合約已放寬為現行「468機制」：指僱員連續受僱於同一僱主 4 星期或以上，4 星期內總工作時數滿 68 小時或以上，即屬連續性合約並享有法定福利（如休息日、有薪年假、疾病津貼等）。",
            "red_flag": "錯誤將實質僱傭關係包裝為「獨立承包人（假自僱）」，或刻意打斷工時以惡意規避 468 連續性合約門檻。",
            "gov_advice": "【董事會管治】應立即重新審視兼職與散工的排班策略及工時結算演算法，防範潛在的集體勞資索償風險。\n\n【前線營運提示】請確實記錄兼職員工的上下班時間，切勿口頭要求員工「提早下班」以惡意避開 468 工時門檻。"
        },
        "en": {
            "title": "Chapter 1: Application of the Employment Ordinance & '468' Continuous Contract",
            "statute": "The EO applies to all employees engaged under a contract of employment. A 'continuous contract' (now the 468 rule) means an employee works for the same employer for 4 weeks or more, with at least 68 hours in total over the 4 weeks, entitling them to statutory benefits.",
            "red_flag": "Misclassifying employees as independent contractors (false self-employment) or artificially breaking the 468 continuous contract to evade benefits.",
            "gov_advice": "[Board-Level Governance] Immediately review rostering strategies and time-tracking algorithms for non-standard workforce to mitigate class action risks.\n\n[Line Manager Actions] Ensure accurate time-tracking for part-timers. Do not informally ask staff to clock out early to evade the 468 threshold."
        }
    },
    "ch2": {
        "keys": ["僱傭合約", "contracts of employment", "contract", "合約", "更改合約", "variation", "簽約", "試用期", "probation", "轉制", "減薪", "pay cut", "調職"],
        "zh": {
            "title": "第二章：僱傭合約之訂立與條款變更",
            "statute": "僱傭合約可以書面或口頭訂立。僱主在僱員就職前，必須向僱員詳細說明僱用條件。如無僱員同意，僱主不得單方面更改合約條款。",
            "red_flag": "未經僱員同意單方面更改合約條款（如強制減薪、更改工作地點），構成不合理更改僱傭合約條款。",
            "gov_advice": "【董事會管治】所有合約變更必須落實書面同意（Mutual Consent），制定標準化入職與合約變更 SOP，確保資訊透明度。\n\n【前線營運提示】任何崗位調動或薪酬調整，在系統執行前必須確認已收妥員工親筆簽署的變更同意書。"
        },
        "en": {
            "title": "Chapter 2: Contract of Employment & Variation of Terms",
            "statute": "Contracts can be written or oral. Employers must clearly inform employees of the conditions of employment before employment begins. Unilateral variation of terms is not permitted without consent.",
            "red_flag": "Unilateral variation of contract terms (e.g., pay cut, relocation) without employee consent, constituting unreasonable variation.",
            "gov_advice": "[Board-Level Governance] Ensure all contract variations are documented with mutual written consent. Develop standardized SOPs for onboarding and contract changes.\n\n[Line Manager Actions] Do not implement any relocation or pay adjustment without a signed mutual consent form from the employee."
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
            "statute": "凡按連續性合約受僱，每 7 天可享育不少於 1 天休息日（強迫工作屬違法）。所有僱員均享有法定假日（勞工假）。僱主不得以款項代替發放法定假日（即法律嚴禁「買假」）。",
            "red_flag": "強迫僱員在休息日工作、混淆「銀行假」與「勞工假」，或違法以額外薪金直接買斷法定假日。",
            "gov_advice": "【董事會管治】將法定假日與公眾假期（Bank Holidays）的政策差異清晰列明於員工手冊，並在排班系統中設定硬性防呆機制，防範「七休一」違規。\n\n【前線營運提示】如果因餐飲或零售旺記要求員工在法定假日（勞工假）上班，必須依法在 60 天內安排「另定假日」補假，絕不能用錢「買假」解決。"
        },
        "en": {
            "title": "Chapter 4: Rest Days & Statutory Holidays",
            "statute": "Employees under a continuous contract are entitled to at least 1 rest day in every 7 days (compulsion is an offence). All employees are entitled to statutory holidays. Buy-out of statutory holidays with payment is strictly prohibited by law.",
            "red_flag": "Forcing employees to work on rest days, buying out statutory holidays,
