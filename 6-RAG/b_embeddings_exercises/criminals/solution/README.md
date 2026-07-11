## Criminals Project Solution

- The criminals project uses a [list of pdf files](../posters/) containing homicide victim images and case descriptions.
- The project is basically a RAG project, that:
  - embed images in ChromaDB (collection **suspect_face_vectors**)
  - embed case description in the same ChromaDB, but in another collection (**case_report_vectors**)

The solution id contained in these files:
- [1-preparation.py](./1-preparation.py)  
Reads the pdf files and extract the images (into a folder as files) and text (into a SQLite db).  
Most of the important work is done in the [preparations.preparation_pdf](./preparations/preparation_pdf.py) module.
  - Main libraries:
    - The **PIL (Image) library**: Used for handling and manipulating the extracted images.
    - Custom Module ([preparations.preparation_pdf](./preparations/preparation_pdf.py)): Contains helper functions specifically tailored for PDF extraction and database management.
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

- [preparations/preparation_pdf.py](./preparations/preparation_pdf.py)
This script acts as the foundational data processing pipeline. It reads raw PDF crime or missing-person posters, extracts their text and images, uses OpenAI models to clean the text into structured JSON and filter for human faces, and stores the structured data into a local SQLite database.
  - main libraries:
    - **fitz (PyMuPDF)**: Used to open PDFs and extract raw text and embedded images from the pages.
    - **sqlite3**: Used to create and manage the relational database (documents and document_assets tables).
    - **PIL (Image) & io**: Used to open, duplicate, resize, and save extracted image byte streams.
    - **base64**: Used to encode images into string format so they can be sent over HTTP to OpenAI.
    - **gpt-4o-mini**: 
    The OpenAI multimodal LLM utilized twice: 
      - once as a vision model to verify if a cropped image contains a person, 
      - and once as a text model to parse unstructured OCR text into structured JSON.
  - main functions:
    - **extract_poster_components(poster_path)**:  
    Extracts all raw text and images from a PDF poster, filters out non-human images, and cleans the text.
    - **is_person(img)**:  
    Resizes an image and sends it to gpt-4o-mini to determine via a vision prompt if a person is present in the frame.
    - **save_images(image_PIL_objects, tempdata_dir, doc_id, DBconn)**:  
    Saves approved images as physical PNG files and records their paths and parent document IDs in the database.
    - **clean_text_to_json(full_text)**: Prompts gpt-4o-mini to transform raw, unstructured poster text into a clean, standardized JSON object.
    - **save_full_text(full_text, posterfile, DBconn)**:  
    Inserts the cleaned poster text JSON into the database and returns the newly generated unique document ID.


- [2-vectorization.py](./2-vectorization.py)
Create embeddings from images and texts, and store thise in ChromaDB (in separate collections)
**Uses ArcFace model to detect a face in an image** (wo that we get the correct image)  
**Uses text-embedding-3-large model to 
  - main libraries:
    - **sqlite3**: Connects to the local database to fetch existing image paths and documents.
    - **cv2 (OpenCV)**: Loads and processes images from the file system.
    - **chromadb**: Acts as the vector database to store and index the generated embeddings using cosine similarity.
    - **openai (OpenAI)**: Used to interface with OpenAI's API.
    - **InsightFace (FaceAnalysis)**: Python toolkit used for face detection and extraction.
    - **buffalo_l (ArcFace model)**: The specific InsightFace model used to extract high-accuracy face embeddings.
    - **text-embedding-3-large**: The OpenAI model used to generate deep, high-dimensional text embeddings.
  - main functions:
    - **build_face_index(db_name, collection)**:  
    Extracts the highest-scoring face embedding from database image assets using InsightFace and saves them into the ChromaDB face collection.
    - **build_text_index(db_name, collection)**:  
    Generates vector embeddings for all document text via OpenAI's API and stores them in the ChromaDB text collection.
    - **vectorize_all()**:  
    Clears previous vector data, initializes the persistent ChromaDB client, and runs both the face and text indexing pipelines.



- [3-search.py](./3-search.py)  
This is actually a small demo of the RAG data.  
It takes a target query image, extracts the most prominent face embedding, and searches the persistent ChromaDB vector database to return the top 5 closest matching criminal or missing-person file entries based on facial features.
  - Main libraries:
    - **cv2 (OpenCV)**: Used to read the input query image file from disk.
    - **chromadb**: Connects to the local database to query the stored face vectors using vector similarity.
    - **insightface (FaceAnalysis)**: The high-performance framework used to localize faces and extract identity features.
    - **buffalo_l (ArcFace model)**: The specific face recognition deep learning model used to map the face into a unique geometric embedding.
  - Main Functions:
    - **get_face_embedding(image_path, app)**:  
    Reads an image, detects all faces inside it, selects the highest-confidence face, and returns its normalized vector embedding as a list.
    - **query_face_collection(embedding, top_k)**:  
    Connects to ChromaDB and performs a vector search against the face vector collection to retrieve the closest matching document IDs and metadata.
    - **search_by_image(query_image_path, top_k)**:  
    Acts as the main pipeline coordinator by initializing the facial model, triggering the embedding extraction, running the database query, and outputting the results.
