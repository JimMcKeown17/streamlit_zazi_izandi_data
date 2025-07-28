import os
import sendgrid
from sendgrid.helpers.mail import Email, To, Content, Mail

def send_test_email():
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
    from_email = Email("jim@masinyusane.org")
    to_email = To("jim@masinyusane.org")
    content = Content("text/plain", "This is an important test email")
    mail = Mail(from_email, to_email, "Test email", content).get()
    response = sg.client.mail.send.post(request_body=mail)
    print(response.status_code)

send_test_email()