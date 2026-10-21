#!/usr/bin/env python3
"""Build the monthly POS class/UE dataset from an AHASS UE workbook.

Usage:
  python generate_ue_class_data.py "UE POS AHASS1.xlsx" --year 2026

Reads worksheets named like "UE POS JUN", "UE POS JUL", ..., "UE POS OKT".
Only summary/daily Unit Entry fields from those monthly sheets are exported.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
MONTHS = {
    "JAN": 1, "JANUARI": 1,
    "FEB": 2, "FEBRUARI": 2,
    "MAR": 3, "MARET": 3,
    "APR": 4, "APRIL": 4,
    "MAY": 5, "MEI": 5,
    "JUN": 6, "JUNI": 6,
    "JUL": 7, "JULI": 7,
    "AUG": 8, "AGU": 8, "AGUSTUS": 8,
    "SEP": 9, "SEPTEMBER": 9,
    "OCT": 10, "OKT": 10, "OKTOBER": 10,
    "NOV": 11, "NOVEMBER": 11,
    "DEC": 12, "DES": 12, "DESEMBER": 12,
}


def col_number(ref: str) -> int:
    m = re.match(r"([A-Z]+)", ref or "")
    if not m:
        return 0
    n = 0
    for ch in m.group(1):
        n = n * 26 + ord(ch) - 64
    return n


def as_number(v, default=0):
    try:
        if v in (None, ""):
            return default
        return int(round(float(str(v).replace(",", "").strip())))
    except (TypeError, ValueError, OverflowError):
        return default


def as_float(v, default=0.0):
    try:
        if v in (None, ""):
            return default
        return float(str(v).replace(",", "").strip())
    except (TypeError, ValueError, OverflowError):
        return default


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "pos-ahass"


def read_shared_strings(zf):
    path = "xl/sharedStrings.xml"
    if path not in zf.namelist():
        return []
    values = []
    with zf.open(path) as stream:
        for _, elem in ET.iterparse(stream, events=("end",)):
            if elem.tag == f"{{{MAIN_NS}}}si":
                values.append("".join(elem.itertext()))
                elem.clear()
    return values


def resolve_sheets(zf):
    wb_xml = ET.fromstring(zf.read("xl/workbook.xml"))
    rel_xml = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    rels = {r.attrib["Id"]: r.attrib["Target"] for r in rel_xml}
    result = []
    for sheet in wb_xml.findall(f"{{{MAIN_NS}}}sheets/{{{MAIN_NS}}}sheet"):
        target = rels[sheet.attrib[f"{{{REL_NS}}}id"]].lstrip("/")
        if not target.startswith("xl/"):
            target = "xl/" + target
        result.append((sheet.attrib["name"], target))
    return result


def parse_cell(cell, shared_strings):
    cell_type = cell.attrib.get("t")
    v_node = cell.find(f"{{{MAIN_NS}}}v")
    if cell_type == "inlineStr":
        inline = cell.find(f"{{{MAIN_NS}}}is")
        return "".join(inline.itertext()) if inline is not None else ""
    if v_node is None:
        return None
    value = v_node.text
    if value is None:
        return None
    if cell_type == "s":
        try:
            return shared_strings[int(value)]
        except (ValueError, IndexError):
            return value
    if cell_type == "b":
        return value == "1"
    if cell_type in ("str", "e"):
        return value
    try:
        number = float(value)
        if number.is_integer():
            return int(number)
        return number
    except (TypeError, ValueError):
        return value


def rows_for_sheet(zf, sheet_path, shared_strings):
    rows = []
    with zf.open(sheet_path) as stream:
        for _, elem in ET.iterparse(stream, events=("end",)):
            if elem.tag != f"{{{MAIN_NS}}}row":
                continue
            row_number = as_number(elem.attrib.get("r"), 0)
            values = {}
            for cell in elem:
                if cell.tag != f"{{{MAIN_NS}}}c":
                    continue
                col = col_number(cell.attrib.get("r", ""))
                values[col] = parse_cell(cell, shared_strings)
            rows.append((row_number, values))
            elem.clear()
    return rows


def export_workbook(input_path: Path, year: int, output_path: Path):
    if not input_path.exists():
        raise FileNotFoundError(f"Workbook tidak ditemukan: {input_path}")
    records = []
    months_seen = set()
    with zipfile.ZipFile(input_path) as zf:
        shared = read_shared_strings(zf)
        for sheet_name, sheet_path in resolve_sheets(zf):
            # Only worksheets explicitly named as monthly UE POS tabs are read.
            m = re.match(r"^UE\s+POS\s+(.+?)\s*$", sheet_name, re.I)
            if not m:
                continue
            month_token = re.sub(r"[^A-Z]", "", m.group(1).upper())
            month_num = MONTHS.get(month_token)
            if not month_num:
                continue
            month = f"{year:04d}-{month_num:02d}"
            months_seen.add(month)
            rows = rows_for_sheet(zf, sheet_path, shared)
            for row_num, cells in rows:
                # Source data begins on row 6: B=AHASS code, D=class, F=POS name.
                name = str(cells.get(6) or "").strip()
                code_val = cells.get(2)
                kelas = str(cells.get(4) or "").strip().upper()
                if row_num < 6 or not name or kelas not in {"HIGH", "MIDDLE", "LOW"}:
                    continue
                dealer_code = str(code_val).strip() if code_val is not None else ""
                daily = [as_number(cells.get(c), 0) for c in range(7, 38)]  # G:AK, days 1–31
                total = as_number(cells.get(38), sum(daily))             # AL, Total
                target = as_number(cells.get(39), 0)                    # AM, Target Fix
                acv_raw = cells.get(40)                                 # AN, ACV
                acv = as_float(acv_raw, (total / target if target else 0.0))
                submitted_raw = cells.get(41)                           # AO, PENGUMPULAN SIP
                submitted = submitted_raw if isinstance(submitted_raw, bool) else str(submitted_raw or "").strip().lower() in {"true", "yes", "1", "ya"}
                group = str(cells.get(3) or "").strip()
                pos_type = str(cells.get(5) or "").strip()
                rank = as_number(cells.get(1), 0) or None
                records.append({
                    "month": month,
                    "posId": slugify(name),
                    "rank": rank,
                    "dealerCode": dealer_code,
                    "group": group,
                    "kelas": kelas,
                    "posType": pos_type,
                    "posName": name,
                    "dailyUE": daily,
                    "totalUE": total,
                    "targetFix": target,
                    "acv": acv,
                    "sipSubmitted": bool(submitted),
                    "sourceSheet": sheet_name,
                })
    if not records:
        raise ValueError("Tidak ditemukan data. Pastikan sheet bernama seperti 'UE POS OKT' dan memiliki data mulai baris 6.")
    records.sort(key=lambda r: (r["month"], r["kelas"], r["rank"] or 999, r["posName"]))
    months_sorted = sorted(months_seen)
    latest_month = months_sorted[-1]
    unique_pos = sorted({r["posId"] for r in records})
    payload = {
        "meta": {
            "generatedAt": dt.datetime.now().date().isoformat(),
            "sourceFile": input_path.name,
            "sourceSheets": sorted({r["sourceSheet"] for r in records}),
            "recordCount": len(records),
            "posCount": len(unique_pos),
            "monthCount": len(months_sorted),
            "latestMonth": latest_month,
            "year": year,
        },
        "months": months_sorted,
        "records": records,
    }
    output_path.write_text("window.POS_CLASS_MONTHLY_DATA = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    print(f"Berhasil: {len(records)} record | {len(unique_pos)} POS | {len(months_sorted)} bulan")
    print(f"Periode: {months_sorted[0]} s.d. {months_sorted[-1]}")
    print(f"Output: {output_path.resolve()}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", help="Path Excel UE POS bulanan")
    parser.add_argument("--year", type=int, default=dt.date.today().year, help="Tahun untuk tab bulanan tanpa tahun (default: tahun sekarang)")
    parser.add_argument("--output", default="ue_class_data.js", help="Nama file output JavaScript")
    args = parser.parse_args()
    export_workbook(Path(args.workbook), args.year, Path(args.output))


if __name__ == "__main__":
    main()
