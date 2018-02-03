import RPi.GPIO as GPIO
import MFRC522
import time 

KEY = [0xFF,0xFF,0xFF,0xFF,0xFF,0xFF]
BLOCK_ADDRS = [8, 9, 10]

def uid_to_hex_string(uid):
    ret = ""
    for byte in uid:
        ret = ret+format(byte,'x')
    return ret.upper()

READER = MFRC522.MFRC522()

def uid_to_hex_string(uid):
    ret = ""
    for byte in uid:
        ret = ret+format(byte,'x')
    return ret.upper()

def read_card():
    tag_read = False
    (status, TagType) = READER.MFRC522_Request(READER.PICC_REQIDL)
    if status != READER.MI_OK:
        return False
    (status, uid) = READER.MFRC522_Anticoll()
    if status != READER.MI_OK:
        return False
    status = READER.MFRC522_Auth(READER.PICC_AUTHENT1A, 11, KEY, uid)
    READER.MFRC522_StopCrypto1()
    return uid_to_hex_string(uid)

while 1:
    card = read_card()
    if(card):
        print("ok: %s"%card)
    else: 
        print("fail")
    time.sleep(0.2)