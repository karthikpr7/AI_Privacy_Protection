from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT
from xml.sax.saxutils import escape


def create_protected_pdf(
    masked_text,
    output_path
):
    """
    Create a new PDF containing the protected/masked text.
    """

    document = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    body_style = styles["BodyText"]
    body_style.alignment = TA_LEFT
    body_style.leading = 16

    story = []

    for line in masked_text.splitlines():

        if line.strip():

            story.append(
                Paragraph(
                    escape(line),
                    body_style
                )
            )

            story.append(
                Spacer(1, 8)
            )

    if not story:

        story.append(
            Paragraph(
                "No text available.",
                body_style
            )
        )

    document.build(story)