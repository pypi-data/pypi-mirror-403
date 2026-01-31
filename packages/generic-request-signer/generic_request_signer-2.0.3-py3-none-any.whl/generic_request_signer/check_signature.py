import hashlib
import apysigner
import re

from generic_request_signer import constants


def generate_hash_for_binary(binary_data):
    return {'binary_data': hashlib.md5(str.encode(binary_data)).hexdigest()}


def check_signature_for_binary(signature, private_key, full_path, binary):
    binary_hash = generate_hash_for_binary(binary)
    return check_signature(signature, private_key, full_path, binary_hash)


def check_signature(signature, private_key, full_path, payload):
    """
    Checks signature received and verifies that we are able to re-create
    it from the private key, path, and payload given.

    :param signature:
        Signature received from request.
    :param private_key:
        Base 64, url encoded private key.
    :full_path:
        Full path of request, including GET query string (excluding host)
    :payload:
        The request.POST data if present. None if not.

    :returns:
        Boolean of whether signature matched or not.
    """
    if isinstance(private_key, bytes):
        private_key = private_key.decode("ascii")

    if isinstance(payload, bytes):
        payload = payload.decode()

    url_to_check = _strip_signature_from_url(signature, full_path)
    computed_signature = apysigner.get_signature(private_key, url_to_check, payload)
    return constant_time_compare(signature, computed_signature)


def _strip_signature_from_url(signature, url_path):
    signature_qs = r"(\?|&)?{0}={1}$".format(constants.SIGNATURE_PARAM_NAME, signature)
    clean_url = re.sub(signature_qs, '', url_path, count=1)
    return clean_url


def constant_time_compare(val1, val2):  # noqa: C901
    """
    **This code was taken from the django 1.4.x codebase along with the test code**
    Returns True if the two strings are equal, False otherwise.

    The time taken is independent of the number of characters that match.
    """
    if len(val1) != len(val2):
        return False

    if isinstance(val1, bytes):
        val1 = val1.decode("ascii")
    if isinstance(val2, bytes):
        val2 = val2.decode("ascii")

    result = 0
    for x, y in zip(val1, val2):
        result |= ord(x) ^ ord(y)
    return result == 0
