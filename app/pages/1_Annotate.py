"""アノテーションページ: 1サンプルずつ表示してスコアリング"""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import OP_COLORS, OP_LABELS, SCORE_LABELS, SCORE_OPTIONS
from data_loader import (
    annotation_path,
    build_record,
    load_existing,
    load_samples,
    samples_mtime,
    save_all,
)

st.set_page_config(
    page_title="ASR メタ評価アノテーション",
    page_icon="📝",
    layout="wide",
)

# --- セッション確認 ---
if "samples" not in st.session_state or "annotator" not in st.session_state:
    st.warning("先にトップページからアノテーションを開始してください。")
    if st.button("トップページへ"):
        st.switch_page("Home.py")
    st.stop()

# --- samples.jsonl 差し替え検出 → 最初からやり直し ---
mtime = samples_mtime()
if st.session_state.get("samples_mtime") != mtime:
    st.session_state["samples_mtime"] = mtime
    st.session_state["samples"] = load_samples(mtime)
    st.session_state["current_idx"] = 0
    for key in list(st.session_state.keys()):
        if key.startswith("inputs_"):
            del st.session_state[key]
    st.info("サンプルが差し替えられたため、先頭から再開します。")
    st.rerun()

samples: list[dict] = st.session_state["samples"]
annotator: str = st.session_state["annotator"]
idx: int = st.session_state.get("current_idx", 0)

if not samples:
    st.error("サンプルがありません。")
    st.stop()
idx = max(0, min(idx, len(samples) - 1))

sample = samples[idx]
alignment = sample.get("alignment", [])

# --- 既存アノテーションを読み込み ---
existing_by_sid = load_existing(annotator)
saved_record = existing_by_sid.get(sample["sample_id"])

# 入力 state（このサンプル用）を初期化
state_key = f"inputs_{sample['sample_id']}"
if state_key not in st.session_state:
    init: dict[int, dict] = {}
    if saved_record:
        for op in saved_record.get("operations", []):
            init[op["op_idx"]] = {
                "score_label": op.get("score_label", "acceptable"),
                "alignment_flag": bool(op.get("alignment_flag", False)),
            }
    st.session_state[state_key] = init


# =============================================================================
# UI: ヘッダ
# =============================================================================

st.markdown(f"### サンプル {idx + 1} / {len(samples)}")
header_cols = st.columns([3, 1])
with header_cols[0]:
    st.caption(
        f"`{sample['sample_id']}` "
        f"｜ model: `{sample.get('model','?')}` "
        f"｜ talk: `{sample.get('talk_id','?')}` utt: `{sample.get('utterance_id','?')}`"
    )
with header_cols[1]:
    legend = (
        f'<div style="text-align:right;">'
        f'<span style="background:{OP_COLORS["substitute"]};padding:2px 6px;margin-right:6px;border-radius:3px;">置換</span>'
        f'<span style="background:{OP_COLORS["delete"]};padding:2px 6px;margin-right:6px;border-radius:3px;">削除</span>'
        f'<span style="background:{OP_COLORS["insert"]};padding:2px 6px;border-radius:3px;">挿入</span>'
        f'</div>'
    )
    st.markdown(legend, unsafe_allow_html=True)


# =============================================================================
# UI: アラインメント表示
# =============================================================================

def render_alignment_html(alignment: list[dict]) -> str:
    """ref / hyp 二段の色分け HTMLテーブル"""
    ref_cells, hyp_cells = [], []
    for chunk in alignment:
        ctype = chunk["type"]
        r = chunk.get("ref_text", "") or ""
        h = chunk.get("hyp_text", "") or ""
        bg = OP_COLORS.get(ctype, "transparent")
        if ctype == "match":
            ref_cells.append(f'<td style="padding:3px 6px;">{r}</td>')
            hyp_cells.append(f'<td style="padding:3px 6px;">{h}</td>')
        elif ctype == "delete":
            ref_cells.append(
                f'<td style="padding:3px 6px;background:{bg};font-weight:bold;">{r}</td>'
            )
            hyp_cells.append(
                f'<td style="padding:3px 6px;background:{bg};color:#888;">−</td>'
            )
        elif ctype == "insert":
            ref_cells.append(
                f'<td style="padding:3px 6px;background:{bg};color:#888;">−</td>'
            )
            hyp_cells.append(
                f'<td style="padding:3px 6px;background:{bg};font-weight:bold;">{h}</td>'
            )
        else:  # substitute
            ref_cells.append(
                f'<td style="padding:3px 6px;background:{bg};font-weight:bold;">{r}</td>'
            )
            hyp_cells.append(
                f'<td style="padding:3px 6px;background:{bg};font-weight:bold;">{h}</td>'
            )

    return (
        '<table style="border-collapse:collapse;font-size:18px;margin:8px 0 16px 0;">'
        f'<tr><td style="padding-right:10px;font-weight:bold;color:#666;">REF</td>{"".join(ref_cells)}</tr>'
        f'<tr><td style="padding-right:10px;font-weight:bold;color:#666;">HYP</td>{"".join(hyp_cells)}</tr>'
        '</table>'
    )


