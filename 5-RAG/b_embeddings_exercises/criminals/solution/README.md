## Criminals Project Solution

- The criminals project uses a [list of pdf files](../posters/) containing homicide victim images and case descriptions.
- The project is basically a RAG project, that:
  - embed images in ChromaDB (collection **suspect_face_vectors**)
  - embed case description in the same ChromaDB, but in another collection (**case_report_vectors**)

The solution id contained in these files:
- [1-preparation.py](./1-preparation.py) 
Reads the pdf files and extract the images (into a folder as files) and text (into a SQLite db).
  - The PIL (Image) library: Used for handling and manipulating the extracted images.
  - Custom Module ([preparations.preparation_pdf](./preparations/preparation_pdf.py)): Contains helper functions specifically tailored for PDF extraction and database management. It uses the fitx (PyMuPDF) library to extract items from a pdf file.
  - main functions:
    - **process_all_pdf_files(tempdata_dir, DB_NAME)**: 
    Iterates through all PDF files in the posters folder, extracts their text and images, and saves the results to the database and temporary directory.
    - **prepare_tempdata_dir(tempdata_dir)**: 
    Creates or cleans up the temporary directory where extracted image files will be stored.
    - **extract_poster_components(poster_path)**: 
    Parses a single PDF poster to extract its full text and image objects.
    - **save_full_text(full_text, posterfile, DBconn)**: 
    Inserts the extracted poster text into the database and returns the generated document ID.
    - **save_images(image_PIL_objects, tempdata_dir, doc_id, DBconn)**: 
    Saves the extracted images as files in the temporary directory and logs their metadata in the database linked to the document ID.

- [2-vectorization.py](./2-vectorization.py)
Create embeddings from images and texts, and store thise in ChromaDB (in separate collections)
  - main libraries:
    - sqlite3: Connects to the local database to fetch existing image paths and documents.
    - cv2 (OpenCV): Loads and processes images from the file system.
    - chromadb: Acts as the vector database to store and index the generated embeddings using cosine similarity.
    - openai (OpenAI): Used to interface with OpenAI's API.
    - InsightFace (FaceAnalysis): Python toolkit used for face detection and extraction.
    - buffalo_l (ArcFace model): The specific InsightFace model used to extract high-accuracy face embeddings.
    - text-embedding-3-large: The OpenAI model used to generate deep, high-dimensional text embeddings.
