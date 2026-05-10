"""samples.jsonl の読み込み・アノテーション結果のJSONL読み書き"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import streamlit as st

from config import ANNOTATIONS_DIR, SAMPLES_PATH, samples_path_for


def samples_mtime(annotator: str | None = None) -> float:
    """samples ファイルの mtime（差し替え検出用）。無ければ -1.0"""
    p = samples_path_for(annotator)
    return p.stat().st_mtime if p.exists() else -1.0


@st.cache_data
def load_samples(mtime: float, annotator: str | None = None) -> list[dict]:
    """事前計算された samples を読み込む。

    `mtime` と `annotator` をキャッシュキーに含めることで、ファイル差し替え時や
    アノテーター切替時に自動でキャッシュが無効化される。

    annotator 個別ファイル `samples_<annotator>.jsonl` があればそちらを優先。
    なければ共通の `samples.jsonl`。

    各レコードに含まれるフィールド（asr-edit 側で生成）:
      sample_id      : ユニークID
      model          : モデル識別子
      talk_id, utterance_id
      ref_raw, hyp_raw         : 正規化前
      ref_norm, hyp_norm       : 正規化後（アライメントはこれに対して計算済）
      alignment      : 単語単位のアラインメントリスト
                       各要素: {type, ref_text, hyp_text,
                                ref_start, ref_end, hyp_start, hyp_end}
    """
    p = samples_path_for(annotator)
    if not p.exists():
        return []
    with open(p, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def annotation_path(annotator: str) -> Path:
    """アノテーター名から保存先パスを返す"""
    safe = "".join(c for c in annotator if c.isalnum() or c in "-_")
    return ANNOTATIONS_DIR / f"{safe}.jsonl"


def load_existing(annotator: str) -> dict[str, dict]:
    """このアノテーターの既存アノテーションを sample_id でキー化して返す"""
    path = annotation_path(annotator)
    if not path.exists():
        return {}
    out: dict[str, dict] = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            out[r["sample_id"]] = r
    return out


def save_all(annotator: str, by_sample_id: dict[str, dict]) -> Path:
    """全件を一度に書き出す（順不同なので sample_id でソートして再現性確保）"""
    path = annotation_path(annotator)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for sid in sorted(by_sample_id.keys()):
            f.write(json.dumps(by_sample_id[sid], ensure_ascii=False) + "\n")
    return path


def build_record(
    sample: dict,
    annotator: str,
    op_inputs: dict[int, dict],
) -> dict:
    """サンプルとUI入力からアノテーション保存レコードを構築

    op_inputs: {op_idx_in_alignment: {"score_label": str, "alignment_flag": bool}}
    """
    operations: list[dict] = []
    for op_idx, chunk in enumerate(sample["alignment"]):
        if chunk["type"] == "match":
            continue
        ipt = op_inputs.get(op_idx)
        if ipt is None:
            continue
        from config import LABEL_TO_VALUE
        label = ipt["score_label"]
        score_value = LABEL_TO_VALUE.get(label)
        operations.append({
            "op_idx": op_idx,
            "type": chunk["type"],
            "ref_text": chunk["ref_text"],
            "hyp_text": chunk["hyp_text"],
            "ref_start": chunk["ref_start"],
            "ref_end": chunk["ref_end"],
            "hyp_start": chunk["hyp_start"],
            "hyp_end": chunk["hyp_end"],
            "score_label": label,
            "score": score_value,
            "alignment_flag": bool(ipt.get("alignment_flag", False)),
        })

    return {
        "sample_id": sample["sample_id"],
        "annotator": annotator,
        "model": sample.get("model"),
        "talk_id": sample.get("talk_id"),
        "utterance_id": sample.get("utterance_id"),
        "ref_norm": sample.get("ref_norm"),
        "hyp_norm": sample.get("hyp_norm"),
        "operations": operations,
        "annotated_at": datetime.now().isoformat(timespec="seconds"),
    }
