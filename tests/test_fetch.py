import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import fetch


def test_page_still_challenged_detects_marker():
    assert fetch.page_still_challenged("<html>Just a moment...</html>")


def test_page_still_challenged_clean_page():
    assert not fetch.page_still_challenged("<html><body>Hello world</body></html>")


def test_parse_chrome_major_version():
    assert fetch.parse_chrome_major_version("Google Chrome 148.0.7778.215") == 148


def test_parse_chrome_major_version_no_match():
    assert fetch.parse_chrome_major_version("not a version string") is None


def _response_received(status, doc_type, frame_id):
    return {
        "message": json.dumps(
            {
                "message": {
                    "method": "Network.responseReceived",
                    "params": {
                        "type": doc_type,
                        "frameId": frame_id,
                        "response": {"status": status},
                    },
                }
            }
        )
    }


def test_extract_status_from_logs_picks_last_document_status():
    logs = [
        _response_received(302, "Document", "main"),
        _response_received(200, "Document", "main"),
        _response_received(200, "Image", "main"),
    ]
    assert fetch.extract_status_from_logs(logs) == 200


def test_extract_status_from_logs_ignores_other_frames():
    logs = [
        _response_received(403, "Document", "iframe-1"),
        _response_received(200, "Document", "main"),
    ]
    assert fetch.extract_status_from_logs(logs, main_frame_id="main") == 200


def test_extract_status_from_logs_no_documents_returns_none():
    logs = [_response_received(200, "Script", "main")]
    assert fetch.extract_status_from_logs(logs) is None


def _make_cookie_db(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute("CREATE TABLE cookies (host_key TEXT, name TEXT)")
    conn.executemany("INSERT INTO cookies (host_key, name) VALUES (?, ?)", rows)
    conn.commit()
    conn.close()


def test_reset_domain_deletes_only_matching_cookies(tmp_path):
    cookie_db = tmp_path / "Default" / "Network" / "Cookies"
    _make_cookie_db(
        cookie_db,
        [
            ("example.com", "session"),
            ("sub.example.com", "session"),
            ("other.com", "session"),
        ],
    )
    fetch._reset_domain_locked("example.com", profile_dir=tmp_path)
    conn = sqlite3.connect(str(cookie_db))
    remaining = conn.execute("SELECT host_key FROM cookies").fetchall()
    conn.close()
    assert remaining == [("other.com",)]


def test_reset_domain_no_profile_yet(tmp_path, capsys):
    result = fetch._reset_domain_locked("example.com", profile_dir=tmp_path)
    assert result == 0
    assert "nothing to reset" in capsys.readouterr().out
