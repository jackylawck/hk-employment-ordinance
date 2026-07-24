"""
AIGP 随身考官 2026 — Streamlit App
Fixes: cache pollution, bank-switch state reset, answer-parse stripping,
       revealed-state persistence, exception handling.
New features: Score tracker, Mistake tracker, Quick jump, Retry question.
Requires: streamlit >= 1.28
"""

import json
import os
import streamlit as st

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────
QUESTION_BANKS: dict[str, str] = {
    "📋 官方模拟题 v2":         "questions/official_mock_v2.json",
    "🔥 2026 情景题":           "questions/current_2026_scenarios.json",
    "🧠 AI 基础练习":           "questions/ai_foundations_practice.json",
    "📖 深度参考题":            "questions/references_deep_dive.json",
}

REQUIRED_FIELDS = {"question", "options", "answer"}
PASS_THRESHOLD  = 0.75          # 75 % = AIGP pass line


# ──────────────────────────────────────────────
# Data loading (cached with TTL to avoid stale data)
# ──────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_questions(filepath: str) -> tuple[list, str | None]:
    """
    Load and validate a JSON question bank.
    Returns (questions_list, error_message).
    error_message is None on success.
    """
    abs_path = os.path.join(os.path.dirname(__file__), filepath)

    # 1. File existence
    if not os.path.exists(abs_path):
        return [], f"❌ 找不到题库文件：`{filepath}`\n请确认文件已放入 `questions/` 目录。"

    # 2. File size
    if os.path.getsize(abs_path) == 0:
        return [], f"❌ 题库文件为空：`{filepath}`"

    # 3. Permission
    try:
        with open(abs_path, "r", encoding="utf-8-sig") as f:
            raw = f.read()
    except PermissionError:
        return [], f"❌ 无权限读取文件：`{filepath}`\n请检查文件权限设置。"
    except UnicodeDecodeError:
        return [], (
            f"❌ 编码错误：`{filepath}`\n"
            "请将文件保存为 UTF-8（含或不含 BOM）格式后重试。"
        )
    except OSError as e:
        return [], f"❌ 读取文件时发生系统错误：{e}"

    # 4. JSON parse
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return [], (
            f"❌ JSON 格式错误（`{filepath}`）\n"
            f"错误位置：第 {e.lineno} 行，第 {e.colno} 列\n"
            f"详情：{e.msg}"
        )

    # 5. Top-level type
    if not isinstance(data, list):
        return [], f"❌ 题库格式错误：根节点应为 JSON 数组，当前为 `{type(data).__name__}`。"

    if len(data) == 0:
        return [], f"⚠️ 题库 `{filepath}` 中没有任何题目。"

    # 6. Schema validation per question
    errors: list[str] = []
    valid_questions: list[dict] = []
    for i, q in enumerate(data, start=1):
        if not isinstance(q, dict):
            errors.append(f"  题 {i}：不是 JSON 对象")
            continue
        missing = REQUIRED_FIELDS - q.keys()
        if missing:
            errors.append(f"  题 {i}：缺少字段 {sorted(missing)}")
            continue
        if not isinstance(q.get("options"), list) or len(q["options"]) < 2:
            errors.append(f"  题 {i}：`options` 必须是至少含 2 项的数组")
            continue
        valid_questions.append(q)

    if errors:
        summary = "\n".join(errors[:10])
        tail    = f"\n  …（共 {len(errors)} 条错误）" if len(errors) > 10 else ""
        return valid_questions, (
            f"⚠️ `{filepath}` 中有 {len(errors)} 道题格式有误（已跳过）：\n{summary}{tail}"
        )

    return valid_questions, None


# ──────────────────────────────────────────────
# Session state management
# ──────────────────────────────────────────────
def init_session_state(bank_key: str) -> None:
    """
    Initialise or reset per-bank state when the user switches question banks.
    mistake_log is global (persists across bank switches).
    """
    # Global state (survive bank switches)
    if "mistake_log" not in st.session_state:
        st.session_state.mistake_log: list[dict] = []

    bank_changed = st.session_state.get("current_bank") != bank_key

    if bank_changed or "q_index" not in st.session_state:
        st.session_state.current_bank  = bank_key
        st.session_state.q_index       = 0
        st.session_state.revealed      = {}   # {q_index: True}
        st.session_state.user_answers  = {}   # {q_index: chosen_option_str}
        st.session_state.results       = {}   # {q_index: bool}


