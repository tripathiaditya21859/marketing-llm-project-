"""Excel helpers: read contact sheets, write downloadable workbooks."""
import io
import re

from openpyxl import Workbook, load_workbook

NAME_HEADERS = {"name", "full name", "fullname", "customer name", "customer", "contact name"}
PHONE_HEADERS = {"phone", "phone number", "mobile", "mobile number", "number", "contact number",
                 "whatsapp", "whatsapp number", "contact", "mobile no", "phone no"}
EMAIL_HEADERS = {"email", "email id", "e-mail", "email address", "mail", "mail id"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _cell(value):
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value).strip()


def normalize_phone(raw, country_code="+91"):
    """Returns '+<digits>' or None when it cannot be a valid number."""
    raw = _cell(raw)
    if not raw:
        return None
    cc = re.sub(r"\D", "", country_code or "")
    plus = raw.startswith("+")
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("00") and not plus:
        digits, plus = digits[2:], True
    if not plus:
        if len(digits) == 10 and cc:
            digits = cc + digits
        elif digits.startswith("0") and cc and 10 <= len(digits) - 1 <= 11:
            digits = cc + digits[1:]
    if not 8 <= len(digits) <= 15:
        return None
    return "+" + digits


def read_contacts(data: bytes, filename: str, max_rows=1000):
    """Parse an .xlsx/.csv contact sheet. Returns (contacts, rows_over_limit)."""
    if filename.lower().endswith(".csv"):
        import csv
        text = data.decode("utf-8-sig", errors="ignore")
        rows = [tuple(r) for r in csv.reader(io.StringIO(text))]
    else:
        wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        ws = wb.active
        rows = [tuple(r) for r in ws.iter_rows(values_only=True)]
        wb.close()
    rows = [r for r in rows if any(_cell(c) for c in r)]
    if not rows:
        raise ValueError("The sheet is empty.")
    header = [_cell(c).lower() for c in rows[0]]
    idx = {}
    for i, h in enumerate(header):
        if h in NAME_HEADERS:
            idx.setdefault("name", i)
        elif h in PHONE_HEADERS:
            idx.setdefault("phone", i)
        elif h in EMAIL_HEADERS:
            idx.setdefault("email", i)
    if "phone" not in idx and "email" not in idx:
        raise ValueError("Could not find a 'Phone' or 'Email' column in the first row. "
                         "Use headers such as: Name, Phone, Email.")

    def get(r, key):
        return _cell(r[idx[key]]) if key in idx and idx[key] < len(r) else ""

    contacts = [{"name": get(r, "name"), "phone": get(r, "phone"), "email": get(r, "email")}
                for r in rows[1:max_rows + 1]]
    return contacts, max(0, len(rows) - 1 - max_rows)


def build_workbook(sheets):
    """sheets: {title: (headers, rows)} -> xlsx bytes."""
    wb = Workbook()
    wb.remove(wb.active)
    for title, (headers, rows) in sheets.items():
        ws = wb.create_sheet(title[:31])
        ws.append(headers)
        for row in rows:
            ws.append(list(row))
            for cell in ws[ws.max_row]:
                if isinstance(cell.value, str):
                    cell.data_type = "s"  # always plain text: user data can never run as a formula
        for col in ws.columns:
            width = max(len(str(c.value)) if c.value is not None else 0 for c in col)
            ws.column_dimensions[col[0].column_letter].width = min(max(12, width + 2), 60)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
