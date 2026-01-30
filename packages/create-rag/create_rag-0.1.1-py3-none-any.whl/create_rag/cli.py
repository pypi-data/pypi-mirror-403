import os
import sys

PROJECT_STRUCTURE = {
    "data": {
        "pdfs": {},
        "texts": {
            "data.txt": "text file for ingestion\n"
        }
    },
    "src": {
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
    ".gitignore": ""
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
