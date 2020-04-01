import base64


def safe_base64(un_encoded_data) -> str:
    """
    takes in a string or bytes
    returns a string
    """
    if isinstance(un_encoded_data, str):
        un_encoded_data = un_encoded_data.encode("utf8")
    r = base64.urlsafe_b64encode(un_encoded_data).rstrip(b"=")
    return r.decode("utf8")
