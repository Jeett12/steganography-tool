#!/usr/bin/env python3
"""
Simple PNG LSB steganography tool.

This hides UTF-8 text inside 8-bit PNG pixel bytes by replacing the least
significant bit of each byte. It supports non-interlaced PNGs with color types
0, 2, 4, and 6.
"""

from __future__ import annotations

import argparse
import binascii
import hashlib
import os
import struct
import sys
import zlib
from dataclasses import dataclass


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAGIC = b"STEGPY1"
HEADER_SIZE = len(MAGIC) + 1 + 16 + 4
FLAG_PASSWORD = 1


class StegError(Exception):
    """Raised for user-facing steganography errors."""


@dataclass
class PngImage:
    width: int
    height: int
    bit_depth: int
    color_type: int
    compression: int
    filter_method: int
    interlace: int
    raw_pixels: bytearray


def bytes_per_pixel(color_type: int, bit_depth: int) -> int:
    if bit_depth != 8:
        raise StegError("Only 8-bit PNG files are supported.")

    channels_by_type = {
        0: 1,  # grayscale
        2: 3,  # RGB
        4: 2,  # grayscale + alpha
        6: 4,  # RGBA
    }

    if color_type not in channels_by_type:
        raise StegError("Supported PNG color types: grayscale, RGB, grayscale+alpha, RGBA.")

    return channels_by_type[color_type]


def paeth_predictor(left: int, above: int, upper_left: int) -> int:
    p = left + above - upper_left
    pa = abs(p - left)
    pb = abs(p - above)
    pc = abs(p - upper_left)

    if pa <= pb and pa <= pc:
        return left
    if pb <= pc:
        return above
    return upper_left


def read_chunks(data: bytes) -> list[tuple[bytes, bytes]]:
    if not data.startswith(PNG_SIGNATURE):
        raise StegError("Input is not a valid PNG file.")

    chunks: list[tuple[bytes, bytes]] = []
    offset = len(PNG_SIGNATURE)

    while offset < len(data):
        if offset + 8 > len(data):
            raise StegError("PNG file is truncated.")

        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        offset += 8

        chunk_data = data[offset : offset + length]
        offset += length

        if offset + 4 > len(data):
            raise StegError("PNG chunk CRC is missing.")

        offset += 4
        chunks.append((chunk_type, chunk_data))

        if chunk_type == b"IEND":
            break

    return chunks


