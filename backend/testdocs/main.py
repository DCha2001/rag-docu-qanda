from unstructured.partition.auto import partition
from unstructured.chunking.title import chunk_by_title
from unstructured.staging.base import elements_to_json
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
import json

import pdb 


file_path = "C:/Users/Derek/OneDrive/Desktop/AIDocuReader/backend/testdocs/docs"
base_file_name = "layout-parser-paper-fast"

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

def ingest():
    pass

def parse(file_path:str) -> list:
    elements = partition(
        filename=file_path,
        strategy="fast",          # accurate but slower; use "fast" for prototyping
        infer_table_structure=True,  # captures tables properly
        include_page_breaks=True,)
    return elements

def chunk(elements:list) -> list:
    chunked_elements = chunk_by_title(
        elements=elements, 
        max_characters=1500,       # max chunk size
        new_after_n_chars=1000,    # soft limit — break early if a new title appears
        combine_text_under_n_chars=300)  # combine tiny fragments

    return [c for c in chunked_elements if c.text.strip()]

def embed(chunks:list[str]) -> list[list[float]]:
    try:
        embedded = embeddings.embed_documents([element.text for element in chunks])
        return embedded
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except IOError:
        print(f"Error: Unable to access file '{file_path}'.")



def main():
    elements = parse(f"{file_path}/{base_file_name}.pdf")
    chunked_elements = chunk(elements)
    # json_output = elements_to_json(chunked_elements)
    embedded = embed(chunked_elements)
    embedded_json = json.dumps(embedded)
    with open(f"{file_path}/{base_file_name}-embeddings.json", "w") as f:
        f.write(embedded_json)
    # embed(f"{file_path}/{base_file_name}-output.json")

if __name__ == "__main__":
    main()