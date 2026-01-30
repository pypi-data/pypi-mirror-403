# AIT-CLI

## 概要

**AIT-CLI** は、AIT開発に関連するコマンドラインツールです。このツールを使用すると、以下の操作をコマンドラインから簡単に実行できます。

- AITテンプレートの作成
- AIT開発環境のJupyter Labの起動
- サードパーティの通知生成
- AITパッケージの圧縮
- AITのGitHubへのプッシュ

これにより、AITのセットアップや操作を効率的に行うことができます。

## 対象ユーザー

- AIT開発者

## インストール方法

以下のコマンドでインストールできます。

```bash
pip install ait-cli
```

> [!IMPORTANT]
> ローカル環境（システム全体）にインストールした場合、`ait-cli`コマンドは**システム全体**で利用可能です。仮想環境にインストールした場合、`ait-cli`コマンドは**インストールした仮想環境でのみ**利用可能です。

> [!TIP]
> #### Windows
> Windowsにインストールする際、権限の問題でインストール時にait-cliの実行ファイルが作成されない場合があります。その場合は、`pip install ait-cli`を**管理者権限**で立ち上げたコマンドプロンプトで実行してください。 
> #### Mac, Linux 
> MacまたはLinuxにインストールする際、ait-cliのパスが通らない場合があります。`bashrc`もしくは`zshrc`を修正して、ait-cliの実行ファイル（binファイル）のパスを通してください。 通常、実行ファイルは`~/.local/bin`に作成されます。   
> bashの例    
> ```bash
> echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
> source ~/.bashrc
> ```

## 実行環境

AIT-CLIは「gitコマンドの使用」「gitのuser.emailとuser.nameの設定」「GitHubへのSSH接続」「dockerコマンドの使用」を前提としております。
以下コマンドの実行結果がそれぞれ問題ないことを確認してください。

- **gitコマンド**

```bash
git --version
# 「git version ～」のようにgitのバージョンが表示されることを確認してください
```

- **user.emailとuser.nameの設定**
```bash
git config --global user.email
# Eメールが表示されることを確認してください

git config --global user.name
# 名前が表示されることを確認してください
```

- **GitHubへのSSH接続**

```bash
ssh -T git@github.com
# 「Hi <ユーザ名>! You've successfully authenticated, but GitHub does not provide shell access.」のようなメッセージが表示されることを確認してください
```

- **dockerコマンド**

```bash
docker --version
# 「Docker version ～」のようにdockerのバージョンが表示されることを確認してください
```

インストールや設定方法についてはリンク先でご確認ください。
- **git**: https://git-scm.com/
- **GitHubへのSSH接続**: https://docs.github.com/ja/authentication/connecting-to-github-with-ssh
- **docker**: https://www.docker.com/ja-jp/

> [!CAUTION]
> 本ガイド執筆時点で、Docker Desktopの無償利用には条件があり、必ずしも利用者の手元において問題なく利用できるとは限りません。ご自身で使用許諾条件を確認いただく必要があります。


## 使用方法

### コマンド構成

`ait-cli`は、複数のサブコマンドを提供しています。以下のコマンドでヘルプを確認できます。

```bash
ait-cli --help
```

### サブコマンド

以下のサブコマンドを利用できます。

| コマンド              | 説明                                    | オプション                                                                 |
|-----------------------|----------------------------------------|--------------------------------------------------------------------------|
| `create`              | AITテンプレートをセットアップする       | `--ait_name`: 開発するAITの名前（必須）<br> `--path`: AITの配置先のパス |
| `jupyter`             | AITをJupyter Labで起動する      | `--path`: Jupyter Labを起動するAITのパス               |
| `thirdparty-notice`   | AITのサードパーティライセンス通知を生成 | `--path`: サードパーティ通知を生成するAITのパス             |
| `zip`                 | AITをzipに圧縮する                   | `--path`: 圧縮するAITのパス                                   |
| `git-push`            | AITを指定したGitHubのリポジトリにプッシュする            | `--github_repository`: GitHubリポジトリURL（初回のプッシュ時に必須）<br> `--path`: プッシュするAITのパス |

### `create`コマンド

指定したディレクトリに、`--ait_name`で指定した名前のAITテンプレートをセットアップします。

```bash
ait-cli create --ait_name <YourAITName> --path <directory path>
```

#### 引数

- `--ait_name`: 開発するAITの名前（必須）
- `--path`: AITの配置先のパス。デフォルトは現在のディレクトリ