def record_mistake(bank_key: str, q: dict, chosen: str, correct: str) -> None:
    """Add a wrong answer to mistake_log (de-duplicated by question text)."""
    existing_texts = {m["question"] for m in st.session_state.mistake_log}
    if q["question"] not in existing_texts:
        st.session_state.mistake_log.append({
            "bank":     bank_key,
            "question": q["question"],
            "chosen":   chosen,
            "correct":  correct,
        })


def get_correct_letter(answer_field: str) -> str:
    """
    Robustly extract the answer letter from formats like:
      'B', 'B:', 'B: Some explanation', ' B ', etc.
    """
    return answer_field.split(":")[0].strip().upper()


# ──────────────────────────────────────────────
# UI helpers
# ──────────────────────────────────────────────
def render_score_sidebar(bank_key: str) -> None:
    """Render score statistics and mistake tracker in the sidebar."""
    st.sidebar.title("📊 得分统计")

    results = st.session_state.get("results", {})
    answered = len(results)
    correct  = sum(1 for v in results.values() if v)
    wrong    = answered - correct

    if answered > 0:
        rate = correct / answered
        st.sidebar.metric("已作答", f"{answered} 题")
        st.sidebar.metric("✅ 正确", f"{correct} 题")
        st.sidebar.metric("❌ 错误", f"{wrong} 题")
        st.sidebar.metric("正确率", f"{rate:.1%}")
        st.sidebar.progress(rate)
        if rate >= PASS_THRESHOLD:
            st.sidebar.success(f"🎉 PASS 水平（≥{PASS_THRESHOLD:.0%}）")
        else:
            st.sidebar.warning(f"📚 继续努力（目标 {PASS_THRESHOLD:.0%}）")
    else:
        st.sidebar.info("尚未作答任何题目")

    st.sidebar.divider()

    # ── Mistake tracker ──────────────────────────────
    st.sidebar.title("📝 错题记录本")
    mistakes = st.session_state.get("mistake_log", [])

    if not mistakes:
        st.sidebar.caption("暂无错题记录 🎯")
    else:
        st.sidebar.caption(f"共 {len(mistakes)} 道错题（跨题库保留）")
        with st.sidebar.expander("查看最近 10 道错题", expanded=False):
            for idx, m in enumerate(reversed(mistakes[-10:]), start=1):
                st.markdown(
                    f"**{idx}.** {m['question'][:60]}…\n\n"
                    f"- 你选：`{m['chosen']}`\n"
                    f"- 正确：`{m['correct']}`\n"
                    f"- 来源：{m['bank']}",
                    unsafe_allow_html=False,
                )
                st.divider()
        if st.sidebar.button("🗑️ 清空错题记录", key="clear_mistakes"):
            st.session_state.mistake_log = []
            st.rerun()

    st.sidebar.divider()
    st.sidebar.caption("AIGP 随身考官 2026 · v2.0")


