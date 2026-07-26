def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "healthy"

def test_metrics_endpoint(client):
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    json_data = response.json()
    assert "total_lessons_indexed" in json_data

def test_ocr_text_endpoint(client):
    payload = {
        "lesson_title": "درس البلاغة العربية",
        "text_content": "البلاغة هي مطابقة الكلام لمقتضى الحال مع فصاحته. وتقسم البلاغة إلى ثلاثة علوم: علم المعاني، وعلم البيان، وعلم البديع."
    }
    response = client.post("/api/v1/ocr", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "lesson_id" in data
    assert data["indexed"] is True
