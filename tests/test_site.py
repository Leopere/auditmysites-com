from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "docs/index.html").read_text()
JS = (ROOT / "docs/assessment-form.js").read_text()
WORKFLOW = (ROOT / ".github/workflows/pages.yml").read_text()
IMAGE_SOURCES = (ROOT / "docs/IMAGE_SOURCES.md").read_text()
PHOTO_PATHS = [
    ROOT / "docs/aenow-collaboration.avif",
    ROOT / "docs/aenow-collaboration.webp",
    ROOT / "docs/aenow-workspace.avif",
    ROOT / "docs/aenow-workspace.webp",
]


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
assert '<picture class="hero-photo hero-photo-main" data-source="aenow.com/application/files/7117/6409/3218/collab.webp">' in HTML
assert '<source srcset="aenow-collaboration.avif" type="image/avif">' in HTML
assert '<img src="aenow-collaboration.webp" alt="" width="960" height="540" loading="eager" decoding="async" fetchpriority="high">' in HTML
assert '<picture class="hero-photo hero-photo-inset" data-source="aenow.com/application/files/7816/6741/8419/dom-blog.jpg">' in HTML
assert '<source srcset="aenow-workspace.avif" type="image/avif">' in HTML
assert '<img src="aenow-workspace.webp" alt="" width="1920" height="860" loading="eager" decoding="async">' in HTML
assert '<meta name="description" content="Evidence-based website assessments across search, security, performance, content, and accessibility for people, assistive technology, and AI agents.">' in HTML
assert "Audit My Sites combines a focused site crawl, broad technical checks, search-demand evidence, and accessibility review for people and AI agents in one clear assessment." in HTML
assert all(path.exists() and path.stat().st_size < 120_000 for path in PHOTO_PATHS)
assert sum(path.stat().st_size for path in PHOTO_PATHS) < 350_000
assert "The source archive did not include license, permission, or attribution metadata." in IMAGE_SOURCES
assert "https://aenow.com/application/files/7117/6409/3218/collab.webp" in IMAGE_SOURCES
assert "https://aenow.com/application/files/7816/6741/8419/dom-blog.jpg" in IMAGE_SOURCES
assert "<h3>Accessibility for people and AI agents</h3>" in HTML
assert "assistive technology, browser-based AI agents, traditional search engines, answer engines, and generative systems" in HTML
assert "Accessibility findings are bounded observations, not certification or a guarantee of conformance." in HTML
responsive_hero_rule = HTML.split("@media (max-width: 980px) {", 1)[1].split("@media (max-width: 760px) {", 1)[0]
assert ".hero-art { display: none; }" not in responsive_hero_rule
assert ".hero-photo-inset { display: none; }" in responsive_hero_rule
deliverables_eyebrow_rule = HTML.split(".deliverables .eyebrow {", 1)[1].split("}", 1)[0]
assert "color: #08745f;" in deliverables_eyebrow_rule
assert contrast_ratio("#08745f", "#ffffff") >= 4.5
assert "runs-on: [self-hosted, Linux, ARM64, leopere, local, public-safe]" in WORKFLOW
assert "path: ./docs" in WORKFLOW
print("site contract passed")
