import io
from datetime import datetime
from flask import Flask, jsonify, render_template, request, send_file
from config import Config
import db
from services.excel_service import (
    export_contacts_to_excel,
    generate_import_template,
    parse_contacts_from_excel,
)


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    db_path = app.config.get("DATABASE_PATH")
    seed_default = not app.config.get("TESTING", False)
    db.init_db(db_path=db_path, seed_default=seed_default)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "service": "xp-address-book"})

    @app.route("/api/contacts", methods=["GET"])
    def api_list_contacts():
        search = request.args.get("search", "")
        category = request.args.get("category", "ALL")
        bookmarked_only = request.args.get("bookmarked", "0").lower() in (
            "1",
            "true",
            "yes",
        )
        contacts = db.list_contacts(
            search=search,
            category=category,
            bookmarked_only=bookmarked_only,
            db_path=app.config.get("DATABASE_PATH"),
        )
        all_contacts = db.list_contacts(db_path=app.config.get("DATABASE_PATH"))
        total_count = len(all_contacts)
        bookmarked_count = sum(1 for c in all_contacts if c.get("bookmarked"))
        categories = sorted(
            {c.get("category") or "未分类" for c in all_contacts if c.get("category")}
        )
        return jsonify(
            {
                "contacts": contacts,
                "stats": {
                    "total": total_count,
                    "bookmarked": bookmarked_count,
                    "filtered": len(contacts),
                    "categories": categories,
                },
            }
        )

    @app.route("/api/contacts/<int:contact_id>", methods=["GET"])
    def api_get_contact(contact_id: int):
        contact = db.get_contact(contact_id, db_path=app.config.get("DATABASE_PATH"))
        if not contact:
            return jsonify({"error": "未找到该联系人 (Contact not found)"}), 404
        return jsonify(contact)

    @app.route("/api/contacts", methods=["POST"])
    def api_create_contact():
        payload = request.get_json(silent=True) or {}
        try:
            created = db.create_contact(
                payload, db_path=app.config.get("DATABASE_PATH")
            )
            return jsonify(created), 201
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

    @app.route("/api/contacts/<int:contact_id>", methods=["PUT"])
    def api_update_contact(contact_id: int):
        payload = request.get_json(silent=True) or {}
        try:
            updated = db.update_contact(
                contact_id, payload, db_path=app.config.get("DATABASE_PATH")
            )
            if not updated:
                return jsonify({"error": "未找到该联系人 (Contact not found)"}), 404
            return jsonify(updated)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

    @app.route("/api/contacts/<int:contact_id>/bookmark", methods=["PATCH", "POST"])
    def api_toggle_bookmark(contact_id: int):
        payload = request.get_json(silent=True) or {}
        bookmarked = payload.get("bookmarked") if "bookmarked" in payload else None
        updated = db.toggle_bookmark(
            contact_id,
            bookmarked=bookmarked,
            db_path=app.config.get("DATABASE_PATH"),
        )
        if not updated:
            return jsonify({"error": "未找到该联系人 (Contact not found)"}), 404
        return jsonify(updated)

    @app.route("/api/contacts/<int:contact_id>", methods=["DELETE"])
    def api_delete_contact(contact_id: int):
        deleted = db.delete_contact(
            contact_id, db_path=app.config.get("DATABASE_PATH")
        )
        if not deleted:
            return jsonify({"error": "未找到该联系人 (Contact not found)"}), 404
        return jsonify({"message": "联系人已删除", "id": contact_id})

    @app.route("/api/contacts/export", methods=["GET"])
    def api_export_excel():
        bookmarked_only = request.args.get("bookmarked", "0").lower() in (
            "1",
            "true",
            "yes",
        )
        search = request.args.get("search", "")
        category = request.args.get("category", "ALL")
        contacts = db.list_contacts(
            search=search,
            category=category,
            bookmarked_only=bookmarked_only,
            db_path=app.config.get("DATABASE_PATH"),
        )
        excel_bytes = export_contacts_to_excel(contacts)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"address_book_contacts_{timestamp}.xlsx"
        return send_file(
            io.BytesIO(excel_bytes),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=filename,
        )

    @app.route("/api/contacts/template", methods=["GET"])
    def api_download_template():
        template_bytes = generate_import_template()
        return send_file(
            io.BytesIO(template_bytes),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name="address_book_import_template.xlsx",
        )

    @app.route("/api/contacts/import", methods=["POST"])
    def api_import_excel():
        if "file" not in request.files:
            return jsonify({"error": "请选择要上传的 Excel (.xlsx) 文件"}), 400
        file = request.files["file"]
        if not file or not file.filename:
            return jsonify({"error": "未选择文件"}), 400
        if not file.filename.lower().endswith(".xlsx"):
            return jsonify({"error": "仅支持 .xlsx 格式的 Excel 文件"}), 400

        try:
            file_bytes = file.read()
            parsed_contacts, warnings = parse_contacts_from_excel(file_bytes)
            if not parsed_contacts:
                return (
                    jsonify(
                        {
                            "error": "Excel 中未找到可导入的有效联系人记录",
                            "warnings": warnings,
                        }
                    ),
                    400,
                )
            imported_count = 0
            for item in parsed_contacts:
                db.create_contact(item, db_path=app.config.get("DATABASE_PATH"))
                imported_count += 1
            return jsonify(
                {
                    "message": f"成功导入 {imported_count} 位联系人",
                    "imported_count": imported_count,
                    "warnings": warnings,
                }
            )
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except Exception as exc:
            return jsonify({"error": f"解析 Excel 文件失败: {exc}"}), 400

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
