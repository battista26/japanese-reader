import tkinter as tk
from tkinter import font
from PIL import ImageGrab, Image
import pytesseract
import pykakasi
from deep_translator import GoogleTranslator
import os

# ================= CONFIGURATION =================
# If on Windows, you MUST set the path to your tesseract.exe
# If on Mac/Linux, you can usually comment this line out.
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# ================= SETUP ENGINES =================

# 1. Setup Converter (Kanji -> Hiragana/Romaji)
kks = pykakasi.kakasi()
conv = kks.convert

# 2. Setup Translator
translator = GoogleTranslator(source='ja', target='en')

# ================= NEW HELPER FUNCTION =================

def preprocess_image(img):
    """
    Cleans up the image for OCR:
    1. Grayscale
    2. Resize (3x upscaling)
    3. Threshold (Binarize) & Invert
    """
    # 1. Convert to Grayscale
    img = img.convert("L")

    # 2. Scale up (Resizing helps Tesseract read low-res screen text drastically)
    # We use LANCZOS for high-quality downsampling/upsampling
    width, height = img.size
    img = img.resize((width * 3, height * 3), Image.Resampling.LANCZOS)

    # 3. Threshold and Invert
    # The Goal: Make the Text BLACK (0) and Background WHITE (255)
    # Your image has White Text (~255) and Dark BG (<100).
    # Logic: If pixel > 140 (bright), make it 0 (Black Text). Else 255 (White BG).
    
    threshold_value = 140  # Adjust this if text is too thin (decrease) or too thick (increase)
    img = img.point(lambda p: 0 if p > threshold_value else 255)
    
    # Optional: Debugging - Save the image to see what Tesseract sees
    img.save("debug_view.png") 
    
    return img

# ================= CORE FUNCTIONS =================

def process_clipboard():
    """Grabs image, PREPROCESSES it, OCRs it, parses reading, and translates."""
    status_label.config(text="Processing...", fg="blue")
    root.update()

    try:
        img = ImageGrab.grabclipboard()
        
        if img is None:
            status_label.config(text="No image found!", fg="red")
            return

        # --- NEW STEP: Preprocess the image ---
        processed_img = preprocess_image(img)
        # --------------------------------------

        # Perform OCR on the PROCESSED image
        raw_text = pytesseract.image_to_string(processed_img, lang='jpn')
        
        # Clean up text
        clean_text = raw_text.replace(" ", "").replace("\n", "")
        
        if not clean_text:
            status_label.config(text="No text detected.", fg="red")
            return

        # Get Reading
        result = conv(clean_text)
        hiragana_text = "".join([item['hira'] for item in result])
        romaji_text = " ".join([item['hepburn'] for item in result])

        # Translate
        translation = translator.translate(clean_text)

        # Update UI
        text_orig.delete("1.0", tk.END)
        text_orig.insert(tk.END, clean_text)
        
        text_reading.delete("1.0", tk.END)
        text_reading.insert(tk.END, f"{hiragana_text}\n[{romaji_text}]")
        
        text_trans.delete("1.0", tk.END)
        text_trans.insert(tk.END, translation)
        
        status_label.config(text="Success", fg="green")

    except Exception as e:
        status_label.config(text="Error", fg="red")
        print(f"Error details: {e}")

# ================= GUI SETUP =================

root = tk.Tk()
root.title("JP Screen Reader")
root.geometry("400x500")
root.attributes("-topmost", False) # Keep window always on top

# Styling
header_font = font.Font(family="Helvetica", size=10, weight="bold")
jp_font = font.Font(family="Meiryo", size=14) # Meiryo is good for JP text

# Button
btn_frame = tk.Frame(root, pady=10)
btn_frame.pack()
analyze_btn = tk.Button(btn_frame, text="Analyze Clipboard Image", command=process_clipboard, bg="#dddddd", font=header_font)
analyze_btn.pack()

status_label = tk.Label(btn_frame, text="Ready", fg="grey")
status_label.pack()

# Original Text Area
tk.Label(root, text="Original (Kanji):", anchor="w").pack(fill="x", padx=10)
text_orig = tk.Text(root, height=3, font=jp_font, wrap="char")
text_orig.pack(padx=10, pady=(0, 10), fill="x")

# Reading Area
tk.Label(root, text="Reading (Hiragana/Romaji):", anchor="w").pack(fill="x", padx=10)
text_reading = tk.Text(root, height=3, font=jp_font, wrap="char", fg="#2e86c1")
text_reading.pack(padx=10, pady=(0, 10), fill="x")

# Translation Area
tk.Label(root, text="Meaning:", anchor="w").pack(fill="x", padx=10)
text_trans = tk.Text(root, height=4, font=("Helvetica", 11), wrap="word")
text_trans.pack(padx=10, pady=(0, 10), fill="x")

root.mainloop()