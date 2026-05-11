"""samples の読み込み、アノテーション結果のJSONL読み書き"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import streamlit as st

from config import LABEL_TO_VALUE, annotation_path, samples_path_for


def samples_mtime(annotator: str, set_name: str) -> float:
    """sample ファイルの mtime（差し替え検出用）。無ければ -1.0"""
    p = samples_path_for(annotator, set_name)
    return p.stat().st_mtime if p.exists() else -1.0


@st.cache_data
def load_samples(mtime: float, annotator: str, set_name: str) -> list[dict]:
    """事前計算された samples を読み込む（mtime/annotator/set をキャッシュキーに）"""
    p = samples_path_for(annotator, set_name)
    if not p.exists():
        return []
    with open(p, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_existing(annotator: str, set_name: str) -> dict[str, dict]:
    """このアノテーター・セットの既存アノテーションを sample_id でキー化して返す"""
    path = annotation_path(annotator, set_name)
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


def save_all(annotator: str, set_name: str, by_sample_id: dict[str, dict]) -> Path:
    """全件を sample_id でソートして書き出し"""
    path = annotation_path(annotator, set_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for sid in sorted(by_sample_id.keys()):
            f.write(json.dumps(by_sample_id[sid], ensure_ascii=False) + "\n")
    return path


def build_record(
    sample: dict,
    annotator: str,
    set_name: str,
    op_inputs: dict[int, dict],
) -> dict:
    """サンプル+UI入力から保存レコードを構築"""
    operations: list[dict] = []
    for op_idx, chunk in enumerate(sample["alignment"]):
        if chunk["type"] == "match":
            continue
        ipt = op_inputs.get(op_idx)
        if ipt is None:
            continue
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
        "set": set_name,
        "model": sample.get("model"),
        "talk_id": sample.get("talk_id"),
        "utterance_id": sample.get("utterance_id"),
        "ref_norm": sample.get("ref_norm"),
        "hyp_norm": sample.get("hyp_norm"),
        "operations": operations,
        "annotated_at": datetime.now().isoformat(timespec="seconds"),
    }
