import os
import sys
from PIL import Image

SIZE = (310, 310)  # максимальний розмір зображення

def process_image(input_path):
    try:
        with Image.open(input_path) as img:
            # змінюємо розмір зі збереженням пропорцій
            img.thumbnail(SIZE)

            # вихідний шлях з тим самим ім'ям, але .webp
            output_path = os.path.splitext(input_path)[0] + ".webp"

            # зберігаємо у WebP (прозорість не чіпаємо)
            img.save(output_path, "webp", quality=85)

        # видаляємо оригінал, якщо це не webp
        if not input_path.lower().endswith(".webp"):
            os.remove(input_path)

        print(f"✅ {input_path} → {output_path}")
    except Exception as e:
        print(f"❌ Помилка з {input_path}: {e}")

def main():
    if len(sys.argv) < 2:
        print("Використання: python resize_to_webp.py <шлях_до_папки>")
        sys.exit(1)

    folder = sys.argv[1]

    if not os.path.isdir(folder):
        print(f"❌ Папку не знайдено: {folder}")
        sys.exit(1)

    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                process_image(os.path.join(root, file))

if __name__ == "__main__":
    main()
