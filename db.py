import os
import sqlite3
from typing import Any, Dict, List, Optional
from config import Config


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    path = db_path or Config.DATABASE_PATH
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[str] = None, seed_default: bool = False) -> None:
    conn = get_connection(db_path)
    try:
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT '未分类',
                    company TEXT NOT NULL DEFAULT '',
                    title TEXT NOT NULL DEFAULT '',
                    notes TEXT NOT NULL DEFAULT '',
                    bookmarked INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS contact_methods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contact_id INTEGER NOT NULL,
                    method_type TEXT NOT NULL,
                    label TEXT NOT NULL DEFAULT '',
                    value TEXT NOT NULL,
                    FOREIGN KEY (contact_id) REFERENCES contacts (id) ON DELETE CASCADE
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_contacts_bookmarked ON contacts(bookmarked);"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_methods_contact_id ON contact_methods(contact_id);"
            )
    finally:
        conn.close()


def _attach_methods(
    conn: sqlite3.Connection, contact_rows: List[sqlite3.Row]
) -> List[Dict[str, Any]]:
    if not contact_rows:
        return []
    contacts = [dict(r) for r in contact_rows]
    ids = [c["id"] for c in contacts]
    placeholders = ",".join(["?"] * len(ids))
    method_rows = conn.execute(
        f"""
        SELECT id, contact_id, method_type, label, value
        FROM contact_methods
        WHERE contact_id IN ({placeholders})
        ORDER BY id ASC
        """,
        ids,
    ).fetchall()

    methods_by_contact: Dict[int, List[Dict[str, Any]]] = {cid: [] for cid in ids}
    for m in method_rows:
        md = dict(m)
        methods_by_contact[md["contact_id"]].append(md)

    for c in contacts:
        c["bookmarked"] = bool(c["bookmarked"])
        c["methods"] = methods_by_contact.get(c["id"], [])
    return contacts


def list_contacts(
    search: str = "",
    category: str = "",
    bookmarked_only: bool = False,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    conn = get_connection(db_path)
    try:
        clauses = ["1=1"]
        params: List[Any] = []

        if bookmarked_only:
            clauses.append("c.bookmarked = 1")

        if category and category != "ALL":
            clauses.append("c.category = ?")
            params.append(category)

        if search and search.strip():
            kw = f"%{search.strip()}%"
            clauses.append(
                """
                (
                    c.name LIKE ?
                    OR c.company LIKE ?
                    OR c.title LIKE ?
                    OR c.notes LIKE ?
                    OR c.category LIKE ?
                    OR EXISTS (
                        SELECT 1 FROM contact_methods cm
                        WHERE cm.contact_id = c.id AND (cm.value LIKE ? OR cm.label LIKE ?)
                    )
                )
                """
            )
            params.extend([kw, kw, kw, kw, kw, kw, kw])

        where_sql = " AND ".join(clauses)
        rows = conn.execute(
            f"""
            SELECT c.*
            FROM contacts c
            WHERE {where_sql}
            ORDER BY c.bookmarked DESC, c.name COLLATE NOCASE ASC, c.id DESC
            """,
            params,
        ).fetchall()
        return _attach_methods(conn, rows)
    finally:
        conn.close()


def get_contact(contact_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM contacts WHERE id = ?", (contact_id,)
        ).fetchone()
        if not row:
            return None
        return _attach_methods(conn, [row])[0]
    finally:
        conn.close()


def create_contact(
    data: Dict[str, Any], db_path: Optional[str] = None
) -> Dict[str, Any]:
    name = (data.get("name") or "").strip()
    if not name:
        raise ValueError("联系人姓名不能为空 (Contact name is required)")

    category = (data.get("category") or "未分类").strip() or "未分类"
    company = (data.get("company") or "").strip()
    title = (data.get("title") or "").strip()
    notes = (data.get("notes") or "").strip()
    bookmarked = 1 if data.get("bookmarked") else 0
    methods = data.get("methods") or []

    conn = get_connection(db_path)
    try:
        with conn:
            cur = conn.execute(
                """
                INSERT INTO contacts (name, category, company, title, notes, bookmarked)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (name, category, company, title, notes, bookmarked),
            )
            contact_id = cur.lastrowid
            _insert_methods(conn, contact_id, methods)
        return get_contact(contact_id, db_path=db_path)  # type: ignore
    finally:
        conn.close()


def update_contact(
    contact_id: int, data: Dict[str, Any], db_path: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    existing = get_contact(contact_id, db_path=db_path)
    if not existing:
        return None

    name = (data.get("name") if "name" in data else existing["name"]).strip()
    if not name:
        raise ValueError("联系人姓名不能为空 (Contact name is required)")

    category = (
        (data.get("category") if "category" in data else existing["category"]).strip()
        or "未分类"
    )
    company = (data.get("company") if "company" in data else existing["company"]).strip()
    title = (data.get("title") if "title" in data else existing["title"]).strip()
    notes = (data.get("notes") if "notes" in data else existing["notes"]).strip()
    bookmarked = (
        (1 if data["bookmarked"] else 0)
        if "bookmarked" in data
        else (1 if existing["bookmarked"] else 0)
    )

    conn = get_connection(db_path)
    try:
        with conn:
            conn.execute(
                """
                UPDATE contacts
                SET name = ?, category = ?, company = ?, title = ?, notes = ?,
                    bookmarked = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (name, category, company, title, notes, bookmarked, contact_id),
            )
            if "methods" in data and isinstance(data["methods"], list):
                conn.execute(
                    "DELETE FROM contact_methods WHERE contact_id = ?", (contact_id,)
                )
                _insert_methods(conn, contact_id, data["methods"])
        return get_contact(contact_id, db_path=db_path)
    finally:
        conn.close()


# Bookmark helper added in Commit 09
def _toggle_bookmark_placeholder(
    contact_id: int, bookmarked: Optional[bool] = None, db_path: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    existing = get_contact(contact_id, db_path=db_path)
    if not existing:
        return None

    new_val = (not existing["bookmarked"]) if bookmarked is None else bool(bookmarked)
    conn = get_connection(db_path)
    try:
        with conn:
            conn.execute(
                """
                UPDATE contacts
                SET bookmarked = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (1 if new_val else 0, contact_id),
            )
        return get_contact(contact_id, db_path=db_path)
    finally:
        conn.close()


def delete_contact(contact_id: int, db_path: Optional[str] = None) -> bool:
    conn = get_connection(db_path)
    try:
        with conn:
            cur = conn.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
            return cur.rowcount > 0
    finally:
        conn.close()


def _insert_methods(
    conn: sqlite3.Connection, contact_id: int, methods: List[Dict[str, Any]]
) -> None:
    valid_types = {"phone", "email", "social", "address"}
    for m in methods:
        if not isinstance(m, dict):
            continue
        m_type = (m.get("method_type") or "phone").strip().lower()
        if m_type not in valid_types:
            m_type = "phone"
        label = (m.get("label") or "").strip()
        value = (m.get("value") or "").strip()
        if not value:
            continue
        conn.execute(
            """
            INSERT INTO contact_methods (contact_id, method_type, label, value)
            VALUES (?, ?, ?, ?)
            """,
            (contact_id, m_type, label, value),
        )
