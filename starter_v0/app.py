from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

import streamlit as st

from chat import run_model_tool_loop, write_transcript
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

ROOT = Path(__file__).resolve().parent
ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"
SYSTEM_PROMPT_PATH = ARTIFACTS_DIR / "system_prompt.md"
TOOLS_PATH = ARTIFACTS_DIR / "tools.yaml"

load_lab_env(ROOT)


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return slug.strip("_") or "run"


def load_prompt_and_tools() -> tuple[str, list[dict[str, object]]]:
    system_prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    tool_declarations = load_tool_declarations(TOOLS_PATH)
    openai_tools = to_openai_tools(tool_declarations)
    return system_prompt, openai_tools


def init_transcript(version: str, provider: str, model: str | None, system_prompt: str, tools_path: str) -> dict[str, object]:
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([safe_slug(version), safe_slug(provider), timestamp])
    artifact_version = build_artifact_version(version, SYSTEM_PROMPT_PATH, TOOLS_PATH)
    return {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_version),
        "provider": provider,
        "model": model,
        "system_prompt": str(SYSTEM_PROMPT_PATH),
        "tools": str(TOOLS_PATH),
        "history_window": 5,
        "max_tool_rounds": 4,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "turns": [],
    }


def append_turn(transcript: dict[str, object], turn_record: dict[str, object]) -> None:
    transcript["turns"].append(turn_record)
    transcript["updated_at"] = datetime.now().isoformat(timespec="seconds")


