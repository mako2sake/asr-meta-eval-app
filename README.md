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

サンプルデータ（`samples/` 配下）はリポジトリにコミットされているので、別途取得不要です。

## 起動

```bash
uv run streamlit run app/Home.py
```

ブラウザが開いたら：

1. **名前を選ぶ**（管理者から指示された名前）
2. **セットを選ぶ**（`set1` または `set2`、管理者から指示）
3. **「開始」**を押すとアノテーション画面に遷移
4. 各サンプルでエラー操作ごとに 5択：
   - `acceptable` (0.00) — 影響なし
   - `minor`      (0.33) — 軽微
   - `major`      (0.67) — 重要
   - `critical`   (1.00) — 致命的
   - `unscorable` (—)    — 判定不能
5. アライメントが不適切に見える場合は **「アライメント不適切」** にチェック
6. **「次へ」**で自動保存
7. 終わったらサイドバーの **ダウンロードボタン**で JSONL を取り出し、Slack 等で著者に送付

### キーボードショートカット

- `→` : 次へ（保存して次へ）
- `←` : 前へ
- `s` : ここで保存

※ テキスト入力中はショートカット無効

## ディレクトリ構成

```
asr-meta-eval-app/
├── app/
│   ├── Home.py                  名前/セット選択 + 開始
│   ├── pages/1_Annotate.py      アノテーション画面
│   ├── config.py                パス・スコア定義
│   └── data_loader.py           JSONL 読み書き
├── samples/                     ★コミット済み（配布データ）
│   ├── samples_ken_set1.jsonl
│   ├── samples_ken_set2.jsonl
│   ├── samples_alice_set1.jsonl
│   ├── samples_alice_set2.jsonl
│   ├── samples_bob_set1.jsonl
│   ├── samples_bob_set2.jsonl
│   ├── samples_taro_set1.jsonl
│   └── samples_taro_set2.jsonl
└── data/
    └── annotations/             ★gitignored（個人データ）
        ├── ken_set1.jsonl
        ├── ken_set2.jsonl
        └── ...
```

## 出力スキーマ

`data/annotations/<annotator>_<set>.jsonl`、1行=1発話：

```json
{
  "sample_id": "...",
  "annotator": "ken",
  "set": "set1",
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
