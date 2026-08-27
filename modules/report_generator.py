from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable
)
from reportlab.lib.colors import HexColor


def generate_report(result, document_name="Text Input"):
    """
    Generates the web-page report text.
    Kept for compatibility with detector.py.
    """

    detections = result.get("detections", [])
    risk = result.get("risk", {})

    score = risk.get("score", 0)
    level = risk.get("level", "LOW")

    lines = []

    lines.append("AI-Based Privacy Protection")
    lines.append("----------------------------------------")
    lines.append(f"Document: {document_name}")
    lines.append("")

    lines.append(
        f"Total PII Detected: {len(detections)}"
    )

    lines.append(
        f"Privacy Score: {score}/100"
    )

    lines.append(
        f"Risk Level: {level}"
    )

    lines.append("")
    lines.append("Detected PII:")

    counts = {}

    for detection in detections:

        entity = detection.get(
            "label",
            detection.get("entity", "UNKNOWN")
        )

        counts[entity] = counts.get(entity, 0) + 1

    for entity in sorted(counts):

        lines.append(
            f"{entity}: {counts[entity]}"
        )

    lines.append("")
    lines.append("Recommendation:")

    if level == "CRITICAL":

        lines.append(
            "Critical privacy risk detected. "
            "Protect or mask sensitive information before sharing."
        )

    elif level == "HIGH":

        lines.append(
            "High privacy risk detected. "
            "Protect sensitive information before sharing."
        )

    elif level == "MEDIUM":

        lines.append(
            "Moderate privacy risk detected. "
            "Review sensitive information before sharing."
        )

    else:

        lines.append(
            "Low privacy risk detected. "
            "Review the detected information before sharing."
        )

    return "\n".join(lines)


