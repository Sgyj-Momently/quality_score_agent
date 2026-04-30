from fastapi.testclient import TestClient
from unittest import TestCase

from src.api_server import app
from src.scorer import bucket, score_bundle, score_photo


class QualityScoreAgentTest(TestCase):
    def test_scores_photo_from_summary_confidence_and_filename(self):
        score = score_photo(
            {
                "file_name": "hero_cafe.jpg",
                "photo_summary": {
                    "summary": "A bright bakery counter with many pastries and warm lighting.",
                    "confidence": 0.9,
                    "ocr_text": ["ETOILE"],
                },
            }
        )

        self.assertGreater(score["overall"], 0.7)
        self.assertEqual(bucket(score["overall"]), "excellent")

    def test_low_quality_filename_receives_lower_bucket(self):
        score = score_photo({"file_name": "blur_duplicate.jpg", "photo_summary": {"summary": "", "confidence": 0.2}})

        self.assertEqual(bucket(score["overall"]), "low")

    def test_scores_bundle_and_average(self):
        result = score_bundle(
            {
                "photos": [
                    {"file_name": "hero.jpg", "photo_summary": {"summary": "rich scene", "confidence": 0.9}},
                    {"file_name": "dark.jpg", "photo_summary": {"summary": "", "confidence": 0.3}},
                ]
            }
        )

        self.assertEqual(result["quality_status"], "ok")
        self.assertEqual(result["photo_count"], 2)
        self.assertGreater(result["average_score"], 0)
        self.assertIn("quality_score", result["scored_photos"][0])

    def test_health_endpoint(self):
        client = TestClient(app)

        response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["service"], "quality_score_agent")

    def test_quality_endpoint(self):
        client = TestClient(app)

        response = client.post(
            "/api/v1/quality-scores",
            json={"project_id": "sample", "photos": [{"file_name": "IMG.jpg"}]},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["project_id"], "sample")
        self.assertEqual(response.json()["photo_count"], 1)

