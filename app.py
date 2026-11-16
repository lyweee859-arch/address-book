from flask import Flask, jsonify, render_template, request
from config import Config
import db


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    db.init_db(db_path=app.config.get("DATABASE_PATH"), seed_default=not app.config.get("TESTING", False))

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
        contacts = db.list_contacts(
            search=search,
            category=category,
            db_path=app.config.get("DATABASE_PATH"),
        )
        return jsonify({"contacts": contacts, "stats": {"total": len(contacts), "bookmarked": 0, "categories": []}})

    @app.route("/api/contacts", methods=["POST"])
    def api_create_contact():
        payload = request.get_json(silent=True) or {}
        try:
            created = db.create_contact(payload, db_path=app.config.get("DATABASE_PATH"))
            return jsonify(created), 201
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

    @app.route("/api/contacts/<int:contact_id>", methods=["PUT"])
    def api_update_contact(contact_id: int):
        payload = request.get_json(silent=True) or {}
        try:
            updated = db.update_contact(contact_id, payload, db_path=app.config.get("DATABASE_PATH"))
            if not updated:
                return jsonify({"error": "未找到该联系人"}), 404
            return jsonify(updated)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

    @app.route("/api/contacts/<int:contact_id>", methods=["DELETE"])
    def api_delete_contact(contact_id: int):
        deleted = db.delete_contact(contact_id, db_path=app.config.get("DATABASE_PATH"))
        if not deleted:
            return jsonify({"error": "未找到该联系人"}), 404
        return jsonify({"message": "联系人已删除", "id": contact_id})

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
