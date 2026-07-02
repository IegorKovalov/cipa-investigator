import sys
from browser import capture
from classifier import classify
from agent_legal import write_legal_narrative
from reporter import generate

if len(sys.argv) < 2:
    print("Usage: python test_phase1.py <url>")
    sys.exit(1)
url = sys.argv[1]
output = "evidence_package.pdf"

print(f"CIPA Evidence Scanner")
print(f"Target: {url}")
print("=" * 60)

evidence = capture(url, headless=False)
findings = classify(evidence)
findings = write_legal_narrative(findings)
generate(findings, evidence["screenshots"], output)

print("\n" + "=" * 60)
print(f"SUMMARY")
print("=" * 60)
print(f"Wiretap violations (§631):      {findings['summary']['wiretap_count']}")
print(f"Pen register violations (§638.51): {findings['summary']['pen_register_count']}")
print(f"Consent mechanism present:      {'No' if findings['summary']['no_consent_mechanism'] else 'Yes'}")
print(f"Trackers before banner:         {findings['summary']['trackers_before_banner']}")
print(f"\nEvidence package saved to: {output}")
