import os
from pathlib import Path
from PIL import Image
from dotenv import load_dotenv
from preparations.preparation_pdf import init_db, prepare_tempdata_dir, extract_poster_components, save_full_text, save_images

SCRIPT_DIR = Path(__file__).parent
POSTERS_FOLDER = SCRIPT_DIR / "../posters"
tempdata_dir = SCRIPT_DIR / "tempdata"
DB_NAME = str(SCRIPT_DIR / "posters.db")

load_dotenv(dotenv_path=SCRIPT_DIR / '../../../../.env', override=True)
print(f"Key found: {os.getenv('OPENAI_API_KEY')[:90]}...")


def process_all_pdf_files(tempdata_dir, DB_NAME):
    DBconn = init_db(DB_NAME)
    tempdata_dir = prepare_tempdata_dir(tempdata_dir)
    for posterfile in os.listdir(POSTERS_FOLDER):
        if posterfile.lower().endswith(".pdf"):
            print(f"  🧬 Processing: {posterfile}")
            poster_path = POSTERS_FOLDER / posterfile
            full_text, image_PIL_objects = extract_poster_components(poster_path)
            doc_id = save_full_text(full_text, posterfile, DBconn)
            save_images(image_PIL_objects, tempdata_dir, doc_id, DBconn)


# ===========================================================================
process_all_pdf_files(tempdata_dir, DB_NAME)
