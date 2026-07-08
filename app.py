# ==========================================
# 4. 輔助函式與「高危法務路徑」硬阻斷護欄 (Guardrails & Legal Diagnostics)
# ==========================================
# 💡 修正阻斷清單，避免與「補償、薪酬」等常規 HR 詞彙發生碰撞
OUT_OF_SCOPE_WORDS = ["稅務", "immigration", "強積金投資", "mpf investment", "入境處", "簽證", "visa", "移民", "報稅"]

def check_out_of_scope(query):
    query_lower = query.lower()
    return any(word in query_lower for word in OUT_OF_SCOPE_WORDS)

# 💡 核心硬化：升級高危路徑硬阻斷引擎（新增工傷期解僱刑事紅線）
def diagnose_high_risk_breach(query):
    query_lower = query.lower()
    
    # ------------------------------------------
    # 軌道一：孕期解僱硬阻斷 (保持不變)
    # ------------------------------------------
    pregnancy_signals = ["懷孕", "大肚", "pregnant", "有咗", "產檢", "醫生證明"]
    termination_signals = ["解僱", "炒", "離職", "代通知金", "裁員", "辭退", "fire", "terminate", "dismiss", "炒人"]
    if any(p in query_lower for p in pregnancy_signals) and any(t in query_lower for t in termination_signals):
        if not any(ex in query_lower for ex in ["偷", "打架", "犯法", "欺詐", "steal", "打交"]):
            if st.session_state.lang == '繁體中文':
                return "❌ **【最高級別合規危機：孕期解僱決策絕對不可行！】** 🛑\n\n根據香港《僱傭條例》(Cap. 57) 第 15 條，解僱懷孕僱員即屬違法，多給代通知金無法豁免刑事責任，最高可被罰款 HK$100,000[cite: 2]。"
            else:
                return "❌ **【CRITICAL BREACH: PREGNANCY TERMINATION INFEASIBLE!】** 🛑"

    # ------------------------------------------
    # 💡 軌道二：最新增設：工傷假解僱硬阻斷（交叉審計 Cap. 57 & Cap. 282）
    # ------------------------------------------
    work_injury_signals = ["工傷", "工傷假", "判傷", "工作受傷", "補償條例", "injury at work"]
    
    if any(w in query_lower for w in work_injury_signals) and any(t in query_lower for t in termination_signals):
        # 排除符合 Section 9 即時解僱的極端犯罪行為
        if any(ex in query_lower for ex in ["偷", "打架", "犯法", "欺詐", "steal", "打交"]):
            return None
            
        if st.session_state.lang == '繁體中文':
            return """
            ❌ **【最高級別合規危機：工傷期終止合約方案絕對不可行！】** 🛑
            
            ⚖️ **法律定性：觸犯刑事罪行 (Criminal Offence)**
            * **跨條例核心法規：** 根據香港《僱員補償條例》(Cap. 282) 第 48 條及《僱傭條例》(Cap. 57) 第 41 條，在僱員遭遇工傷並在其合法的工傷病假期間（即尚未與僱員達成工傷補償協議，或尚未獲發評估證明書/判傷證明書前），僱主終止其僱傭合約即屬違法。
            * **致命誤區：** 董事會層面以為「表現不達標 / KPI 未滿」且「給足一個月代通知金 + 現金折算年假」就能合法解僱，這是極其嚴重的法理盲區。**民事金錢補償與代通知金，在香港成文法下完全無法豁免或對沖工傷保護的刑事責任**。
            
            🚨 **董事會與企業面臨的嚴重後果：**
            1. **刑事檢控與巨額罰款 (Criminal Prosecution & Fines)：** 僱主在工傷期解僱員工屬於刑事罪行。一經定罪，公司及**同意該決策的董事會責任人**最高可被罰款 **HK$100,000**[cite: 1, 2]。
            2. **民事強制性補償責任：** 僱主必須在終止合約後 7 天內，額外向員工支付：一個月代通知金作為賠償、一筆相等於 7 天工資的法定補償金，以及其在工傷期內應得的所有工傷病假津貼。
            3. **平機會與司法申索：** 若解僱伴隨對其工傷殘疾的歧視，員工可透過《殘疾歧視條例》提出申索，董事會須面臨極高昂且 uncapped（無上限）的精神受損賠償訴訟。
            
            🛡️ **法律與管治專家緊急替代方案 (Pivot Actions)：**
            * 董事會必須**立即終止並撤回**該一攬子解僱方案！
            * 企業必須容許該店鋪主管繼續放取合法的工傷假期，直至勞工處正式簽發工傷評估證明書（兩份條例下要求的正式判傷結果落實）且工時補償程序全部完結為止[cite: 1, 2]。
            * 10 天累積年假繼續保留在系統內。在工傷假期間，**不能強行以現金買斷**其法定大假，必須等其工傷期滿復工後，再安排其放取年假或在離職時進行合法清算[cite: 1, 2]。
            """
        else:
            return """
            ❌ **【CRITICAL BREACH: DISMISSAL DURING WORK INJURY PERIOD ABSOLUTELY INFEASIBLE!】** 🛑
            
            ⚖️ **Legal Rationale: Criminal Offence Triggered**
            * **Statutory Provision:** Under Section 48 of the Employees' Compensation Ordinance (Cap. 282) and Cap. 57, it is a criminal offence for an employer to terminate an employment contract before a work injury compensation agreement has been entered into or before a certificate of assessment is issued[cite: 1, 2].
            * **Fatal Fallacy:** Enhanced financial compensation or payment in lieu of notice **cannot contract out or immunize individual directors and management from criminal liabilities** under HKSAR statutory law[cite: 1, 2].
            
            🚨 **Severe Consequences:**
            1. **Criminal Prosecution:** Conviction carries a maximum corporate/personal fine of **HK$100,000**[cite: 1, 2].
            2. **Mandatory Civil Compensations:** Statutory penalties include notice pay plus an additional 7 days' wages as statutory compensation.
            
            🛡️ **Urgent Governance Pivot:**
            * The Board must **immediately revoke** the termination proposal. 
            * Freeze all actions until the Labour Department issues the formal Certificate of Assessment and all statutory injury proceedings are fully discharged[cite: 1, 2].
            """
            
    # --- 軌道三：最新「468機制」四週工時動態數字審計 (保持不變) ---
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
    if len(extracted_hours) == 4 or any(k in query_lower for k in ["舊418", "舊 418", "卡418", "卡 418", "卡他"]):
        w1, w2, w3, w4 = extracted_hours if len(extracted_hours) == 4 else (0,0,0,0)
        total_hours = sum(extracted_hours) if len(extracted_hours) == 4 else 0
        if total_hours >= 68 or any(k in query_lower for k in ["舊418", "舊 418", "卡418", "卡 418", "卡他"]):
            if st.session_state.lang == '繁體中文':
                calc_details = f"（第一週 {w1} 小時 + 第二週 {w2} 小時 + 第三週 {w3} 小時 + 第四週 {w4} 小時 = 總共 {total_hours} 小時）" if len(extracted_hours) == 4 else ""
                return f"🛑 **【高危法務警報：該名兼職員工已 100% 觸發連續性合約！】** ❌\n\n實質總工時：{calc_details}。最新 468 修訂放寬了限制，主管若繼續用舊 418 卡人拒發福利，每項一經定罪最高可被罰款港幣 5 萬元[cite: 1, 2]。"
            else:
                return f"🛑 **【COMPLIANCE BREACH: EMPLOYEE QUALIFIES UNDER 468 RULE!】** ❌"
                
    return None
