# Student Data Pipeline

A data engineering pipeline that extracts student and course data from MongoDB, stores raw documents as JSON, processes and validates the data using Pandas, and exports ML-ready datasets to CSV and SQLite.

## Project Architecture

```text
MongoDB
   |
   | PyMongo
   v
data/raw/
   ├── students.json
   └── courses.json
   |
   | Pandas
   v
Data Cleaning
   |
   v
Data Validation
   |
   +----------------------+
   |                      |
   v                      v
CSV Files              SQLite
   |                      |
   v                      v
students_ml_ready.csv   students
courses_ml_ready.csv    courses

student_data_pipeline/
│
├── main.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── src/
│   └── pipeline.py
│
├── data/
│   ├── raw/
│   │   ├── students.json
│   │   └── courses.json
│   │
│   └── processed/
│       ├── students_ml_ready.csv
│       └── courses_ml_ready.csv
│
├── logs/
│   └── pipeline.log
│
└── university_data.db