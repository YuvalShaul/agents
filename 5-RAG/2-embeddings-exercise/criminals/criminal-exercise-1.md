## Multimodal Vector Database

1. Project Objective
- In this exercise you will build a manual Multimodal Retrieval System. 
- You'll convert pdf files that contain text and images of criminals into vector embeddings.
- Then you'll build a manual vector database to store and retrieve the embeddings.

### Phase I: Decomposition
- For every PDF in your dataset:
    - Text Extraction: Use fitz to pull the raw text from the document. This text serves as the "description" for your vector.
    - Image Extraction: Locate and extract the suspect/victim's photo from the PDF.
    - Standardization: Ensure all images are converted to RGB and all text is stripped of non-standard characters.
- As you process each PDF, create a temporary directory to save the extracted images (as .jpg or .png) and the text inside an SQLite database.
- This allows you to verify that the extraction from the PDF was successful be
fore moving into the vectorization phase. If the math fails later, you still have the "clean" data to look at.
- Here's the sql entry structure:
  - vector_idx (Integer): This is the most critical column. It acts as the "bridge" or pointer to the specific position in your .bin file. If the math search finds a match at index #42, you query the database for the row where vector_idx is 42.

  - case_text (Text): This stores the full, cleaned text extracted from the PDF. Instead of managing separate .txt files, you keep the entire "Description of Incident," "Location," and "Date" here as a single string.

  - image_filename (Text): This stores the relative path or filename of the suspect/victim photo (e.g., images/bassett_darnell_0.jpg). You store the name/path rather than the image itself to keep the database lightweight.

  - original_pdf (Text): The name of the source file (e.g., bassett_darnell_0.pdf). This allows you to trace the data back to its original government document if needed.
- Tools:
  - **PyMuPDF (fitz)**: To open PDF files and extract the raw suspect image and the text stream.

  - **Pillow (PIL)**: To process and standardize the extracted images.
  - **SQLite3**: To store the extracted images and text.


