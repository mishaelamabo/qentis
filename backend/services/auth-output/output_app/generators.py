import os
import uuid
from datetime import datetime

import qrcode
from PIL import Image
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from django.conf import settings


# ── Serial Number Generator ────────────────────────────────────────────

def generate_serial_number(category, year=None):
    """
    Generates a unique human-readable serial number.
    Format: QNT-{YEAR}-{CATEGORY_CODE}-{RANDOM}
    Example: QNT-2026-ACAD-A3F2B1
    """
    if year is None:
        year = datetime.now().year

    category_codes = {
        'ACADEMIC': 'ACAD',
        'PHARMA':   'PHRM',
        'DOCUMENT': 'DOCS',
        'CURRENCY': 'CURR',
    }

    code   = category_codes.get(category, 'GENR')
    random = uuid.uuid4().hex[:6].upper()

    return f"QNT-{year}-{code}-{random}"


# ── QR Code Generator ──────────────────────────────────────────────────

def generate_qr_code(item_hash, serial_number, item_id):
    """
    Generates a QR code image containing the verification URL.
    The verifier scans this to verify the item instantly.
    Returns the file path of the saved QR code image.
    """
    verification_url = f"http://qentis.cm/verify?hash={item_hash}&serial={serial_number}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(verification_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    media_dir = os.path.join(settings.MEDIA_ROOT, 'qrcodes')
    os.makedirs(media_dir, exist_ok=True)

    filename  = f"qr_{item_id}_{uuid.uuid4().hex[:8]}.png"
    file_path = os.path.join(media_dir, filename)
    img.save(file_path)

    return file_path


# ── Digital Signature Generator ────────────────────────────────────────

def generate_key_pair():
    """
    Generates an RSA private/public key pair.
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    return private_key, private_key.public_key()


def generate_digital_signature(item_hash, item_id):
    """
    Generates a digital signature for a certificate or document.
    Returns the file paths of the signature and public key files.
    """
    private_key, public_key = generate_key_pair()

    signature = private_key.sign(
        item_hash.encode(),
        padding.PKCS1v15(),
        hashes.SHA256()
    )

    media_dir = os.path.join(settings.MEDIA_ROOT, 'signatures')
    os.makedirs(media_dir, exist_ok=True)

    sig_filename  = f"sig_{item_id}_{uuid.uuid4().hex[:8]}.bin"
    sig_file_path = os.path.join(media_dir, sig_filename)
    with open(sig_file_path, 'wb') as f:
        f.write(signature)

    pub_filename  = f"pub_{item_id}_{uuid.uuid4().hex[:8]}.pem"
    pub_file_path = os.path.join(media_dir, pub_filename)
    pub_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    with open(pub_file_path, 'wb') as f:
        f.write(pub_bytes)

    return sig_file_path, pub_file_path


def verify_digital_signature(item_hash, signature_bytes, public_key_bytes):
    """
    Verifies a digital signature against the item hash.
    Returns True if authentic, False if not.
    """
    try:
        public_key = serialization.load_pem_public_key(
            public_key_bytes,
            backend=default_backend()
        )
        public_key.verify(
            signature_bytes,
            item_hash.encode(),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False


# ── Watermark Generator ────────────────────────────────────────────────

def embed_watermark(image_path, item_hash, item_id):
    """
    Embeds an invisible watermark into a document image.
    Uses LSB (Least Significant Bit) steganography via Pillow.
    Returns the file path of the watermarked image.
    """
    img    = Image.open(image_path).convert('RGB')
    pixels = list(img.getdata())

    message      = item_hash + '||END||'
    message_bits = ''.join(format(ord(c), '08b') for c in message)

    if len(message_bits) > len(pixels) * 3:
        raise ValueError('Image too small to embed watermark.')

    new_pixels = []
    bit_index  = 0

    for pixel in pixels:
        r, g, b = pixel
        if bit_index < len(message_bits):
            r = (r & ~1) | int(message_bits[bit_index])
            bit_index += 1
        if bit_index < len(message_bits):
            g = (g & ~1) | int(message_bits[bit_index])
            bit_index += 1
        if bit_index < len(message_bits):
            b = (b & ~1) | int(message_bits[bit_index])
            bit_index += 1
        new_pixels.append((r, g, b))

    img.putdata(new_pixels)

    media_dir = os.path.join(settings.MEDIA_ROOT, 'watermarks')
    os.makedirs(media_dir, exist_ok=True)

    filename = f"wm_{item_id}_{uuid.uuid4().hex[:8]}.png"
    out_path = os.path.join(media_dir, filename)
    img.save(out_path)

    return out_path


def extract_watermark(image_path):
    """
    Extracts the hidden watermark from an image.
    Returns the extracted hash string, or None if no watermark found.
    """
    try:
        img    = Image.open(image_path).convert('RGB')
        pixels = list(img.getdata())

        bits    = []
        message = ''

        for pixel in pixels:
            for channel in pixel:
                bits.append(str(channel & 1))

        for i in range(0, len(bits), 8):
            byte = ''.join(bits[i:i+8])
            if len(byte) < 8:
                break
            char     = chr(int(byte, 2))
            message += char
            if message.endswith('||END||'):
                return message[:-7]

        return None
    except Exception:
        return None