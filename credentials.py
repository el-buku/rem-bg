import random
import time

credentials = [
    {
        "email_addr":  "testtest1234test1234@cock.li",
        "email_pass": "slobozsloboz99",
        "adobe_pass": "Dolari99",
        "locked_at":''
    },
       {
        "email_addr":  "testtest1234test12345@cock.li",
        "email_pass": "slobozsloboz99",
        "adobe_pass": "Dolari99",
        "locked_at":''
    },
       {
        "email_addr":  "testtest1234test123456@cock.li",
        "email_pass": "slobozsloboz99",
        "adobe_pass": "Dolari99",
        "locked_at":''
    },
       {
        "email_addr":  "testtest1234test1234567@cock.li",
        "email_pass": "slobozsloboz99",
        "adobe_pass": "Dolari99",
        "locked_at":''
    },
]

CREDENTIALS_MIN_LOCK = 5*60 # 5 minutes
async def select_credential():
    # Filter out locked credentials or credentials locked less than 5 minutes ago
    unlocked_credentials = [cred for cred in credentials if not cred ["locked_at"] or (cred["locked_at"] and (time.time() - cred["locked_at"]) > CREDENTIALS_MIN_LOCK)]
     # If there are no unlocked credentials, return None
    if not unlocked_credentials:
        raise Exception("No unlocked accounts left, wait a few minutes and try again")
    # Select a random unlocked credential
    credential = random.choice(unlocked_credentials)
    return credential

async def lock_credential(email_addr: str):
    for cred in credentials:
        if cred["email_addr"] == email_addr:
            cred["locked_at"] = time.time()
            break
