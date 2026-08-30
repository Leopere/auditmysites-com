from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "docs/index.html").read_text()
JS = (ROOT / "docs/assessment-form.js").read_text()
WORKFLOW = (ROOT / ".github/workflows/pages.yml").read_text()
SVG_PATH = ROOT / "docs/audit-evidence.svg"
SVG = SVG_PATH.read_text()


def relative_luminance(hex_color):
    channels = [int(hex_color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(foreground, background):
    lighter, darker = sorted((relative_luminance(foreground), relative_luminance(background)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


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
assert '<form class="assessment-form" id="assessment-form" method="post">' in HTML
assert 'id="submit-request" type="submit" disabled' in HTML
assert {"name", "email", "phone", "site_url", "message", "consent"} <= parser.required
assert {"name", "email", "phone", "site-url", "market", "message"} <= parser.labels
assert parser.status
assert HTML.count('href="#request"') == 2
assert "https://forms.motherboardrepair.ca" in HTML
assert '<script src="assessment-form.js" defer></script>' in HTML
assert "https://forms.motherboardrepair.ca/api/form-proof" in JS
assert "https://forms.motherboardrepair.ca/api/submit" in JS
assert "auditmysites_assessment" in JS
assert "window.location.origin + window.location.pathname" in JS
assert '<img class="hero-artwork" src="audit-evidence.svg" alt="" width="760" height="680" decoding="async">' in HTML
assert HTML.count('src="audit-evidence.svg"') == 1
assert "aenow" not in HTML.lower()
svg_root = ElementTree.parse(SVG_PATH).getroot()
assert svg_root.tag == "{http://www.w3.org/2000/svg}svg"
assert svg_root.attrib["viewBox"] == "0 0 760 680"
assert "width" not in svg_root.attrib and "height" not in svg_root.attrib
assert SVG_PATH.stat().st_size < 12_000
for forbidden_svg_content in ("<script", "<image", "<foreignobject", "href=", "url("):
    assert forbidden_svg_content not in SVG.lower()
deliverables_eyebrow_rule = HTML.split(".deliverables .eyebrow {", 1)[1].split("}", 1)[0]
assert "color: #08745f;" in deliverables_eyebrow_rule
assert contrast_ratio("#08745f", "#ffffff") >= 4.5
assert "runs-on: [self-hosted, Linux, ARM64, leopere, local, public-safe]" in WORKFLOW
assert "path: ./docs" in WORKFLOW
print("site contract passed")
