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
- safety/constraint は **1つだけ**
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
- benchmark拡張
- 複数LLM backendの同時運用

## Quick Start

### 1. Create venv

```bash
python -m venv .venv
source .venv/bin/activate