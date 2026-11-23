# Work Piece ダウンロード数の自動記録

`work-piece/WorkPiece` の Release `v1.0` にある
`work-piece-company-profile.pdf` の累計ダウンロード数を、毎日CSVに記録します。

## 導入するファイル

このフォルダ内の構成を、そのまま `work-piece/WorkPiece` リポジトリのルートへ追加します。

- `.github/workflows/track-release-downloads.yml`
- `scripts/track_release_downloads.py`
- `data/download_history.csv`

## GitHub側の設定

1. `work-piece/WorkPiece` を開く。
2. 上記3ファイルをリポジトリの既定ブランチへ追加する。
3. リポジトリの **Settings → Actions → General → Workflow permissions** を開く。
4. Actionsの書き込み権限を制限している場合は、ワークフローに設定した `permissions: contents: write` が有効になるよう確認する。
5. **Actions** タブに `Track Release Downloads` が表示されることを確認する。
6. `Track Release Downloads` → **Run workflow** で初回テストを実行する。

Personal Access Tokenの新規発行は不要です。ワークフローに付与される `GITHUB_TOKEN` を使用します。

## 実行時刻

毎日 00:05（日本時間）。GitHub Actionsのタイムゾーン指定 `Asia/Tokyo` を使用します。
Actionsの混雑などにより、実際の開始が数分遅れる場合があります。
Actionsタブから手動実行することもできます。

## CSVの列

| 列 | 内容 |
|---|---|
| `date_jst` | 記録日（日本時間） |
| `repository` | リポジトリ |
| `release_tag` | Releaseタグ |
| `asset_name` | 対象ファイル |
| `download_count` | GitHubが返す累計ダウンロード数 |
| `daily_delta` | 前回記録との差 |
| `collected_at_utc` | 取得時刻（UTC） |

同じ日に再実行した場合は同じ日付の行を更新し、重複行を作りません。
初回記録の `daily_delta` は空欄です。初回導入前の過去の日別内訳は復元できません。

## 注意事項

- この数字はGitHub Release Assetの累計ダウンロード数です。ダウンロードした人数や利用者数ではありません。
- 同じ人による複数回のダウンロードもカウントに含まれます。
- この仕組みの導入後、毎日の取得時点での累計値を保存します。日次の差分は「前回記録からの増加数」であり、厳密な24時間単位のアクセスログではありません。
- 対象のReleaseタグ・ファイル名を変更した場合は、スクリプト内の `TAG` / `ASSET_NAME` を変更してください。
- 公開リポジトリのスケジュール実行は、60日間リポジトリにアクティビティがないと自動停止される場合があります。このワークフローはCSV更新時にコミットを行います。
