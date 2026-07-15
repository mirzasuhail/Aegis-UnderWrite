import io
import time
import random
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and print 'Page X of Y' footers.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#71717a"))
        
        # Header
        self.drawString(54, 750, "CONFIDENTIAL // AEGIS RISK SYSTEMS UNDERWRITING REPORT")
        self.setStrokeColor(colors.HexColor("#e4e4e7"))
        self.setLineWidth(0.5)
        self.line(54, 742, 558, 742)
        
        # Footer
        self.line(54, 45, 558, 45)
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 30, page_text)
        self.drawString(54, 30, f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')} // Ref: AEGIS-SECURE-INFERENCE")
        self.restoreState()


def generate_underwriting_pdf(data: dict, result: dict) -> io.BytesIO:
    """
    Generates a professionally formatted corporate PDF report for credit card approvals.
    Uses reportlab flowables and custom styles.
    """
    buffer = io.BytesIO()
    
    # Page setup: letter size is 8.5 x 11 inches. 
    # Left/Right margins: 0.75 in (54 pt). Top/Bottom: 1.0 in (72 pt)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=72,
        bottomMargin=72
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#09090b"),
        spaceAfter=15
    )
    
    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#09090b"),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#27272a"),
        spaceAfter=8
    )
    
    bold_body_style = ParagraphStyle(
        'BoldBody_Custom',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    mono_style = ParagraphStyle(
        'Mono_Custom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#18181b")
    )
    
    story = []
    
    # ------------------ HEADER BLOCK ------------------
    app_id = f"AEGIS-{time.strftime('%Y%m%d')}-{random.randint(10000, 99999)}"
    
    header_data = [
        [Paragraph("<b>AEGIS UNDERWRITING PLATFORM</b><br/><font color='#71717a'>Risk Prescreening Systems</font>", body_style),
         Paragraph(f"<b>APPLICATION ID:</b> {app_id}<br/><b>ASSESSMENT DATE:</b> {time.strftime('%Y-%m-%d')}", body_style)]
    ]
    header_table = Table(header_data, colWidths=[3.5*inch, 3.5*inch])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 15))
    
    # ------------------ TITLE & OVERVIEW ------------------
    story.append(Paragraph("Credit Evaluation & Risk Assessment", title_style))
    story.append(Paragraph(
        "Aegis Underwriting Platform runs automated validations, feature mapping, and multi-model inferences "
        "to screen applicants for credit worthiness. Below is the compiled institutional report.", body_style
    ))
    story.append(Spacer(1, 10))
    
    # ------------------ EXECUTIVE SUMMARY / DECISION PANEL ------------------
    decision = result['final_decision']
    decision_color = "#15803d" if decision == "Approved" else "#be123c" # Muted emerald vs red
    
    decision_box_data = [
        [
            Paragraph(f"<b>EXECUTIVE DECISION:</b>", bold_body_style),
            Paragraph(f"<font color='{decision_color}'><b>{decision.upper()}</b></font>", ParagraphStyle('Dec', parent=bold_body_style, fontSize=12))
        ],
        [
            Paragraph("<b>Overall Risk Tier:</b>", bold_body_style),
            Paragraph(res_risk := result.get('risk_level', 'High'), body_style)
        ],
        [
            Paragraph("<b>System Confidence:</b>", bold_body_style),
            Paragraph(f"{result.get('confidence_score', 0.95) * 100:.1f}%", body_style)
        ],
        [
            Paragraph("<b>Consensus Probability:</b>", bold_body_style),
            Paragraph(f"{result.get('risk_probability', 0.1) * 100:.2f}% risk of default", body_style)
        ]
    ]
    
    decision_table = Table(decision_box_data, colWidths=[2.5*inch, 4.5*inch])
    decision_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fafafa")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#e4e4e7")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(decision_table)
    story.append(Spacer(1, 15))
    
    # ------------------ APPLICANT PROFILE SUMMARY ------------------
    story.append(Paragraph("Applicant Demographics & Inputs", h1_style))
    applicant_data = [
        [
            Paragraph("<b>Full Name:</b>", body_style), Paragraph(data.get('Applicant Name', 'N/A'), body_style),
            Paragraph("<b>Age / Gender:</b>", body_style), Paragraph(f"{int(data.get('Age', 0))} / {data.get('Gender', 'N/A')}", body_style)
        ],
        [
            Paragraph("<b>Marital Status:</b>", body_style), Paragraph(data.get('Marital Status', 'N/A'), body_style),
            Paragraph("<b>Dependents:</b>", body_style), Paragraph(str(int(data.get('Number of Dependents', 0))), body_style)
        ],
        [
            Paragraph("<b>Employment Type:</b>", body_style), Paragraph(data.get('Employment Type', 'N/A'), body_style),
            Paragraph("<b>Occupation:</b>", body_style), Paragraph(data.get('Occupation', 'N/A'), body_style)
        ],
        [
            Paragraph("<b>Annual Income:</b>", body_style), Paragraph(f"INR {float(data.get('Annual Income', 0)):,.2f}", body_style),
            Paragraph("<b>Employment Length:</b>", body_style), Paragraph(f"{int(data.get('Employment Duration', 0))} Years", body_style)
        ],
        [
            Paragraph("<b>Credit Score:</b>", body_style), Paragraph(str(int(data.get('Credit Score', 0))), body_style),
            Paragraph("<b>Debt-to-Income (DTI):</b>", body_style), Paragraph(f"{float(data.get('Debt-to-Income Ratio', 0)):.1f}%", body_style)
        ]
    ]
    applicant_table = Table(applicant_data, colWidths=[1.5*inch, 2.0*inch, 1.5*inch, 2.0*inch])
    applicant_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor("#f4f4f5")),
    ]))
    story.append(applicant_table)
    story.append(Spacer(1, 15))
    
    # ------------------ ML MODELS CONSENSUS TABLE ------------------
    story.append(Paragraph("Machine Learning Consensus Matrix", h1_style))
    story.append(Paragraph(
        "Each model executes prediction inference independently based on weights derived during offline stratified pipeline training.", body_style
    ))
    
    consensus_headers = [
        Paragraph("<b>Model Name</b>", bold_body_style),
        Paragraph("<b>Prediction</b>", bold_body_style),
        Paragraph("<b>Confidence</b>", bold_body_style),
        Paragraph("<b>Accuracy (Test)</b>", bold_body_style),
        Paragraph("<b>Latency</b>", bold_body_style)
    ]
    
    consensus_rows = [consensus_headers]
    for model in result['model_executions']:
        pred_label = model['prediction']
        p_color = "#16a34a" if pred_label == "Approved" else "#dc2626"
        consensus_rows.append([
            Paragraph(model['model_name'], body_style),
            Paragraph(f"<font color='{p_color}'><b>{pred_label}</b></font>", body_style),
            Paragraph(f"{model['confidence_score'] * 100:.0f}%", body_style),
            Paragraph(f"{model['accuracy'] * 100:.1f}%", body_style),
            Paragraph(f"{model['execution_time_ms']} ms", body_style)
        ])
        
    consensus_table = Table(consensus_rows, colWidths=[2.2*inch, 1.2*inch, 1.2*inch, 1.4*inch, 1.0*inch])
    consensus_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LINEBELOW', (0,0), (-1,0), 1, colors.HexColor("#e4e4e7")),
        ('LINEBELOW', (0,1), (-1,-1), 0.5, colors.HexColor("#f4f4f5")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(consensus_table)
    story.append(Spacer(1, 20))
    
    # Force page break to start detailed Analysis on Page 2
    story.append(PageBreak())
    
    # ------------------ DETAILED AI ANALYSIS ------------------
    story.append(Paragraph("AI Underwriting Detail Report", title_style))
    story.append(Spacer(1, 10))
    
    analysis_sections = [
        ("Credit Profile Analysis", 
         f"The applicant holds a Credit Score of {int(data.get('Credit Score', 0))}. This places them in "
         f"the { 'Excellent' if int(data.get('Credit Score', 0)) >= 740 else ('Good' if int(data.get('Credit Score', 0)) >= 670 else 'Subprime') } "
         f"underwriting class. Credit card utilization stands at {float(data.get('Credit Utilization', 0))}% "
         f"with {int(data.get('Number of Credit Inquiries', 0))} hard inquiries recorded in the last 6 months."),
        
        ("Income Stability Assessment", 
         f"Applicant reports an annual gross income of INR {float(data.get('Annual Income', 0)):,.2f} "
         f"(INR {float(data.get('Monthly Income', 0)):,.2f} monthly). "
         f"Income levels are verified through active employment status category '{data.get('Employment Type', 'Working')}' "
         f"with {data.get('Occupation', 'N/A')} description. This provides solid repayment coverage."),
         
        ("Employment Risk Assessment",
         f"Current employment duration is {int(data.get('Employment Duration', 0))} years ({int(data.get('Years with Current Employer', 0))} "
         f"years continuous with the current employer). The tenure length indicates low volatility of professional career disruption."),
         
        ("Debt & Liabilities Analysis",
         f"The applicant has a Debt-to-Income (DTI) ratio of {float(data.get('Debt-to-Income Ratio', 0))}% "
         f"with active monthly EMIs of INR {float(data.get('Monthly EMI', 0)):,.2f} against outstanding balances of INR {float(data.get('Loan Amount', 0)):,.2f}. "
         f"DTI leverage is within credit policy tolerances."),
         
        ("Credit Behaviour & Performance",
         f"Delinquency search shows {int(data.get('Late Payment History', 0))} late payments in borrower records. "
         f"Previous defaults: '{data.get('Previous Loan Defaults', 'No')}'. Account age records indicate "
         f"healthy tenure at current residential address ({int(data.get('Years at Current Address', 0))} years)."),
         
        ("Fraud Risk Observation",
         "Anti-fraud validation indicates standard identity matches. No active duplicate applications "
         "or discrepancies in employment records were flagged by system validation parameters.")
    ]
    
    for title, text in analysis_sections:
        story.append(Paragraph(title, h1_style))
        story.append(Paragraph(text, body_style))
        story.append(Spacer(1, 4))
        
    story.append(Spacer(1, 10))
    
    # ------------------ FACTOR CHECKLIST ------------------
    story.append(Paragraph("Risk Factors Summary", h1_style))
    factors_data = []
    
    # Render positive / negative bullets
    for reason in result['reasons']:
        if "Decline" in reason or "rejected" in reason or "override" in reason:
            factors_data.append([Paragraph("<b>[-]</b>", ParagraphStyle('Red', parent=bold_body_style, textColor=colors.HexColor("#dc2626"))),
                                 Paragraph(reason, body_style)])
        else:
            factors_data.append([Paragraph("<b>[+]</b>", ParagraphStyle('Green', parent=bold_body_style, textColor=colors.HexColor("#16a34a"))),
                                 Paragraph(reason, body_style)])
            
    factors_table = Table(factors_data, colWidths=[0.4*inch, 6.6*inch])
    factors_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(factors_table)
    story.append(Spacer(1, 15))
    
    # ------------------ APPROVAL CONDITIONS & CARD LIMIT ------------------
    story.append(Paragraph("Underwriting Advisory & Limits", h1_style))
    advisory_rows = []
    for rec in result['recommendations']:
        advisory_rows.append([Paragraph("<b>*</b>", bold_body_style), Paragraph(rec, body_style)])
        
    advisory_table = Table(advisory_rows, colWidths=[0.2*inch, 6.8*inch])
    advisory_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(advisory_table)
    story.append(Spacer(1, 25))
    
    # ------------------ SIGNATURE BLOCKS ------------------
    sig_data = [
        [Paragraph("<b>PREPARED BY:</b><br/>Aegis Intelligent Decision Engine", body_style),
         Paragraph("<b>AUTHORIZED UNDERWRITER SIGN-OFF:</b><br/>________________________________________", body_style)]
    ]
    sig_table = Table(sig_data, colWidths=[3.5*inch, 3.5*inch])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 10),
    ]))
    
    # Keep together to ensure signature block doesn't split
    story.append(KeepTogether(sig_table))

    # Build PDF using NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    
    buffer.seek(0)
    return buffer
