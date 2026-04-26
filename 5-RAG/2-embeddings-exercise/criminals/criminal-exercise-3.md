### Phase III: Testting the VectorDB (The Math)


In this phase you will test your vector database.

You are testing whether your $1,024$-dimensional fused vectors actually "understand" the relationship between visual faces and textual crime descriptions.

---

## 1. The Setup: Loading the DB into Memory
Before running tests, you must bridge the gap between your two storage systems:
* **Load the Math:** Read the entire `.bin` file into a list or array. If you have $50$ posters, you should have a matrix of $50 \times 1024$ numbers.
* **Prepare the Logic:** Write a simple "Similarity Function" (using a standard loop or a dot product) that compares a query vector to every vector in your list and returns the `vector_idx` with the highest score.

---

## 2. Test 1: The "Visual-Only" Search (Face Matching)
**The Scenario:** You have a new "Mystery Photo" of a suspect (e.g., the photo with glasses) and you want to know which case it belongs to.
* **Create Query Vector:** Pass the photo through the **CLIP Processor** and the **CLIPVisionModel** to get $512$ numbers. Pad the remaining $512$ slots (the text half) with **zeros**.
* **The Math:** Compare this $1,024$-dim query against your `.bin` file.
* **The Validation:** Use the winning `vector_idx` to fetch the record from **SQLite3**. 
* **Success:** Does the image filename in SQL match the person in your mystery photo? This proves the "Visual half" of your fused vector works.

---

## 3. Test 2: The "Textual-Only" Search (Meaning Matching)
**The Scenario:** You remember a case involved "hiding a body near a street," but you don't have the exact words used in the poster.
* **Create Query Vector:** Pass your natural language phrase through the **CLIP Processor** and the **CLIPTextModel** to get $512$ numbers. Pad the first $512$ slots (the image half) with **zeros**.
* **The Math:** Run the similarity loop against the `.bin` file.
* **The Validation:** Retrieve the `case_text` from the winning SQL record.
* **Success:** Does the retrieved text describe the incident you searched for, even if the keywords are different? This proves the "Textual half" of your vector captures semantic meaning.

---

## 4. Test 3: The "Multimodal" Search (The Identity Lock)
**The Scenario:** You have a photo of a person, but there are multiple similar-looking suspects. You add a text clue like "Location: 37th Street" to narrow it down.
* **Create Query Vector:** 1.  Generate the $512$ visual numbers from the photo.
    2.  Generate the $512$ text numbers from the location string.
    3.  Concatenate them into a full $1,024$-dim vector.
* **The Math:** Run the similarity loop.
* **The Validation:** Retrieve the full record from SQL.
* **Success:** This should produce your **highest similarity score**. It demonstrates that the VectorDB is "fusing" both types of data to provide a more accurate match than text or image could do alone.



---

## 5. Summary of the Verification
By the end of these three tests, you have verified the integrity of your custom DB:
1.  **Binary Integrity:** Your `.bin` file correctly stores and retrieves $4,096$-byte blocks.
2.  **Relational Integrity:** Your `vector_idx` in **SQLite3** correctly points to the right mathematical "slot."
3.  **Model Integrity:** The **CLIP** vectors are successfully mapping "Vibes" and "Faces" to the same coordinate system.

**If you find the correct Darnell Bassett poster using a photo he isn't wearing glasses in, but your query photo has glasses—your VectorDB is officially "smart" enough.**