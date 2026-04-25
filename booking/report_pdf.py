"""
report_pdf.py
─────────────
توليد PDF احترافي لتقرير الطالب باستخدام reportlab.
الاستخدام في views.py:
    from .report_pdf import generate_student_report_pdf
"""

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ─── ألوان ────────────────────────────────────────────────────
PRIMARY        = colors.HexColor("#1e40af")   # أزرق غامق
PRIMARY_LIGHT  = colors.HexColor("#dbeafe")   # أزرق فاتح
SECONDARY      = colors.HexColor("#0f766e")   # أخضر
SUCCESS        = colors.HexColor("#16a34a")
WARNING        = colors.HexColor("#d97706")
DANGER         = colors.HexColor("#dc2626")
PURPLE         = colors.HexColor("#7c3aed")
GRAY_DARK      = colors.HexColor("#1f2937")
GRAY_MID       = colors.HexColor("#6b7280")
GRAY_LIGHT     = colors.HexColor("#f3f4f6")
WHITE          = colors.white
ROW_ALT        = colors.HexColor("#f8fafc")

# ─── Styles ───────────────────────────────────────────────────
styles = getSampleStyleSheet()

H1 = ParagraphStyle(
    "H1", fontSize=22, textColor=WHITE,
    alignment=TA_CENTER, spaceAfter=4, fontName="Helvetica-Bold",
)
H2 = ParagraphStyle(
    "H2", fontSize=13, textColor=PRIMARY,
    spaceBefore=14, spaceAfter=6, fontName="Helvetica-Bold",
)
H3 = ParagraphStyle(
    "H3", fontSize=11, textColor=GRAY_DARK,
    spaceBefore=8, spaceAfter=4, fontName="Helvetica-Bold",
)
NORMAL = ParagraphStyle(
    "NORMAL_CUSTOM", fontSize=9, textColor=GRAY_DARK,
    fontName="Helvetica", leading=14,
)
SMALL = ParagraphStyle(
    "SMALL", fontSize=8, textColor=GRAY_MID, fontName="Helvetica",
)
CENTER = ParagraphStyle(
    "CENTER", fontSize=9, textColor=GRAY_DARK,
    alignment=TA_CENTER, fontName="Helvetica",
)
SUBTITLE = ParagraphStyle(
    "SUBTITLE", fontSize=10, textColor=WHITE,
    alignment=TA_CENTER, fontName="Helvetica",
)


# ─── Helpers ──────────────────────────────────────────────────

def _hr():
    return HRFlowable(width="100%", thickness=1, color=PRIMARY_LIGHT, spaceAfter=6, spaceBefore=2)


def _section_title(text, color=PRIMARY):
    """عنوان القسم مع خط ملون"""
    style = ParagraphStyle(
        "ST", fontSize=13, textColor=color,
        fontName="Helvetica-Bold", spaceBefore=18, spaceAfter=2,
    )
    return [Paragraph(text, style), _hr()]


def _kv_table(rows, col_widths=None):
    """جدول مفتاح/قيمة بسيط"""
    col_widths = col_widths or [5 * cm, 11 * cm]
    data = [[Paragraph(f"<b>{k}</b>", NORMAL), Paragraph(str(v), NORMAL)] for k, v in rows]
    t = Table(data, colWidths=col_widths, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), GRAY_LIGHT),
        ("TEXTCOLOR",  (0, 0), (0, -1), PRIMARY),
        ("FONTNAME",   (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, ROW_ALT]),
        ("GRID",       (0, 0), (-1, -1), 0.4, colors.HexColor("#e5e7eb")),
        ("PADDING",    (0, 0), (-1, -1), 6),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def _stat_boxes(items):
    """
    صناديق إحصاء ملونة في صف واحد
    items = [("Label", "Value", color), ...]
    """
    cell_data = []
    for label, value, color in items:
        cell_data.append([
            Paragraph(f"<b>{value}</b>", ParagraphStyle(
                "VAL", fontSize=18, textColor=color,
                alignment=TA_CENTER, fontName="Helvetica-Bold",
            )),
            Paragraph(label, ParagraphStyle(
                "LBL", fontSize=8, textColor=GRAY_MID,
                alignment=TA_CENTER, fontName="Helvetica",
            )),
        ])

    n = len(items)
    col_w = 16.5 * cm / n
    # نحول كل item لعمود
    rows = [[item[0] for item in cell_data], [item[1] for item in cell_data]]
    t = Table(rows, colWidths=[col_w] * n, hAlign="CENTER")
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, -1), GRAY_LIGHT),
        ("BOX",         (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("INNERGRID",   (0, 0), (-1, -1), 0.4, colors.HexColor("#e5e7eb")),
        ("PADDING",     (0, 0), (-1, -1), 10),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 0), (-1, 0), [WHITE]),
    ]))
    return t


