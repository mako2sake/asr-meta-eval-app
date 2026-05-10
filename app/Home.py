"""トップページ: アノテーター名 → サンプル読み込み → アノテーション開始"""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

from config import DATA_DIR, SAMPLES_PATH, samples_path_for
from data_loader import load_existing, load_samples, samples_mtime


def _reset_navigation_state() -> None:
    """サンプル差し替え時にナビゲーション関連の session_state を破棄"""
    for key in list(st.session_state.keys()):
        if key == "samples" or key == "current_idx" or key.startswith("inputs_"):
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

# --- アノテーター名入力 ---
st.subheader("1. アノテーター名")
default_name = st.session_state.get("annotator", "")
annotator = st.text_input(
    "あなたの識別子（アルファベット・数字・ハイフン・アンダースコアのみ）",
    value=default_name,
    placeholder="例: alice, bob, taro",
    help="保存ファイル名 `data/annotations/<annotator>.jsonl` に使われます。"
         f" `data/samples_<annotator>.jsonl` があればそれを優先的に読み込みます。",
)

if annotator:
    safe = "".join(c for c in annotator if c.isalnum() or c in "-_")
    if safe != annotator:
        st.warning(f"使用可能文字に整形されます: `{safe}`")
    annotator = safe

# --- データ読み込み（annotator 個別ファイルを優先、mtime でキャッシュ無効化） ---
mtime = samples_mtime(annotator)
prev_key = (st.session_state.get("samples_mtime"),
            st.session_state.get("samples_annotator"))
new_key = (mtime, annotator)
if prev_key[0] is not None and prev_key != new_key:
    _reset_navigation_state()
st.session_state["samples_mtime"] = mtime
st.session_state["samples_annotator"] = annotator

samples = load_samples(mtime, annotator)
if not samples:
    used_path = samples_path_for(annotator)
    rel = used_path.relative_to(Path.cwd()) if used_path.is_relative_to(Path.cwd()) else used_path
    st.error(
        f"サンプルが見つかりません。`{rel}` または `{SAMPLES_PATH.name}` を `{DATA_DIR}` に配置してください。"
    )
    st.stop()

# どのファイルを読んだかを表示
loaded_path = samples_path_for(annotator)
st.success(
    f"`{loaded_path.name}` を読み込みました: **{len(samples)} 件**"
)

# --- 既存進捗 ---
n_done = 0
if annotator:
    existing = load_existing(annotator)
    n_done = len(existing)
    st.markdown(f"**進捗**: 既存アノテーション {n_done} / {len(samples)} 件")

# --- 開始ボタン ---
st.subheader("2. アノテーション開始")

c1, c2 = st.columns([1, 1])
with c1:
    start_disabled = not annotator
    if st.button("▶ アノテーション開始（最初の未完了から）", type="primary", disabled=start_disabled):
        st.session_state["annotator"] = annotator
        st.session_state["samples"] = samples
        existing = load_existing(annotator)
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
    if annotator and st.button("◀ 先頭から開始（既存はそのまま保持）"):
        st.session_state["annotator"] = annotator
        st.session_state["samples"] = samples
        st.session_state["current_idx"] = 0
        st.switch_page("pages/1_Annotate.py")

st.divider()

with st.expander("使い方"):
    st.markdown(
        """
        1. **アノテーター名**を入力（既存の進捗があれば自動で再開）
        2. 各サンプルで、エラー操作ごとに `acceptable / minor / major / critical / unscorable` を選択
        3. アライメントが不適切に見える場合は **「アライメント不適切」** にチェック
        4. 「次へ」を押すと自動保存されます
        5. 終わったら左サイドバーの **「Annotate」** ページの最下部からダウンロード可能
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
