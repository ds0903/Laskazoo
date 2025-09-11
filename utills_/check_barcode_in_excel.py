# pip install pandas sqlalchemy psycopg2-binary openpyxl
import re
import pandas as pd
from sqlalchemy import create_engine, text

EXCEL_PATH = r"C:\Users\Supik\Downloads\Product_table_Miau_UA.xlsx"
DB_URL = "postgresql+psycopg2://danil:danilus15@127.0.0.1:5432/laska_db"
DB_TABLE = "products_product"
DB_BARCODE_COL = "barcode"

# Які довжини вважаємо штрихкодами (EAN-8, EAN-13/GTIN-12/14)
EAN_LENS = {8, 12, 13, 14}

def extract_codes(cell) -> list[str]:
    """Витягує всі коди з клітинки, лишає тільки цифри."""
    if cell is None:
        return []
    s = str(cell).strip()
    if not s:
        return []
    # розділювачі: пробіли, коми, крапки з комою, /, |, перенос рядка, таби
    toks = re.split(r"[\s,;\/|]+", s)
    out = []
    for t in toks:
        digits = re.sub(r"\D+", "", t)  # тільки цифри
        if digits and len(digits) in EAN_LENS:
            out.append(digits)
    return out

def guess_barcode_cols(df: pd.DataFrame) -> list[int]:
    """
    Оцінює кожну колонку: скільки клітинок містять хоча б один EAN.
    Повертає список індексів колонок з найкращими показниками.
    """
    scores = []
    for col in df.columns:
        cnt = 0
        for val in df[col].dropna():
            if extract_codes(val):
                cnt += 1
        scores.append((cnt, col))
    scores.sort(reverse=True)  # за кількістю збігів
    best = []
    if scores:
        top_cnt = scores[0][0]
        # беремо всі колонки, які набрали ≥70% від максимуму і мають мінімум 5 збігів
        thr = max(5, int(top_cnt * 0.7))
        best = [col for cnt, col in scores if cnt >= thr and cnt >= 5]
    return best

def load_excel_barcodes(path: str):
    """
    Повертає список трійок (sheet, excel_row, code)
    """
    out = []
    xls = pd.ExcelFile(path, engine="openpyxl")
    for sheet in xls.sheet_names:
        # читаємо взагалі без заголовків — усе як є
        df = pd.read_excel(xls, sheet_name=sheet, header=None, dtype=str)
        if df.empty:
            print(f"[!] Аркуш '{sheet}' порожній")
            continue

        cand_cols = guess_barcode_cols(df)
        if not cand_cols:
            print(f"[!] На аркуші '{sheet}' не вдалось визначити колонку зі штрихкодами.")
            # на крайній випадок: прогнати все полотно і ловити коди хоч десь
            for (r, c), val in df.stack().items():
                for code in extract_codes(val):
                    out.append((sheet, int(r) + 1, code))
            continue

        print(f"[i] Аркуш '{sheet}': кандидатні колонки {cand_cols}")
        for col in cand_cols:
            for i, val in df[col].items():
                for code in extract_codes(val):
                    # Excel-рядок = індекс + 1 (бо читаємо без заголовків)
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