def load_transcript(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def reset_chat_session(
    version: str,
    provider: str,
    model: str | None,
    system_prompt: str,
    tools_path: str,
) -> None:
    transcript = init_transcript(version, provider, model, system_prompt, tools_path)
    transcript_path = TRANSCRIPTS_DIR / f"{transcript['transcript_id']}.transcript.json"
    st.session_state["transcript"] = transcript
    st.session_state["transcript_path"] = transcript_path
    st.session_state["history"] = []
    st.session_state["provider"] = make_provider(provider)
    st.session_state["current_turn"] = None


def main() -> None:
    st.set_page_config(page_title="Research Agent UI", layout="wide")
    st.title("Research Agent UI")

    with st.sidebar.form(key="config_form"):
        provider_name = st.selectbox("Provider", ["openai", "openrouter", "anthropic", "gemini"], index=0)
        model_override = st.text_input("Model override", value="")
        version_label = st.text_input("Artifact version", value="v1")
        history_window = st.number_input("History window", min_value=1, max_value=20, value=5)
        max_tool_rounds = st.number_input("Max tool rounds", min_value=1, max_value=6, value=4)
        regenerate = st.form_submit_button("Apply config")

    system_prompt, openai_tools = load_prompt_and_tools()
    selected_model = model_override.strip() or None

    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

    if "transcript" not in st.session_state or regenerate:
        reset_chat_session(
            version=version_label,
            provider=provider_name,
            model=selected_model,
            system_prompt=str(SYSTEM_PROMPT_PATH),
            tools_path=str(TOOLS_PATH),
        )

    if "history" not in st.session_state:
        st.session_state["history"] = []
    if "provider" not in st.session_state:
        st.session_state["provider"] = make_provider(provider_name)
    if "transcript_path" not in st.session_state:
        st.session_state["transcript_path"] = TRANSCRIPTS_DIR / f"{st.session_state['transcript']['transcript_id']}.transcript.json"

    st.sidebar.markdown("---")

    transcript_options = sorted(TRANSCRIPTS_DIR.glob("*.transcript.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    selected_transcript = None
    if transcript_options:
        selected_transcript = st.sidebar.selectbox(
            "Load saved transcript",
            [str(path.name) for path in transcript_options],
            index=0,
        )
        if st.sidebar.button("Load transcript") and selected_transcript:
            transcript_path = TRANSCRIPTS_DIR / selected_transcript
            try:
                transcript = load_transcript(transcript_path)
                st.session_state["transcript"] = transcript
                st.session_state["transcript_path"] = transcript_path
                loaded_history: list[dict[str, str]] = []
                for turn in transcript["turns"]:
                    loaded_history.append({"role": "user", "content": turn["user"]})
                    loaded_history.append({"role": "assistant", "content": turn["assistant_text"]})
                st.session_state["history"] = loaded_history
                st.session_state["provider"] = make_provider(provider_name)
                st.session_state["current_turn"] = transcript["turns"][-1] if transcript["turns"] else None
            except Exception as exc:
                st.sidebar.error(f"Không thể load transcript: {exc}")

    if st.sidebar.button("Reset chat session"):
        reset_chat_session(
            version=version_label,
            provider=provider_name,
            model=selected_model,
            system_prompt=str(SYSTEM_PROMPT_PATH),
            tools_path=str(TOOLS_PATH),
        )

    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("Chat")
        if "history" not in st.session_state:
            st.session_state["history"] = []

        display_history = list(st.session_state["history"])
        with st.form(key="chat_form"):
            user_input = st.text_input("Hỏi agent...", key="user_input")
            send_clicked = st.form_submit_button("Gửi")

        if send_clicked and user_input.strip():
            messages = [
                {"role": "system", "content": system_prompt},
                *st.session_state["history"][-history_window * 2 :],
                {"role": "user", "content": user_input},
            ]
            provider = make_provider(provider_name)
            try:
                result = run_model_tool_loop(
                    provider=provider,
                    messages=messages,
                    tools=openai_tools,
                    model=selected_model,
                    max_tool_rounds=max_tool_rounds,
                )
            except Exception as exc:
                st.error(f"Provider error: {type(exc).__name__}: {exc}")
                result = {
                    "status": "provider_error",
                    "assistant_text": None,
                    "rounds": [],
                    "tool_events": [],
                }

            turn_record = {
                "turn_index": len(st.session_state["transcript"]["turns"]) + 1,
                "started_at": datetime.now().isoformat(timespec="seconds"),
                "user": user_input,
                "status": result.get("status", "unknown"),
                "assistant_text": result.get("assistant_text"),
                "rounds": result.get("rounds", []),
                "tool_events": result.get("tool_events", []),
                "ended_at": datetime.now().isoformat(timespec="seconds"),
            }
            append_turn(st.session_state["transcript"], turn_record)
            write_transcript(st.session_state["transcript_path"], st.session_state["transcript"])

            st.session_state["history"].append({"role": "user", "content": user_input})
            assistant_text = result.get("assistant_text") or "(No assistant response)"
            st.session_state["history"].append({"role": "assistant", "content": assistant_text})
            st.session_state["current_turn"] = turn_record
            display_history.append({"role": "user", "content": user_input})
            display_history.append({"role": "assistant", "content": assistant_text})

        for index, message in enumerate(display_history):
            role = message["role"]
            content = message["content"]
            if role == "user":
                st.chat_message("user").write(content)
            else:
                st.chat_message("assistant").write(content)

    with col2:
        st.subheader("Transcript")
        st.write(f"**Version:** {version_label}")
        st.write(f"**Provider:** {provider_name}")
        st.write(f"**Model:** {selected_model or '(default)'}")
        st.write(f"**History window:** {history_window}")
        st.write(f"**Max tool rounds:** {max_tool_rounds}")
        if st.session_state["transcript"]["turns"]:
            st.write(f"**Turn count:** {len(st.session_state['transcript']['turns'])}")
            st.write(f"**Transcript file:** {st.session_state['transcript_path']}")
            st.write(f"**Last saved:** {st.session_state['transcript']['updated_at']}")
        else:
            st.info("Chưa có tương tác nào. Gõ câu hỏi vào ô chat bên trái.")

        if st.session_state["transcript"]["turns"]:
            with st.expander("Session history", expanded=True):
                for turn in st.session_state["transcript"]["turns"]:
                    st.markdown(f"**Turn {turn['turn_index']}**: {turn['started_at']} -> {turn['ended_at']}")
                    st.markdown(f"- User: {turn['user']}")
                    st.markdown(f"- Assistant: {turn['assistant_text']}")
                    if turn["rounds"]:
                        with st.expander("Tool round details", expanded=False):
                            st.json(turn["rounds"])
                    st.markdown("---")

        with st.expander("Prompt & Tools"):
            st.markdown("**System prompt**")
            st.code(system_prompt, language="markdown")
            st.markdown("**Tools schema**")
            st.code(json.dumps(openai_tools, ensure_ascii=False, indent=2), language="json")

        if st.session_state["transcript"]["turns"]:
            with st.expander("Latest turn details", expanded=True):
                last_turn = st.session_state["transcript"]["turns"][-1]
                st.json(last_turn)

        if st.button("Tải transcript JSON"):
            st.download_button(
                label="Download transcript",
                data=json.dumps(st.session_state["transcript"], ensure_ascii=False, indent=2),
                file_name=f"{st.session_state['transcript']['transcript_id']}.transcript.json",
                mime="application/json",
            )

    st.markdown("---")
    st.caption("Research Agent UI - Powered by Streamlit.")


if __name__ == "__main__":
    main()
