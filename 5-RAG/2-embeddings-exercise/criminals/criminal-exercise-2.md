### Phase II: The Fused Vector (The Math)

In the **Vectorization Phase**, the goal is to transform the "human-readable" assets stored in your staging area (the images and SQL text) into "machine-understandable" math. This phase acts as the brain of your retrieval system.

---

#### 1. Generating the Image Vector
- To turn the suspect's photo into a mathematical representation, you use:
  - **Vision Transformer (ViT)**.
  - **The Tool:** The **`transformers`** library by Hugging Face.
  - **The Model:** `CLIPVisionModel` (part of the `openai/clip-vit-base-patch32` suite).
- **How it works:** 
  - You load the image file using **Pillow**
  - You use the CLIP Processor (a needed tool) to resize and normalize it
  - You feed the processed image into the CLIP vision model. 
  - The model outputs a **512-dimensional vector** that captures visual patterns like facial structure and clothing.
- Storing in the Binary File (.bin)
To keep the AI math separate from the human facts, you save the vectors in a raw format.
  - The Tool: Python's built-in struct module.
  - The Format: Store each number as a float32 (4 bytes per number).
  - The File: A single vectors.bin file.
    - Since each vector is 1,024 numbers, each poster occupies exactly 4,096 bytes in your .bin file. 
    - You append each new vector to the end of this file.

- Generating the Text VectorThe Source: 
  - You pull the case_text string directly from your SQLite database record.
  - The Tool: The transformers library.
  - The Model: CLIPTextModel (from the openai/clip-vit-base-patch32 suite).
  - The Workflow: 
    1.  Pass the string to the CLIP Processor (Tokenizer).
    2.  The processor converts the words into a grid of numbers (Tensors).
    3.  Feed the Tensors into the CLIPTextModel.
    4.  The model outputs a 512-dimensional vector representing the meaning of the crime report.2. 
- Fusing the Vectors (The "Addition")
  - You don't literally add the numbers together (like $1+1=2$); 
  - you Concatenate them.
  How: 
    - You take the 512 numbers from the image and the 512 numbers from the text and "glue" them end-to-end.
    - The Result: You now have a single list of 1,024 numbers.
    - Final Step: You Normalize this 1,024-dimension vector. 
    This is a mathematical requirement that ensures the vector has a "length" of 1.0, making it ready for high-speed similarity comparisons.3. 
- Storing in the Binary File (.bin)
  - This new combined vector replaces any previous individual attempts. 
  - It is the final "ID" for that case.
  - Where: You append it to your single .bin file.
  - How: You use Python's struct module to pack the 1,024 floats into raw bytes ($4,096$ bytes total) and write them to the end of the file.
  - The File Layout:
    [Vector 0 (1024 floats)][Vector 1 (1024 floats)][Vector 2 (1024 floats)]...4. 
- Referencing from SQL (The Pointer)
  - Once the vector is safely in the binary file, you need to tell your SQL database exactly where it is.
  - The Column: Go to the row in your SQLite table that matches the case you just processed.
  - The Value: Update the vector_idx column with the integer position of that vector.
  - If it's the first vector in the file, vector_idx = 0. If it's the second, vector_idx = 1.