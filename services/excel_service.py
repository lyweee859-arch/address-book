import io
import re
from typing import Any, Dict, List, Tuple
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


EXPORT_HEADERS = [
    "姓名 (Name)",
    "分组 (Category)",
    "公司/单位 (Company)",
    "职位/头衔 (Title)",
    "是否收藏 (Bookmarked)",
    "电话号码 (Phone Numbers)",
    "电子邮箱 (Email Addresses)",
    "社交账号 (Social Media)",
    "联系地址 (Addresses)",
    "备注 (Notes)",
]


def _format_methods_cell(methods: List[Dict[str, Any]], method_type: str) -> str:
    items = [m for m in methods if m.get("method_type") == method_type and m.get("value")]
    parts = []
    for m in items:
        label = (m.get("label") or "").strip()
        val = (m.get("value") or "").strip()
        if label:
            parts.append(f"{label}: {val}")
        else:
            parts.append(val)
    return "; ".join(parts)


def _parse_methods_cell(cell_text: str, method_type: str, default_label: str) -> List[Dict[str, str]]:
    if not cell_text:
        return []
    raw_items = re.split(r"[;；\n]+", str(cell_text).strip())
    results: List[Dict[str, str]] = []
    for item in raw_items:
        cleaned = item.strip()
        if not cleaned:
            continue
        if ":" in cleaned or "：" in cleaned:
            sep = ":" if ":" in cleaned else "："
            # Avoid splitting URLs like https://... when no label prefix exists
            prefix, rest = cleaned.split(sep, 1)
            if prefix.lower() in ("http", "https"):
                results.append(
                    {"method_type": method_type, "label": default_label, "value": cleaned}
                )
            else:
                results.append(
                    {
                        "method_type": method_type,
                        "label": prefix.strip() or default_label,
                        "value": rest.strip(),
                    }
                )
        else:
            results.append(
                {"method_type": method_type, "label": default_label, "value": cleaned}
            )
    return [r for r in results if r["value"]]


def export_contacts_to_excel(contacts: List[Dict[str, Any]]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "通讯录联系人 (Contacts)"

    header_fill = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")
    header_font = Font(name="Microsoft YaHei", size=11, bold=True, color="FFFFFF")
    body_font = Font(name="Microsoft YaHei", size=10, color="1E293B")
    bookmark_fill = PatternFill(start_color="FEF9C3", end_color="FEF9C3", fill_type="solid")
    thin_border = Border(
        left=Side(style="thin", color="E2E8F0"),
        right=Side(style="thin", color="E2E8F0"),
        top=Side(style="thin", color="E2E8F0"),
        bottom=Side(style="thin", color="E2E8F0"),
    )

    ws.append(EXPORT_HEADERS)
    for col_idx in range(1, len(EXPORT_HEADERS) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border
    ws.row_dimensions[1].height = 28

    for row_idx, contact in enumerate(contacts, start=2):
        methods = contact.get("methods") or []
        is_bookmarked = bool(contact.get("bookmarked"))
        row_values = [
            contact.get("name") or "",
            contact.get("category") or "未分类",
            contact.get("company") or "",
            contact.get("title") or "",
            "是" if is_bookmarked else "否",
            _format_methods_cell(methods, "phone"),
            _format_methods_cell(methods, "email"),
            _format_methods_cell(methods, "social"),
            _format_methods_cell(methods, "address"),
            contact.get("notes") or "",
        ]
        ws.append(row_values)
        ws.row_dimensions[row_idx].height = 24
        for col_idx in range(1, len(EXPORT_HEADERS) + 1):
            c = ws.cell(row=row_idx, column=col_idx)
            c.font = body_font
            c.border = thin_border
            c.alignment = Alignment(
                horizontal="center" if col_idx in (2, 5) else "left",
                vertical="center",
                wrap_text=True,
            )
            if is_bookmarked and col_idx == 5:
                c.fill = bookmark_fill

    col_widths = [20, 16, 24, 18, 16, 34, 34, 30, 38, 30]
    for idx, width in enumerate(col_widths, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = width

    ws.freeze_panes = "A2"

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()


