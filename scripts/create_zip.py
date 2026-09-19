import os
import zipfile

PROJECT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
ZIP_FILENAME = os.path.join(PROJECT_DIR, "document_intelligence_submission.zip")

EXCLUDE_DIRS = {"__pycache__", ".pytest_cache", ".git", "venv", ".venv", ".idea", ".vscode"}
EXCLUDE_EXTS = {".pyc", ".pyo", ".db", ".sqlite3"}


def create_submission_zip():
    print(f"Creating submission zip: {ZIP_FILENAME}...")
    count = 0
    with zipfile.ZipFile(ZIP_FILENAME, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(PROJECT_DIR):
            # Exclude specified directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

            for file in files:
                if file == "document_intelligence_submission.zip":
                    continue
                ext = os.path.splitext(file)[1]
                if ext in EXCLUDE_EXTS:
                    continue

                abs_filepath = os.path.join(root, file)
                rel_filepath = os.path.relpath(abs_filepath, PROJECT_DIR)
                zipf.write(abs_filepath, rel_filepath)
                count += 1

    zip_size_mb = os.path.getsize(ZIP_FILENAME) / (1024 * 1024)
    print(f"Successfully packaged {count} files into '{ZIP_FILENAME}' ({zip_size_mb:.2f} MB)")


if __name__ == "__main__":
    create_submission_zip()