def _section_stats_table(label, stats, color):
    """جدول إحصائيات Section واحد"""
    correct_pct = stats.get("correct_percentage", 0)
    wrong_pct   = stats.get("wrong_percentage", 0)

    data = [
        [Paragraph("<b>Metric</b>", NORMAL), Paragraph("<b>Value</b>", NORMAL)],
        ["Total Score",            str(stats.get("total_score", 0))],
        ["Questions Solved",       str(stats.get("total_questions_solved", 0))],
        ["Total Attempts",         str(stats.get("total_attempts", 0))],
        ["Correct Answers",        str(stats.get("correct_answers", 0))],
        ["Correct %",              f"{correct_pct}%"],
        ["Wrong %",                f"{wrong_pct}%"],
        ["First Try Correct",      str(stats.get("correct_on_first_try", 0))],
        ["First Try %",            f"{stats.get('first_try_percentage', 0)}%"],
        ["Used Show Answer",       str(stats.get("used_show_answer_count", 0))],
    ]

    last = stats.get("last_activity")
    if last:
        if hasattr(last, "strftime"):
            last_str = last.strftime("%Y-%m-%d %H:%M")
        else:
            last_str = str(last)[:16]
        data.append(["Last Activity", last_str])

    t = Table(data, colWidths=[8 * cm, 8 * cm], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), color),
        ("TEXTCOLOR",   (0, 0), (-1, 0), WHITE),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, ROW_ALT]),
        ("GRID",        (0, 0), (-1, -1), 0.4, colors.HexColor("#e5e7eb")),
        ("PADDING",     (0, 0), (-1, -1), 7),
        ("BACKGROUND",  (0, 1), (0, -1), GRAY_LIGHT),
        ("TEXTCOLOR",   (0, 1), (0, -1), color),
        ("FONTNAME",    (0, 1), (0, -1), "Helvetica-Bold"),
    ]))
    return t


def _by_type_table(by_type_list, color):
    """جدول breakdown per question type"""
    if not by_type_list:
        return Paragraph("No data yet.", SMALL)

    header = [
        Paragraph("<b>Question Type</b>", NORMAL),
        Paragraph("<b>Attempts</b>", NORMAL),
        Paragraph("<b>Solved</b>", NORMAL),
        Paragraph("<b>Score</b>", NORMAL),
        Paragraph("<b>Solved %</b>", NORMAL),
    ]
    data = [header]
    for item in by_type_list:
        attempts = item.get("attempts", 0)
        solved   = item.get("solved", 0)
        pct      = round(solved / attempts * 100, 1) if attempts else 0
        data.append([
            item.get("question_type", ""),
            str(attempts),
            str(solved),
            str(item.get("score") or 0),
            f"{pct}%",
        ])

    col_widths = [5 * cm, 3 * cm, 3 * cm, 3 * cm, 2.5 * cm]
    t = Table(data, colWidths=col_widths, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0), color),
        ("TEXTCOLOR",      (0, 0), (-1, 0), WHITE),
        ("FONTNAME",       (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",       (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, ROW_ALT]),
        ("GRID",           (0, 0), (-1, -1), 0.4, colors.HexColor("#e5e7eb")),
        ("PADDING",        (0, 0), (-1, -1), 7),
        ("ALIGN",          (1, 0), (-1, -1), "CENTER"),
    ]))
    return t


# ─── Header بالـ Canvas ───────────────────────────────────────

def _draw_header(canvas, doc, student_name, generated_at):
    canvas.saveState()
    # شريط علوي
    canvas.setFillColor(PRIMARY)
    canvas.rect(0, A4[1] - 3.5 * cm, A4[0], 3.5 * cm, fill=True, stroke=False)
    # عنوان
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 20)
    canvas.drawCentredString(A4[0] / 2, A4[1] - 1.6 * cm, "Student Performance Report")
    canvas.setFont("Helvetica", 10)
    canvas.drawCentredString(A4[0] / 2, A4[1] - 2.3 * cm, f"Student: {student_name}")
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(A4[0] / 2, A4[1] - 2.9 * cm, f"Generated: {generated_at}")

    # footer
    canvas.setFillColor(PRIMARY)
    canvas.rect(0, 0, A4[0], 1 * cm, fill=True, stroke=False)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(A4[0] / 2, 0.35 * cm, "Sabrlinguaa - Confidential Report")
    canvas.drawRightString(A4[0] - 1.5 * cm, 0.35 * cm, f"Page {doc.page}")

    canvas.restoreState()


