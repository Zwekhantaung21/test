from flask import Flask, render_template, request, send_file
import qrcode
import io
import zipfile
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.enums import TA_JUSTIFY
import datetime
from reportlab.lib import utils
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table


app = Flask(__name__)

# Unique secret key for your own scanner
SECRET_KEY = "your-secret-key"

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/GS1Myanmar_QR', methods=['POST'])
def generate():
    data = request.form['data']
    formats = request.form.getlist('format[]')

    qr_image = generate_qr_code(data)

    if 'verify' in formats:
        return generate_zip_with_pdf_and_image(data, qr_image)
    elif 'image' in formats:
        return send_qr_image(qr_image)

    return render_template('index.html')


@app.route('/generate_qr')
@app.route('/generate_qr')
def generate_qr():
    data = request.args.get('data')
    qr_image = generate_qr_code(data)
    qr_image_buffer = io.BytesIO()
    qr_image.save(qr_image_buffer, format='PNG')
    qr_image_buffer.seek(0)
    return send_file(qr_image_buffer, mimetype='image/png')


def generate_qr_code(data):
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_Q, box_size=5, border=2)
    # Quartile
    qr.add_data(data)
    qr.make(fit=True)
    qr_image = qr.make_image(fill_color="black", back_color="white")
    return qr_image


def send_qr_image(qr_image):
    qr_image_buffer = io.BytesIO()
    qr_image.save(qr_image_buffer, format='PNG')
    qr_image_buffer.seek(0)
    return send_file(qr_image_buffer, attachment_filename='GS1Myanmar_QR.png', as_attachment=True)


def generate_zip_with_pdf_and_image(data, qr_image):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        # Save the QR image to BytesIO buffer
        qr_image_buffer = io.BytesIO()
        qr_image.save(qr_image_buffer, format='PNG')
        qr_image_buffer.seek(0)
        zip_file.writestr('GS1Myanmar_QR.png', qr_image_buffer.getvalue())

        # Generate the PDF file
        pdf_buffer = generate_pdf(data, qr_image_buffer)
        zip_file.writestr('GS1Myanmar_Verify.pdf', pdf_buffer.getvalue())

    zip_buffer.seek(0)
    return send_file(zip_buffer, attachment_filename='GS1Myanmar_Verify.zip', as_attachment=True)


def generate_pdf(data, qr_image_buffer):
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)

    styles = getSampleStyleSheet()
    qr_code_text = '<strong>This QR code is generated by GS1 Myanmar QR code generator</strong> '
    qr_code_text_style = ParagraphStyle(
        'qr_code_style',
        parent=styles['BodyText'],
        textColor='#012D6C',
        alignment=TA_CENTER
    )
    qr_code_image = Image(qr_image_buffer)

    # Add your own image to the PDF
    # your_image_path = 'static/GS1mm_Verify4.png'  
    # your_image = Image(your_image_path)

    gs1_logo_path = 'static/gs1_logo.png'  # Replace with the path to your GS1 logo
    mba_logo_path = 'static/mba_logo.png'  # Replace with the path to your MBA logo
    gs1_logo = utils.ImageReader(gs1_logo_path)
    mba_logo = utils.ImageReader(mba_logo_path)
    header_style = ParagraphStyle(
        'header_style',
        parent=styles['Normal'],
        fontSize=9,
        textColor='#012D6C',
        alignment=TA_CENTER
    )

    generated_on_text = f'''Generated on: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    <br/>ECC Level: Quartile(QR Code ECC LEVEL Q : 25% of the data can be restored.)
    <br/>Quiet Zone: Margin - 2
    <br/>Generated by: GS1 Myanmar QR Generator'''
    generated_on_text_style = ParagraphStyle(
        'generated_on_text_style',
        parent=styles['BodyText'],
        alignment=TA_CENTER,
        textColor='#012D6C',
        fontSize=9

    )

    additional_text2 = '''
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
    This attachment is about Verifying your QR code that was produced by GS1 Myanmar.
    You can use our QR code in your Product, Website, Marketing, Healthcare, Events etc.
    
    If there is any issues related to 'YOUR DISTRIBUTIONS' of QR produced by GS1 Myanmar,
    we would like to inform you that we will not be responsible for solving it aspect
    an error of GS1 Myanmar QR Generator(Bad resolution, ECC error, Quietzone Error).
    
    If you had an error with our generator contact us as soon as possible.
   '''
    additional_text2_style = ParagraphStyle(
        'additional_text2_style',
        parent=styles['BodyText'],
        fontSize=10,
        spaceAfter=6,
        textColor='#012D6C',
        alignment=TA_JUSTIFY,
        leading = 25
    )

    # Additional text to be added at the bottom of the PDF
    additional_text = f'''Address: UMFCCI 5 Floor, Min Ye Kyaw Swar Road, Lanmadaw TSP, Yangon<br/>
Email: info@gs1myanmar.org<br/>
Phone: +959446868002, +959446868004<br/>
Wesbite: https://gs1mm.org'''

    additional_text_style = ParagraphStyle(
        'additional_text_style',
        parent=styles['BodyText'],
        fontSize=9,
        textColor='#012D6C',
        spaceAfter=6,
        alignment=TA_CENTER
    )

   
    story = []

    header_table = Table([
    [Image(gs1_logo_path, width=140, height=80), '', Image(mba_logo_path, width=140, height=80)]
], colWidths=[150, 240, 180])
   
    story.append(header_table)
    story.append(Paragraph(data, styles['Heading1']))
    story.append(Spacer(1, 12))
    # Set the width and height of the QR code image
    qr_code_image.drawHeight = 120
    qr_code_image.drawWidth = 120
    story.append(qr_code_image)
    story.append(Spacer(1, 12))
    story.append(Paragraph(qr_code_text, qr_code_text_style))
    story.append(Paragraph(generated_on_text, generated_on_text_style))  # Add generated date and time
    story.append(Spacer(1, 12))   
    story.append(Paragraph(additional_text2, additional_text2_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph(additional_text, additional_text_style))
    # story.append(your_image)  

    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer


if __name__ == '__main__':
    app.run(debug=True)
