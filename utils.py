import random
import string
import datetime

def generate_verification_code(length=6):
    code = ""
    for _ in range(length):
        choice = random.choice(["upper", "lower", "digit"])

        if choice == "upper":
            code += chr(random.randint(65, 90))       # A–Z
        elif choice == "lower":
            code += chr(random.randint(97, 122))      # a–z
        else:
            code += chr(random.randint(48, 57))       # 0–9

    return code

def is_code_expired(created_at, minutes=30):
    return (datetime.datetime.utcnow() - created_at).total_seconds() > minutes * 60
