import typst
import marimo as mo

SETUP = """

#show math.equation: it => context {
  // only wrap in frame on html export
  if target() == "html" {
    
    show: if it.block { it => it } else { box }
    html.frame(it)
  } else {
    it
  }
}

#show math.equation.where(block: false): box

"""

HTML_TEMPLATE = """
<marimo-typst>
    {content}
</marimo-typst>

<script>
class MarimoTypst extends HTMLElement {{
    constructor() {{
        super();
    }}
}}
customElements.define('marimo-typst', MarimoTypst);
</script>

<style>
    marimo-typst {{
        display: block;
        padding: 1rem;
    }}
    
    marimo-typst h1 {{
        font-size: 1.5rem;
        margin-bottom: 0.5rem;
    }}
    marimo-typst h2 {{
        font-size: 1.25rem;
        margin-bottom: 0.5rem;
    }}
</style>
"""


class MoTypst:
    def __init__(self, typst_text: str, format="html"):
        raw_typst = SETUP + typst_text
        compiled_html = typst.compile(raw_typst.encode(), format=format)

        self.html_content = compiled_html.decode()

    def _display_(self):
        rendered = HTML_TEMPLATE.format(content=self.html_content)
        return mo.Html(rendered)
