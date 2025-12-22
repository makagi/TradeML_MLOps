# Git Branching & AI-Driven Workflow for MLOps

このドキュメントでは、本プロジェクトにおける Git ブランチ戦略、CI/CD 連携、および AI アシスタント（Antigravity, Cursor, Cline等）との効率的な連携ルールを定義します。

## 1. ブランチ戦略 (Branching Strategy)

| ブランチ | ターゲット | ライフサイクル | 役割・用途 |
| :--- | :--- | :--- | :--- |
| `main` | Production | 永続 | 安定稼働コード。Vertex AIへの正式なモデルデプロイに使用。 |
| `develop` | Staging | 永続 | 統合ブランチ。すべての `feature` がここに集まり、クラウド検証が行われる。 |
| `feature/*` | Develop | 短期 | 機能追加、バグ修正。完了後は `develop` へ PR。 |
| `experiment/*` | Research | 短期 | 模型、特徴量の実験。コードの整合性より試行錯誤を優先。 |

## 2. CI/CD 連携オートメーション

- **Push to `feature/*`**:
  - `tests/test_components.py` (コンポーネント登録テスト)
  - `tests/test_system.py` (YAML設定整合性テスト)
- **Merge to `develop`**:
  - `scripts/verify_run.py` (Vertex AIでのパイプライン試運転)
  - 成功時に `evaluation_report.md` を自動生成。
- **Release (Tagging `v*`) from `main`**:
  - `scripts/run_pipeline.py` (本番実行)
  - 学習完了モデルを Vertex AI Model Registry に登録。

## 3. AI アシスタントへの指示ルール (AI Interaction Rules)

AI に作業を依頼する際は、以下のルールを前提として伝えてください：

1. **コンテキストの明示**: 
   - 「`develop` ブランチから `feature/xxx` を作成して作業を開始してください」
2. **パリティ（再現性）の維持**:
   - 「`src/` を変更した後は、必ず `tests/test_parity.py` を実行して、ローカルとクラウドの精度一致 (`0.5465...`) が維持されているか確認してください」
3. **ドキュメント駆動**:
   - 「実装を終えたら、`docs/` 以下の関連ドキュメントを更新し、`walkthrough.md` に変更内容を追記してください」
4. **コミットメッセージ**:
   - `chore`: インフラ・整理、 `feat`: 機能追加、 `fix`: 修正、 `exp`: 実験

## 4. 運用フロー例

1. **開発開始**:
   - ユーザー: 「AI、新しいRSIアルゴリズムを試したい。`experiment/rsi-opt` ブランチを作って作業して」
2. **AI実装**:
   - AI: ブランチ作成、`src/components/feature_engineering/` 修正、`tests/` 実行。
3. **パリティ確認**:
   - AI: `tests/test_parity.py` で精度が変わっていないか、あるいは意図した変化かを確認。
4. **統合**:
   - ユーザー: `develop` へのマージを承認 → CI が Vertex AI でパイプラインを回す。
