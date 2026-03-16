import os
from .mpesa_utils import get_access_token, generate_password
from dotenv import load_dotenv
load_dotenv()

def create_stk_push_payload(amount, phone_number, account_reference="Test", transaction_desc="Test Transaction"):
    password, timestamp = generate_password()
    short_code = os.getenv('BUSINESS_SHORTCODE')

    headers = {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json"
    }

    payload = {
        "BusinessShortCode": os.getenv('BUSINESS_SHORTCODE'),
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": str(amount),
        "PartyA": phone_number,
        "PartyB": short_code,
        "PhoneNumber": phone_number,
        "CallBackURL": "https://quickdine.ink/platform/mpesa/callback/",
        "AccountReference": account_reference,
        "TransactionDesc": transaction_desc
    }
    return payload, headers