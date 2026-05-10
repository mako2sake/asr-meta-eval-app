# asr-meta-eval-app

ASR メタ評価のための人手アノテーション Streamlit アプリ。

各 ASR 出力（hypothesis）の編集操作（置換・削除・挿入）に対して
**書き起こしとして問題かどうか**を 0〜1 のスコアで評価する。

## 必要なもの

- Python 3.11+
- [uv](https://github.com/astral-sh/uv)（推奨）

uv が未インストールの場合（macOS）:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## セットアップ

```bash
git clone <this-repo>
cd asr-meta-eval-app
uv sync
```

## アノテーションデータの配置

データ準備担当（asr-edit プロジェクト側）から `samples.jsonl` を受け取り、以下に配置：

```
data/samples.jsonl
```

ファイル形式は `data/samples.example.jsonl` を参照。各行が1サンプルで以下のフィールドを含む：

```json
{
  "sample_id": "...",
  "model": "openai/whisper-medium",
  "talk_id": "...", "utterance_id": "...",
  "ref_raw": "...", "hyp_raw": "...",
  "ref_norm": "...", "hyp_norm": "...",
  "alignment": [
    {"type": "match|substitute|delete|insert",
     "ref_text": "...", "hyp_text": "...",
     "ref_start": 0, "ref_end": 1,
     "hyp_start": 0, "hyp_end": 1}
  ]
}
```

アライメントは asr-edit 側で**事前計算済み**（Sudachi mode A 単語境界 + 文字 Levenshtein 投影）。
このアプリでは計算しないので Sudachi 等の依存は不要。

## 起動

```bash
uv run streamlit run app/Home.py
```

ブラウザが開いたら：

1. **アノテーター名**を入力（半角英数 / `-` / `_` のみ）
2. **「アノテーション開始」**を押下
3. 各サンプルでエラー操作ごとに 5択から選ぶ
   - `acceptable` (0.00) — 影響なし
   - `minor`      (0.33) — 軽微
   - `major`      (0.67) — 重要
   - `critical`   (1.00) — 致命的
   - `unscorable` (—)    — 判定不能
4. アライメントが不適切に見える場合は **「アライメント不適切」** にチェック
5. **「次へ」**で自動保存
6. 終わったらページ下部の **ダウンロードボタン**で JSONL を取り出し、Slack 等で著者に送付

## 出力

- ローカル保存: `data/annotations/<annotator>.jsonl`
- 1行 = 1サンプルのアノテーション結果
- 中断・再開はそのまま可能（同名で再開すると既存ファイルから読み込み）

出力スキーマ:

```json
{
  "sample_id": "...",
  "annotator": "alice",
  "model": "...", "talk_id": "...", "utterance_id": "...",
  "ref_norm": "...", "hyp_norm": "...",
  "operations": [
    {"op_idx": 1, "type": "substitute",
     "ref_text": "いた", "hyp_text": "致",
     "ref_start": 1, "ref_end": 2,
     "hyp_start": 1, "hyp_end": 2,
     "score_label": "minor", "score": 0.33,
     "alignment_flag": false}
  ],
  "annotated_at": "2026-..."
}
```

## ディレクトリ構成

```
asr-meta-eval-app/
├── app/
│   ├── Home.py              トップページ
│   ├── pages/1_Annotate.py  アノテーションページ
│   ├── config.py            パス・スコア定義
│   └── data_loader.py       JSONL 読み書き
├── data/
│   ├── samples.example.jsonl  入力フォーマット例
│   ├── samples.jsonl          ★配布されたサンプルをここに
│   └── annotations/           ★出力（自動生成）
└── pyproject.toml
```
