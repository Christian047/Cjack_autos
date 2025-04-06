
from django.contrib import messages
from email.message import EmailMessage
import ssl
import smtplib
from django.views import View
from django.shortcuts import render, redirect
from base.models import *
from reviews.models import *


class Suscribe(View):
    def get(self, request):
        review = Review.objects.all()
        context= {'review': review}
        return render(request, 'base/index1.html',context)
        
    def post(self, request):
        name = request.POST.get('name')
        email = request.POST.get('email')
        customer_query = request.POST.get('customer_query')
        body = request.POST.get('body')
        
        
        if not name or not email:
            messages.error(request, 'fill in the name and email')
        try:
            self.send_email(name, email)
            Get_in_touch.objects.create(name=name, email=email, customer_query=customer_query, body=body)
            messages.success(request, 'message sent')
        except Exception as e:
            messages.success(request,  f'this is the error: {e}')
        return render(request, 'base/index1.html')

    def send_email(self, name, email):
        email_sender = 'Padigachris@gmail.com'
        email_password = 'eivt sumy iaic okwh'
        email_receiver = email
        subject = 'Thanks for subscribing'
        body = f'Thanks for subscibing, {name}!'

        em = EmailMessage()
        em['From'] = email_sender
        em['To'] = email_receiver
        em['Subject'] = subject
        em.set_content(body)

        context = ssl.create_default_context()

        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(email_sender, email_password)
            smtp.sendmail(email_sender, email_receiver, em.as_bytes())
            print('Message sent')