def generate_privacy_report_pdf(
    output_path,
    result,
    document_name="Text Input"
):

    detections = result.get(
        "detections",
        []
    )

    risk = result.get(
        "risk",
        {}
    )

    score = risk.get(
        "score",
        0
    )

    risk_level = risk.get(
        "level",
        "LOW"
    )

    total_pii = len(detections)

    # --------------------------------------------------
    # COLORS
    # --------------------------------------------------

    NAVY = HexColor("#111827")
    INDIGO = HexColor("#4F46E5")
    RED = HexColor("#DC2626")
    RED_BG = HexColor("#FEF2F2")
    GREEN = HexColor("#059669")

    TEXT = HexColor("#1F2937")
    MUTED = HexColor("#64748B")
    LIGHT = HexColor("#F8FAFC")
    BORDER = HexColor("#E2E8F0")

    # --------------------------------------------------
    # DOCUMENT
    # --------------------------------------------------

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=18 * mm,
        title="AI-Based Privacy Protection Report",
        author="AI-Based Privacy Protection"
    )

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="Brand",
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=colors.white
        )
    )

    styles.add(
        ParagraphStyle(
            name="Meta",
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=HexColor("#CBD5E1")
        )
    )

    styles.add(
        ParagraphStyle(
            name="Eyebrow",
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=INDIGO,
            tracking=1.2
        )
    )

    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=29,
            textColor=NAVY
        )
    )

    styles.add(
        ParagraphStyle(
            name="Body",
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            textColor=TEXT
        )
    )

    styles.add(
        ParagraphStyle(
            name="Muted",
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=MUTED
        )
    )

    styles.add(
        ParagraphStyle(
            name="Label",
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=10,
            textColor=MUTED,
            tracking=0.8
        )
    )

    styles.add(
        ParagraphStyle(
            name="Score",
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=28,
            textColor=NAVY
        )
    )

    styles.add(
        ParagraphStyle(
            name="Risk",
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=RED
        )
    )

    styles.add(
        ParagraphStyle(
            name="Section",
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=NAVY
        )
    )

    styles.add(
        ParagraphStyle(
            name="TableHead",
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=10,
            textColor=MUTED
        )
    )

    styles.add(
        ParagraphStyle(
            name="TableCell",
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=TEXT
        )
    )

    styles.add(
        ParagraphStyle(
            name="Recommendation",
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=14,
            textColor=HexColor("#991B1B")
        )
    )

    story = []

    # --------------------------------------------------
    # HEADER
    # --------------------------------------------------

    from datetime import datetime

    generated = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    header = Table(
        [[
            Paragraph(
                "AI-Based Privacy Protection",
                styles["Brand"]
            ),

            Paragraph(
                f"<b>PRIVACY ANALYSIS REPORT</b><br/>"
                f"Document: {document_name}<br/>"
                f"Generated: {generated}",
                styles["Meta"]
            )
        ]],
        colWidths=[
            105 * mm,
            65 * mm
        ]
    )

    header.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                NAVY
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                14
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                14
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                13
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                13
            )
        ])
    )

    story += [
        header,
        Spacer(1, 9 * mm),

        Paragraph(
            "PRIVACY OVERVIEW",
            styles["Eyebrow"]
        ),

        Spacer(1, 2 * mm),

        Paragraph(
            "Privacy analysis completed",
            styles["ReportTitle"]
        ),

        Spacer(1, 2 * mm),

        Paragraph(
            "Sensitive information was detected and "
            "a project-defined privacy risk score was calculated.",
            styles["Body"]
        ),

        Spacer(1, 6 * mm)
    ]

    # --------------------------------------------------
    # SUMMARY CARDS
    # --------------------------------------------------

    cards = Table(
        [[
            [
                Paragraph(
                    "PRIVACY SCORE",
                    styles["Label"]
                ),

                Paragraph(
                    f"<b>{score}</b>"
                    "<font size='10'>/100</font>",
                    styles["Score"]
                )
            ],

            [
                Paragraph(
                    "RISK LEVEL",
                    styles["Label"]
                ),

                Paragraph(
                    risk_level,
                    styles["Risk"]
                )
            ],

            [
                Paragraph(
                    "TOTAL PII",
                    styles["Label"]
                ),

                Paragraph(
                    f"<b>{total_pii}</b>",
                    styles["Score"]
                )
            ]
        ]],
        colWidths=[
            56 * mm,
            56 * mm,
            56 * mm
        ]
    )

    cards.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                LIGHT
            ),

            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.7,
                BORDER
            ),

            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.7,
                BORDER
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                10
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                10
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                10
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                10
            )
        ])
    )

    story += [
        cards,
        Spacer(1, 7 * mm),

        Paragraph(
            "<b>Overall privacy exposure</b>",
            styles["Body"]
        ),

        Spacer(1, 2 * mm)
    ]

    # --------------------------------------------------
    # SCORE BAR
    # --------------------------------------------------

    bar = Table(
        [[""]],
        colWidths=[168 * mm],
        rowHeights=[5 * mm]
    )

    bar.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                RED
            )
        ])
    )

    story += [
        bar,
        Spacer(1, 1.5 * mm),

        Paragraph(
            f"{score}/100 — "
            f"{risk_level} privacy exposure based on "
            f"detected sensitive information.",
            styles["Muted"]
        ),

        Spacer(1, 7 * mm),

        Paragraph(
            "Detected PII",
            styles["Section"]
        ),

        Spacer(1, 2 * mm),

        Paragraph(
            "Sensitive entities identified by the "
            "privacy detection system.",
            styles["Muted"]
        ),

        Spacer(1, 4 * mm)
    ]

    # --------------------------------------------------
    # DETECTION TABLE
    # --------------------------------------------------

    table_data = [[
        Paragraph(
            "ENTITY",
            styles["TableHead"]
        ),

        Paragraph(
            "VALUE",
            styles["TableHead"]
        ),

        Paragraph(
            "METHOD",
            styles["TableHead"]
        ),

        Paragraph(
            "RISK",
            styles["TableHead"]
        )
    ]]

    for detection in detections:

        entity = detection.get(
            "label",
            detection.get(
                "entity",
                "UNKNOWN"
            )
        )

        value = detection.get(
            "value",
            ""
        )

        method = detection.get(
            "source",
            "UNKNOWN"
        )

        entity_upper = str(
            entity
        ).upper()

        if entity_upper in {
            "AADHAAR",
            "CREDITCARDNUMBER",
            "BANKACCOUNT"
        }:

            entity_risk = "CRITICAL"

        elif entity_upper in {
            "PAN",
            "IFSC"
        }:

            entity_risk = "HIGH"

        elif entity_upper in {
            "EMAIL",
            "TELEPHONENUM"
        }:

            entity_risk = "MEDIUM"

        else:

            entity_risk = "LOW"

        table_data.append([
            Paragraph(
                str(entity),
                styles["TableCell"]
            ),

            Paragraph(
                str(value),
                styles["TableCell"]
            ),

            Paragraph(
                str(method).upper(),
                styles["TableCell"]
            ),

            Paragraph(
                entity_risk,
                styles["TableCell"]
            )
        ])

    detection_table = Table(
        table_data,
        colWidths=[
            43 * mm,
            62 * mm,
            30 * mm,
            30 * mm
        ],
        repeatRows=1
    )

    detection_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                HexColor("#F1F5F9")
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                BORDER
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                7
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                7
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                7
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                7
            )
        ])
    )

    story += [
        detection_table,
        Spacer(1, 7 * mm)
    ]

    # --------------------------------------------------
    # RECOMMENDATION
    # --------------------------------------------------

    if risk_level == "CRITICAL":

        recommendation = (
            "Critical privacy risk detected. "
            "Protect or mask sensitive information "
            "before sharing."
        )

    elif risk_level == "HIGH":

        recommendation = (
            "High privacy risk detected. "
            "Protect sensitive information before sharing."
        )

    elif risk_level == "MEDIUM":

        recommendation = (
            "Moderate privacy risk detected. "
            "Review sensitive information before sharing."
        )

    else:

        recommendation = (
            "Low privacy risk detected. "
            "Review the detected information before sharing."
        )

    recommendation_box = Table(
        [[
            Paragraph(
                "<b>RECOMMENDATION</b><br/><br/>"
                + recommendation,
                styles["Recommendation"]
            )
        ]],
        colWidths=[
            163 * mm
        ]
    )

    recommendation_box.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                RED_BG
            ),

            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.8,
                HexColor("#FECACA")
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                12
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                12
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                11
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                11
            )
        ])
    )

    story += [
        recommendation_box,
        Spacer(1, 8 * mm),

        HRFlowable(
            width="100%",
            thickness=0.6,
            color=BORDER
        ),

        Spacer(1, 3 * mm),

        Paragraph(
            "The privacy score and risk thresholds are "
            "defined by this project and are not presented "
            "as an official privacy standard.",
            styles["Muted"]
        )
    ]

    # --------------------------------------------------
    # FOOTER
    # --------------------------------------------------

    def footer(canvas, doc):

        canvas.saveState()

        canvas.setFont(
            "Helvetica",
            7.5
        )

        canvas.setFillColor(
            MUTED
        )

        canvas.drawString(
            18 * mm,
            9 * mm,
            "AI-Based Privacy Protection"
        )

        canvas.drawRightString(
            A4[0] - 18 * mm,
            9 * mm,
            f"Page {doc.page}"
        )

        canvas.restoreState()

    doc.build(
        story,
        onFirstPage=footer,
        onLaterPages=footer
    )