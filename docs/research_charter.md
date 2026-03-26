# Research Charter — SolarWill Kernel

## Main Question

SolarWill は、単一応答よりも、理由と制約が追える意思決定支援を作れるか？

## Why this repo exists

この repo の目的は、巨大な思想体系をいきなり完成させることではない。  
まずは、**小さく、読めて、壊して、直せる**最小核を作り、そこから学ぶことにある。

SolarWill Kernel は、夢を小さくするための repo ではない。  
**夢を検証可能な大きさに切る**ための repo である。

## Hypotheses

1. constraint + trace を持つ出力は、単一応答より監査しやすい
2. options + risks + next_questions を固定すると、出力の再利用性が上がる

## Non-goals (Week 1)

Week 1 では以下をやらない。

- multi-agent / philosopher swarm
- REST API
- Docker
- UI / viewer
- memory system
- benchmark 拡張
- 複数LLM backend の同時運用
- 「AI全体への優越」の主張
- 完成品としての製品化

## Success Metrics (Week 1)

Week 1 の成功条件は次の3つだけ。

1. `solarwill run` で常に構造化 JSON が返る
2. 危険入力で `blocked`、注意入力で `warn` が返る
3. 実行ごとに trace が保存される

## Failure Criteria

以下のどれかが起きたら、Week 1 は失敗とみなす。

1. 出力 schema が毎回崩れる
2. constraint 判定が trace に残らない
3. stub fallback でも最低応答が返らない

## Minimal Baselines

Week 1 で使う比較対象は次だけ。

- baseline A: stub backend
- baseline B: single live backend（Gemini or Ollama のどちらか1つ）

## Non-claims

Week 1 の時点では、以下を主張しない。

- SolarWill は既存AIより賢い
- SolarWill は哲学AIとして完成している
- SolarWill は高リスク意思決定を任せられる
- SolarWill はプロダクトとして完成している

## Week 1 Decision

Week 1 では以下を固定する。

- backend は 1つだけ
- constraint は 1つだけ
- trace schema は 1つだけ
- output contract は 1つだけ
- entry point は CLI 1本だけ

## Review Rule

Week 1 の終わりに次を確認する。

- 何が動いたか
- 何が壊れたか
- 何を学んだか
- Week 2 で増やすべきものは本当に1つか

増やす前に、まず理解する。

_Last updated: 2026-03-22_