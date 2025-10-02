# NLP Query Engine for Employee Data

This project is a full-stack web application that provides a natural language query interface for an employee database. [cite_start]It dynamically adapts to the database schema and can query both structured SQL data and unstructured documents without hard-coding any table or column names[cite: 3, 4].

## Core Features

-   [cite_start]**Dynamic Schema Discovery**: Automatically discovers the database schema, including tables, columns, and relationships, upon connection[cite: 7].
-   [cite_start]**Hybrid Query Processing**: Classifies natural language queries to target the SQL database, unstructured documents, or both[cite: 67].
-   **Text-to-SQL**: Translates natural language questions into secure, executable SQL queries.
-   [cite_start]**Document Search**: Processes and indexes uploaded documents (PDF, DOCX, etc.) for semantic search[cite: 83].
-   [cite_start]**Production Ready**: Built with performance and scalability in mind, featuring caching, connection pooling, and asynchronous operations to handle concurrent users [cite: 194-198, 201].

## Project Structure

The project is organized into a `backend` (FastAPI) and a `frontend` (React) application, managed via Docker.
