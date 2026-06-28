# Project Report: PNG Steganography Tool

## Aim

Is project ka aim ek command-line tool banana hai jo PNG image ke andar secret text hide aur extract kar sake using Least Significant Bit steganography.

## Problem Statement

Normal image dekhne par secret message visible nahi hona chahiye, lekin correct tool se message recover ho jana chahiye.

## Technology Used

- Language: Python
- File format: PNG
- Technique: LSB steganography
- Libraries: Python standard library only

## Algorithm

### Hide

1. Input PNG image read karo.
2. PNG image data decompress karo.
3. Secret message ko UTF-8 bytes me convert karo.
4. Message header add karo: magic value, flags, salt, length.
5. Har message bit ko image pixel bytes ke least significant bit me store karo.
6. Modified image data ko compress karke new PNG save karo.

### Extract

1. Stego PNG image read karo.
2. Pixel bytes ke least significant bits read karo.
3. Header se message length aur flags identify karo.
4. Message bytes recover karo.
5. Agar password enabled hai to same password se decode karo.
6. UTF-8 text print ya file me save karo.

## Modules

- `load_png`: PNG chunks parse aur image data decode karta hai.
- `save_png`: Modified pixel data ko PNG file me write karta hai.
- `embed_message`: Secret message image me hide karta hai.
- `extract_message`: Hidden message image se recover karta hai.
- `image_capacity`: Image me kitna message fit hoga batata hai.
- `make_sample_cover`: Demo ke liye sample PNG banata hai.

## Advantages

- External dependency ki zarurat nahi.
- Command line se easy use.
- Message invisible rehta hai under normal viewing.
- Password option available hai.

## Limitations

- Sirf 8-bit non-interlaced PNG supported hai.
- Password feature learning/demo level obfuscation hai, professional encryption nahi.
- Heavy image compression ya editing hidden data ko corrupt kar sakti hai.

## Test Cases

| Test | Expected Result |
| --- | --- |
| Sample cover create | PNG file create hoti hai |
| Capacity check | Available bytes print hote hain |
| Hide normal message | Output stego PNG create hoti hai |
| Extract normal message | Original message print hota hai |
| Extract password message without password | Error show hota hai |
| Extract password message with password | Original message print hota hai |

## Future Scope

- JPG support add karna.
- GUI interface banana.
- Strong cryptography library integrate karna.
- File hiding support add karna, sirf text nahi.
