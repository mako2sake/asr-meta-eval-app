"""パス・定数定義"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# 入力（asr-edit から配布される samples.jsonl を置く）
SAMPLES_PATH = PROJECT_ROOT / "data" / "samples.jsonl"

# 出力（アノテーションごとのJSONL）
ANNOTATIONS_DIR = PROJECT_ROOT / "data" / "annotations"

# スコア定義（4分位 + unscorable）
SCORE_OPTIONS = [
    ("acceptable", 0.0,  "0.00", "影響なし（フィラー削除、表記揺れ等）"),
    ("minor",      0.33, "0.33", "軽微な誤り（読みは伝わる）"),
    ("major",      0.67, "0.67", "重要な誤り（理解に支障あり）"),
    ("critical",   1.0,  "1.00", "致命的（意味が完全に変わる）"),
    ("unscorable", None, "—",    "判定不能（アライメントずれ等）"),
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
