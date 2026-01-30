import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>ASVS Compliance Report</title>
    <style>
        body {{ font-family: system-ui, sans-serif; margin: 2rem; background: #f4f4f9; }}
        .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 1rem; }}
        .summary {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 2rem; }}
        .card {{ padding: 1rem; background: #f8f9fa; border-radius: 6px; text-align: center; }}
        .card h3 {{ margin: 0; font-size: 2rem; color: #3498db; }}
        .section {{ margin-top: 2rem; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
        th, td {{ text-align: left; padding: 0.75rem; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9fa; }}
        .badge {{ padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.875rem; font-weight: bold; }}
        .pass {{ background: #d4edda; color: #155724; }}
        .fail {{ background: #f8d7da; color: #721c24; }}
        .timestamp {{ color: #666; font-size: 0.875rem; margin-top: 2rem; text-align: right; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>ASVS Compliance Dashboard</h1>
        
        <div class="summary">
            <div class="card">
                <h3>{total_coverage}%</h3>
                <p>Compliance Coverage</p>
            </div>
            <div class="card">
                <h3>{passed_checks}</h3>
                <p>Checks Passed</p>
            </div>
            <div class="card">
                <h3>{failed_checks}</h3>
                <p>Checks Failed</p>
            </div>
        </div>

        <div class="section">
            <h2>Detailed Findings</h2>
            <table>
                <thead>
                    <tr>
                        <th>Requirement</th>
                        <th>Source</th>
                        <th>Status</th>
                        <th>Details</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>

        <div class="timestamp">Generated on: {date}</div>
    </div>
</body>
</html>
"""

def generate_html(compliance_data, verification_data):
    rows = ""
    passed = 0
    total = 0

    # Process Compliance Gate Result
    if compliance_data:
        doc_results = compliance_data.get("documents", {}).get("results", [])
        if isinstance(compliance_data.get("results"), list): 
             doc_results = compliance_data["results"]

        for doc in doc_results:
            total += 1
            status = "pass" if doc.get("is_valid") else "fail"
            if status == "pass": passed += 1
            rows += f"""
            <tr>
                <td>Documentation</td>
                <td>Compliance Gate</td>
                <td><span class="badge {status}">{status.upper()}</span></td>
                <td>{doc.get('document', 'Unknown')}</td>
            </tr>
            """
        
        # Evidence
        evidence_results = compliance_data.get("evidence", {}).get("results", [])
        for ev in evidence_results:
            total += 1
            status = "pass" if ev.get("passed") else "fail"
            if status == "pass": passed += 1
            rows += f"""
            <tr>
                <td>{ev.get('requirement')}</td>
                <td>Evidence Verifier</td>
                <td><span class="badge {status}">{status.upper()}</span></td>
                <td>{ev.get('type')}: {ev.get('target')}</td>
            </tr>
            """

    # Process Verification Suite Results
    if verification_data:
        for test in verification_data.get("tests", []):
            total += 1
            res_val = test.get("result", "")
            status = "pass" if res_val == "pass" or res_val == "TestResult.PASS" else "fail"
            if status == "pass": passed += 1
            rows += f"""
            <tr>
                <td>{test.get('asvs_id')}</td>
                <td>Verification Suite</td>
                <td><span class="badge {status}">{status.upper()}</span></td>
                <td>{test.get('name')}</td>
            </tr>
            """

    coverage = int((passed / total * 100)) if total > 0 else 0
    
    return HTML_TEMPLATE.format(
        total_coverage=coverage,
        passed_checks=passed,
        failed_checks=total - passed,
        rows=rows,
        date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--compliance-json", type=Path, help="Output from compliance_gate.py")
    parser.add_argument("--verification-json", type=Path, help="Output from verification_suite.py")
    parser.add_argument("--output", type=Path, default=Path("compliance-report.html"))
    args = parser.parse_args()

    comp_data = {}
    ver_data = {}

    if args.compliance_json and args.compliance_json.exists():
        comp_data = json.loads(args.compliance_json.read_text())
    
    if args.verification_json and args.verification_json.exists():
        ver_data = json.loads(args.verification_json.read_text())

    html = generate_html(comp_data, ver_data)
    args.output.write_text(html, encoding="utf-8")
    print(f"Report generated: {args.output}")

if __name__ == "__main__":
    main()