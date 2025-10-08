# AI-Powered NLP Query Engine

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/release/python-390/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![React](https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)

An intelligent full-stack application that allows users to ask questions in plain English to query both structured SQL databases and unstructured documents simultaneously.



## 📜 Description

This project solves the problem of querying disparate data sources by providing a unified, natural language interface. Instead of writing complex SQL queries or manually searching through documents, users can simply ask questions. The system dynamically introspects any connected SQL database to understand its schema on the fly and uses a Large Language Model (LLM) to translate user questions into executable database queries. It also performs semantic vector search on an indexed corpus of documents to answer questions that can't be resolved by the database alone.

## ✨ Key Features

* **Dynamic Schema Discovery**: Automatically analyzes and adapts to any connected PostgreSQL database schema without hard-coding, ensuring high adaptability.
* **LLM-Powered Text-to-SQL**: Integrates Google Gemini to translate natural language questions into secure and executable SQL queries.
* **Hybrid Search**: Combines traditional SQL data retrieval with semantic vector search for unstructured documents (PDFs, TXT, DOCX), providing a unified query experience.
* **Document Ingestion & Indexing**: A robust pipeline for uploading, parsing, chunking, and generating vector embeddings for various document formats.
* **Asynchronous RESTful API**: A scalable backend built with FastAPI (Python) to handle concurrent user requests for data ingestion and querying.
* **Containerized Environment**: The entire application stack (FastAPI, React, PostgreSQL) is containerized using Docker and Docker Compose for consistent, one-command deployment.

## 🛠️ Technology Stack

* **Backend**: Python, FastAPI, SQLAlchemy, Google Generative AI
* **Frontend**: React, JavaScript, HTML, CSS
* **AI/ML**: `sentence-transformers`, NumPy (for vector search)
* **Database**: PostgreSQL
* **DevOps**: Docker, Docker Compose

## 🚀 Getting Started

Follow these instructions to get the project up and running on your local machine.

### Prerequisites

* **Docker Desktop**: Make sure it's installed and running on your system.
* **Node.js & npm**: Required for installing frontend dependencies.

### Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone <your-repository-url>
    cd NLPQueryEngine
    ```

2.  **Configure Environment Variables**
    * Navigate to the `backend` directory.
    * Create a `.env` file by copying the example: `cp .env.example .env` (or create it manually).
    * Open `backend/.env` and add your Google Gemini API key:
        ```
        DATABASE_URL="postgresql://user:pass@db:5432/company_db"
        GEMINI_API_KEY="PASTE_YOUR_API_KEY_HERE"
        ```

3.  **Install Frontend Dependencies**
    * From the project's **root directory**, run:
        ```bash
        npm install
        ```

4.  **Set Up the Database**
    * Start the database service in the background:
        ```bash
        docker compose up -d db
        ```
    * Connect to the running PostgreSQL container (find the container name with `docker ps`):
        ```bash
        docker exec -it nlpqueryengine-db-1 psql -U user -d company_db
        ```
    * Inside the `psql` prompt, paste the SQL commands to create and populate your tables (e.g., `employees`, `departments`).

5.  **Build and Run the Application**
    * From the project's **root directory**, run:
        ```bash
        docker compose up --build
        ```
    * The application will be available at `http://localhost:3000`.

## ⚙️ Usage

1.  **Open the Web Interface**: Navigate to `http://localhost:3000`.
2.  **Connect to Database**: Click the "Connect & Analyze" button to have the engine discover the database schema.
3.  **Upload Documents**: (Optional) Drag and drop PDF, DOCX, or TXT files to the uploader to make them available for querying.
4.  **Ask a Question**: Type a question in plain English (e.g., "How many employees are in Engineering?") and press "Submit Query" to see the results.

## 🔮 Future Improvements

* Implement a dedicated vector database (e.g., ChromaDB, Weaviate) for more scalable document search.
* Improve the Text-to-SQL prompt to handle more complex queries and edge cases.
* Add support for more SQL database dialects (e.g., MySQL, SQLite).
* Implement user authentication and multi-tenancy.
* Enhance query caching with a system like Redis for better performance.

## 📄 License

This project is licensed under the MIT License.
