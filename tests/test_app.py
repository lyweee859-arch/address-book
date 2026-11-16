import io
import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app


@pytest.fixture()
def client():
    fd, tmp_db = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    app = create_app({"TESTING": True, "DATABASE_PATH": tmp_db})
    with app.test_client() as test_client:
        yield test_client
    if os.path.exists(tmp_db):
        os.remove(tmp_db)


def test_create_and_multiple_contact_methods(client):
    payload = {
        "name": "测试用户A",
        "category": "同学",
        "company": "福州大学",
        "title": "开发",
        "bookmarked": False,
        "methods": [
            {"method_type": "phone", "label": "手机", "value": "13800001111"},
            {"method_type": "phone", "label": "宿舍", "value": "0591-22223333"},
            {"method_type": "email", "label": "学校邮箱", "value": "test_a@fzu.edu.cn"},
            {"method_type": "social", "label": "微信", "value": "wx_test_a"},
            {"method_type": "address", "label": "地址", "value": "福州市旗山校区"},
        ],
    }
    res = client.post("/api/contacts", json=payload)
    assert res.status_code == 201
    data = res.get_json()
    assert data["name"] == "测试用户A"
    assert len(data["methods"]) == 5


def test_bookmark_toggle_and_filtering(client):
    c1 = client.post("/api/contacts", json={"name": "普通联系人", "bookmarked": False}).get_json()
    c2 = client.post("/api/contacts", json={"name": "重要联系人", "bookmarked": False}).get_json()

    # Toggle bookmark on c2
    res_bm = client.patch(f"/api/contacts/{c2['id']}/bookmark")
    assert res_bm.status_code == 200
    assert res_bm.get_json()["bookmarked"] is True

    # Verify bookmarked filter returns only c2
    res_list = client.get("/api/contacts?bookmarked=1")
    contacts = res_list.get_json()["contacts"]
    assert len(contacts) == 1
    assert contacts[0]["id"] == c2["id"]
    assert contacts[0]["id"] != c1["id"]


def test_excel_export_and_import_roundtrip(client):
    client.post(
        "/api/contacts",
        json={
            "name": "导出测试员",
            "category": "同事",
            "company": "测试科技",
            "bookmarked": True,
            "methods": [
                {"method_type": "phone", "label": "手机", "value": "13911112222"},
                {"method_type": "email", "label": "工作", "value": "export@test.cn"},
            ],
        },
    )

    export_res = client.get("/api/contacts/export")
    assert export_res.status_code == 200
    excel_bytes = export_res.data
    assert len(excel_bytes) > 0

    # Import the exported Excel file back
    data = {"file": (io.BytesIO(excel_bytes), "contacts.xlsx")}
    import_res = client.post(
        "/api/contacts/import", data=data, content_type="multipart/form-data"
    )
    assert import_res.status_code == 200
    assert import_res.get_json()["imported_count"] == 1
