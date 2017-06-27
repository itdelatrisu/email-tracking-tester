import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class Mailer:
    def __init__(self, settings):
        self.user = settings['username']
        self.password = settings['password']
        self.server = settings['smtp_server']
        self.port = settings['smtp_port']
        if not (self.user and self.password and self.server and self.port):
            raise ValueError('Invalid mailer parameters. Please check your configuration file!')

    def send(self, to_address, img_url, link_url, results_url, unsubscribe_url):
        # set MIME headers
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Test Email'
        msg['From'] = '"Email Tracking Test" <' + self.user + '>'
        msg['To'] = to_address
        msg['List-Unsubscribe'] = '<' + unsubscribe_url + '>'

        # create email bodies
        text = 'Your email client does not render HTML.'
        html = '''\
<html>
    <head></head>
    <body>
        <div>
            <p>Hi!</p>
            <p>This email contains your tracking tests. Please click on the provided tracking link below.</p>
            <p>Afterwards, you can view your results <a href="%s">here</a>.</p>
            <hr>
            <p>
                <strong>Tracking image:</strong><br />
                <img src="%s">
            </p>
            <p>
                <strong>Tracking link:</strong><br />
                <a href="%s">Click here!</a>
            </p>
            <hr>
            <p>If you didn't request this email, sorry! You can opt-out from all future emails by clicking <a href="%s">this link</a>.</p>
        </div>
    </body>
</html>
''' % (results_url, img_url, link_url, unsubscribe_url)

        # attach body parts (last part is most preferred)
        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))

        # send email
        mailserver = smtplib.SMTP(self.server, self.port)
        mailserver.ehlo()
        mailserver.starttls()
        mailserver.ehlo()
        mailserver.login(self.user, self.password)
        mailserver.sendmail(self.user, to_address, msg.as_string())
        mailserver.quit()
