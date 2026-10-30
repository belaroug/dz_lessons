import json
import os
import shutil
import subprocess
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "edu_admin_secret"

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
LESSONS_FILE = os.path.join(REPO_DIR, "lessons.json")
PDF_DIR = os.path.join(REPO_DIR, "pdfs")
os.makedirs(PDF_DIR, exist_ok=True)

GITHUB_USER = "belaroug"
REPO_NAME = "dz_lessons"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة رفع الفروض والدروس الذكية</title>
    <style>
        body { font-family: system-ui, sans-serif; background: #F4F6F9; margin: 0; padding: 20px; color: #333; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 25px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); }
        h2 { color: #1565C0; text-align: center; margin-top: 0; }
        .form-group { margin-bottom: 15px; }
        label { display: block; font-weight: bold; margin-bottom: 5px; }
        input, select, textarea { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; }
        button { background: #1565C0; color: white; border: none; padding: 12px; width: 100%; font-size: 1.1em; border-radius: 6px; cursor: pointer; font-weight: bold; }
        button:hover { background: #0D47A1; }
        .alert { padding: 10px; background: #E8F5E9; color: #2E7D32; border-radius: 6px; margin-bottom: 15px; text-align: center; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h2>📚 لوحة التحكم ونشر الفروض (ذكية)</h2>
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="alert">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        <form method="POST" enctype="multipart/form-data">
            <div class="form-group">
                <label>اختر ملف الـ PDF:</label>
                <input type="file" name="pdf_file" accept=".pdf" required onchange="autoDetect(this)">
            </div>
            <div class="form-group">
                <label>عنوان الدرس أو الفرض:</label>
                <input type="text" name="title" id="title" placeholder="مثال: الفرض الأول للفصل الأول في الرياضيات" required>
            </div>
            <div class="form-group">
                <label>المادة المقترحة:</label>
                <select name="subject" id="subject">
                    <option value="الرياضيات">الرياضيات</option>
                    <option value="العلوم الطبيعية">العلوم الطبيعية</option>
                    <option value="اللغة الإنجليزية">اللغة الإنجليزية</option>
                    <option value="اللغة الفرنسية">اللغة الفرنسية</option>
                </select>
            </div>
            <div class="form-group">
                <label>الفصل الدراسي المقترح:</label>
                <select name="term" id="term">
                    <option value="1">الفصل الأول</option>
                    <option value="2">الفصل الثاني</option>
                    <option value="3">الفصل الثالث</option>
                </select>
            </div>
            <div class="form-group">
                <label>التصنيف:</label>
                <select name="type" id="type">
                    <option value="فرض">فرض</option>
                    <option value="اختبار">اختبار</option>
                    <option value="درس">درس</option>
                    <option value="ملخص">ملخص</option>
                </select>
            </div>
            <button type="submit">🚀 رفع ونشر فوراً لكل التلاميذ</button>
        </form>
    </div>

    <script>
        // ميزة الاقتراح الذكي بناءً على اسم الملف المختار
        function autoDetect(input) {
            if (input.files && input.files[0]) {
                let filename = input.files[0].name.toLowerCase();
                let titleInput = document.getElementById('title');
                let subjectSelect = document.getElementById('subject');
                let typeSelect = document.getElementById('type');
                
                titleInput.value = input.files[0].name.replace('.pdf', '');

                if (filename.includes('math') || filename.includes('رياضيات')) subjectSelect.value = 'الرياضيات';
                else if (filename.includes('science') || filename.includes('علوم')) subjectSelect.value = 'العلوم الطبيعية';
                else if (filename.includes('english') || filename.includes('انجليزية')) subjectSelect.value = 'اللغة الإنجليزية';
                else if (filename.includes('french') || filename.includes('فرنسية')) subjectSelect.value = 'اللغة الفرنسية';

                if (filename.includes('اختبار') || filename.includes('test')) typeSelect.value = 'اختبار';
                else if (filename.includes('ملخص')) typeSelect.value = 'ملخص';
                else typeSelect.value = 'فرض';
            }
        }
    </script>
</body>
</html>
"""

def load_lessons():
    if not os.path.exists(LESSONS_FILE):
        return []
    with open(LESSONS_FILE, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return []

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("pdf_file")
        if file and file.filename.endswith(".pdf"):
            title = request.form.get("title", "فرض مبرمج")
            subject = request.form.get("subject", "الرياضيات")
            term = int(request.form.get("term", 1))
            doc_type = request.form.get("type", "فرض")

            lessons = load_lessons()
            new_id = max([item.get("id", 0) for item in lessons], default=100) + 1

            filename = f"doc_{new_id}.pdf"
            dest_path = os.path.join(PDF_DIR, filename)
            file.save(dest_path)

            raw_pdf_url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/main/pdfs/{filename}"

            new_entry = {
                "id": new_id,
                "grade": "2am",
                "term": term,
                "subject": subject,
                "type": doc_type,
                "order": new_id,
                "title": title,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "lesson_content": "<p>ملف PDF جاهز للمطالعة.</p>",
                "exercises_content": "",
                "pdf_url": raw_pdf_url
            }

            lessons.append(new_entry)
            with open(LESSONS_FILE, "w", encoding="utf-8") as f:
                json.dump(lessons, f, ensure_ascii=False, indent=2)

            # الرفع التلقائي إلى GitHub
            try:
                subprocess.run(["git", "add", "."], check=True)
                subprocess.run(["git", "commit", "-m", f"Web Admin: Add {title}"], check=True)
                subprocess.run(["git", "push", "origin", "main"], check=True)
                flash("🎉 تم رفع الفرض ونشره بنجاح لجميع التلاميذ!")
            except Exception as e:
                flash(f"تم الحفظ محلياً، تأكد من الاتصال بالإنترنت للرفع: {e}")

            return redirect(url_for("index"))

    return render_template_string(HTML_TEMPLATE)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
