# Financial Analysis & Compliance Automation

## Project Summary

This project automates the analysis and compliance checking of financial documents, including auditor's reports, director's reports, and financial ratios. It leverages AI (Google Gemini) to extract insights, check compliance, and generate executive summaries, making it easier for users to assess the financial health and regulatory status of a company.

## Features

- **AI-powered analysis** of auditor's and director's reports.
- **Automatic financial ratio calculation and commentary** from uploaded markdown files.
- **Compliance checking** against customizable rules for director's reports.
- **Combined executive summary** endpoint for quick board-level insights.
- **REST API** for integration with frontend or other systems.

## Technology Stack

- **Backend:** Python, Flask, Google Gemini API
- **Frontend:** React (with TypeScript)
- **Database:** (See below for structure; currently, the project uses in-memory storage for analysis results. For production, a database is recommended.)
- **Other:** Flask-CORS for cross-origin requests

## How to Use

### 1. Setup

- Install Python dependencies:
  ```
  pip install flask flask-cors
  ```
- Set up your Google Gemini API credentials as required by your code.
- (Optional) Install frontend dependencies and run the React app.

### 2. Running the Backend

Start the Flask server:
```
python app.py
```

### 3. API Endpoints

#### Analyze Auditor's Report
```
POST /api/analyze-audit-report
Form Data: md_file (Markdown file)
Response: JSON with analysis
```

#### Analyze Director's Report
```
POST /api/analyze-directors-report
Form Data: md_file (Markdown file)
Response: JSON with compliance results and conclusion
```

#### Analyze Financial Ratios
```
POST /analyze_pdf_ratios
Form Data: markdown (Markdown file)
Response: JSON with ratio analysis
```

#### Get Combined Summary
```
GET /api/summary-report
Response: JSON with overall summary and detailed breakdowns
```

### 4. Using the Frontend

- The React frontend provides a UI for uploading files and viewing summaries.
- The summary page fetches the combined summary from `/api/summary-report`.

## Database Structure

> **Note:**  
> The current implementation uses **in-memory global variables** to store the latest analysis results for each report type.  
> For production or multi-user support, you should use a database.  
> Below is a suggested structure for a relational database (e.g., SQLite, PostgreSQL):

### Tables

#### `analyses`
| Column           | Type        | Description                                 |
|------------------|-------------|---------------------------------------------|
| id               | INTEGER     | Primary key                                 |
| user_id          | INTEGER     | (Optional) Reference to user                |
| report_type      | TEXT        | 'auditor', 'director', 'financial'          |
| original_text    | TEXT        | The uploaded markdown text                  |
| analysis_result  | JSON/TEXT   | The AI-generated analysis result            |
| created_at       | DATETIME    | Timestamp                                   |

#### `summary_reports`
| Column           | Type        | Description                                 |
|------------------|-------------|---------------------------------------------|
| id               | INTEGER     | Primary key                                 |
| user_id          | INTEGER     | (Optional) Reference to user                |
| auditor_id       | INTEGER     | FK to analyses.id (auditor)                 |
| director_id      | INTEGER     | FK to analyses.id (director)                |
| financial_id     | INTEGER     | FK to analyses.id (financial)               |
| summary_text     | TEXT        | The combined summary                        |
| created_at       | DATETIME    | Timestamp                                   |

### Example Usage Flow

1. User uploads auditor, director, and financial markdown files via the frontend.
2. Each file is sent to its respective endpoint and analyzed by the AI.
3. The results are stored (currently in memory; in production, in the `analyses` table).
4. When the user requests a summary, `/api/summary-report` combines the latest results and generates an executive summary (optionally stored in `summary_reports`).

---

## Customization

- **Compliance Rules:**  
  Update the `COMPLIANCE_RULES` variable in `app.py` to change what is checked in director's reports.

- **Ratio Formulas:**  
  Update the `RATIO_FORMULAS` variable to add or modify financial ratios.

---

## Notes

- For multi-user or persistent storage, implement the above database schema and update the endpoints to read/write from the database instead of global variables.
- Ensure your Gemini API credentials are secured and not exposed in the frontend.
- For production, add authentication and proper error handling.



Database:
```
CREATE DATABASE financial_analysis
```

Table:
```
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
```
CREATE TABLE feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    feedback TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```
---
## License

MIT License (or your preferred license)

