import json
import os
import shutil
import subprocess
from datetime import datetime

GITHUB_USER = "belaroug"
REPO_NAME = "dz_lessons"
LESSONS_FILE = "lessons.json"
PDF_DIR = "pdfs"

def load_lessons():
    if not os.path.exists(LESSONS_FILE):
        return []
    with open(LESSONS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return []

def main():
    print("=== 📄 إضافة فرض أو ملف PDF سحابياً ===")
    pdf_source = input("مسار ملف الـ PDF (مثال /sdcard/Download/fard.pdf): ").strip()
    if not os.path.exists(pdf_source):
        print("❌ الملف غير موجود في المسار المحدد!")
        return

    subject = input("المادة (اللغة الإنجليزية / اللغة الفرنسية): ").strip()
    term = int(input("الفصل الدراسي (1 أو 2 أو 3): ").strip() or "1")
    doc_type = input("التصنيف (فرض / اختبار / درس / ملخص): ").strip() or "فرض"
    title = input("عنوان الملف: ").strip()

    lessons = load_lessons()
    new_id = max([item.get("id", 0) for item in lessons], default=100) + 1

    filename = f"doc_{new_id}.pdf"
    dest_path = os.path.join(PDF_DIR, filename)
    shutil.copy2(pdf_source, dest_path)

    raw_pdf_url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/main/{PDF_DIR}/{filename}"

    new_entry = {
        "id": new_id,
        "grade": "2am",
        "term": term,
        "subject": subject,
        "type": doc_type,
        "order": new_id,
        "title": title,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "lesson_content": "<p>ملف PDF جاهز للمطالعة والتحميل.</p>",
        "exercises_content": "",
        "pdf_url": raw_pdf_url
    }

    lessons.append(new_entry)

    with open(LESSONS_FILE, "w", encoding="utf-8") as f:
        json.dump(lessons, f, ensure_ascii=False, indent=2)

    print("🚀 جاري رفع الملف وتحديث السحابة...")
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", f"Add PDF: {title}"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("🎉 تم النشر بنجاح! أغلق الإنترنت الآن، وسيصل التحديث لكل الهواتف.")
    except Exception as e:
        print(f"⚠️ تأكد من فتح الإنترنت ثم نفذ 'git push': {e}")

if __name__ == "__main__":
    main()
