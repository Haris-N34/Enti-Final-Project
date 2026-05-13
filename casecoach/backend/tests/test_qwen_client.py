from pathlib import Path

from app.extractors.qwen_vl_client import QwenVLClient, _dashscope_app_url, _is_dashscope_app_call


def test_qwen_payload_is_openai_compatible_without_images():
    client = QwenVLClient("https://models.example/v1", "secret", "Qwen/Qwen3-VL-8B-Instruct")
    payload = client.build_multimodal_payload("Return JSON.")
    assert payload["model"] == "Qwen/Qwen3-VL-8B-Instruct"
    assert payload["messages"][1]["content"] == "Return JSON."
    assert payload["response_format"]["type"] == "json_object"


def test_qwen_payload_embeds_image_data_url(tmp_path):
    image = tmp_path / "frame.jpg"
    image.write_bytes(b"fakejpg")
    client = QwenVLClient("https://models.example/v1", "secret", "model")
    payload = client.build_multimodal_payload("Analyze.", [Path(image)])
    image_part = payload["messages"][1]["content"][1]
    assert image_part["type"] == "image_url"
    assert image_part["image_url"]["url"].startswith("data:image/jpeg;base64,")


def test_numeric_dashscope_model_uses_application_api_for_text_calls():
    assert _is_dashscope_app_call("https://dashscope-intl.aliyuncs.com/compatible-mode/v1", "210965", None)
    assert not _is_dashscope_app_call("https://dashscope-intl.aliyuncs.com/compatible-mode/v1", "qwen-plus", None)
    assert not _is_dashscope_app_call("https://dashscope-intl.aliyuncs.com/compatible-mode/v1", "210965", [Path("frame.jpg")])


def test_dashscope_application_url_uses_region_from_base_url():
    assert (
        _dashscope_app_url("https://dashscope-intl.aliyuncs.com/compatible-mode/v1", "210965")
        == "https://dashscope-intl.aliyuncs.com/api/v1/apps/210965/completion"
    )
    assert (
        _dashscope_app_url("https://dashscope.aliyuncs.com/compatible-mode/v1", "210965")
        == "https://dashscope.aliyuncs.com/api/v1/apps/210965/completion"
    )
