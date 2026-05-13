from app.storage.db import JobStore


def test_job_lifecycle(tmp_path):
    store = JobStore(tmp_path / "jobs.sqlite3")
    job = store.create_job("job-1", {"case_prompt": "prompt"}, {"original_video": "video.mp4"})
    assert job["status"] == "uploaded"
    assert job["metadata"]["case_prompt"] == "prompt"

    updated = store.update_status("job-1", "preprocessing")
    assert updated["status"] == "preprocessing"

    updated = store.update_paths("job-1", {"report_json": "report.json"})
    assert updated["paths"]["report_json"] == "report.json"

    failed = store.fail_job("job-1", "boom")
    assert failed["status"] == "failed"
    assert failed["error"] == "boom"

