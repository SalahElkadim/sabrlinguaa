# exceptions.py
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Custom exception handler that formats all errors as {"error_message": "..."}
    """
    response = exception_handler(exc, context)
    
    if response is not None:
        error_message = ""
        
        if isinstance(response.data, dict):
            # Handle serializer errors
            if 'errors' in response.data:
                errors = response.data['errors']
                if isinstance(errors, dict):
                    # Get first error from dict
                    for field, messages in errors.items():
                        if isinstance(messages, list):
                            error_message = messages[0] if messages else "حدث خطأ في التحقق من البيانات"
                        else:
                            error_message = str(messages)
                        break
                else:
                    error_message = str(errors)
            # Handle other error formats
            elif 'detail' in response.data:
                error_message = response.data['detail']
            elif 'error' in response.data:
                error_message = response.data['error']
            else:
                # Get first field error
                for field, messages in response.data.items():
                    if isinstance(messages, list):
                        error_message = messages[0] if messages else "حدث خطأ"
                    else:
                        error_message = str(messages)
                    break
        elif isinstance(response.data, list):
            error_message = response.data[0] if response.data else "حدث خطأ"
        else:
            error_message = str(response.data)
        
        response.data = {"error_message": error_message}
    
    return response


def format_serializer_errors(errors):
    """
    Convert serializer errors dict to single error message
    """
    if isinstance(errors, dict):
        for field, messages in errors.items():
            if isinstance(messages, list):
                return messages[0] if messages else "حدث خطأ في التحقق من البيانات"
            elif isinstance(messages, dict):
                return format_serializer_errors(messages)
            else:
                return str(messages)
    return "حدث خطأ في التحقق من البيانات"