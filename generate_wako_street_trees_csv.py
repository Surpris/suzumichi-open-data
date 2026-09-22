"""wako_street_trees.csv 生成スクリプト

[すずみち](https://suzumichi-mvp.web.app)(日陰・暑さを考慮した経路提案アプリ)向けに、
`wako_street_tree_source/tree_map_wako.geojson`(地理院地図アノテーション由来の
和光市街路樹位置・樹種データ)を、東京都建設局「都道の街路樹」オープンデータ
(https://catalog.data.metro.tokyo.lg.jp/dataset/t000014d2000000029)と同じ12列
フォーマットへ変換し、`wako_street_trees.csv`として書き出す。

すずみちアプリ本体(https://github.com/Surpris/suzumichi、Private)が使う
`street_tree_import.py`は、東京23区・和光市とも本リポジトリの`wako_street_trees.csv`と
同じ列構成のCSVを共通ロジックで読む。このスクリプト自体はすずみちアプリ本体に
依存しない(`requests`のみが外部依存)。データの透明性のため、元データ・変換ロジックを
すべて本リポジトリ内で完結させている。

## 出力CSVの列構成(東京都建設局CSVと完全互換)

樹種,区分,樹高(m),枝張(m),幹周(cm),行政区,種別,整理番号,路線名,通称道路名,経度,緯度

`区分`は全行"高木"固定(元データに高木/中木の区別が無いため)、`行政区`は"和光市"固定。
`樹高(m)`・`幹周(cm)`・`種別`・`整理番号`は元データに無いため空欄。`路線名`に
アノテーションの出典を示す固定文字列を入れ、`通称道路名`は空欄にする。

## 樹冠直径(枝張(m))の代用方針

和光市データは位置・樹種のみで、樹冠の実測値を持たない。東京都建設局CSVを
千代田区×高木でグルーピングした樹種別平均値(小数第1位に丸め)で代用する。

## 樹種名のエイリアス

地理院地図アイコンのラベルは通称であり、東京都建設局CSVの表記と異なるものがある。
`WAKO_SPECIES_ALIAS`で正規化する(プラタナス→スズカケノキ、モミジ→イロハモミジ)。
クスノキ・イチョウ・ハナミズキ・ケヤキはラベルがそのまま一致するためエイリアス不要。

## 実行方法

```bash
pip install -r requirements.txt
python3 generate_wako_street_trees_csv.py
```

`wako_street_trees.csv`(リポジトリルート)を上書きする。
"""

from __future__ import annotations

import argparse
import csv
import io
import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import requests

# 東京都建設局「都道の街路樹」オープンデータ(CC BY 4.0)。
TOKYO_SOURCE_URL = "https://www.opendata.metro.tokyo.lg.jp/kensetsu/tokyo_gairoju.csv"
TOKYO_SOURCE_ENCODING = "cp932"
REQUEST_TIMEOUT_S = 60
TARGET_TREE_CLASS = "高木"
CHIYODA_WARD = "千代田区"

SOURCE_DIR = Path(__file__).parent / "wako_street_tree_source"
GEOJSON_PATH = SOURCE_DIR / "tree_map_wako.geojson"
ICON_SPECIES_MAP_PATH = SOURCE_DIR / "png-tree-pair.json"

DEFAULT_OUTPUT_PATH = Path(__file__).parent / "wako_street_trees.csv"

CSV_FIELDNAMES = [
    "樹種", "区分", "樹高(m)", "枝張(m)", "幹周(cm)",
    "行政区", "種別", "整理番号", "路線名", "通称道路名", "経度", "緯度",
]

TREE_CLASS = "高木"
WARD_NAME = "和光市"
SURVEY_LOCATION_NOTE = "地理院地図アノテーション(2019年空中写真ベース、現地確認済み)"
CANOPY_DIAMETER_PRECISION = Decimal("0.1")

WAKO_SPECIES_ALIAS: dict[str, str] = {
    "プラタナス": "スズカケノキ",
    "モミジ": "イロハモミジ",
}


def fetch_tokyo_rows() -> list[dict[str, str]]:
    """東京都建設局「都道の街路樹」CSVを全件取得する。"""
    resp = requests.get(TOKYO_SOURCE_URL, timeout=REQUEST_TIMEOUT_S)
    resp.raise_for_status()
    text = resp.content.decode(TOKYO_SOURCE_ENCODING)
    return list(csv.DictReader(io.StringIO(text)))


