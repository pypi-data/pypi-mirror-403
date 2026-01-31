# Documents

Methods:

- <code title="get /v1/documents">client.documents.<a href="./src/rayrift/resources/documents.py">list</a>() -> None</code>
- <code title="delete /v1/documents/{id}">client.documents.<a href="./src/rayrift/resources/documents.py">delete_document</a>(id) -> None</code>
- <code title="post /v1/documents">client.documents.<a href="./src/rayrift/resources/documents.py">ingest_file</a>() -> None</code>
- <code title="post /v1/documents">client.documents.<a href="./src/rayrift/resources/documents.py">ingest_raw_text</a>() -> None</code>
- <code title="post /v1/documents">client.documents.<a href="./src/rayrift/resources/documents.py">ingest_url</a>() -> None</code>
- <code title="patch /v1/documents/{id}">client.documents.<a href="./src/rayrift/resources/documents.py">update_document</a>(id) -> None</code>

# Search

Methods:

- <code title="post /v1/search">client.search.<a href="./src/rayrift/resources/search.py">query</a>() -> None</code>

# Folders

Methods:

- <code title="post /v1/folders">client.folders.<a href="./src/rayrift/resources/folders.py">create_folder</a>() -> None</code>
- <code title="delete /v1/folders/{id}">client.folders.<a href="./src/rayrift/resources/folders.py">delete_folder</a>(id) -> None</code>
- <code title="get /v1/folders/{id}/documents">client.folders.<a href="./src/rayrift/resources/folders.py">list_documents</a>(id) -> None</code>
- <code title="get /v1/folders">client.folders.<a href="./src/rayrift/resources/folders.py">list_folders</a>() -> None</code>
- <code title="get /v1/folders/{id}">client.folders.<a href="./src/rayrift/resources/folders.py">retrieve_folder</a>(id) -> None</code>
- <code title="patch /v1/folders/{id}">client.folders.<a href="./src/rayrift/resources/folders.py">update_folder</a>(id) -> None</code>
