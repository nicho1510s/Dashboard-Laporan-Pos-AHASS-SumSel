#!/usr/bin/env python3
"""Extract safe POS performance fields from the 'Form Responses 1' sheet.

Usage:
  python generate_data.py "/path/to/Laporan Pos Sumatera Selatan (Responses).xlsx"

Only operational summary fields are exported. No customer/transaction-level sheets are read.
"""
import datetime as dt
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


def col_number(cell_ref: str) -> int:
    match = re.match(r"([A-Z]+)", cell_ref or "")
    if not match:
        return 0
    number = 0
    for letter in match.group(1):
        number = number * 26 + ord(letter) - 64
    return number


def excel_serial_to_date(value):
    try:
        serial = float(value)
        # Excel's default 1900 date system (including its compatibility offset).
        return (dt.datetime(1899, 12, 30) + dt.timedelta(days=serial)).date().isoformat()
    except (TypeError, ValueError, OverflowError):
        return None


def number(value) -> int:
    try:
        return int(round(float(str(value).replace(",", "").strip())))
    except (TypeError, ValueError):
        return 0


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "pos-ahass"


def find_sheet_path(zf, sheet_name: str) -> str:
    workbook = ET.fromstring(zf.read("xl/workbook.xml"))
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    rel_map = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels}
    for sheet in workbook.findall(f"{{{MAIN_NS}}}sheets/{{{MAIN_NS}}}sheet"):
        if sheet.attrib.get("name") == sheet_name:
            target = rel_map[sheet.attrib[f"{{{REL_NS}}}id"]].lstrip("/")
            if not target.startswith("xl/"):
                target = "xl/" + target
            return target
    raise ValueError(f"Sheet '{sheet_name}' tidak ditemukan di workbook.")


def read_shared_strings(zf):
    strings = []
    # iterparse keeps the expanded XML tree small enough for large workbooks.
    with zf.open("xl/sharedStrings.xml") as stream:
        for _, elem in ET.iterparse(stream, events=("end",)):
            if elem.tag == f"{{{MAIN_NS}}}si":
                strings.append("".join(elem.itertext()))
                elem.clear()
    return strings


def iter_sheet_rows(zf, sheet_path, shared_strings):
    with zf.open(sheet_path) as stream:
        for _, elem in ET.iterparse(stream, events=("end",)):
            if elem.tag != f"{{{MAIN_NS}}}row":
                continue
            row = {}
            for cell in elem:
                if cell.tag != f"{{{MAIN_NS}}}c":
                    continue
                idx = col_number(cell.attrib.get("r", ""))
                cell_type = cell.attrib.get("t")
                value_node = cell.find(f"{{{MAIN_NS}}}v")
                inline_node = cell.find(f"{{{MAIN_NS}}}is")
                value = ""
                if cell_type == "s" and value_node is not None:
                    string_index = int(value_node.text)
                    if 0 <= string_index < len(shared_strings):
                        value = shared_strings[string_index]
                elif cell_type == "inlineStr" and inline_node is not None:
                    value = "".join(inline_node.itertext())
                elif value_node is not None:
                    value = value_node.text or ""
                row[idx] = value
            yield row
            elem.clear()


def extract(source: Path):
    with zipfile.ZipFile(source, "r") as zf:
        sheet_path = find_sheet_path(zf, "Form Responses 1")
        shared_strings = read_shared_strings(zf)
        records = []
        seen_ids = Counter()
        for row in iter_sheet_rows(zf, sheet_path, shared_strings):
            name = str(row.get(2, "")).strip()
            date = excel_serial_to_date(row.get(3, ""))
            if not name or not date or name.lower() == "nama ahass pos / ahass":
                continue

            code_raw = str(row.get(15, "")).strip()
            if re.fullmatch(r"\d+\.0", code_raw):
                code_raw = code_raw[:-2]
            slug_base = slugify(name)
            seen_ids[slug_base] += 1
            pos_id = slug_base if seen_ids[slug_base] == 1 else f"{slug_base}-{code_raw or seen_ids[slug_base]}"

            ue_regular = number(row.get(4, ""))
            kpb1 = number(row.get(5, ""))
            kpb2 = number(row.get(6, ""))
            kpb3 = number(row.get(7, ""))
            kpb4 = number(row.get(8, ""))
            revenue_service = number(row.get(9, ""))
            revenue_oil = number(row.get(10, ""))
            revenue_hgp = number(row.get(11, ""))
            ue_kpb = kpb1 + kpb2 + kpb3 + kpb4
            records.append({
                "posId": pos_id,
                "posName": name,
                "dealerCode": code_raw,
                "date": date,
                "month": date[:7],
                "ueRegular": ue_regular,
                "kpb1": kpb1,
                "kpb2": kpb2,
                "kpb3": kpb3,
                "kpb4": kpb4,
                "ueKpb": ue_kpb,
                "ueTotal": ue_regular + ue_kpb,
                "revenueService": revenue_service,
                "revenueOil": revenue_oil,
                "revenueHgp": revenue_hgp,
                "revenueTotal": revenue_service + revenue_oil + revenue_hgp,
                "mechanicsPresent": number(row.get(12, "")),
            })

    # Normalize IDs consistently when a POS name appears in multiple records.
    # Use a single ID per unique POS name + AHASS code pair.
    pos_pairs = sorted({(r["posName"], r["dealerCode"]) for r in records})
    pair_ids = {}
    used = set()
    for name, code in pos_pairs:
        base = slugify(name)
        candidate = base
        if candidate in used:
            candidate = f"{base}-{slugify(code or 'pos')}"
        suffix = 2
        while candidate in used:
            candidate = f"{base}-{slugify(code or 'pos')}-{suffix}"
            suffix += 1
        used.add(candidate)
        pair_ids[(name, code)] = candidate
    for record in records:
        record["posId"] = pair_ids[(record["posName"], record["dealerCode"])]

    records.sort(key=lambda r: (r["posName"].lower(), r["date"]))
    today = dt.date.today().isoformat()
    dates = [r["date"] for r in records]
    pos_count = len({r["posId"] for r in records})
    meta = {
        "generatedAt": today,
        "sourceSheet": "Form Responses 1",
        "reportCount": len(records),
        "posCount": pos_count,
        "dateRangeStart": min(dates) if dates else None,
        "dateRangeEnd": max(dates) if dates else None,
        "futureRecordCount": sum(1 for r in records if r["date"] > today),
    }
    return {"meta": meta, "records": records}


def main():
    if len(sys.argv) < 2:
        print('Usage: python generate_data.py "Laporan Pos Sumatera Selatan (Responses).xlsx"', file=sys.stderr)
        return 2
    source = Path(sys.argv[1]).expanduser()
    if not source.is_file():
        print(f"File tidak ditemukan: {source}", file=sys.stderr)
        return 2
    data = extract(source)
    destination = Path(__file__).with_name("data.js")
    serialized = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    destination.write_text("window.POS_DASHBOARD_DATA = " + serialized + ";\n", encoding="utf-8")
    print(f"Berhasil membuat {destination} | {data['meta']['reportCount']} laporan | {data['meta']['posCount']} POS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
