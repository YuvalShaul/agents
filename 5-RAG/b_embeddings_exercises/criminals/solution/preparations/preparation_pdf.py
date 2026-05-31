import os
import io
import shutil
import sqlite3
import fitz
import time
import base64
from PIL import Image
from pathlib import Path
from openai import OpenAI


def prepare_tempdata_dir(tempdata_dir):

    # If it's there, kill it
    if tempdata_dir.exists():
        shutil.rmtree(tempdata_dir)

    # Create it fresh.
    tempdata_dir.mkdir()
    return tempdata_dir

def init_db(DB_NAME):
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Main Document Table
    c.execute('''CREATE TABLE IF NOT EXISTS documents 
                 (id INTEGER PRIMARY KEY, file_name TEXT, full_text TEXT)''')
    # Assets Table (Multiple images per 1 document)
    c.execute('''CREATE TABLE IF NOT EXISTS document_assets 
                 (id INTEGER PRIMARY KEY, doc_id INTEGER, file_path TEXT,
                  FOREIGN KEY(doc_id) REFERENCES documents(id))''')
    conn.commit()
    return conn


def extract_poster_components(poster_path):
    doc = fitz.open(poster_path)
    full_text = ''
    image_list = []
    image_PIL_objects = []

    for page in doc:
        # 1. Extract the Text
        full_text += page.get_text("text")  # Retreive text, and return it s a simple text

        # 2. Get Images from page
        image_list += page.get_images(full=True)
    
    full_text = clean_text_to_json(full_text)

    for image in image_list:
        xref = image[0]    # This is just a cross reference of the image
        base_image = doc.extract_image(xref)      # Get Image data (dict) 
        img = Image.open(io.BytesIO(base_image["image"]))  # base_image['image'] type is bytes

        # Skip images that are perfectly square (likely logos)
        if is_person(img):
            print('yes')
            image_PIL_objects.append((img,poster_path.stem) )
    
    return full_text, image_PIL_objects


def is_person(img):
   
    time.sleep(2)   
    client = OpenAI()
   # Create a separate copy so the original stays full-size
    img_work = img.copy() 
    
    # Now, shrinking img_work won't affect the 'img' outside this function
    img_work.thumbnail((378, 378))
    
    temp_path = Path("tmp_check.jpg").resolve()
    img_work.save(temp_path, format="JPEG", quality=85)

    with open(temp_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Is there a person in this image? Answer only 'yes' or 'no'."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }],
        max_tokens=5
        )
        content = response.choices[0].message.content.lower()
        print(f'Content: {content}')
        return "yes" in content
    finally:
        if temp_path.exists():
            temp_path.unlink()

# ===========================================================================
def save_images(image_PIL_objects, tempdata_dir, doc_id, DBconn):

    c = DBconn.cursor()
    for i, img in enumerate(image_PIL_objects):
        
        file_name = f"{img[1]}.png"
        save_path = tempdata_dir / file_name
    
        # Save the PIL object to the path
        img[0].save(save_path, format="PNG")
        print(f"Saved: {save_path}")

        # Save details into the DB
        c.execute("INSERT INTO document_assets (doc_id, file_path) VALUES (?, ?)", 
                          (doc_id, str(save_path)))
            
        DBconn.commit()

# ===========================================================================
def clean_text_to_json(full_text):
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a structured data extractor. Given raw text from a crime/missing-person poster, "
                    "return ONLY a JSON object with these keys: "
                    "case_number, crime_type, victim_name, location_and_time, case_summary, investigating_officers. "
                    "If a field is not found, use null. Return raw JSON only — no markdown, no code fences."
                )
            },
            {"role": "user", "content": full_text}
        ],
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


# ===========================================================================
def save_full_text(full_text, posterfile, DBconn):
    c = DBconn.cursor()
    c.execute("INSERT INTO documents (file_name, full_text) VALUES (?, ?)", 
               (posterfile, full_text))
    doc_id = c.lastrowid
    DBconn.commit()
    return doc_id