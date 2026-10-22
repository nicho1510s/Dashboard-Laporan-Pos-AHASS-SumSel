#!/usr/bin/env python3
"""Fetch the user's shared Google spreadsheet, refresh dashboard datasets, and fail clearly on access/schema problems.

The spreadsheet ID is configured from the URL provided by the user. The source must be accessible
without an interactive sign-in (Anyone with the link: Viewer), because GitHub Actions runs unattended.
"""
from __future__ import annotations
import argparse
import datetime as dt
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
SPREADSHEET_ID = "17uQxNnFVIUxRWOZ4DISYrpUzoD3OQmTq"
EXPORT_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=xlsx"
MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def workbook_sheet_names(path: Path) -> list[str]:
    """Read worksheet names from an XLSX without third-party dependencies."""
    with zipfile.ZipFile(path) as zf:
        workbook = ET.fromstring(zf.read("xl/workbook.xml"))
        return [node.attrib.get("name", "") for node in workbook.findall(f"{{{MAIN_NS}}}sheets/{{{MAIN_NS}}}sheet")]


def download_workbook(destination: Path) -> None:
    request = urllib.request.Request(
        EXPORT_URL,
        headers={"User-Agent": "Mozilla/5.0 (compatible; POS-AHASS-Dashboard-Sync/1.0)"},
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response, destination.open("wb") as output:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                output.write(chunk)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"Google Sheets mengembalikan HTTP {exc.code}. Pastikan spreadsheet dapat diakses oleh "
            "'Anyone with the link' sebagai Viewer dan ID spreadsheet benar."
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Tidak dapat mengakses Google Sheets: {exc}") from exc

    if not zipfile.is_zipfile(destination):
        snippet = destination.read_bytes()[:300].decode("utf-8", errors="replace")
        raise RuntimeError(
            "Tautan Google Sheets tidak menghasilkan file XLSX. Kemungkinan spreadsheet dibatasi login "
            "atau URL export tidak didukung untuk file ini. Pastikan General access = Anyone with the link / Viewer. "
            f"Awal respons: {snippet!r}"
        )
    with zipfile.ZipFile(destination) as zf:
        if "xl/workbook.xml" not in zf.namelist():
            raise RuntimeError("File hasil unduhan bukan workbook Excel XLSX yang valid.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=None, help="Tahun untuk sheet bulanan yang nama tabnya tidak mencantumkan tahun")
    args = parser.parse_args()
    year = args.year or dt.datetime.now(ZoneInfo("Asia/Jakarta")).year

    with tempfile.TemporaryDirectory(prefix="pos-ahass-sync-") as temp_dir:
        workbook_path = Path(temp_dir) / "google-sheet-latest.xlsx"
        print(f"Mengunduh spreadsheet ID {SPREADSHEET_ID} ...", flush=True)
        download_workbook(workbook_path)
        sheet_names = workbook_sheet_names(workbook_path)
        print("Tab ditemukan:", " | ".join(sheet_names), flush=True)

        monthly_sheets = [s for s in sheet_names if re.match(r"^UE\s+POS\s+.+$", s.strip(), re.I)]
        if not monthly_sheets:
            raise RuntimeError(
                "Tidak menemukan tab bulanan dengan nama seperti 'UE POS JUN' atau 'UE POS OKT'. "
                "Tidak ada file data yang diterbitkan agar dashboard tidak tertimpa data kosong."
            )
        subprocess.run(
            [sys.executable, str(ROOT / "generate_ue_class_data.py"), str(workbook_path), "--year", str(year)],
            cwd=ROOT,
            check=True,
        )

        if "Form Responses 1" in sheet_names:
            print("Tab 'Form Responses 1' ditemukan; memperbarui laporan operasional juga.", flush=True)
            subprocess.run(
                [sys.executable, str(ROOT / "generate_data.py"), str(workbook_path)],
                cwd=ROOT,
                check=True,
            )
        else:
            print(
                "PERHATIAN: tab 'Form Responses 1' tidak ditemukan. ue_class_data.js diperbarui, "
                "tetapi data.js (UE/KPB/revenue laporan harian) tetap menggunakan snapshot repository. "
                "Agar bagian laporan harian ikut otomatis, sumbernya perlu tersedia sebagai tab 'Form Responses 1' "
                "di workbook yang sama atau dikonfigurasi sebagai sumber kedua.",
                flush=True,
            )

    print("Sinkronisasi Google Sheets selesai.", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR SINKRONISASI: {exc}", file=sys.stderr)
        raise SystemExit(1)