st.markdown(render_alignment_html(alignment), unsafe_allow_html=True)


# =============================================================================
# UI: 操作ごとのスコア入力
# =============================================================================

st.subheader("操作スコア")

inputs: dict[int, dict] = st.session_state[state_key]

error_ops = [
    (i, c) for i, c in enumerate(alignment) if c["type"] != "match"
]
if not error_ops:
    st.info("このサンプルにはエラー操作がありません。次へ進んでください。")
else:
    # ガイド（コンパクト表示）
    with st.expander("スコアの目安", expanded=False):
        for label, value, vstr, desc in SCORE_OPTIONS:
            st.markdown(f"- **{label}** ({vstr}): {desc}")

    for op_idx, chunk in error_ops:
        ctype = chunk["type"]
        label = OP_LABELS.get(ctype, ctype)
        color = OP_COLORS.get(ctype, "#ddd")

        if ctype == "delete":
            desc = f"「{chunk['ref_text']}」→ ∅"
        elif ctype == "insert":
            desc = f"∅ →「{chunk['hyp_text']}」"
        else:
            desc = f"「{chunk['ref_text']}」→「{chunk['hyp_text']}」"

        cols = st.columns([3, 5, 1])
        with cols[0]:
            st.markdown(
                f'<span style="background:{color};padding:3px 8px;border-radius:4px;font-weight:bold;">'
                f"{label}</span> {desc}",
                unsafe_allow_html=True,
            )
        with cols[1]:
            current = inputs.get(op_idx, {}).get("score_label", "acceptable")
            try:
                default = SCORE_LABELS.index(current)
            except ValueError:
                default = 0
            chosen = st.radio(
                label=f"score_{op_idx}",
                options=SCORE_LABELS,
                index=default,
                key=f"score_{sample['sample_id']}_{op_idx}",
                horizontal=True,
                label_visibility="collapsed",
            )
            inputs.setdefault(op_idx, {})["score_label"] = chosen
        with cols[2]:
            flagged = st.checkbox(
                "アライメント不適切",
                value=inputs.get(op_idx, {}).get("alignment_flag", False),
                key=f"flag_{sample['sample_id']}_{op_idx}",
            )
            inputs.setdefault(op_idx, {})["alignment_flag"] = flagged


# =============================================================================
# UI: 保存ヘルパ
# =============================================================================

def persist_current() -> Path:
    """現在のサンプルのアノテーションを保存"""
    record = build_record(sample, annotator, st.session_state[state_key])
    by_sid = load_existing(annotator)
    by_sid[record["sample_id"]] = record
    return save_all(annotator, by_sid)


# =============================================================================
# Sidebar: ナビゲーション + 保存 + ダウンロード（常時表示）
# =============================================================================

with st.sidebar:
    st.markdown(f"### 📍 {idx + 1} / {len(samples)}")

    by_sid = load_existing(annotator)
    n_done = len(by_sid)
    st.progress(
        min(1.0, n_done / max(1, len(samples))),
        text=f"進捗: {n_done} / {len(samples)}",
    )

    if st.button("← 前", disabled=(idx == 0), use_container_width=True):
        persist_current()
        st.session_state["current_idx"] = idx - 1
        st.rerun()

    if st.button("次へ →", type="primary",
                 disabled=(idx >= len(samples) - 1),
                 use_container_width=True):
        persist_current()
        st.session_state["current_idx"] = idx + 1
        st.rerun()

    if st.button("💾 ここで保存", use_container_width=True):
        path = persist_current()
        st.success(f"保存: {path.name}")

    st.divider()

    # ダウンロード
    apath = annotation_path(annotator)
    if apath.exists():
        with open(apath, "rb") as f:
            st.download_button(
                label="📥 結果をダウンロード",
                data=f.read(),
                file_name=apath.name,
                mime="application/jsonl",
                use_container_width=True,
            )
        st.caption(f"`{apath.name}`")
    else:
        st.caption("（まだ保存ファイルなし）")

    st.divider()

    # サンプルジャンプ
    target = st.number_input(
        "サンプルNoへ移動",
        min_value=1, max_value=len(samples),
        value=idx + 1, step=1,
    )
    if st.button("移動", use_container_width=True):
        persist_current()
        st.session_state["current_idx"] = int(target) - 1
        st.rerun()
