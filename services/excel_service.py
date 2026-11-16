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


def generate_import_template() -> bytes:
    sample_contacts = [
        {
            "name": "张明轩 (示例联系人)",
            "category": "同事",
            "company": "未来云科技有限公司",
            "title": "后端架构师",
            "bookmarked": True,
            "notes": "多个联系方式可用分号 ; 分隔，支持“标签: 内容”格式",
            "methods": [
                {"method_type": "phone", "label": "手机", "value": "138-1234-5678"},
                {"method_type": "phone", "label": "办公", "value": "0591-83210000"},
                {"method_type": "email", "label": "工作邮箱", "value": "mingxuan@futurecloud.cn"},
                {"method_type": "social", "label": "微信", "value": "zmx_cloud"},
                {"method_type": "address", "label": "办公地址", "value": "福州市高新区创新园二期A座"},
            ],
        },
        {
            "name": "李语桐 (示例联系人)",
            "category": "同学 / 项目组",
            "company": "福州大学",
            "title": "前端开发工程师",
            "bookmarked": False,
            "notes": "课程结对编程合作伙伴",
            "methods": [
                {"method_type": "phone", "label": "手机", "value": "159-8888-9999"},
                {"method_type": "email", "label": "学校邮箱", "value": "yutong.li@fzu.edu.cn"},
                {"method_type": "social", "label": "GitHub", "value": "github.com/liyutong"},
                {"method_type": "address", "label": "宿舍地址", "value": "福州大学旗山校区学生公寓"},
            ],
        },
    ]
    return export_contacts_to_excel(sample_contacts)


def parse_contacts_from_excel(file_bytes: bytes) -> Tuple[List[Dict[str, Any]], List[str]]:
    wb = load_workbook(filename=io.BytesIO(file_bytes), data_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise ValueError("Excel 文件为空，请检查文件内容 (Excel file is empty)")

    raw_headers = [str(cell).strip() if cell is not None else "" for cell in rows[0]]
    col_map = _map_columns(raw_headers)
    if "name" not in col_map:
        raise ValueError(
            "未识别到“姓名 (Name)”列，请先下载并使用标准模板格式导入"
        )

    parsed_contacts: List[Dict[str, Any]] = []
    warnings: List[str] = []

    for row_idx, row in enumerate(rows[1:], start=2):
        if not row or all(cell is None or str(cell).strip() == "" for cell in row):
            continue

        def get_val(field: str) -> str:
            idx = col_map.get(field)
            if idx is None or idx >= len(row) or row[idx] is None:
                return ""
            return str(row[idx]).strip()

        name = get_val("name")
        if not name:
            warnings.append(f"第 {row_idx} 行缺少姓名，已跳过")
            continue

        category = get_val("category") or "未分类"
        company = get_val("company")
        title = get_val("title")
        notes = get_val("notes")
        bm_raw = get_val("bookmarked").lower()
        bookmarked = bm_raw in ("是", "yes", "true", "1", "y", "收藏", "★", "⭐")

        methods: List[Dict[str, str]] = []
        methods.extend(_parse_methods_cell(get_val("phone"), "phone", "手机"))
        methods.extend(_parse_methods_cell(get_val("email"), "email", "邮箱"))
        methods.extend(_parse_methods_cell(get_val("social"), "social", "社交账号"))
        methods.extend(_parse_methods_cell(get_val("address"), "address", "地址"))

        parsed_contacts.append(
            {
                "name": name,
                "category": category,
                "company": company,
                "title": title,
                "notes": notes,
                "bookmarked": bookmarked,
                "methods": methods,
            }
        )

    return parsed_contacts, warnings


def _map_columns(headers: List[str]) -> Dict[str, int]:
    mapping: Dict[str, int] = {}
    aliases = {
        "name": ["姓名", "name", "联系人", "full name"],
        "category": ["分组", "分类", "类别", "category", "group", "tag"],
        "company": ["公司", "单位", "学校", "组织", "company", "organization"],
        "title": ["职位", "头衔", "职务", "title", "role", "position"],
        "bookmarked": ["收藏", "书签", "星标", "bookmarked", "bookmark", "favorite", "star"],
        "phone": ["电话", "手机", "号码", "phone", "mobile", "tel"],
        "email": ["邮箱", "邮件", "电邮", "email", "e-mail", "mail"],
        "social": ["社交", "微信", "qq", "github", "微博", "social", "wechat"],
        "address": ["地址", "住址", "位置", "address", "location"],
        "notes": ["备注", "说明", "简介", "notes", "note", "remark"],
    }
    for idx, h in enumerate(headers):
        h_lower = h.lower()
        for field, kw_list in aliases.items():
            if field in mapping:
                continue
            if any(kw in h_lower for kw in kw_list):
                mapping[field] = idx
                break
    return mapping
