import json
from pathlib import Path
from tools.generate_report import generate_html

def test_html_generation():
    comp_data = {
        "documents": {"results": [{"document": "test.md", "is_valid": True}]},
        "evidence": {"results": [{"requirement": "V1.1", "passed": False, "type": "grep", "target": "file"}]}
    }
    ver_data = {
        "tests": [{"asvs_id": "V3.5", "result": "pass", "name": "CSRF"}]
    }
    
    html = generate_html(comp_data, ver_data)
    
    assert "ASVS Compliance Dashboard" in html
    assert "66%" in html # 2 passed out of 3 total checks
    assert "test.md" in html
    assert "CSRF" in html