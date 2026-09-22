# suzumichi-open-data

[すずみち](https://suzumichi-mvp.web.app)(日陰・暑さを考慮した経路提案アプリ)向けに、公式のオープンデータでは代替できないデータを、開発者個人が作成・公開するリポジトリです。

## wako_street_trees.csv

埼玉県和光市(駅周辺)の街路樹データです。和光市には東京23区のような街路樹の個体単位オープンデータが存在しないため、開発者が[地理院地図](https://maps.gsi.go.jp/)上で2019年撮影の空中写真を底図としてアノテーション(現地確認済み)した位置・樹種データを、[東京都建設局「都道の街路樹」オープンデータ](https://catalog.data.metro.tokyo.lg.jp/dataset/t000014d2000000029)と同じ列構成のCSVへ変換して公開しています。

- `wako_street_trees.csv`: 公開データ本体
- `wako_street_tree_source/tree_map_wako.geojson`: 元データ(地理院地図アノテーション、295件のPoint FeatureCollection)
- `wako_street_tree_source/png-tree-pair.json`: アイコンファイル名→樹種ラベルの対応表
- `generate_wako_street_trees_csv.py`: 元データからCSVを生成するスクリプト

### 列構成

東京都建設局CSVと同一の12列です。

| 列名 | 内容 |
|---|---|
| 樹種 | 樹種名(千代田区データのマッピング表のキーへ正規化済み) |
| 区分 | 常に「高木」固定(元データに高木/中木の区別が無いため) |
| 樹高(m) | 未取得のため空欄 |
| 枝張(m) | 千代田区データ(東京都建設局CSV)の樹種別平均値による代用値 |
| 幹周(cm) | 未取得のため空欄 |
| 行政区 | 常に「和光市」固定 |
| 種別 | 未取得のため空欄 |
| 整理番号 | 未取得のため空欄 |
| 路線名 | 出典メモ(「地理院地図アノテーション(2019年空中写真ベース、現地確認済み)」固定) |
| 通称道路名 | 空欄 |
| 経度・緯度 | アノテーション座標(EPSG:4326) |

### 生成方法

元データ(`wako_street_tree_source/tree_map_wako.geojson`・`png-tree-pair.json`)から、本リポジトリの`generate_wako_street_trees_csv.py`が生成しています。元データ・変換ロジックとも本リポジトリ内で完結しており(外部依存は`requests`のみ)、すずみちアプリ本体のリポジトリ(Private)を参照する必要はありません。

```bash
pip install -r requirements.txt
python3 generate_wako_street_trees_csv.py
```

すずみちアプリ側(`batch/street_tree_import.py`)は、`street_tree_sources.json`経由で本リポジトリの`wako_street_trees.csv`を直接ダウンロードして利用します。

### 件数・樹種内訳(2026-09-22時点)

295件、6樹種(ケヤキ117・イチョウ97・スズカケノキ33・イロハモミジ20・クスノキ18・ハナミズキ10)。

## ライセンス

[CC BY 4.0](LICENSE)。東京都建設局「都道の街路樹」オープンデータ(CC BY 4.0)と同じライセンスです。

利用の際は、出典として本リポジトリ(`https://github.com/Surpris/suzumichi-open-data`)、および元データの底図である国土地理院「地理院地図(空中写真)」を明記してください。
