from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.graphics.shapes import Drawing, Path
from reportlab.graphics import renderPDF
import os

COMPANY_NAME = "Autoprotinting"
COMPANY_ADDRESS = "44 Edwin Pearson Street"
COMPANY_CITY = "Aurora, ON, L4G 0S1"
COMPANY_COUNTRY = "Canada"
COMPANY_PHONE = "(647) 771-1112"
COMPANY_EMAIL = "autoprotinting@gmail.com"
COMPANY_HST = "HST# 73543 4672 RC0001"
HST_RATE = 0.13


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
    normal_style = ParagraphStyle('Normal2', parent=styles['Normal'], fontSize=9)
    title_style = ParagraphStyle('Title2', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=14, alignment=TA_CENTER)
    right_style = ParagraphStyle('Right', parent=styles['Normal'], fontSize=9, alignment=TA_RIGHT)
    right_bold = ParagraphStyle('RightBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, alignment=TA_RIGHT)

    story.append(Paragraph("Invoice", title_style))
    story.append(Spacer(1, 0.2*inch))

    # Logo
    logo_path = get_logo()
    if logo_path and logo_path.endswith('.png'):
        logo = Image(logo_path, width=1.5*inch, height=0.6*inch)
        logo_cell = logo
    else:
        logo_cell = Paragraph('<b><font size=14>///APT</font></b>', bold_style)

    # Header
    header_data = [
        [
            Paragraph(f"<b>{COMPANY_NAME}</b>", bold_style),
            '',
            logo_cell,
        ],
        [
            Paragraph(COMPANY_ADDRESS, normal_style),
            '',
            Paragraph(f"<b>Invoice Number: {invoice.invoice_number}</b>", right_bold),
        ],
        [
            Paragraph(COMPANY_CITY, normal_style),
            '',
            Paragraph(f"PO Number: {invoice.po_number or 'N/A'}", right_style),
        ],
        [
            Paragraph(COMPANY_COUNTRY, normal_style),
            '',
            Paragraph(f"Work Order Close Date: {invoice.work_order_close_date.strftime('%m/%d/%Y') if invoice.work_order_close_date else ''}", right_style),
        ],
        [
            Paragraph(COMPANY_PHONE, normal_style),
            '',
            Paragraph(f"Invoice Date: {invoice.invoice_date.strftime('%m/%d/%Y')}", right_style),
        ],
        [
            Paragraph(COMPANY_EMAIL, normal_style),
            '',
            Paragraph("Net Terms: DUE UPON RECEIPT", right_style),
        ],
        [
            Paragraph(COMPANY_HST, normal_style),
            '',
            '',
        ],
    ]

    header_table = Table(header_data, colWidths=[3*inch, 1.5*inch, 3*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.2*inch))

    # Billing Address
    billing_data = [
        [Paragraph("<b>Billing Address:</b>", bold_style), Paragraph("<b>Service Address:</b>", bold_style)],
        [Paragraph(invoice.customer.name, normal_style), Paragraph("Same as Billing Address", normal_style)],
        [Paragraph(invoice.customer.address or '', normal_style), ''],
        [Paragraph(f"{invoice.customer.city}, {invoice.customer.province}", normal_style), ''],
        [Paragraph(f"Primary Phone: {invoice.customer.phone}", normal_style), ''],
        [Paragraph(f"Email: {invoice.customer.email}", normal_style), ''],
    ]

    billing_table = Table(billing_data, colWidths=[4*inch, 3.5*inch])
    billing_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(billing_table)
    story.append(Spacer(1, 0.2*inch))

    # Car info box
    car_title = f"{invoice.car.make} {invoice.car.model}"
    if invoice.car.stock_number or invoice.car.vin:
        car_title += f" ( Stock#: {invoice.car.stock_number}, VIN: {invoice.car.vin})"

    car_data = [[Paragraph(car_title, bold_style)]]
    car_table = Table(car_data, colWidths=[7.5*inch])
    car_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(car_table)
    story.append(Spacer(1, 0.1*inch))

    # Items
    items_data = []
    for item in invoice.items.all():
        items_data.append([
            Paragraph(f"<b>{item.description}</b>", bold_style),
            Paragraph(f"${item.price:,.2f}", right_style),
        ])

    if items_data:
        items_table = Table(items_data, colWidths=[6*inch, 1.5*inch])
        items_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(items_table)

    story.append(Spacer(1, 0.2*inch))

    if invoice.notes:
        story.append(Paragraph("<b>Comments:</b>", bold_style))
        story.append(Paragraph(invoice.notes, normal_style))
        story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("Thank you for your business", normal_style))
    story.append(Spacer(1, 0.2*inch))

    # Work completed by + Generated by
    if invoice.work_completed_by or invoice.created_by:
        worker_data = []
        if invoice.work_completed_by:
            worker_data.append([
                Paragraph(f"<b>Work completed by:</b> {invoice.work_completed_by.get_full_name()}", normal_style),
                '',
            ])
        if invoice.created_by:
            worker_data.append([
                Paragraph(f"<b>Generated By:</b> {invoice.created_by.get_full_name()}", normal_style),
                '',
            ])

        worker_table = Table(worker_data, colWidths=[4*inch, 3.5*inch])
        worker_table.setStyle(TableStyle([
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(worker_table)
        story.append(Spacer(1, 0.1*inch))

    # Totals
    subtotal = invoice.subtotal
    hst = invoice.hst
    total = invoice.total

    totals_data = [
        ['', Paragraph('<b>Sub Total:</b>', right_style), Paragraph(f'${subtotal:,.2f}', right_style)],
        ['', Paragraph('<b>HST:</b>', right_style), Paragraph(f'${hst:,.2f}', right_style)],
        ['', Paragraph('<b>Total:</b>', right_bold), Paragraph(f'${total:,.2f}', right_bold)],
    ]

    totals_table = Table(totals_data, colWidths=[4.5*inch, 1.5*inch, 1.5*inch])
    totals_table.setStyle(TableStyle([
        ('LINEABOVE', (1, 2), (2, 2), 0.5, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(totals_table)

    doc.build(story)


def generate_monthly_report_pdf(response, customer, invoices, month, year):
    import calendar
    doc = SimpleDocTemplate(response, pagesize=letter,
                            rightMargin=0.5*inch, leftMargin=0.5*inch,
                            topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    story = []

    bold_style = ParagraphStyle('Bold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10)
    normal_style = ParagraphStyle('Normal2', parent=styles['Normal'], fontSize=9)
    title_style = ParagraphStyle('Title2', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=14, alignment=TA_CENTER)
    right_style = ParagraphStyle('Right', parent=styles['Normal'], fontSize=9, alignment=TA_RIGHT)

    month_name = calendar.month_name[int(month)]

    story.append(Paragraph("Invoice Statement", title_style))
    story.append(Spacer(1, 0.2*inch))

    logo_path = get_logo()
    if logo_path and logo_path.endswith('.png'):
        logo = Image(logo_path, width=1.5*inch, height=0.6*inch)
        logo_cell = logo
    else:
        logo_cell = Paragraph('<b>///APT</b>', bold_style)

    header_data = [
        [Paragraph(f"<b>{COMPANY_NAME}</b>", bold_style), '', logo_cell],
        [Paragraph(COMPANY_ADDRESS, normal_style), '', Paragraph(f"<b>Billing Address:</b>", bold_style)],
        [Paragraph(COMPANY_CITY, normal_style), '', Paragraph(customer.name, normal_style)],
        [Paragraph(COMPANY_COUNTRY, normal_style), '', Paragraph(customer.address or '', normal_style)],
        [Paragraph(COMPANY_PHONE, normal_style), '', Paragraph(f"{customer.city}, {customer.province}", normal_style)],
        [Paragraph(COMPANY_EMAIL, normal_style), '', Paragraph(f"Primary Phone: {customer.phone}", normal_style)],
        [Paragraph(COMPANY_HST, normal_style), '', Paragraph(f"Email: {customer.email}", normal_style)],
    ]

    header_table = Table(header_data, colWidths=[3*inch, 1*inch, 3.5*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(f"Statement Date: {month_name} {year}", right_style))
    story.append(Spacer(1, 0.2*inch))

    table_data = [
        [
            Paragraph('<b>Invoice Number</b>', bold_style),
            Paragraph('<b>Invoice Date</b>', bold_style),
            Paragraph('<b>Due Date</b>', bold_style),
            Paragraph('<b>Status</b>', bold_style),
            Paragraph('<b>Total</b>', bold_style),
            Paragraph('<b>Paid</b>', bold_style),
            Paragraph('<b>Balance</b>', bold_style),
        ]
    ]

    grand_total = 0
    for inv in invoices:
        grand_total += inv.total
        table_data.append([
            Paragraph(inv.invoice_number, normal_style),
            Paragraph(inv.invoice_date.strftime('%m/%d/%Y'), normal_style),
            Paragraph(inv.due_date.strftime('%m/%d/%Y') if inv.due_date else '', normal_style),
            Paragraph(inv.status.capitalize(), normal_style),
            Paragraph(f'${inv.total:,.2f}', right_style),
            Paragraph('$0.00', right_style),
            Paragraph(f'${inv.total:,.2f}', right_style),
        ])

    table_data.append([
        '', '', '', Paragraph('<b>Total Due</b>', bold_style), '', '',
        Paragraph(f'<b>${grand_total:,.2f}</b>', bold_style),
    ])

    col_widths = [1.3*inch, 1*inch, 1*inch, 0.8*inch, 1*inch, 0.8*inch, 1*inch]
    inv_table = Table(table_data, colWidths=col_widths)
    inv_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('BOX', (0, 0), (-1, -2), 0.5, colors.black),
        ('INNERGRID', (0, 0), (-1, -2), 0.25, colors.lightgrey),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEABOVE', (0, -1), (-1, -1), 0.5, colors.black),
    ]))
    story.append(inv_table)
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Thank you for your business", normal_style))

    doc.build(story)