# ─── الدالة الرئيسية ──────────────────────────────────────────

def generate_student_report_pdf(report: dict) -> bytes:
    """
    يأخذ dict التقرير من _build_student_report()
    ويرجع bytes جاهز للـ HttpResponse
    """
    buffer = io.BytesIO()

    basic        = report.get("basic_info", {})
    summary      = report.get("overall_summary", {})
    sections     = report.get("sections", {})
    subs         = report.get("subscriptions", {})
    generated_at = report.get("generated_at", datetime.now())

    student_name  = basic.get("full_name", "Student")
    if hasattr(generated_at, "strftime"):
        generated_str = generated_at.strftime("%Y-%m-%d %H:%M UTC")
    else:
        generated_str = str(generated_at)[:16]

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=4.2 * cm,
        bottomMargin=1.8 * cm,
    )

    def header_footer(canvas, doc):
        _draw_header(canvas, doc, student_name, generated_str)

    story = []

    # ══════════════════════════════════════════════════════════
    # 1. Basic Info
    # ══════════════════════════════════════════════════════════
    story += _section_title("Student Information", PRIMARY)
    story.append(_kv_table([
        ("Full Name",       basic.get("full_name", "-")),
        ("Email",           basic.get("email", "-")),
        ("User Type",       basic.get("user_type", "-").capitalize()),
        ("Date Joined",     str(basic.get("date_joined", "-"))[:10]),
        ("Email Verified",  "Yes" if basic.get("is_email_verified") else "No"),
        ("Phone",           basic.get("phone_number") or "-"),
    ]))
    story.append(Spacer(1, 10))

    # ══════════════════════════════════════════════════════════
    # 2. Overall Summary — Stat Boxes
    # ══════════════════════════════════════════════════════════
    story += _section_title("Overall Summary", SECONDARY)
    story.append(_stat_boxes([
        ("Total Score",      summary.get("total_score", 0),        PRIMARY),
        ("Questions Solved", summary.get("total_questions_solved", 0), SECONDARY),
        ("Total Attempts",   summary.get("total_attempts", 0),     PURPLE),
        ("Correct %",        f"{summary.get('correct_percentage', 0)}%", SUCCESS),
        ("Wrong %",          f"{summary.get('wrong_percentage', 0)}%",   DANGER),
    ]))
    story.append(Spacer(1, 8))

    # Strongest / Weakest / Most Active
    story.append(_kv_table([
        ("Strongest Skill",    summary.get("strongest_skill") or "-"),
        ("Weakest Skill",      summary.get("weakest_skill") or "-"),
        ("Most Active Section",summary.get("most_active_section") or "-"),
        ("Last Activity",      str(summary.get("last_activity") or "-")[:16]),
    ]))
    story.append(Spacer(1, 8))

    # Sections Ranking
    story.append(Paragraph("<b>Sections Ranking by Score</b>", H3))
    ranking = summary.get("sections_ranking", [])
    if ranking:
        rank_data = [[Paragraph("<b>#</b>", NORMAL),
                      Paragraph("<b>Section</b>", NORMAL),
                      Paragraph("<b>Score</b>", NORMAL)]]
        for i, item in enumerate(ranking, 1):
            rank_data.append([str(i), item.get("section", ""), str(item.get("score", 0))])
        rt = Table(rank_data, colWidths=[2 * cm, 8 * cm, 6.5 * cm], hAlign="LEFT")
        rt.setStyle(TableStyle([
            ("BACKGROUND",     (0, 0), (-1, 0), PRIMARY),
            ("TEXTCOLOR",      (0, 0), (-1, 0), WHITE),
            ("FONTNAME",       (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",       (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, ROW_ALT]),
            ("GRID",           (0, 0), (-1, -1), 0.4, colors.HexColor("#e5e7eb")),
            ("PADDING",        (0, 0), (-1, -1), 7),
            ("ALIGN",          (0, 0), (-1, -1), "CENTER"),
        ]))
        story.append(rt)
    story.append(Spacer(1, 8))

    # Skills Breakdown (all sections combined)
    story.append(Paragraph("<b>Skills Breakdown (All Sections Combined)</b>", H3))
    skills = summary.get("skills_breakdown", [])
    if skills:
        sk_data = [[
            Paragraph("<b>Skill</b>", NORMAL),
            Paragraph("<b>Attempts</b>", NORMAL),
            Paragraph("<b>Solved</b>", NORMAL),
            Paragraph("<b>Score</b>", NORMAL),
        ]]
        for sk in skills:
            sk_data.append([
                sk.get("question_type", ""),
                str(sk.get("attempts", 0)),
                str(sk.get("solved", 0)),
                str(sk.get("score", 0)),
            ])
        skt = Table(sk_data, colWidths=[5 * cm, 3.8 * cm, 3.8 * cm, 3.9 * cm], hAlign="LEFT")
        skt.setStyle(TableStyle([
            ("BACKGROUND",     (0, 0), (-1, 0), SECONDARY),
            ("TEXTCOLOR",      (0, 0), (-1, 0), WHITE),
            ("FONTNAME",       (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",       (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, ROW_ALT]),
            ("GRID",           (0, 0), (-1, -1), 0.4, colors.HexColor("#e5e7eb")),
            ("PADDING",        (0, 0), (-1, -1), 7),
            ("ALIGN",          (1, 0), (-1, -1), "CENTER"),
        ]))
        story.append(skt)

    # ══════════════════════════════════════════════════════════
    # 3. Sections Detail
    # ══════════════════════════════════════════════════════════
    section_config = [
        ("IELTS",   "ielts",   PRIMARY),
        ("STEP",    "step",    SECONDARY),
        ("ESP",     "esp",     PURPLE),
        ("General", "general", WARNING),
    ]

    for label, key, color in section_config:
        stats = sections.get(key, {})
        story += _section_title(f"{label} Section", color)

        # جدول الإحصائيات
        story.append(_section_stats_table(label, stats, color))
        story.append(Spacer(1, 8))

        # جدول by question type
        story.append(Paragraph("<b>Breakdown by Question Type</b>", H3))
        story.append(_by_type_table(stats.get("by_question_type", []), color))
        story.append(Spacer(1, 6))

    # ══════════════════════════════════════════════════════════
    # 4. Subscriptions
    # ══════════════════════════════════════════════════════════
    story += _section_title("Subscriptions", colors.HexColor("#0891b2"))
    story.append(_kv_table([
        ("Total Subscriptions", subs.get("total", 0)),
        ("Paid Subscriptions",  subs.get("paid", 0)),
    ], col_widths=[6 * cm, 10 * cm]))
    story.append(Spacer(1, 8))

    sub_list = subs.get("list", [])
    if sub_list:
        sub_header = [
            Paragraph("<b>Ref #</b>", NORMAL),
            Paragraph("<b>Program</b>", NORMAL),
            Paragraph("<b>Teacher</b>", NORMAL),
            Paragraph("<b>Amount</b>", NORMAL),
            Paragraph("<b>Status</b>", NORMAL),
            Paragraph("<b>Date</b>", NORMAL),
        ]
        sub_data = [sub_header]
        for s in sub_list:
            status_color = SUCCESS if s.get("payment_status") == "paid" else DANGER
            sub_data.append([
                str(s.get("reference_number") or "-"),
                Paragraph(str(s.get("program_title", "-")), SMALL),
                str(s.get("teacher_name", "-")),
                f"{s.get('amount', 0)} SAR",
                Paragraph(
                    f'<font color="{status_color.hexval()}">'
                    f'<b>{s.get("payment_status","").upper()}</b></font>',
                    CENTER
                ),
                str(s.get("created_at", "-"))[:10],
            ])
        sub_col = [2.5*cm, 5*cm, 3*cm, 2.5*cm, 2*cm, 2.5*cm]
        subt = Table(sub_data, colWidths=sub_col, hAlign="LEFT")
        subt.setStyle(TableStyle([
            ("BACKGROUND",     (0, 0), (-1, 0), colors.HexColor("#0891b2")),
            ("TEXTCOLOR",      (0, 0), (-1, 0), WHITE),
            ("FONTNAME",       (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",       (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, ROW_ALT]),
            ("GRID",           (0, 0), (-1, -1), 0.4, colors.HexColor("#e5e7eb")),
            ("PADDING",        (0, 0), (-1, -1), 6),
            ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(subt)
    else:
        story.append(Paragraph("No subscriptions found.", SMALL))

    # ──────────────────────────────────────────────────────────
    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    return buffer.getvalue()