> ### AITの命名規則
> AITの命名時に推奨される命名規則は以下の通りです。
> * `{prefix}_{target}_{format}_{task}_{measure}`
> 
> | 項目名               | 必須 | 説明                                                           |
> |----------------------|------|----------------------------------------------------------------|
> | prefix               | ○   | AITのタイプを表します。<br>- eval : 品質評価<br>- alyz : 分析<br>- misc : その他<br>- generate : AITに入力するデータを生成するAITに使います。 |
> | target               | ○   | AITの評価対象によって"dataset"か"model"のいずれかを選択します。|
> | task                 | ×   | AITが対象とする問題<br>例.image_classifier                              |
> | format               | ×   | AITが取り扱うデータの形式<br>例. table                                      |
> | measure              | ×   | AITで取り扱う品質特性<br>例. coverage_of_dataset                                          |
> 
> * 制限
>   * 名称は50文字以下にする必要があります
>   * 利用可能な文字は、半角英数字 と `_` です

### `prepare`コマンド

Jupyter起動前に基本的な情報を対話型形式で入力します。

```bash
ait-cli prepare --path <directory path>
```

#### 引数

- `--path`: Jupyter Labを起動するAITのパス。デフォルトは現在のディレクトリ

> [!TIP]
> 実行は任意です。後から手入力することも可能です。

### `jupyter`コマンド

AITをJupyter Labで起動します。

```bash
ait-cli jupyter --path <directory path>
```

#### 引数

- `--path`: Jupyter Labを起動するAITのパス。デフォルトは現在のディレクトリ

> [!TIP]
> dockerが起動していない場合、Jupyter Labは起動しません。

### `thirdparty-notice`コマンド

AITのサードパーティ通知を生成します。

```bash
ait-cli thirdparty-notice --path <directory path>
```

#### 引数

- `--path`: サードパーティ通知を生成するAITのパス。デフォルトは現在のディレクトリ

> [!CAUTION]
> `thirdparty-notic`コマンドはOSSライセンスの完全なリストアップを保証しません。必ずご自身で内容を確認してください

### `zip`コマンド

AITをzip圧縮します。

```bash
ait-cli zip --path <directory path>
```

#### 引数

- `--path`: 圧縮するAITのパス。デフォルトは現在のディレクトリ

> [!TIP]
> zipパッケージがインストールされていない場合、このコマンドは失敗します。特にLinux環境で頻発する問題です。`sudo apt-get install zip`を実行したのちに、再度`ait-cli zip`の実行をお願いします。

### `git-push`コマンド

AITを指定したGitHubのリポジトリにプッシュします。

```bash
ait-cli git-push --github_repository <Your GitHub repository URL> --path <directory path>
```

#### 引数

- `--github_repository`: 最初のプッシュ時にGitHubリポジトリのURLを指定してください。2回目以降は省略可能です。2回目以降のプッシュ時にURLを**上書き**する場合にはこのオプションを指定してください。
- `--path`: プッシュするAITのパス。デフォルトは現在のディレクトリ

> [!TIP]
> 事前にGITHUBでリポジトリを作成してください。リポジトリは公開に設定してください。

> [!CAUTION]
> GITHUBへ登録すると、開発したAITは一般公開されます。AITの公開に際しては、個人情報や機密情報を公開していないか、また公開が目的に即しているか、十分確認した上で実施してください。

## 使用例

実際のAIT開発フローに沿った使用例を紹介します。

1. AIT-CLIをインストール

```bash
pip install ait-cli
```

2. AITテンプレートをセットアップ

```bash
ait-cli create --ait_name AIT_sample
```

3. ディレクトリを移動し、Jupyter Labを立ち上げる

```bash
cd AIT_sample
ait-cli prepare (任意)
ait-cli jupyter
```

4. Jupyter Lab内でAITの開発とユニットテスト

5. サードパーティ通知の生成

```bash
ait-cli thirdparty-notice
```

6. Qunomonとの結合テスト用にAITをzipに圧縮

```bash
ait-cli zip
```

7. 結合テストを実施

8. 開発したAITをGitHubに登録

```bash
ait-cli git-push --github_repository git@github.com:~
```

**AIT開発の詳細なガイドについてはこちらをご確認ください**  
https://qunomon.github.io/qunomon/ait-guide/index.html

## トラブルシューティング

### エラー: `create`コマンドが失敗した場合

```bash
Error: Failed to clone the repository. Please check your network connection or the repository URL.
Details: Command execution failed with error code: <エラーコード>
...
```

**解決策**: gitがインストールされているか、GitHubとSSH接続が確立できているか、PCがオンラインであるか、を確認してください。

### エラー: スクリプトが見つからない

```bash
Error: Script '<script_name>' not found. Please verify the path.
```

**解決策**: `ait-cli`コマンドがAITのルートディレクトリで実行されているか、`--path`オプションが正しいか、を確認してください。

### エラー: ディレクトリが見つからない

```bash
Error: Directory '<directory_name>' not found. Please verify the path.
```

**解決策**: `ait-cli`コマンドがAITのルートディレクトリで実行されているか、`--path`オプションが正しいか、を確認してください。

## 作成者
AIST AIRC  

## ライセンス

Apache License Version 2.0