from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "docs/index.html").read_text()
JS = (ROOT / "docs/assessment-form.js").read_text()
WORKFLOW = (ROOT / ".github/workflows/pages.yml").read_text()


class FormParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.forms, self.labels, self.required = [], set(), set()
        self.status = False

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "form": self.forms.append(values.get("id"))
        if tag == "label" and values.get("for"): self.labels.add(values["for"])
        if tag in {"input", "textarea"} and "required" in values: self.required.add(values.get("name"))
        if values.get("id") == "form-status" and values.get("role") == "status": self.status = True


parser = FormParser()
parser.feed(HTML)
assert parser.forms == ["assessment-form"]
assert {"name", "email", "phone", "site_url", "message", "consent"} <= parser.required
assert {"name", "email", "phone", "site-url", "market", "message"} <= parser.labels
assert parser.status
assert HTML.count('href="#request"') == 2
assert "https://forms.motherboardrepair.ca" in HTML
assert '<script src="assessment-form.js" defer></script>' in HTML
assert "https://forms.motherboardrepair.ca/api/form-proof" in JS
assert "https://forms.motherboardrepair.ca/api/submit" in JS
assert "auditmysites_assessment" in JS
assert "runs-on: [self-hosted, Linux, ARM64, leopere, local, public-safe]" in WORKFLOW
assert "path: ./docs" in WORKFLOW
print("site contract passed")
