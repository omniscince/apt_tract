from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
import os
from django.conf import settings as django_settings
from decimal import Decimal

COMPANY_NAME = "Autoprotinting INC."
COMPANY_ADDRESS = "44 Edwin Pearson Street"
COMPANY_CITY = "Aurora, ON, L4G 0S1"
COMPANY_COUNTRY = "Canada"
COMPANY_PHONE = "(647) 771-1112"
COMPANY_EMAIL = "autoprotinting@gmail.com"
COMPANY_HST = "HST# 73543 4672 RC0001"


def get_logo():
    possible_paths = [
        os.path.join(os.path.dirname(__file__), '..', 'static', 'images', 'logoDark.png'),
        os.path.join(os.path.dirname(__file__), '..', 'static', 'images', 'logo.png'),
    ]
    for path in possible_paths:
        path = os.path.normpath(path)
        if os.path.exists(path):
            return path
    return None


def generate_invoice_pdf(response, invoice):
    doc = SimpleDocTemplate(response, pagesize=letter,
                            rightMargin=0.5*inch, leftMargin=0.5*inch,
                            topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    story = []

    bold_style = ParagraphStyle('Bold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10)
    company_style = ParagraphStyle('CompanyName', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=15, spaceAfter=0, spaceBefore=0, leading=18)
    normal_style = ParagraphStyle('Normal2', parent=styles['Normal'], fontSize=9)
    small_style = ParagraphStyle('Small', parent=styles['Normal'], fontSize=8)
    title_style = ParagraphStyle('Title2', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=16, alignment=TA_CENTER)
    right_style = ParagraphStyle('Right', parent=styles['Normal'], fontSize=9, alignment=TA_RIGHT)
    right_bold = ParagraphStyle('RightBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, alignment=TA_RIGHT)
    right_bold_large = ParagraphStyle('RightBoldLarge', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, alignment=TA_RIGHT)

    # Logo
    logo_path = get_logo()
    if logo_path:
        logo = Image(logo_path, width=1.8*inch, height=0.7*inch)
        logo_cell = logo
    else:
        logo_cell = Paragraph('<b><font size=14>///APT</font></b>', bold_style)

    # Header: company info left, logo + invoice info right
    header_data = [
        [
            Paragraph(f"<b>{COMPANY_NAME}</b>", company_style),
            logo_cell,
        ],
        [
            Paragraph(COMPANY_ADDRESS, normal_style),
            Paragraph(f"<b>Invoice Number: {invoice.invoice_number}</b>", right_bold),
        ],
        [
            Paragraph(COMPANY_CITY, normal_style),
            Paragraph(f"PO Number: {invoice.po_number or 'N/A'}", right_style),
        ],
        [
            Paragraph(COMPANY_COUNTRY, normal_style),
            Paragraph(f"Work Order Close Date: {invoice.last_edit_date.strftime('%B %d, %Y') if invoice.last_edit_date else ''}", right_style),
        ],
        [
            Paragraph(COMPANY_PHONE, normal_style),
            Paragraph(f"Invoice Date: {invoice.invoice_date.strftime('%B %d, %Y')}", right_style),
        ],
        [
            Paragraph(COMPANY_EMAIL, normal_style),
            Paragraph("Net Terms: DUE UPON RECEIPT", right_style),
        ],
        [
            Paragraph(COMPANY_HST, normal_style),
            '',
        ],
    ]

    header_table = Table(header_data, colWidths=[4*inch, 3.5*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 1),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.15*inch))

    # Horizontal line
    line_data = [['', '']]
    line_table = Table(line_data, colWidths=[7.5*inch])
    line_table.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(line_table)
    story.append(Spacer(1, 0.15*inch))

    # Billing Address
    customer_name = invoice.get_customer_display()
    if invoice.customer:
        c = invoice.customer
        addr_lines = [customer_name]
        if c.company:
            addr_lines.insert(0, c.company)
        if c.address:
            addr_lines.append(c.address)
        if c.city or c.province:
            addr_lines.append(f"{c.city}, {c.province}")
        if c.phone:
            addr_lines.append(f"Primary Phone: {c.phone}")
        emails = c.get_all_emails()
        if emails:
            addr_lines.append(f"Email: {', '.join(emails)}")
        billing_text = '<br/>'.join(addr_lines)
    else:
        billing_text = customer_name

    billing_data = [
        [
            Paragraph("<b>Billing Address:</b>", bold_style),
            Paragraph("<b>Service Address:</b>", bold_style),
        ],
        [
            Paragraph(billing_text, normal_style),
            Paragraph("Same as Billing Address", normal_style),
        ],
    ]

    billing_table = Table(billing_data, colWidths=[4*inch, 3.5*inch])
    billing_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(billing_table)
    story.append(Spacer(1, 0.15*inch))

    # Car info box
    car_display = invoice.get_car_display()
    car_data = [[Paragraph(f"<b>{car_display}</b>", bold_style)]]
    car_table = Table(car_data, colWidths=[7.5*inch])
    car_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f0f0')),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(car_table)
    story.append(Spacer(1, 0.05*inch))

    # Items table with header
    items_header = [
        Paragraph('<b>Description</b>', bold_style),
        Paragraph('<b>Amount</b>', right_bold),
    ]
    items_data = [items_header]
    for item in invoice.items.all():
        items_data.append([
            Paragraph(item.description, normal_style),
            Paragraph(f"${item.price:,.2f}", right_style),
        ])

    items_table = Table(items_data, colWidths=[6*inch, 1.5*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f0f0')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.black),
        ('INNERGRID', (0, 1), (-1, -1), 0.25, colors.HexColor('#dddddd')),
        ('PADDING', (0, 0), (-1, -1), 7),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.15*inch))

    story.append(Paragraph("Thank you for your business", normal_style))
    story.append(Spacer(1, 0.15*inch))

    # Work completed by + Generated by
    worker_lines = []
    if invoice.work_completed_by:
        worker_lines.append(f"<b>Work completed by:</b> {invoice.work_completed_by.get_full_name()}")

    # Totals
    subtotal = invoice.subtotal
    hst_rate = getattr(django_settings, 'HST_RATE', Decimal('0.13'))
    hst = invoice.hst
    total = invoice.total

    totals_rows = [
        ['', Paragraph('<b>Subtotal:</b>', right_style), Paragraph(f'${subtotal:,.2f}', right_style)],
    ]

    if hst_rate > 0:
        totals_rows.append(
            ['', Paragraph(f'<b>HST ({int(hst_rate * 100)}%):</b>', right_style), Paragraph(f'${hst:,.2f}', right_style)]
        )

    totals_rows.append(
        ['', Paragraph('<b>Total:</b>', right_bold_large), Paragraph(f'<b>${total:,.2f}</b>', right_bold_large)]
    )

    # Worker info left, totals right
    if worker_lines:
        worker_para = Paragraph('<br/>'.join(worker_lines), normal_style)
    else:
        worker_para = Paragraph('', normal_style)

    bottom_data = [[worker_para, '']]
    bottom_table = Table(bottom_data, colWidths=[4*inch, 3.5*inch])
    bottom_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(bottom_table)

    totals_table = Table(totals_rows, colWidths=[4.5*inch, 1.5*inch, 1.5*inch])
    totals_table.setStyle(TableStyle([
        ('LINEABOVE', (1, -1), (2, -1), 1, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(totals_table)

    doc.build(story)


def generate_monthly_report_pdf(response, invoices):
    import calendar
    from django.utils import timezone

    doc = SimpleDocTemplate(response, pagesize=letter,
                            rightMargin=0.5*inch, leftMargin=0.5*inch,
                            topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    story = []

    bold_style = ParagraphStyle('Bold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10)
    company_style = ParagraphStyle('CompanyName', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=15, spaceAfter=0, spaceBefore=0, leading=18)
    normal_style = ParagraphStyle('Normal2', parent=styles['Normal'], fontSize=9)
    title_style = ParagraphStyle('Title2', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=14, alignment=TA_CENTER)
    right_style = ParagraphStyle('Right', parent=styles['Normal'], fontSize=9, alignment=TA_RIGHT)
    right_bold = ParagraphStyle('RightBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, alignment=TA_RIGHT)

    logo_path = get_logo()
    if logo_path:
        logo = Image(logo_path, width=1.8*inch, height=0.7*inch)
        logo_cell = logo
    else:
        logo_cell = Paragraph('<b>///APT</b>', bold_style)

    header_data = [
        [Paragraph(f"<b>{COMPANY_NAME}</b>", bold_style), logo_cell],
        [Paragraph(COMPANY_ADDRESS, normal_style), ''],
        [Paragraph(COMPANY_CITY, normal_style), ''],
        [Paragraph(COMPANY_PHONE, normal_style), ''],
        [Paragraph(COMPANY_EMAIL, normal_style), ''],
        [Paragraph(COMPANY_HST, normal_style), ''],
    ]

    header_table = Table(header_data, colWidths=[4*inch, 3.5*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.1*inch))

    today = timezone.now().strftime('%B %d, %Y')
    story.append(Paragraph(f"<b>Invoice Statement</b> — Generated: {today}", title_style))
    story.append(Spacer(1, 0.2*inch))

    table_data = [[
        Paragraph('<b>Invoice #</b>', bold_style),
        Paragraph('<b>Date</b>', bold_style),
        Paragraph('<b>Customer</b>', bold_style),
        Paragraph('<b>Car</b>', bold_style),
        Paragraph('<b>Staff</b>', bold_style),
        Paragraph('<b>Total</b>', bold_style),
    ]]

    grand_total = 0
    for inv in invoices:
        grand_total += inv.total
        table_data.append([
            Paragraph(inv.invoice_number, normal_style),
            Paragraph(inv.invoice_date.strftime('%B %d, %Y'), normal_style),
            Paragraph(inv.get_customer_display(), normal_style),
            Paragraph(inv.get_car_display()[:30], normal_style),
            Paragraph(inv.created_by.get_full_name() if inv.created_by else '', normal_style),
            Paragraph(f'${inv.total:,.2f}', right_style),
        ])

    table_data.append([
        '', '', '', '',
        Paragraph('<b>Total:</b>', right_bold),
        Paragraph(f'<b>${grand_total:,.2f}</b>', right_bold),
    ])

    col_widths = [1.2*inch, 0.9*inch, 1.7*inch, 1.5*inch, 1.2*inch, 1*inch]
    inv_table = Table(table_data, colWidths=col_widths)
    inv_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f0f0')),
        ('BOX', (0, 0), (-1, -2), 0.5, colors.black),
        ('INNERGRID', (0, 0), (-1, -2), 0.25, colors.HexColor('#dddddd')),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEABOVE', (0, -1), (-1, -1), 0.5, colors.black),
    ]))
    story.append(inv_table)
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Thank you for your business", normal_style))

    doc.build(story)