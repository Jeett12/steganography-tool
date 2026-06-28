# PNG Steganography Tool

A simple Python command-line project that hides and extracts secret text inside PNG images using Least Significant Bit (LSB) steganography.

## Features

- Hide a text message inside a PNG image
- Extract a hidden message from a stego image
- Optional password-based message obfuscation
- Image capacity checking
- Sample cover image generation
- No external Python packages required

## Requirements

- Python 3.10 or later
- A PNG image, preferably RGB or RGBA

Supported PNG format: 8-bit, non-interlaced grayscale, RGB, grayscale with alpha, or RGBA.

## Usage

Create a sample cover image:

```bash
python steg_tool.py sample-cover -o cover.png
```

Check image capacity:

```bash
python steg_tool.py capacity -i cover.png
```

Hide a message:

```bash
python steg_tool.py hide -i cover.png -o secret.png -m "This is a secret message"
```

Hide a message with a password:

```bash
python steg_tool.py hide -i cover.png -o secret.png -m "Top secret" -p mypass123
```

Extract a message:

```bash
python steg_tool.py extract -i secret.png
```

Extract a password-protected message:

```bash
python steg_tool.py extract -i secret.png -p mypass123
```

Save the extracted text to a file:

```bash
python steg_tool.py extract -i secret.png -o message.txt
```

## How It Works

The tool stores message bits in the least significant bits of the image pixel bytes. Only one bit of each pixel byte is changed, so the visual difference is normally not noticeable.

Payload format:

```text
MAGIC + FLAGS + SALT + MESSAGE_LENGTH + MESSAGE_BYTES
```

The password option XORs the message bytes with a SHA-256 based keystream. This is useful for learning and project demonstration purposes. For high-security encryption, a professional cryptography library should be used.

## Viva Questions

- What is LSB steganography?
- How is image capacity calculated?
- Why does PNG filtering need to be decoded?
- What changes when a password is used?
- What is the difference between steganography and encryption?
