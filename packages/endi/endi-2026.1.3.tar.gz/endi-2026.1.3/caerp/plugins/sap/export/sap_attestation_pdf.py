import io
from typing import Tuple

from caerp.utils.compat import Iterable
from caerp.utils.pdf import (
    HTMLWithHeadersAndFooters,
    Overlay,
    fetch_resource,
    weasyprint_pdf_css,
)

from ..models.sap import SAPAttestation, SAPAttestationLine


def _pdf_renderer(attestation: SAPAttestation, lines: Iterable[Tuple], request):
    footer = Overlay(
        panel_name="sap_attestation_pdf_footer",
        context_dict={"context": attestation},
    )
    content = request.layout_manager.render_panel(
        "sap_attestation_pdf_content",
        context=attestation,
        lines=lines,
    )
    html_object = HTMLWithHeadersAndFooters(
        request,
        content,
        footer_overlay=footer,
        url_fetcher=fetch_resource,
        base_url=".",
    )
    return html_object


def sap_attestation_pdf(
    attestation: SAPAttestation,
    lines: Iterable[SAPAttestationLine],
    request,
):
    result = io.BytesIO()
    html_object = _pdf_renderer(attestation, lines, request)
    html_object.write_pdf(result, stylesheets=weasyprint_pdf_css())
    result.seek(0)
    return result