def load_png(path: str) -> PngImage:
    with open(path, "rb") as file:
        data = file.read()

    chunks = read_chunks(data)
    ihdr_chunks = [chunk_data for chunk_type, chunk_data in chunks if chunk_type == b"IHDR"]
    idat_data = b"".join(chunk_data for chunk_type, chunk_data in chunks if chunk_type == b"IDAT")

    if not ihdr_chunks:
        raise StegError("PNG is missing the IHDR chunk.")
    if not idat_data:
        raise StegError("PNG is missing image data.")

    width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(
        ">IIBBBBB", ihdr_chunks[0]
    )

    if compression != 0 or filter_method != 0:
        raise StegError("Unsupported PNG compression or filter method.")
    if interlace != 0:
        raise StegError("Interlaced PNG files are not supported.")

    bpp = bytes_per_pixel(color_type, bit_depth)
    row_size = width * bpp

    try:
        scanlines = zlib.decompress(idat_data)
    except zlib.error as exc:
        raise StegError(f"Could not decompress PNG image data: {exc}") from exc

    expected_size = height * (row_size + 1)
    if len(scanlines) != expected_size:
        raise StegError("PNG image data size does not match its header.")

    raw_pixels = bytearray()
    previous = bytearray(row_size)

    for y in range(height):
        start = y * (row_size + 1)
        filter_type = scanlines[start]
        encoded = scanlines[start + 1 : start + 1 + row_size]
        row = bytearray(row_size)

        for i, value in enumerate(encoded):
            left = row[i - bpp] if i >= bpp else 0
            above = previous[i]
            upper_left = previous[i - bpp] if i >= bpp else 0

            if filter_type == 0:
                row[i] = value
            elif filter_type == 1:
                row[i] = (value + left) & 0xFF
            elif filter_type == 2:
                row[i] = (value + above) & 0xFF
            elif filter_type == 3:
                row[i] = (value + ((left + above) // 2)) & 0xFF
            elif filter_type == 4:
                row[i] = (value + paeth_predictor(left, above, upper_left)) & 0xFF
            else:
                raise StegError(f"Unsupported PNG row filter: {filter_type}")

        raw_pixels.extend(row)
        previous = row

    return PngImage(
        width=width,
        height=height,
        bit_depth=bit_depth,
        color_type=color_type,
        compression=compression,
        filter_method=filter_method,
        interlace=interlace,
        raw_pixels=raw_pixels,
    )


def make_chunk(chunk_type: bytes, chunk_data: bytes) -> bytes:
    crc = binascii.crc32(chunk_type)
    crc = binascii.crc32(chunk_data, crc) & 0xFFFFFFFF
    return struct.pack(">I", len(chunk_data)) + chunk_type + chunk_data + struct.pack(">I", crc)


def save_png(image: PngImage, path: str) -> None:
    bpp = bytes_per_pixel(image.color_type, image.bit_depth)
    row_size = image.width * bpp

    scanlines = bytearray()
    for y in range(image.height):
        start = y * row_size
        scanlines.append(0)
        scanlines.extend(image.raw_pixels[start : start + row_size])

    ihdr = struct.pack(
        ">IIBBBBB",
        image.width,
        image.height,
        image.bit_depth,
        image.color_type,
        image.compression,
        image.filter_method,
        image.interlace,
    )

    output = bytearray(PNG_SIGNATURE)
    output.extend(make_chunk(b"IHDR", ihdr))
    output.extend(make_chunk(b"IDAT", zlib.compress(bytes(scanlines), level=9)))
    output.extend(make_chunk(b"IEND", b""))

    with open(path, "wb") as file:
        file.write(output)


def keystream(password: str, salt: bytes, length: int) -> bytes:
    password_bytes = password.encode("utf-8")
    stream = bytearray()
    counter = 0

    while len(stream) < length:
        counter_bytes = struct.pack(">I", counter)
        stream.extend(hashlib.sha256(password_bytes + salt + counter_bytes).digest())
        counter += 1

    return bytes(stream[:length])


def xor_bytes(data: bytes, key: bytes) -> bytes:
    return bytes(value ^ key_byte for value, key_byte in zip(data, key))


def build_payload(message: str, password: str | None) -> bytes:
    body = message.encode("utf-8")
    flags = 0
    salt = b"\x00" * 16

    if password:
        flags |= FLAG_PASSWORD
        salt = os.urandom(16)
        body = xor_bytes(body, keystream(password, salt, len(body)))

    return MAGIC + bytes([flags]) + salt + struct.pack(">I", len(body)) + body


def iter_bits(data: bytes):
    for byte in data:
        for bit_index in range(7, -1, -1):
            yield (byte >> bit_index) & 1


def bits_to_bytes(bits: list[int]) -> bytes:
    output = bytearray()
    for i in range(0, len(bits), 8):
        value = 0
        for bit in bits[i : i + 8]:
            value = (value << 1) | bit
        output.append(value)
    return bytes(output)


def read_lsb_bytes(pixel_data: bytearray, byte_count: int) -> bytes:
    bit_count = byte_count * 8
    if bit_count > len(pixel_data):
        raise StegError("Image does not contain enough hidden data.")

    bits = [pixel_data[i] & 1 for i in range(bit_count)]
    return bits_to_bytes(bits)


def embed_message(input_path: str, output_path: str, message: str, password: str | None) -> None:
    image = load_png(input_path)
    payload = build_payload(message, password)
    capacity_bytes = len(image.raw_pixels) // 8

    if len(payload) > capacity_bytes:
        raise StegError(
            f"Message is too large. Capacity: {capacity_bytes - HEADER_SIZE} bytes, "
            f"needed: {len(payload) - HEADER_SIZE} bytes."
        )

    for index, bit in enumerate(iter_bits(payload)):
        image.raw_pixels[index] = (image.raw_pixels[index] & 0xFE) | bit

    save_png(image, output_path)


def extract_message(input_path: str, password: str | None) -> str:
    image = load_png(input_path)
    header = read_lsb_bytes(image.raw_pixels, HEADER_SIZE)

    if not header.startswith(MAGIC):
        raise StegError("No hidden message found, or this image was not created by this tool.")

    flags = header[len(MAGIC)]
    salt_start = len(MAGIC) + 1
    salt = header[salt_start : salt_start + 16]
    length = struct.unpack(">I", header[-4:])[0]

    total_size = HEADER_SIZE + length
    payload = read_lsb_bytes(image.raw_pixels, total_size)[HEADER_SIZE:]

    if flags & FLAG_PASSWORD:
        if not password:
            raise StegError("This message is password-protected. Provide --password.")
        payload = xor_bytes(payload, keystream(password, salt, len(payload)))

    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise StegError("Could not decode message. The password may be wrong.") from exc


def image_capacity(path: str) -> int:
    image = load_png(path)
    return max(0, (len(image.raw_pixels) // 8) - HEADER_SIZE)


def make_sample_cover(path: str, width: int = 320, height: int = 180) -> None:
    raw_pixels = bytearray()

    for y in range(height):
        for x in range(width):
            raw_pixels.extend(
                [
                    (x * 255) // max(1, width - 1),
                    (y * 255) // max(1, height - 1),
                    ((x + y) * 127) // max(1, width + height - 2),
                ]
            )

    image = PngImage(
        width=width,
        height=height,
        bit_depth=8,
        color_type=2,
        compression=0,
        filter_method=0,
        interlace=0,
        raw_pixels=raw_pixels,
    )
    save_png(image, path)


def parse_message(args: argparse.Namespace) -> str:
    if args.message and args.message_file:
        raise StegError("Use either --message or --message-file, not both.")
    if args.message:
        return args.message
    if args.message_file:
        with open(args.message_file, "r", encoding="utf-8") as file:
            return file.read()
    raise StegError("Provide a message using --message or --message-file.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Hide and extract secret text inside PNG images using LSB steganography."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    hide = subparsers.add_parser("hide", help="Hide a text message in a PNG image.")
    hide.add_argument("-i", "--input", required=True, help="Cover PNG image path.")
    hide.add_argument("-o", "--output", required=True, help="Output stego PNG image path.")
    hide.add_argument("-m", "--message", help="Secret message text.")
    hide.add_argument("-f", "--message-file", help="Read secret message from a UTF-8 text file.")
    hide.add_argument("-p", "--password", help="Optional password for lightweight obfuscation.")

    extract = subparsers.add_parser("extract", help="Extract a hidden text message from a PNG.")
    extract.add_argument("-i", "--input", required=True, help="Stego PNG image path.")
    extract.add_argument("-p", "--password", help="Password if the hidden message used one.")
    extract.add_argument("-o", "--output-file", help="Write extracted text to a file.")

    capacity = subparsers.add_parser("capacity", help="Show how many message bytes can fit.")
    capacity.add_argument("-i", "--input", required=True, help="PNG image path.")

    sample = subparsers.add_parser("sample-cover", help="Create a sample PNG cover image.")
    sample.add_argument("-o", "--output", required=True, help="Output sample PNG path.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "hide":
            message = parse_message(args)
            embed_message(args.input, args.output, message, args.password)
            print(f"Hidden message saved to: {args.output}")
        elif args.command == "extract":
            message = extract_message(args.input, args.password)
            if args.output_file:
                with open(args.output_file, "w", encoding="utf-8") as file:
                    file.write(message)
                print(f"Extracted message saved to: {args.output_file}")
            else:
                print(message)
        elif args.command == "capacity":
            print(f"Capacity: {image_capacity(args.input)} bytes")
        elif args.command == "sample-cover":
            make_sample_cover(args.output)
            print(f"Sample cover image saved to: {args.output}")
    except StegError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
