[![PyPI](https://img.shields.io/pypi/v/pydoc-mintlify)](https://pypi.org/project/pydoc-mintlify/)

# pydoc-mintlify

A pydoc-markdown plugin for Mintlify. Comes with a CLI to run a dev server with Mintlify and watch for changes.

## Installation

```
pip install pydoc-mintlify
```

or with

```
uv add pydoc-mintlify
```

## Usage

### Configure pydoc-markdown.yaml

Set the renderer to `pydoc_mintlify.MintlifyRenderer` and configure the fields. Functionally this is the same as docs.json in mintlify.

```yaml
loaders:
  - type: python
    search_path: ["."] # Must specify the search path (e.g. ["."] for flat layout or ["src"] for src/ layout)
    packages: ["<your package name>"] # Must specify you package name (i.e. where all your python files are)

renderer:
  type: pydoc_mintlify.MintlifyRenderer # Must specify the pydoc_mintlify renderer
  docs_base_path: docs # Where your keep all your mintlify .mdx files
  relative_output_path: reference # Where the auto-generated .mdx files will be dumped
  nav: # Navigation configuration for your generated .mdx files. (This will be dumped into a tab with the same name in your docs.json)
    tab: SDK Reference # Must match the name of a tab in your docs.json
    groups:
      - group: Programs
        pages:
          - <your package name>/module_1 # specify pages as relative paths starting with your package name
          - title: <page name> # You can also set the title and description of the page here
            description: <description of module>
            path: <your package name>/module_2
      - group: Context
        pages:
          - title: <page name 2> # You can also set the title and description of the page here
            description: <description of module 2>
            path: <your package name>/module_3
      - <your package name>/module_4
      - title: <page name 3> # You can also set the title and description of the page here
        description: <description of module 3>
        path: <your package name>/module_5
```

### Example pydoc-markdown.yaml file

For the directory layout structure here:

```
.
├── pydoc-markdown.yaml
├── pyproject.toml
├── README.md
├── retrievers
│   ├── __init__.py
│   ├── context
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── dtype_mapping.py
│   │   ├── table.py
│   │   └── text.py
│   ├── databases
│   │   ├── __init__.py
│   │   ├── graph_database.py
│   │   ├── sql_database.py
│   │   └── vector_database
│   │       ├── __init__.py
│   │       ├── vector_database.py
│   │       └── vendors
│   │           ├── milvus.py
│   │           ├── mongodb.py
│   │           ├── pinecone.py
│   │           └── qdrant.py
│   ├── exceptions.py
│   ├── indexing.py
│   ├── query_language.py
│   ├── storage
│   │   ├── __init__.py
│   │   ├── file_store.py
│   │   └── pickle_store.py
│   └── types.py
└── docs

```

The following pydoc-markdown.yaml is used.

```yaml
# pydoc-markdown.yaml
loaders:
  - type: python
    search_path: ["."] # <- flat layout
    packages: ["retrievers"]

renderer:
  type: pydoc_mintlify.MintlifyRenderer
  docs_base_path: docs
  nav:
    tab: SDK Reference
    icon: square-terminal
    groups:
      - group: Context
        pages:
          - title: Bases Classes
            description: The Base Context Classes
            path: retrievers/context/base
          - title: Table
            description: The Table Context Classes
            path: retrievers/context/table
          - title: Text
            description: The Text Context Classes
            path: retrievers/context/text
          - title: DTypes
            description: Retrievers DTypes
            path: retrievers/context/dtype_mapping
      - group: Indexing
        pages:
          - title: Indexing Utils
            description: The Indexing Utils Class
            path: retrievers/indexing
      - group: Databases
        pages:
          - group: Vector Database
            pages:
              - title: VectorDatabase Class
                description: The Vector Database Class
                path: retrievers/databases/vector_database/vector_database
              - group: Vendors
                pages:
                  - title: Milvus
                    description: Milvus Integration
                    path: retrievers/databases/vector_database/vendors/milvus
              - title: VDB Query Language
                description: The Retrievers Query Language Class
                path: retrievers/query_language
          - title: SQL Database
            description: A SQL Database for RAG over Tables
            path: retrievers/databases/sql_database
          - title: Graph Database
            description: A Graph Database for RAG over Graphs
            path: retrievers/databases/graph_database
      - group: Context Storage
        pages:
          - title: File Store
            description: The File Store Class
            path: retrievers/storage/file_store
          - title: Pickle Store
            description: The Pickle Store Class
            path: retrievers/storage/pickle_store
```

Check out the retrievers source code for a full example:

# CLI

You can use the CLI to launch the dev server and build your auto-generated .mdx files.

```
pydoc-mintlify dev       # runs the dev server (rebuilds .mdx files when your .py files change and also runs mint dev)
pydoc-mintlify build     # One shot generation of your .mdx files
pydoc-mintlify docs-watch # Also launvhes the dev server but doesn't run mint dev
```
