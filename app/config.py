"""パス・定数定義"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# 入力（asr-edit から配布される samples.jsonl を置く）
# 1. annotator 個別ファイル `samples_<annotator>.jsonl` を優先
# 2. 共通ファイル `samples.jsonl` にフォールバック
SAMPLES_PATH = DATA_DIR / "samples.jsonl"


def samples_path_for(annotator: str | None = None) -> Path:
    """annotator 個別の samples_<annotator>.jsonl があればそれ、無ければ samples.jsonl"""
    if annotator:
        per_user = DATA_DIR / f"samples_{annotator}.jsonl"
        if per_user.exists():
            return per_user
    return SAMPLES_PATH


# 出力（アノテーションごとのJSONL）
ANNOTATIONS_DIR = DATA_DIR / "annotations"

# スコア定義（4分位 + unscorable）
SCORE_OPTIONS = [
    ("acceptable", 0.0,  "0.00", "正解と同じ読みで同じ意味を表すが異なる表記で文章として許容可能"),
    ("minor",      0.33, "0.33",
     "正解と同じ読みで同じ意味を表すが異なる表記で文章としてはあまり適さない（Aさんが→Aさんガ）／"
     "正解と近い読みで文章としてどちらとも言えなくもない／"
     "正解に存在するものが削除されているがなくても文意を変えない（えーっと→削除）／"
     "正解に存在しないものが挿入されているが文章を壊さない"),
    ("major",      0.67, "0.67",
     "アラインメントを壊さない、正解と同じ・近い読みで表記だけが異なるミス（同音異義語の誤り等）。"
     "文章構成で修正可能性が高いという意味で critical より低いエラー"),
    ("critical",   1.0,  "1.00",
     "文意を構成する上で重要なキーワードの誤り／"
     "アラインメントを崩壊させるような大きい誤認識"),
    ("unscorable", None, "—",
     "判定不能（音声無しでは判断不能、参考情報が決定的に不足、等）"),
]

LABEL_TO_VALUE = {label: value for label, value, _, _ in SCORE_OPTIONS}
SCORE_LABELS = [label for label, _, _, _ in SCORE_OPTIONS]

# 操作タイプの色とラベル
OP_COLORS = {
    "substitute": "#ff6b6b",  # 赤
    "delete":     "#74b9ff",  # 青
    "insert":     "#55efc4",  # 緑
    "match":      "transparent",
}
OP_LABELS = {
    "substitute": "置換",
    "delete":     "削除",
    "insert":     "挿入",
    "match":      "一致",
}
