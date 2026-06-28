# PNG Steganography Tool

Ek simple Python project jo PNG image ke andar secret text hide aur extract karta hai using LSB steganography.

## Features

- Hide text message in PNG image
- Extract hidden message
- Optional password-based obfuscation
- Capacity check
- Sample cover image generator
- No external Python packages required

## Requirements

- Python 3.10+
- PNG image, preferably RGB/RGBA

Supported PNG format: 8-bit, non-interlaced grayscale, RGB, grayscale+alpha, or RGBA.

## Commands

Create sample cover image:

```bash
python steg_tool.py sample-cover -o cover.png
```

Check capacity:

```bash
python steg_tool.py capacity -i cover.png
```

Hide a message:

```bash
python steg_tool.py hide -i cover.png -o secret.png -m "Bhai ye secret message hai"
```

Hide with password:

```bash
python steg_tool.py hide -i cover.png -o secret.png -m "Top secret" -p mypass123
```

Extract message:

```bash
python steg_tool.py extract -i secret.png
```

Extract password-protected message:

```bash
python steg_tool.py extract -i secret.png -p mypass123
```

Save extracted text to a file:

```bash
python steg_tool.py extract -i secret.png -o message.txt
```

## How It Works

Image ke pixel bytes ke least significant bit me message bits store hote hain. Pixel value me sirf 1 bit ka change hota hai, isliye visual difference normally dikhta nahi.

Payload format:

```text
MAGIC + FLAGS + SALT + MESSAGE_LENGTH + MESSAGE_BYTES
```

Password option message bytes ko SHA-256 based keystream se XOR karta hai. Ye learning/project demo ke liye useful hai, high-security encryption ke liye professional cryptography library use karni chahiye.

## Project Ideas For Viva

- LSB steganography kya hota hai?
- Image capacity kaise calculate hoti hai?
- PNG filtering ko decode kyu karna padta hai?
- Password option se extraction me kya change hota hai?
- Steganography aur encryption me difference kya hai?
