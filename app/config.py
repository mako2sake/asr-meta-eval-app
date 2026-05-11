"""パス・定数定義"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# 配布される sample ファイル群（リポジトリにコミットされる）
SAMPLES_DIR = PROJECT_ROOT / "samples"

# アノテーション結果（ローカル保存・git管理外）
ANNOTATIONS_DIR = PROJECT_ROOT / "data" / "annotations"

# サポートするセット名
SETS = ["set1", "set2"]


def samples_path_for(annotator: str, set_name: str) -> Path:
    """`samples/samples_<annotator>_<set>.jsonl` のパスを返す"""
    return SAMPLES_DIR / f"samples_{annotator}_{set_name}.jsonl"


def annotation_path(annotator: str, set_name: str) -> Path:
    """`data/annotations/<annotator>_<set>.jsonl` のパスを返す"""
    safe_ann = "".join(c for c in annotator if c.isalnum() or c in "-_")
    safe_set = "".join(c for c in set_name if c.isalnum() or c in "-_")
    return ANNOTATIONS_DIR / f"{safe_ann}_{safe_set}.jsonl"


def list_available_annotators() -> list[str]:
    """samples/ から既存のアノテーター名一覧を抽出（重複除外、ソート）"""
    names: set[str] = set()
    for p in SAMPLES_DIR.glob("samples_*_set?.jsonl"):
        stem = p.stem  # samples_<name>_<set>
        parts = stem.split("_")
        if len(parts) >= 3 and parts[0] == "samples":
            # parts[1:-1] が name、parts[-1] が set
            name = "_".join(parts[1:-1])
            names.add(name)
    return sorted(names)


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
    "substitute": "#ff6b6b",
    "delete":     "#74b9ff",
    "insert":     "#55efc4",
    "match":      "transparent",
}
OP_LABELS = {
    "substitute": "置換",
    "delete":     "削除",
    "insert":     "挿入",
    "match":      "一致",
}
