from pathlib import Path

from app.extractors.qwen_vl_client import QwenVLClient


def test_qwen_payload_is_openai_compatible_without_images():
    client = QwenVLClient("https://models.example/v1", "secret", "Qwen/Qwen3-VL-8B-Instruct")
    payload = client.build_multimodal_payload("Return JSON.")
    assert payload["model"] == "Qwen/Qwen3-VL-8B-Instruct"
    assert payload["messages"][1]["content"][0]["type"] == "text"
    assert payload["response_format"]["type"] == "json_object"


def test_qwen_payload_embeds_image_data_url(tmp_path):
    image = tmp_path / "frame.jpg"
    image.write_bytes(b"fakejpg")
    client = QwenVLClient("https://models.example/v1", "secret", "model")
    payload = client.build_multimodal_payload("Analyze.", [Path(image)])
    image_part = payload["messages"][1]["content"][1]
    assert image_part["type"] == "image_url"
    assert image_part["image_url"]["url"].startswith("data:image/jpeg;base64,")

