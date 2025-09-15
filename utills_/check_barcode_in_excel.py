import re
import pandas as pd
from sqlalchemy import create_engine, text

EXCEL_PATH = r"C:\Users\Supik\Downloads\Product_table_Miau_UA.xlsx"
DB_URL = "postgresql+psycopg2://danil:danilus15@127.0.0.1:5432/laska_db"
DB_TABLE = "products_product"
DB_BARCODE_COL = "barcode"


EAN_LENS = {8, 12, 13, 14}

def extract_codes(cell) -> list[str]:

    if cell is None:
        return []
    s = str(cell).strip()
    if not s:
        return []

    toks = re.split(r"[\s,;\/|]+", s)
    out = []
    for t in toks:
        digits = re.sub(r"\D+", "", t)  # тільки цифри
        if digits and len(digits) in EAN_LENS:
            out.append(digits)
    return out

def guess_barcode_cols(df: pd.DataFrame) -> list[int]:

    scores = []
    for col in df.columns:
        cnt = 0
        for val in df[col].dropna():
            if extract_codes(val):
                cnt += 1
        scores.append((cnt, col))
    scores.sort(reverse=True)
    best = []
    if scores:
        top_cnt = scores[0][0]

        thr = max(5, int(top_cnt * 0.7))
        best = [col for cnt, col in scores if cnt >= thr and cnt >= 5]
    return best

def load_excel_barcodes(path: str):

    out = []
    xls = pd.ExcelFile(path, engine="openpyxl")
    for sheet in xls.sheet_names:

        df = pd.read_excel(xls, sheet_name=sheet, header=None, dtype=str)
        if df.empty:
            print(f"[!] Аркуш '{sheet}' порожній")
            continue

        cand_cols = guess_barcode_cols(df)
        if not cand_cols:
            print(f"[!] На аркуші '{sheet}' не вдалось визначити колонку зі штрихкодами.")

            for (r, c), val in df.stack().items():
                for code in extract_codes(val):
                    out.append((sheet, int(r) + 1, code))
            continue

        print(f"[i] Аркуш '{sheet}': кандидатні колонки {cand_cols}")
        for col in cand_cols:
            for i, val in df[col].items():
                for code in extract_codes(val):

                    out.append((sheet, int(i) + 1, code))
    return out

def load_db_barcodes():
    engine = create_engine(DB_URL)
    with engine.begin() as conn:
        rows = conn.execute(text(f"""
            SELECT id, {DB_BARCODE_COL}
            FROM {DB_TABLE}
            WHERE {DB_BARCODE_COL} IS NOT NULL AND {DB_BARCODE_COL} <> ''
        """)).fetchall()
    db = {}
    for rid, bc in rows:
        digits = re.sub(r"\D+", "", str(bc or "").strip())
        if digits and len(digits) in EAN_LENS:
            db.setdefault(digits, []).append(rid)
    return db

def main():
    excel_rows = load_excel_barcodes(EXCEL_PATH)
    db_map = load_db_barcodes()
    db_set = set(db_map.keys())

    print(f"[i] З Excel зібрано кодів (з урахуванням дублікатів): {len(excel_rows)}")
    print(f"[i] У БД унікальних кодів: {len(db_set)}")

    found = 0
    for sheet, rowno, bc in excel_rows:
        if bc in db_set:
            found += 1
            ids = ",".join(map(str, db_map[bc]))
            print(f"Збіг: '{sheet}', рядок {rowno} → {bc} (product id: {ids})")

    print(f"\nВсього збігів: {found}")
    if found == 0:
        print("[i] Збігів нема — або інші коди бренду, або в БД їх поки немає.")

if __name__ == "__main__":
    main()