def filter_tall_trees(rows: list[dict[str, str]], ward: str) -> list[dict[str, str]]:
    """指定行政区×高木の行のみを残す。"""
    return [row for row in rows if row["行政区"] == ward and row["区分"] == TARGET_TREE_CLASS]


def average_canopy_diameter_by_species(rows: list[dict[str, str]]) -> dict[str, Decimal]:
    """CSV行(`枝張(m)`列を含む)を樹種別にグルーピングし平均を返す。"""
    totals: dict[str, Decimal] = {}
    counts: dict[str, int] = {}
    for row in rows:
        species = row["樹種"]
        totals[species] = totals.get(species, Decimal("0")) + Decimal(row["枝張(m)"])
        counts[species] = counts.get(species, 0) + 1
    return {species: totals[species] / counts[species] for species in totals}


def load_icon_species_map(path: Path) -> dict[str, str]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_wako_tree_feature(
    feature: dict[str, Any],
    icon_species_map: dict[str, str],
    alias_map: dict[str, str],
) -> dict[str, Any]:
    """GeoJSON Featureの1件を(経度・緯度・正規化後の樹種名)へ変換する。

    `_iconUrl`のbasenameから`icon_species_map`で樹種ラベルを引き、`alias_map`で
    正式樹種名へ正規化する。アイコンラベルが未知の場合はfail-fastする。
    """
    icon_filename = feature["properties"]["_iconUrl"].rsplit("/", 1)[-1]
    try:
        label = icon_species_map[icon_filename]
    except KeyError as e:
        raise ValueError(f"未知のアイコンファイル名です: {icon_filename}") from e

    lon, lat = feature["geometry"]["coordinates"]
    return {"lon": lon, "lat": lat, "genus_species": alias_map.get(label, label)}


def load_wako_tree_features() -> list[dict[str, Any]]:
    data = json.loads(GEOJSON_PATH.read_text(encoding="utf-8"))
    return data["features"]


def build_csv_rows(
    features: list[dict[str, Any]],
    icon_species_map: dict[str, str],
    alias_map: dict[str, str],
    species_avg_canopy: dict[str, Decimal],
) -> list[dict[str, str]]:
    """GeoJSON Featureのリストを、東京都建設局CSV互換のCSV行(dict)リストへ変換する。"""
    rows: list[dict[str, str]] = []
    for feature in features:
        parsed = parse_wako_tree_feature(feature, icon_species_map, alias_map)
        species = parsed["genus_species"]
        try:
            canopy_diameter_m = species_avg_canopy[species]
        except KeyError as e:
            raise ValueError(
                f"樹種'{species}'の東京都建設局CSV(千代田区)平均樹冠直径が見つかりません"
            ) from e

        rows.append(
            {
                "樹種": species,
                "区分": TREE_CLASS,
                "樹高(m)": "",
                "枝張(m)": str(canopy_diameter_m.quantize(CANOPY_DIAMETER_PRECISION)),
                "幹周(cm)": "",
                "行政区": WARD_NAME,
                "種別": "",
                "整理番号": "",
                "路線名": SURVEY_LOCATION_NOTE,
                "通称道路名": "",
                "経度": str(parsed["lon"]),
                "緯度": str(parsed["lat"]),
            }
        )
    return rows


def write_csv(rows: list[dict[str, str]], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def main(output_path: Path = DEFAULT_OUTPUT_PATH) -> None:
    print("fetching tokyo street tree data for canopy diameter averaging...")
    chiyoda_rows = filter_tall_trees(fetch_tokyo_rows(), CHIYODA_WARD)
    species_avg_canopy = average_canopy_diameter_by_species(chiyoda_rows)
    print(f"  averaged over {len(chiyoda_rows)} chiyoda rows / {len(species_avg_canopy)} species")

    icon_species_map = load_icon_species_map(ICON_SPECIES_MAP_PATH)
    features = load_wako_tree_features()
    print(f"  loaded wako features={len(features)}")

    rows = build_csv_rows(features, icon_species_map, WAKO_SPECIES_ALIAS, species_avg_canopy)
    write_csv(rows, output_path)
    print(f"wrote {len(rows)} rows to {output_path}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help=f"出力CSVファイルパス(既定: {DEFAULT_OUTPUT_PATH})",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    main(args.output)
