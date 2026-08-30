# FileModifiedTime v1.0.5

Movable Type の再構築時に、現在のサイト配下にある実ファイルの
最終更新日時（mtime）を返す FUNCTION タグを追加します。

主な用途は CSS / JavaScript のキャッシュバスターです。

## 開発者

- Suffix, Inc.
- https://www.suffix.co.jp/

## 想定環境

- Movable Type 9
- 静的パブリッシング
- CSS / JavaScript 等のキャッシュバスター

## インストール

Movable Type 本体の `plugins` ディレクトリへ、
`FileModifiedTime` ディレクトリをそのまま配置します。

```text
/path/to/mt/
└── plugins/
    └── FileModifiedTime/
        ├── config.yaml
        ├── README.md
        └── lib/
            └── FileModifiedTime/
                └── FileModifiedTime/
                    └── Tags.pm
```

配置後、Movable Type 管理画面のプラグイン一覧で
`FileModifiedTime 1.0.5` が認識されていることを確認してください。

PSGI / FastCGI 等で Movable Type のプロセスを常駐させている場合は、
環境に応じてプロセスの再起動が必要になることがあります。

複数サーバーへ配置する場合は、全サーバーで同一バージョンを配置してください。

## 配布物の生成

ローカルビルド方式を使用します。

Windows PowerShell ではリポジトリルートから次を実行します。

```powershell
.\scripts\build-release.ps1
```

Python を直接実行する場合は次のコマンドでも生成できます。

```bash
python scripts/build_release.py
```

`config.yaml` の `version` を読み取り、既存の `dist/` をいったん削除してから、現在のソースをもとに次の配布物を生成します。

```text
dist/
├── FileModifiedTime/
│   ├── config.yaml
│   ├── README.md
│   └── lib/
│       └── FileModifiedTime/
│           └── FileModifiedTime/
│               └── Tags.pm
└── FileModifiedTime-1.0.5.zip
```

ZIP 内のルートディレクトリは `FileModifiedTime/` です。ディレクトリ権限は `0755`、ファイル権限は `0644` に正規化し、各エントリの更新日時はビルド実行日時で統一します。生成後は展開ディレクトリと ZIP の内容、権限、更新日時をスクリプト内で検証します。

`dist/` はローカル生成物のため Git 管理対象外です。最新版の配布物が必要な場合は、対象ブランチを `git pull` した後にビルドスクリプトを再実行してください。

## 基本仕様

### デフォルト

```html
<mt:FileModifiedTime file="/common/js/main.min.js">
```

出力形式は `YYYYMMDDHHMMSS` です。

例:

```text
20260820101316
```

### Unix timestamp

`format="unix"` を指定します。

```html
<mt:FileModifiedTime
    file="/common/js/main.min.js"
    format="unix"
>
```

出力例:

```text
1787191996
```

### 任意の日時形式

`format` に strftime 形式を指定できます。

```html
<mt:FileModifiedTime
    file="/common/js/main.min.js"
    format="%Y-%m-%d_%H-%M-%S"
>
```

出力例:

```text
2026-08-20_10-13-16
```

## CSS 使用例

```html
<link rel="stylesheet"
      href="/common/css/main.min.css?v=<mt:FileModifiedTime file="/common/css/main.min.css">">
```

再構築後:

```html
<link rel="stylesheet"
      href="/common/css/main.min.css?v=20260820101316">
```

## JavaScript 使用例

```html
<script src="/common/js/main.min.js?v=<mt:FileModifiedTime file="/common/js/main.min.js">"></script>
```

再構築後:

```html
<script src="/common/js/main.min.js?v=20260820101316"></script>
```

## パスの解決

`file` は最終的に現在の Movable Type サイトの `site_path` 配下として解決します。

例:

```text
site_path:
/var/www/html/

file:
/common/js/main.min.js

実ファイル:
/var/www/html/common/js/main.min.js
```

## 自動変換対応

推奨形式はルート相対パスです。

```html
<mt:FileModifiedTime file="/common/js/main.min.js">
```

ただし以下も自動的に正規化します。

```html
<mt:FileModifiedTime file="common/js/main.min.js">
<mt:FileModifiedTime file="<mt:SiteURL>common/js/main.min.js">
<mt:FileModifiedTime file="<mt:WebsiteURL>common/js/main.min.js">
<mt:FileModifiedTime file="<mt:BlogURL>common/js/main.min.js">
<mt:FileModifiedTime file="<mt:SiteRelativeURL>common/js/main.min.js">
<mt:FileModifiedTime file="<$mt:WebsiteURL$>common/js/main.min.js">
```

