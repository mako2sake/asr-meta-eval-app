"""トップページ: アノテーター + セット選択 → 開始"""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

from config import (
    SAMPLES_DIR,
    SETS,
    list_available_annotators,
    samples_path_for,
)
from data_loader import load_existing, load_samples, samples_mtime


def _reset_navigation_state() -> None:
    """サンプル差し替え／切替時にナビゲーション関連の session_state を破棄"""
    for key in list(st.session_state.keys()):
        if key in ("samples", "current_idx") or key.startswith("inputs_"):
            del st.session_state[key]


st.set_page_config(
    page_title="ASR メタ評価アノテーション",
    page_icon="📝",
    layout="wide",
)

st.title("📝 ASR メタ評価アノテーション")
st.markdown(
    "ASR出力の各編集操作（置換・削除・挿入）に対して、"
    "**書き起こしとしてどれだけ問題か**を 0〜1 のスコアで評価します。"
)

# --- アノテーター・セット選択 ---
st.subheader("1. アノテーター名とセットを選ぶ")

annotators = list_available_annotators()
if not annotators:
    st.error(
        f"sample ファイルが見つかりません。`{SAMPLES_DIR}/` に "
        "`samples_<annotator>_set?.jsonl` を配置してください。"
    )
    st.stop()

c1, c2 = st.columns([1, 1])
with c1:
    default_idx = annotators.index(st.session_state["annotator"]) \
        if st.session_state.get("annotator") in annotators else 0
    annotator = st.selectbox(
        "あなたの名前",
        options=annotators,
        index=default_idx,
        help="管理者から指示された名前を選んでください",
    )

with c2:
    default_set = st.session_state.get("set", SETS[0])
    set_name = st.radio(
        "セット",
        options=SETS,
        index=SETS.index(default_set) if default_set in SETS else 0,
        horizontal=True,
        help="今回担当するアノテーションセット",
    )

# --- sample ファイルの存在チェック ---
sample_path = samples_path_for(annotator, set_name)
if not sample_path.exists():
    st.error(f"このセットのサンプルファイルが見つかりません: `{sample_path.name}`")
    st.stop()

mtime = samples_mtime(annotator, set_name)
samples = load_samples(mtime, annotator, set_name)

# 既存進捗
existing = load_existing(annotator, set_name)
n_done = len(existing)

st.success(
    f"`{sample_path.name}` を読み込みました: **{len(samples)} 件** "
    f"｜ 進捗: **{n_done} / {len(samples)}**"
)

# --- 開始ボタン ---
st.subheader("2. アノテーション開始")

# annotator または set が変わったらナビ状態をリセット
prev = (st.session_state.get("annotator"), st.session_state.get("set"),
        st.session_state.get("samples_mtime"))
if prev != (annotator, set_name, mtime) and any(p is not None for p in prev):
    _reset_navigation_state()

st.session_state["annotator"] = annotator
st.session_state["set"] = set_name
st.session_state["samples_mtime"] = mtime
st.session_state["samples"] = samples

c1, c2 = st.columns([1, 1])
with c1:
    if st.button("▶ 最初の未完了から開始", type="primary"):
        next_idx = 0
        for i, s in enumerate(samples):
            if s["sample_id"] not in existing:
                next_idx = i
                break
        else:
            next_idx = len(samples) - 1
        st.session_state["current_idx"] = next_idx
        st.switch_page("pages/1_Annotate.py")

with c2:
    if st.button("◀ 先頭から開始"):
        st.session_state["current_idx"] = 0
        st.switch_page("pages/1_Annotate.py")

st.divider()

with st.expander("使い方"):
    st.markdown(
        """
        1. **あなたの名前**を選び、担当する**セット**を選びます
        2. 「開始」を押すとアノテーション画面に遷移します
        3. 各サンプルでエラー操作ごとに 5択から選ぶ:
           - `acceptable` (0.00) — 影響なし
           - `minor`      (0.33) — 軽微
           - `major`      (0.67) — 重要
           - `critical`   (1.00) — 致命的
           - `unscorable` (—)    — 判定不能
        4. アライメントが不適切に見える場合は **「アライメント不適切」** にチェック
        5. **「次へ」**で自動保存
        6. 終わったらサイドバーの **ダウンロードボタン**で JSONL を取り出し、Slack 等で著者に送付
        """
    )

with st.expander("スコアの目安"):
    st.markdown(
        """
        | スコア | 値 | 目安 |
        |---|---|---|
        | acceptable | 0.00 | 影響なし（フィラー、表記揺れ） |
        | minor      | 0.33 | 軽微（読みは伝わる） |
        | major      | 0.67 | 重要（理解に支障あり） |
        | critical   | 1.00 | 致命的（意味が完全に変わる） |
        | unscorable | —    | 判定不能（アライメントずれ等） |

        - **削除**: 0=フィラーなど消えても情報が失われない / 1=情報を損なう
        - **挿入**: 0=フィラーなど書き起こしを変えない / 1=書き起こしの意味を変える
        - **置換**: 0=ええ↔えー など意味は同じ / 1=意味を大きく変える
        """
    )
