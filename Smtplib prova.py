import smtplib

sender = "Private Person <from@example.com>"
receiver = "A Test User <to@example.com>"

message = f"""\
Subject: Hi Mailtrap
To: {receiver}
From: {sender}

This is a test e-mail message."""

with smtplib.SMTP("sandbox.smtp.mailtrap.io", 2525) as server:
    server.login("d4d29196e19468", "aaa1d572980258")
    server.sendmail(sender, receiver, message)