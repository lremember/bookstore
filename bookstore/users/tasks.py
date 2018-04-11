from __future__ import absolute_import,unicode_literals
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

@shared_task
def send_active_email(token,username,email):
	subject = '天天生鲜用户激活'
	message=''
	sender = settings.EMAIL_FROM
	receiver =[email]
	html_message ='<a href="http://127.0.0.1:8000/user/active/%s/">http://127.0.0.1:8000/user/active/</a>'%token
	send_mail(subject,message,sender,receiver,html_message=html_message)



