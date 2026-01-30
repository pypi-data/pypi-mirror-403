import os
import sys

PROJECT_STRUCTURE = {
    "chroma_db": {},
    "data": {
        "pdfs": {},
        "texts": {
            "sample.txt": "Sample text file for ingestion\n"
        }
    },
    "src": {
        "__init__.py": "",
        "config.py": "",
        "loader.py": "",
        "chunker.py": "",
        "embeddings.py": "",
        "llm.py": "",
        "vector_store.py": "",
        "retriever.py": "",
        "memory.py": "",
        "rag.py": ""
    },
    "app.py": "",
    "ingest.py": "",
    "query.py": "",
    "requirements.txt": "",
    ".env": "",
    ".gitignore": "__pycache__/\n.env\nchroma_db/\n"
}


def create_structure(base_path, structure):
    for name, content in structure.items():
        path = os.path.join(base_path, name)

        if isinstance(content, dict):
            os.makedirs(path, exist_ok=True)
            create_structure(path, content)
        else:
            with open(path, "w") as f:
                f.write(content)


def main():
    if len(sys.argv) < 2:
        print("Usage: create-rag <project-name>")
        sys.exit(1)

    project_name = sys.argv[1]
    os.makedirs(project_name, exist_ok=True)
    create_structure(project_name, PROJECT_STRUCTURE)

    print(f"RAG project '{project_name}' created successfully!")
    print("cd", project_name)
