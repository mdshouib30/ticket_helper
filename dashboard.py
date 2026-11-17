import json
import os
import threading
import urllib.request
from datetime import date, datetime

import pandas as pd
import streamlit as st

from src import database, knowledge
from src.pipeline import process_ticket
from src.replier import FAQ_THRESHOLD

# ---------- Settings ----------
DEMO_MODE = os.getenv("DEMO_MODE", "false").strip().lower() == "true"
SESSION_LIMIT = int(os.getenv("SESSION_LIMIT", "5"))  # checks per visit
DAILY_LIMIT = int(os.getenv("DAILY_LIMIT", "100"))  # checks per day, all visitors
MAX_CHARS = 500

st.set_page_config(page_title="Support Ticket Helper", page_icon="🎫", layout="wide")
if not DEMO_MODE:
    database.init_db()

st.markdown(
    """
    <style>
    [data-testid="stMetric"] {
        background-color: rgba(120, 120, 200, 0.08);
        border: 1px solid rgba(120, 120, 200, 0.25);
        border-radius: 12px;
        padding: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

CATEGORY_LABEL = {
    "billing": "💳 Billing",
    "technical": "🛠️ Technical problem",
    "refund": "↩️ Refund or return",
    "general": "💬 General question",
}
URGENCY_LABEL = {"high": "🔴 Urgent", "medium": "🟡 Medium", "low": "🟢 Not urgent"}
ACTION_LABEL = {
    "SEND TO HUMAN": "🧑 Needs a person",
    "AUTO-REPLY": "✅ Safe to send",
}
HANDLED_LABEL = {
    "RULES": "A simple rule (no AI)",
    "AI": "The AI",
    "AI unavailable": "Nobody (the AI was busy)",
}

EXAMPLES = [
    "Do you deliver abroad?",
    "I was charged twice this month!",
    "Please unsubscribe me from your emails.",
    "Do you sell gift cards?",
]


# ---------- Helpers ----------
def ai_status():
    """Return (is_ok, text) for the status light in the sidebar."""
    base = os.getenv("LLM_BASE_URL", "")
    if "localhost" in base or "127.0.0.1" in base:
        try:
            urllib.request.urlopen(base.split("/v1")[0], timeout=2)
            return True, "The local AI (Ollama) is running"
        except Exception:
            return False, "The local AI is not running. Run: ollama serve"
    if os.getenv("LLM_API_KEY"):
        return True, "The online AI is configured"
    return False, "No AI key found. Check the settings"


@st.cache_resource
def _usage():
    return {"lock": threading.Lock(), "day": "", "count": 0}


def try_use_quota():
    """Count one use. Return a message if a limit is reached, otherwise None."""
    if not DEMO_MODE:
        return None
    if st.session_state.get("uses", 0) >= SESSION_LIMIT:
        return (
            f"You have used all {SESSION_LIMIT} free checks for this visit. "
            "Thank you for trying the demo!"
        )
    usage = _usage()
    with usage["lock"]:
        today = date.today().isoformat()
        if usage["day"] != today:
            usage["day"] = today
            usage["count"] = 0
        if usage["count"] >= DAILY_LIMIT:
            return "The demo reached its daily limit. Please come back tomorrow."
        usage["count"] += 1
    st.session_state["uses"] = st.session_state.get("uses", 0) + 1
    return None


def get_tickets():
    if DEMO_MODE:
        return list(reversed(st.session_state.get("my_tickets", [])))
    return database.list_tickets(limit=500)


def use_example(text: str):
    st.session_state["ticket_text"] = text


def load_samples():
    with open("output/results.json") as f:
        samples = json.load(f)
    for sample in samples:
        data = dict(sample)
        data.setdefault("reply_source", "Sample ticket")
        database.save_ticket(data)


def show_result(data: dict):
    if data["action"] == "SEND TO HUMAN":
        st.warning(
            f"**Next step: a team member should check this ticket.**\n\n{data['why']}"
        )
    else:
        st.success("**Next step: this reply is safe to send automatically.**")

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"**Type of problem**\n\n{CATEGORY_LABEL[data['category']]}")
    c2.markdown(f"**How urgent**\n\n{URGENCY_LABEL[data['urgency']]}")
    c3.markdown(
        f"**Handled by**\n\n{HANDLED_LABEL.get(data['sorted_by'], data['sorted_by'])}"
    )

    with st.container(border=True):
        st.markdown("**Suggested reply**")
        st.write(data["reply"])
        st.caption(f"Where this reply came from: {data['reply_source']}")
    st.caption(f"Why it was sorted this way: {data['reason']}")


# ---------- Sidebar ----------
st.sidebar.title("🎫 Ticket Helper")
st.sidebar.caption("Sorts customer messages and suggests replies.")
status_ok, status_text = ai_status()
if status_ok:
    st.sidebar.success(f"🟢 {status_text}")
else:
    st.sidebar.error(f"🔴 {status_text}")
checks_box = st.sidebar.empty()
st.sidebar.divider()
st.sidebar.markdown("**Colors**\n\n🔴 urgent  \n🟡 medium  \n🟢 not urgent")

# ---------- Header ----------
st.title("🎫 Support Ticket Helper")
st.caption(
    "Paste a customer message and get a category, an urgency, and a suggested reply."
)

if DEMO_MODE:
    st.info(
        "**Public demo.** The company facts and tickets are made up. "
        "Please do not type personal information. Nothing you type is saved "
        f"after you leave. You get {SESSION_LIMIT} free checks per visit."
    )

tab_check, tab_all, tab_faq, tab_help = st.tabs(
    [
        "✨ Check a ticket",
        "📋 My tickets" if DEMO_MODE else "📋 All tickets",
        "📚 Help center (FAQ)",
        "ℹ️ How it works",
    ]
)

# ---------- Tab 1: check a ticket ----------
with tab_check:
    st.subheader("Check a customer message")
    st.write("Type a message from a customer, or click an example.")

    example_cols = st.columns(len(EXAMPLES))
    for col, text in zip(example_cols, EXAMPLES):
        col.button(text, on_click=use_example, args=(text,), key=f"example_{text}")

    message = st.text_area(
        "Customer message",
        key="ticket_text",
        height=110,
        max_chars=MAX_CHARS,
        placeholder="Type or paste a customer message here...",
    )

    if st.button("Check this ticket", type="primary"):
        if not message.strip():
            st.warning("Please type a message first.")
        else:
            limit_message = try_use_quota()
            if limit_message:
                st.warning(limit_message)
            else:
                try:
                    with st.spinner("Working on it. This can take up to a minute..."):
                        data = process_ticket(message.strip())
                        if DEMO_MODE:
                            mine = st.session_state.setdefault("my_tickets", [])
                            data["id"] = len(mine) + 1
                            data["created_at"] = datetime.now().isoformat(
                                timespec="seconds"
                            )
                            mine.append(data)
                        else:
                            data["id"] = database.save_ticket(data)
                    st.session_state["last_result"] = data
                except Exception as exc:
                    st.session_state.pop("last_result", None)
                    st.error(
                        "Something went wrong. The AI may be busy. "
                        "Please try again in a minute."
                    )
                    st.caption(f"Technical details: {exc}")

    if "last_result" in st.session_state:
        st.divider()
        last = st.session_state["last_result"]
        show_result(last)
        if DEMO_MODE:
            st.caption("This result is shown only to you and is not saved.")
        else:
            st.caption(f"Saved as ticket #{last['id']}")

# ---------- Tab 2: tickets ----------
with tab_all:
    tickets = get_tickets()

    if not tickets:
        st.info("No tickets yet. Check one in the first tab.")
        if not DEMO_MODE and os.path.exists("output/results.json"):
            if st.button("Load the sample tickets"):
                load_samples()
                st.rerun()
    else:
        df = pd.DataFrame(tickets)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Tickets", len(df))
        m2.metric("Need a person", int((df["action"] == "SEND TO HUMAN").sum()))
        m3.metric("Handled without AI", int((df["sorted_by"] == "RULES").sum()))
        m4.metric("Urgent", int((df["urgency"] == "high").sum()))

        f1, f2, f3 = st.columns([2, 2, 1])
        search = f1.text_input("Search messages", placeholder="Type a word...")
        urgency_choice = f2.multiselect(
            "Urgency",
            ["high", "medium", "low"],
            default=["high", "medium", "low"],
            format_func=lambda value: URGENCY_LABEL[value],
        )
        only_person = f3.checkbox("Only needs a person")

        view = df[df["urgency"].isin(urgency_choice)]
        if search.strip():
            view = view[
                view["message"].str.contains(
                    search.strip(), case=False, na=False, regex=False
                )
            ]
        if only_person:
            view = view[view["action"] == "SEND TO HUMAN"]

        if view.empty:
            st.info("No tickets match your search or filters.")
        else:
            table = pd.DataFrame(
                {
                    "#": view["id"],
                    "When": view["created_at"],
                    "Message": view["message"],
                    "Type": view["category"].map(CATEGORY_LABEL),
                    "Urgency": view["urgency"].map(URGENCY_LABEL),
                    "Next step": view["action"].map(ACTION_LABEL),
                }
            )
            st.dataframe(table, hide_index=True)
            st.download_button(
                "Download as CSV",
                table.to_csv(index=False).encode("utf-8"),
                "tickets.csv",
                "text/csv",
            )

            st.subheader("Open a ticket")
            chosen = st.selectbox("Pick a ticket number", [int(i) for i in view["id"]])
            data = next(t for t in tickets if t["id"] == chosen)
            st.write(f"**Customer wrote:** {data['message']}")
            show_result(data)

# ---------- Tab 3: FAQ ----------
with tab_faq:
    st.write(
        "This is the notebook of true facts. The reply writer may only use "
        "facts from here."
    )

    if st.session_state.pop("faq_added", False):
        st.success("FAQ added. The search now uses it.")

    st.subheader(f"Help center ({len(knowledge.FAQ)} entries)")
    st.dataframe(
        [
            {"#": item["id"], "Question": item["question"], "Answer": item["answer"]}
            for item in knowledge.FAQ
        ],
        hide_index=True,
    )

    st.subheader("Test the search")
    st.caption("Type a customer message and see which FAQ page the search picks.")
    test_message = st.text_input(
        "Customer message", key="faq_test", max_chars=MAX_CHARS
    )
    if test_message.strip() and st.session_state.get("last_faq_test") != test_message:
        st.session_state["last_faq_test"] = test_message
        st.session_state["faq_limit_message"] = try_use_quota()
        st.session_state["faq_test_result"] = None
        if not st.session_state["faq_limit_message"]:
            try:
                with st.spinner("Searching..."):
                    st.session_state["faq_test_result"] = knowledge.best_faq(
                        test_message
                    )
            except Exception as exc:
                st.session_state["faq_limit_message"] = (
                    f"Could not search right now. Please try again in a minute. ({exc})"
                )

    if test_message.strip():
        if st.session_state.get("faq_limit_message"):
            st.warning(st.session_state["faq_limit_message"])
        elif st.session_state.get("faq_test_result"):
            match, score = st.session_state["faq_test_result"]
            st.progress(max(0.0, min(1.0, score)))
            st.write(f"**Best match:** {match['question']}")
            st.write(f"**Score:** {score:.2f} (needs {FAQ_THRESHOLD:.2f} or more)")
            if score >= FAQ_THRESHOLD:
                st.success(
                    f"Good match. The reply will use this fact: {match['answer']}"
                )
            else:
                st.warning(
                    "No good match. The customer gets the standard "
                    "'a team member will follow up' reply."
                )

    if DEMO_MODE:
        st.caption("Editing the help center is turned off in the public demo.")
    else:
        st.subheader("Add a new FAQ")
        with st.form("add_faq", clear_on_submit=True):
            new_question = st.text_input("Question")
            new_answer = st.text_area("Answer")
            submitted = st.form_submit_button("Add to the help center")

        if submitted:
            if not new_question.strip() or not new_answer.strip():
                st.warning("Please fill in both the question and the answer.")
            else:
                new_id = max([item["id"] for item in knowledge.FAQ], default=0) + 1
                updated = knowledge.FAQ + [
                    {
                        "id": new_id,
                        "question": new_question.strip(),
                        "answer": new_answer.strip(),
                    }
                ]
                with open("data/faq.json", "w") as f:
                    json.dump(updated, f, indent=2)
                knowledge.reload_faq()
                st.session_state["faq_added"] = True
                st.rerun()

# ---------- Tab 4: how it works ----------
with tab_help:
    st.subheader("How it works")
    st.markdown(
        """
        1. **A simple rule** checks the message first. Easy questions like "unsubscribe"
           are answered without any AI.
        2. **The AI** decides the type of problem and how urgent it is.
        3. **The help center** is searched for a true fact. The reply may only use that fact.
        4. **A safety check** decides if the reply can be sent or if a person should look first.
        """
    )

    st.subheader("When does a person check a ticket?")
    st.markdown(
        """
        - The customer is **urgent** (blocked or losing money).
        - The ticket is about **money** (billing or a refund).
        - The reply contains a **number or time** that must be checked.
        - The reply contains a word like **"guarantee"** or **"promise"**.
        - The AI was **busy**, so nobody could sort the ticket.
        """
    )

    st.subheader("Good to know")
    st.markdown(
        """
        - The tickets and the help center facts are **made up** for this demo.
        - If the AI is busy, the system fails safe: a person is asked to look.
        """
    )
    if DEMO_MODE:
        st.markdown("- In the public demo, nothing you type is stored after you leave.")

# ---------- Sidebar footer (updated after any check) ----------
if DEMO_MODE:
    left = max(0, SESSION_LIMIT - st.session_state.get("uses", 0))
    checks_box.caption(f"Free checks left in this visit: {left}")
