# SolarWill Kernel

SolarWill Kernel は、**理由と制約を追跡できる意思決定支援**を最小構成で検証するための研究用リポジトリです。

## What it does

与えられた問いに対して、次を返します。

- 選択肢
- 暫定的な推奨
- 理由
- リスク
- 次に確認すべき問い
- trace（なぜその出力になったかの記録）

## What it is NOT

これは以下ではありません。

- 自律エージェント
- 万能な哲学AI
- 感情ケア用チャットボット
- 最終判断を代行するシステム
- 完成済みの製品

## Main Question

> SolarWill は、単一応答よりも、理由と制約が追える意思決定支援を作れるか？

## Week 1 Scope

この repo の最初の1週間では、次しかやりません。

- backend は **1つだけ**
- safety / constraint は **1つだけ**
- trace schema は **1つだけ**
- 出力形式は **1つだけ**
- baseline は **1つだけ**

### Non-goals for Week 1

- multi-agent swarm
- REST API
- Docker
- vector DB
- UI / viewer
- memory system
- benchmark 拡張
- 複数LLM backend の同時運用

---

## Quick Start

### 1. Create venv

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install

```bash
pip install -e .
```

### 3. Create env file

```bash
cp .env.example .env
```

### 4. Choose one backend

Week 1 は Gemini か Ollama のどちらか **1つだけ** 使います。

**Gemini を使う場合**、`.env` に以下を入れる:

```env
SOLARWILL_BACKEND=gemini
GEMINI_API_KEY=your_key_here
```

**Ollama を使う場合**、`.env` に以下を入れる:

```env
SOLARWILL_BACKEND=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
```

> 最初の1週間は **Gemini 推奨**。
> 理由: まずは SolarWill の構造を理解するべきで、ローカルモデル運用の罠を同時に踏むべきではないから。

### 5. Run

```bash
python -m solarwill run "転職するべきか悩んでいる" --pretty
```

または:

```bash
solarwill run "転職するべきか悩んでいる" --pretty
```

---

## Output Contract

最低限、以下の形で返します。

```json
{
  "status": "ok",
  "question": "転職するべきか悩んでいる",
  "options": [
    "現職に残る",
    "転職活動を始める",
    "期限付きで情報収集する"
  ],
  "recommendation": "期限付きで情報収集する",
  "reasons": [
    "不確実性が高い",
    "即断より比較材料が不足している"
  ],
  "risks": [
    "現職不満の放置",
    "転職期待の過大評価"
  ],
  "next_questions": [
    "何が一番つらいのか",
    "収入と裁量のどちらを優先するか"
  ],
  "trace": {
    "backend_requested": "gemini",
    "backend_used": "gemini",
    "constraint_result": "passed",
    "prompt_version": "v0.1",
    "timestamp": "..."
  }
}
```

---

## Design Rules

1. One question first
2. One backend first
3. One output contract first
4. Trace everything
5. No magic
6. No giant architecture in week 1

---

## Week 1 Success Criteria

- `solarwill run ...` が通る
- stub backend で常に JSON が返る
- `blocked` / `warn` / `ok` の3状態が機能する
- trace JSON が保存される
- baseline 比較の土台ができる
