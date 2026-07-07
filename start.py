import os
import subprocess
import sys

DB_PATH = os.path.join("parsed", "dd_platform.db")


def main():
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python start.py your_email@example.com")

    email = sys.argv[1]

    if os.path.exists(DB_PATH):
        print(f"Found existing data at {DB_PATH} - skipping data collection.")
        print("To force a fresh re-collection, delete that file first (or run "
              "'python run_pipeline.py <email>' directly).")
    else:
        print("No existing data found - collecting it now (this takes a while)...")
        subprocess.run([sys.executable, "run_pipeline.py", email], check=True)

    subprocess.run(["streamlit", "run", "streamlit_app.py"])


if __name__ == "__main__":
    main()
