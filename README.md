# suzumichi-open-data

[すずみち](https://suzumichi-mvp.web.app)(日陰・暑さを考慮した経路提案アプリ)向けに、公式のオープンデータでは代替できないデータを、開発者個人が作成・公開するリポジトリです。データごとにライセンスが異なります。

| データ | 中身 | ライセンス |
|---|---|---|
| [歩行ネットワーク](#歩行ネットワーク)(`suzumichi_walk_network_<area>.gpkg`) | OSMに由来する歩行ネットワークと、車道の区間の歩道の機械的な判定 | [ODbL 1.0](LICENSE) |
| [和光市の街路樹](#wako_street_treescsv)(`wako_street_trees.csv`) | 和光市の街路樹の位置・樹種 | [CC BY 4.0](wako_street_tree_source/LICENSE) |

## 歩行ネットワーク

OpenStreetMap(OSM)に由来する、歩行者向けの道路ネットワークです。すずみちが経路の探索に使う辺(交差点から交差点まで)と、車道の区間ごとの「平行な歩道があるか」の機械的な判定を含みます。

**これは人が確かめていない、機械的な判定です。** 歩道の有無の判定(`algo_left`・`algo_right`)とそこから決めた扱い(`algo_treatment`)は、OSMのデータだけから計算した値で、実際の歩道の有無・歩きやすさを保証しません。空中写真などを使った人の目視の判定は、このデータに含まれません。

### 入手

データの本体(GeoPackage)は大きいため、リポジトリには入れず、[Release](https://github.com/Surpris/suzumichi-open-data/releases)の添付ファイル(zipで圧縮)で配ります。タグ名は`walk-network-v1-<YYYYMMDD>`です。

**準備中**: 最初のReleaseは、すずみちの本番の経路グラフを同じOSMの時点で作り直した後に公開します。

| ファイル | 中身 |
|---|---|
| `suzumichi_walk_network_wako.gpkg.zip` | 和光市(展開すると`suzumichi_walk_network_wako.gpkg`) |
| `suzumichi_walk_network_tokyo.gpkg.zip` | 東京23区(展開すると約400MB) |
| `suzumichi_walk_network_<area>.json` | メタデータ(件数・アルゴリズムの版・OSMの時点・ライセンス・出典・注記) |

### 形式

GeoPackage(1ファイル、座標系EPSG:4326)に、次の2つのレイヤーがあります。

`road_segments`(車道の区間。簡略化した辺のうち、車道の両方向を1つにまとめたもの)

| 列 | 内容 |
|---|---|
| `segment_id` | 区間のID(OSMのway・両端のノード・形から決めるハッシュ16文字) |
| `osm_way_id` | OSMのwayのID |
| `road_type` | OSMの`highway`の値(`trunk`・`primary`・`secondary`・`tertiary`・`unclassified`・`residential`とその`_link`) |
| `algo_version` | 判定のアルゴリズムの版(`v1`) |
| `algo_left`・`algo_right` | 区間の始点から終点に向かって左・右に、平行な歩道があるか(`present`・`absent`) |
| `features` | 左右の特徴量(JSON文字列。歩道までの距離・角度の差・重なる割合・歩道のwayのID) |
| `osm_timestamp` | 歩道のwayを取ったOSMのデータの時点(UTC) |

`walk_edges`(歩行ネットワークの辺。両方向の辺は別の行)

| 列 | 内容 |
|---|---|
| `edge_id`・`from_node_id`・`to_node_id` | 辺とその両端のノードのID |
| `osm_way_id`・`road_type` | OSMのwayのIDと`highway`の値 |
| `length_m` | 辺の長さ(m) |
| `segment_id` | 辺が属する車道の区間(車道の区間でなければ空) |
| `algo_treatment` | アルゴリズムの判定から決めた扱い(`keep`・`heavy`・`exclude`) |
| `algo_treatment_reason` | `connectivity`なら、つながりを保つために戻した区間(それ以外は空) |

### 判定と扱いの決め方

- 区間を始点から5m間隔の点にとり、点ごとに、20m以内にあり、向きの差が30度以内で、垂線の足が線分の上にある歩道(OSMの`highway=footway`かつ`footway=sidewalk`のway)を左右別に探す。左右それぞれで、見つかった点が半分以上なら`present`、そうでなければ`absent`とする
- 扱いは区間ごとに決める。左右とも`present`なら`exclude`(経路から外す)、片側だけ`present`なら`heavy`(重くする)、どちらも`present`でなければ`keep`。両方向の辺に同じ扱いを付ける
- `exclude`の区間をまとめて外すと経路の連結成分の数が増える場合は、`segment_id`の昇順に見て、必要な区間を`heavy`に戻す(`algo_treatment_reason`は`connectivity`)
- 車道の区間に含まれない辺(歩行者用の道など)は`keep`

### データの時点とライセンス

- OSMの時点とアルゴリズムの版は、メタデータのJSON(`osm_timestamp`・`algo_version`)に書いてあります
- **ライセンス: [Open Database License (ODbL) 1.0](LICENSE)**。データベースにはODbLを、個々のデータの内容には[Database Contents License (DbCL) 1.0](https://opendatacommons.org/licenses/dbcl/1-0/)を適用します(OSMと同じ構成です)
- **出典: © OpenStreetMap contributors**。[OSMの著作権とライセンス](https://www.openstreetmap.org/copyright)に従い、利用の際に出典を明記してください。このデータを元に別のデータベースを作って公開する場合は、ODbLの継承(同じ条件での共有)が必要です
- 国土地理院のデータ(ベクトルタイル・空中写真)と、人の目視の判定は含みません

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

### ライセンス

[CC BY 4.0](wako_street_tree_source/LICENSE)。東京都建設局「都道の街路樹」オープンデータ(CC BY 4.0)と同じライセンスです。

利用の際は、出典として本リポジトリ(`https://github.com/Surpris/suzumichi-open-data`)、および元データの底図である国土地理院「地理院地図(空中写真)」を明記してください。