MTタグが展開済みで、

```text
https://www.example.jp/common/js/main.min.js
```

のような絶対URLになっている場合も、パス部分だけを使用します。

HTTPアクセスは行いません。

## format 属性

| 指定 | 出力 |
|---|---|
| 省略 | `YYYYMMDDHHMMSS` |
| `format="unix"` | Unix timestamp |
| その他 | strftime形式として解釈 |

例:

```html
<mt:FileModifiedTime file="/common/js/main.min.js">
```

```text
20260820101316
```

```html
<mt:FileModifiedTime file="/common/js/main.min.js" format="unix">
```

```text
1787191996
```

```html
<mt:FileModifiedTime file="/common/js/main.min.js" format="%Y/%m/%d %H:%M:%S">
```

```text
2026/08/20 10:13:16
```

## タイムゾーンについて

`format="unix"` 以外の出力（デフォルトおよび strftime 形式）は、
再構築を実行したサーバーの `localtime` に基づいて整形されます。

このため、複数サーバーでタイムゾーン設定が異なる場合、
同一ファイルでも整形後の文字列がサーバー間で食い違う可能性があります。

キャッシュバスター用途では実害はありませんが、
サーバー間で値を厳密に一致させたい場合は、
全サーバーのタイムゾーンを統一するか、`format="unix"` を利用してください。
`format="unix"` はタイムゾーンに依存しません。

## 設計上の役割

`FileModifiedTime` が返すのは対象実ファイルの更新時刻だけです。

絶対URLを出力するか、ルート相対URLを出力するかはテンプレート側で決定します。

ルート相対:

```html
<script src="/common/js/main.min.js?v=<mt:FileModifiedTime file="/common/js/main.min.js">"></script>
```

絶対URL:

```html
<script src="<mt:SiteURL>common/js/main.min.js?v=<mt:FileModifiedTime file="/common/js/main.min.js">"></script>
```

## セキュリティ

- 最終的な参照先は現在のサイトの `site_path` 配下
- `../` を使った親ディレクトリ参照は拒否
- バックスラッシュを含むパスは拒否
- NUL文字は拒否
- シンボリックリンクを解決した実パスが `site_path` 配下に収まらない場合は拒否
- URLが渡されても外部HTTPアクセスは実行しない

参照先の判定は、`Cwd::realpath` により `../` やシンボリックリンクを
すべて解決したうえで、`site_path` の実パス配下に収まっているかを検証します。
これにより、`site_path` 配下に外部を指すシンボリックリンクが存在する場合でも、
サイト外のファイルの mtime が漏れることを防ぎます。

## ファイルが存在しない場合

空文字を返します。
`site_path` 配下と判定できない場合も空文字を返します。

## Cache-Control との違い

このプラグインは HTTP の `Cache-Control` ヘッダー自体を変更しません。

実ファイルのmtimeをURLのクエリパラメーターとして利用することで、
CSS / JavaScript 更新時のキャッシュバスティングを可能にします。

Apache / CDN の `Cache-Control` や `Expires` は別途設定してください。

## アンインストール

Movable Type の `plugins` ディレクトリから
`FileModifiedTime` ディレクトリを削除します。

テンプレート内の `<mt:FileModifiedTime>` は先に削除または置換してください。

## 変更履歴

### v1.0.5

- 変更: Movable Type 管理画面のドキュメントリンクを `https://www.suffix.co.jp/documentation/` に変更。

### v1.0.4

- 修正: `config.yaml` のタグハンドラ参照とパッケージ名の不整合を解消
  （`lib/FileModifiedTime/FileModifiedTime/Tags.pm` へ配置、
  パッケージ名を `FileModifiedTime::FileModifiedTime::Tags` に統一）。
  これによりタグが正しく登録・動作するようになりました。
- 追加: `Cwd::realpath` による `site_path` 配下判定を追加し、
  シンボリックリンク経由でサイト外を参照する経路を遮断。
- 追記: 複数サーバー運用時のタイムゾーン依存に関する注記。
- 変更: README のサイト例を `/var/www/html/` に統一。

### v1.0.3

- 既存リリース。
