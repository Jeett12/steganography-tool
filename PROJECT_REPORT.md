# Project Report: PNG Steganography Tool

## Aim

The aim of this project is to create a command-line tool that can hide and extract secret text inside PNG images using Least Significant Bit (LSB) steganography.

## Problem Statement

The secret message should not be visible when the image is opened normally, but it should be recoverable using the correct extraction tool.

## Technology Used

- Language: Python
- File format: PNG
- Technique: LSB steganography
- Libraries: Python standard library only

## Algorithm

### Hide Operation

1. Read the input PNG image.
2. Decompress the PNG image data.
3. Convert the secret message into UTF-8 bytes.
4. Add a message header containing the magic value, flags, salt, and message length.
5. Store each message bit inside the least significant bit of the image pixel bytes.
6. Compress the modified image data and save it as a new PNG file.

### Extract Operation

1. Read the stego PNG image.
2. Read the least significant bits from the pixel bytes.
3. Identify the message length and flags from the header.
4. Recover the hidden message bytes.
5. If password protection is enabled, decode the message using the same password.
6. Print the recovered UTF-8 text or save it to a file.

## Modules

- `load_png`: Parses PNG chunks and decodes image data.
- `save_png`: Writes modified pixel data back into a PNG file.
- `embed_message`: Hides the secret message inside the image.
- `extract_message`: Recovers the hidden message from the image.
- `image_capacity`: Calculates how many message bytes can fit in the image.
- `make_sample_cover`: Creates a sample PNG image for demonstration.

## Advantages

- No external dependency is required.
- The tool is easy to use from the command line.
- The hidden message is not visible during normal image viewing.
- Optional password-based protection is available.

## Limitations

- Only 8-bit non-interlaced PNG images are supported.
- The password feature is demonstration-level obfuscation, not professional encryption.
- Image editing, heavy compression, or format conversion may corrupt the hidden data.

## Test Cases

| Test | Expected Result |
| --- | --- |
| Create sample cover image | A PNG file is created |
| Check capacity | Available message capacity is displayed |
| Hide normal message | A stego PNG image is created |
| Extract normal message | The original message is displayed |
| Extract password message without password | An error message is displayed |
| Extract password message with password | The original message is displayed |

## Future Scope

- Add JPG support.
- Add a graphical user interface.
- Integrate a strong cryptography library.
- Add support for hiding files, not only text messages.
