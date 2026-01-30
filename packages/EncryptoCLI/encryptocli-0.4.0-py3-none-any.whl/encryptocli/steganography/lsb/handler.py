"""LSB steganography utilities using a class-based API."""

import numpy as np
from PIL import Image


class LSBSteganography:
    """Hide and reveal secrets using least significant bit steganography.

    This implementation embeds secret data into the least significant bits (LSBs)
    of image pixels. Supports PNG format (lossless) for reliable embedding and extraction.
    """

    def encrypt_text(
        self, input_image_path: str, secret: str, output_dir: str = "./"
    ) -> None:
        """Embed secret text into an image and save as encrypto.png in output_dir.

        PNG format is recommended for steganography as it is lossless.
        JPEG or other lossy formats will corrupt the hidden data.

        Args:
            input_image_path: Path to the input image file (PNG recommended).
            secret: Secret text to hide in the image.
            output_dir: Directory to save the output image (default: current directory).

        Returns:
            None
        """
        img = Image.open(input_image_path).convert("RGB")
        img_array = np.array(img)
        flat = img_array.flatten()

        # Encode the secret length and data
        secret_bytes = secret.encode("utf-8")
        length = len(secret_bytes)

        # Create payload: 4 bytes for length + secret
        payload = length.to_bytes(4, byteorder="big") + secret_bytes

        # Convert payload to bits
        bit_string = "".join(format(byte, "08b") for byte in payload)
        bit_string += "11111111"  # End marker

        # Embed bits into LSBs of pixel values
        bit_index = 0
        for i in range(len(flat)):
            if bit_index >= len(bit_string):
                break
            bit = int(bit_string[bit_index])
            flat[i] = (flat[i] & 0xFE) | bit  # Modify LSB
            bit_index += 1

        # Reshape and save
        stego_array = flat.reshape(img_array.shape)
        stego_img = Image.fromarray(stego_array.astype(np.uint8), "RGB")
        stego_img.save(f"{output_dir}encrypto.png")

    def decrypt_image(self, input_image_path: str) -> str:
        """Extract hidden text from an image.

        Uses LSB (Least Significant Bit) steganography to extract secret text
        from the least significant bits of image pixels.

        Args:
            input_image_path: Path to the image containing hidden text.

        Returns:
            str: The extracted secret text from the image.
        """
        img = Image.open(input_image_path).convert("RGB")
        img_array = np.array(img)
        flat = img_array.flatten()

        # Extract bits from LSBs
        bit_string = "".join(str(pixel & 1) for pixel in flat)

        # Extract length (first 32 bits)
        if len(bit_string) < 32:
            return ""

        length_bits = bit_string[:32]
        length = int(length_bits, 2)

        # Extract secret bytes
        secret_bits = bit_string[32 : 32 + (length * 8)]

        try:
            secret_bytes = bytes(
                int(secret_bits[i : i + 8], 2) for i in range(0, len(secret_bits), 8)
            )
            return secret_bytes.decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return ""
