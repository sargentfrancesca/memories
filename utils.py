

# utility function to convert a a 5-byte array (the mifare card UID)
# to a 10 character string of hex values - this is our 'card ID' 
# that will be referenced throughout the programme 
def uid_to_hex_string(uid):
    ret = ""
    for byte in uid:
        ret = ret + format(byte, 'x')
    return ret.upper()