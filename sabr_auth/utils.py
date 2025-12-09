from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


def send_password_reset_email(user, reset_url):
    """
    Send password reset email to user
    """
    subject = 'إعادة تعيين كلمة المرور - Sabr Learning Platform'
    
    # HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: 'Arial', sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 20px auto;
                background-color: #ffffff;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .header {{
                background-color: #4CAF50;
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .content {{
                padding: 40px 30px;
                text-align: right;
            }}
            .content h2 {{
                color: #333;
                margin-bottom: 20px;
            }}
            .content p {{
                color: #666;
                line-height: 1.6;
                margin-bottom: 20px;
            }}
            .button {{
                display: inline-block;
                padding: 15px 40px;
                background-color: #4CAF50;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
                font-weight: bold;
            }}
            .button:hover {{
                background-color: #45a049;
            }}
            .footer {{
                background-color: #f8f8f8;
                padding: 20px;
                text-align: center;
                color: #999;
                font-size: 12px;
            }}
            .warning {{
                background-color: #fff3cd;
                border-right: 4px solid #ffc107;
                padding: 15px;
                margin: 20px 0;
                color: #856404;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>إعادة تعيين كلمة المرور</h1>
            </div>
            <div class="content">
                <h2>مرحباً {user.full_name}،</h2>
                <p>
                    لقد تلقينا طلباً لإعادة تعيين كلمة المرور الخاصة بحسابك في منصة Sabr للتعلم.
                </p>
                <p>
                    إذا كنت قد طلبت إعادة تعيين كلمة المرور، يرجى النقر على الزر أدناه:
                </p>
                <div style="text-align: center;">
                    <a href="{reset_url}" class="button">إعادة تعيين كلمة المرور</a>
                </div>
                <p style="text-align: center; color: #999; font-size: 14px;">
                    أو انسخ الرابط التالي في المتصفح:<br>
                    <a href="{reset_url}" style="color: #4CAF50;">{reset_url}</a>
                </p>
                <div class="warning">
                    <strong>تنبيه:</strong> هذا الرابط صالح لمدة ساعة واحدة فقط.
                </div>
                <p>
                    إذا لم تطلب إعادة تعيين كلمة المرور، يرجى تجاهل هذا البريد الإلكتروني. حسابك آمن.
                </p>
            </div>
            <div class="footer">
                <p>© 2024 Sabr Learning Platform. جميع الحقوق محفوظة.</p>
                <p>هذا بريد إلكتروني تلقائي، يرجى عدم الرد عليه.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text content (fallback)
    text_content = f"""
    مرحباً {user.full_name},
    
    لقد تلقينا طلباً لإعادة تعيين كلمة المرور الخاصة بحسابك.
    
    يرجى النقر على الرابط التالي لإعادة تعيين كلمة المرور:
    {reset_url}
    
    هذا الرابط صالح لمدة ساعة واحدة فقط.
    
    إذا لم تطلب إعادة تعيين كلمة المرور، يرجى تجاهل هذا البريد.
    
    مع تحيات فريق Sabr Learning Platform
    """
    
    # Create email
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=f'{settings.DEFAULT_FROM_NAME} <{settings.DEFAULT_FROM_EMAIL}>',
        to=[user.email]
    )
    
    # Attach HTML content
    email.attach_alternative(html_content, "text/html")
    
    # Send email
    try:
        email.send(fail_silently=False)
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False


def send_password_reset_confirmation_email(user):
    """
    Send confirmation email after password reset
    """
    subject = 'تم تغيير كلمة المرور بنجاح - Sabr Learning Platform'
    
    html_content = f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: 'Arial', sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 20px auto;
                background-color: #ffffff;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .header {{
                background-color: #4CAF50;
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .content {{
                padding: 40px 30px;
                text-align: right;
            }}
            .success-icon {{
                text-align: center;
                font-size: 60px;
                color: #4CAF50;
                margin-bottom: 20px;
            }}
            .footer {{
                background-color: #f8f8f8;
                padding: 20px;
                text-align: center;
                color: #999;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>تم تغيير كلمة المرور</h1>
            </div>
            <div class="content">
                <div class="success-icon">✓</div>
                <h2 style="text-align: center;">مرحباً {user.full_name}،</h2>
                <p style="text-align: center;">
                    تم تغيير كلمة المرور الخاصة بحسابك بنجاح.
                </p>
                <p style="text-align: center;">
                    إذا لم تقم بهذا التغيير، يرجى التواصل معنا فوراً.
                </p>
            </div>
            <div class="footer">
                <p>© 2024 Sabr Learning Platform. جميع الحقوق محفوظة.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    مرحباً {user.full_name},
    
    تم تغيير كلمة المرور الخاصة بحسابك بنجاح.
    
    إذا لم تقم بهذا التغيير، يرجى التواصل معنا فوراً.
    
    مع تحيات فريق Sabr Learning Platform
    """
    
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=f'{settings.DEFAULT_FROM_NAME} <{settings.DEFAULT_FROM_EMAIL}>',
        to=[user.email]
    )
    
    email.attach_alternative(html_content, "text/html")
    
    try:
        email.send(fail_silently=False)
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False