# ──────────────────────────────────────────────
# Main application
# ──────────────────────────────────────────────
def main() -> None:
    st.set_page_config(
        page_title="AIGP 随身考官 2026",
        page_icon="🎓",
        layout="wide",
    )

    st.title("🎓 AIGP 随身考官 2026")
    st.caption("AI Governance Professional 备考练习平台")

    # ── Bank selection ────────────────────────────
    bank_key = st.selectbox(
        "选择题库",
        options=list(QUESTION_BANKS.keys()),
        key="bank_selector",
    )

    init_session_state(bank_key)

    # ── Load questions ────────────────────────────
    filepath = QUESTION_BANKS[bank_key]
    questions, load_error = load_questions(filepath)

    render_score_sidebar(bank_key)

    if load_error:
        if not questions:
            st.error(load_error)
            st.stop()
        else:
            st.warning(load_error)

    if not questions:
        st.info("该题库暂无有效题目，请选择其他题库或检查文件内容。")
        st.stop()

    total = len(questions)

    # ── Navigation ───────────────────────────────
    col_prev, col_jump, col_next = st.columns([1, 2, 1])

    with col_prev:
        if st.button("⬅️ 上一题", disabled=st.session_state.q_index == 0):
            st.session_state.q_index -= 1
            st.rerun()

    with col_jump:
        jump_to = st.number_input(
            f"跳至题号（1 – {total}）",
            min_value=1,
            max_value=total,
            value=st.session_state.q_index + 1,
            step=1,
            key="jump_input",
        )
        if jump_to - 1 != st.session_state.q_index:
            st.session_state.q_index = jump_to - 1
            st.rerun()

    with col_next:
        if st.button("下一题 ➡️", disabled=st.session_state.q_index == total - 1):
            st.session_state.q_index += 1
            st.rerun()

    st.divider()

    # ── Current question ─────────────────────────
    idx = st.session_state.q_index
    q   = questions[idx]

    st.subheader(f"第 {idx + 1} / {total} 题")
    st.markdown(f"**{q['question']}**")
    st.write("")

    # ── Answer selection ─────────────────────────
    already_answered = idx in st.session_state.results
    previous_choice  = st.session_state.user_answers.get(idx)

    radio_index = None
    if previous_choice and previous_choice in q["options"]:
        radio_index = q["options"].index(previous_choice)

    chosen = st.radio(
        "请选择答案：",
        options=q["options"],
        index=radio_index,
        key=f"radio_{bank_key}_{idx}",
        disabled=already_answered,
    )

    # ── Submit / Retry ───────────────────────────
    btn_col, retry_col = st.columns([3, 1])

    with btn_col:
        submit_clicked = st.button(
            "✅ 提交答案",
            disabled=(chosen is None or already_answered),
            key=f"submit_{bank_key}_{idx}",
        )

    with retry_col:
        retry_clicked = st.button(
            "🔄 重做本题",
            disabled=not already_answered,
            key=f"retry_{bank_key}_{idx}",
        )

    if retry_clicked:
        # Clear this question's state
        st.session_state.results.pop(idx, None)
        st.session_state.user_answers.pop(idx, None)
        st.session_state.revealed.pop(idx, None)
        # Also remove from mistake_log if present
        q_text = q["question"]
        st.session_state.mistake_log = [
            m for m in st.session_state.mistake_log if m["question"] != q_text
        ]
        st.rerun()

    if submit_clicked and chosen is not None:
        correct_letter = get_correct_letter(q["answer"])
        # The option starts with "X: ..." so the chosen letter is the first char
        chosen_letter  = chosen.split(":")[0].strip().upper()
        is_correct     = chosen_letter == correct_letter

        st.session_state.user_answers[idx] = chosen
        st.session_state.results[idx]      = is_correct
        st.session_state.revealed[idx]     = True

        if not is_correct:
            record_mistake(bank_key, q, chosen_letter, correct_letter)

        st.rerun()

    # ── Result feedback ──────────────────────────
    if st.session_state.revealed.get(idx):
        is_correct     = st.session_state.results.get(idx, False)
        correct_letter = get_correct_letter(q["answer"])

        if is_correct:
            st.success("✅ 回答正确！")
        else:
            chosen_str = st.session_state.user_answers.get(idx, "—")
            st.error(f"❌ 回答错误！你选了 `{chosen_str.split(':')[0].strip()}`")

        # Highlight correct answer
        for opt in q["options"]:
            opt_letter = opt.split(":")[0].strip().upper()
            if opt_letter == correct_letter:
                st.info(f"✔️ 正确答案：{opt}")
                break

        # Explanation
        explanation = q.get("explanation", "").strip()
        if explanation:
            with st.expander("📖 解析", expanded=True):
                st.markdown(explanation)

    # ── Progress bar at bottom ───────────────────
    st.divider()
    progress_val = (idx + 1) / total
    st.progress(progress_val, text=f"进度：{idx + 1} / {total}")


# ──────────────────────────────────────────────
if __name__ == "__main__":
    main()
