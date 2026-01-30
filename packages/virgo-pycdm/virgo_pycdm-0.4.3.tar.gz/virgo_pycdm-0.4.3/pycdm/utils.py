import base64, zlib
from hashlib import sha256


def encode_from_file(input_file: str) -> tuple[bytes, str]:
    with open(input_file, "rb") as f:
        fw = f.read()

    fw_hash = sha256(fw).hexdigest()
    fw_zip = zlib.compress(fw)
    fw_zip_b64 = base64.b64encode(fw_zip)

    return fw_zip_b64, fw_hash


def decode_to_file(encoded_str: bytes | str, dest_file: str) -> None:
    file_zip = base64.b64decode(encoded_str)
    file = zlib.decompress(file_zip)
    with open(dest_file, "xb") as f:
        f.write(file)


def check_valid_board_identifier(s: str) -> str:
    if len(s) > 2:
        raise Exception("Invalid value: {}", s)

    if s[0] != "R" and s[0] != "L":
        raise Exception("Invalid value: {}", s[0])

    if len(s) == 2:
        if int(s[1]) > 3 or int(s[1]) < 0:
            raise Exception("Invalid value: {}", s[0])

    return s
