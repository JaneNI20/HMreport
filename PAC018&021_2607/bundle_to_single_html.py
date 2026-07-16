from __future__ import annotations

import base64
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "index.html"
OUT = ROOT / "移动空调概念测试（PAC018&P021）v28.9_rebundled.html"

source = INDEX.read_text(encoding="utf-8")
pages_match = re.search(r"const pages = (.*?);\n    const sections = ", source, re.S)
if not pages_match:
    raise RuntimeError("Cannot find pages data in index.html")
pages = json.loads(pages_match.group(1))

bundled = []
for page in pages:
    html = (ROOT / page["src"]).read_text(encoding="utf-8")
    new_page = dict(page)
    new_page.pop("src", None)
    new_page["kind"] = "iframe"
    new_page["srcdoc_b64"] = base64.b64encode(html.encode("utf-8")).decode("ascii")
    bundled.append(new_page)

pages_json = json.dumps(bundled, ensure_ascii=False)
source = source[: pages_match.start(1)] + pages_json + source[pages_match.end(1) :]

source = re.sub(
    r"    function renderIframe\(page\) \{.*?    \}\n",
    """    function decodeBase64Utf8(value) {
      const binary = atob(value);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
      return new TextDecoder('utf-8').decode(bytes);
    }

    function renderIframe(page) {
      inlineWrap.hidden = true;
      iframeWrap.hidden = false;
      frame.removeAttribute('src');
      frame.removeAttribute('srcdoc');
      if (page.srcdoc_b64) {
        frame.srcdoc = decodeBase64Utf8(page.srcdoc_b64);
      } else {
        frame.src = page.src;
      }
    }
""",
    source,
    count=1,
    flags=re.S,
)

OUT.write_text(source, encoding="utf-8", newline="\n")
print(OUT)
