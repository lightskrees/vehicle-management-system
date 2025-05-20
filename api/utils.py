from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import Context
from django.template.loader import get_template, render_to_string


def send_email(user, activation_link):
    subject = "Get Started with Vehicle System! Confirm Your Email Address"
    from_email = f"No Reply <{settings.DEFAULT_FROM_EMAIL}>"
    to_email = [user.email]

    # Load the HTML template
    context = {"name": user.full_name, "activation_link": activation_link}
    text_content = render_to_string("email_template.html", context)
    html_content = render_to_string("email_template.html", context)

    # html_content = html_template.render(Context(context))

    # Create the email message
    email_message = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    email_message.attach_alternative(html_content, "text/html")
    email_message.send()
