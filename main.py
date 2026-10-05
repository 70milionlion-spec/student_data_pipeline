from pathlib import Path
import logging

from src.pipeline import (
    connect_to_mongodb,
    load_collection,
    save_raw_json,
    load_json_as_dataframe,

    flatten_students,
    convert_student_data_types,
    clean_students,
    validate_students,

    clean_courses,
    validate_courses,

    save_to_csv,
    save_to_sqlite,

    generate_quality_report,
)


# ============================================================
# Configuration
# ============================================================

MONGO_URI = "mongodb://127.0.0.1:27017/"

MONGO_DATABASE = "university_ai"

STUDENTS_COLLECTION = "students"

COURSE_COLLECTION = "course"


# ============================================================
# Raw data
# ============================================================

STUDENTS_RAW_FILE = Path(
    "data/raw/students.json"
)

COURSES_RAW_FILE = Path(
    "data/raw/courses.json"
)


# ============================================================
# Processed data
# ============================================================

STUDENTS_OUTPUT = Path(
    "data/processed/students_ml_ready.csv"
)

COURSES_OUTPUT = Path(
    "data/processed/courses_ml_ready.csv"
)


# ============================================================
# Database
# ============================================================

DATABASE_FILE = Path(
    "university_data.db"
)


# ============================================================
# Logging
# ============================================================

LOG_FILE = Path(
    "logs/pipeline.log"
)

LOG_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)


logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s - "
        "%(levelname)s - "
        "%(message)s"
    ),
    handlers=[
        logging.FileHandler(
            LOG_FILE,
            encoding="utf-8"
        ),
        logging.StreamHandler()
    ]
)


logger = logging.getLogger(__name__)


# ============================================================
# Pipeline
# ============================================================

def run_pipeline():

    logger.info("=" * 60)
    logger.info("Starting data pipeline")
    logger.info("=" * 60)

    client = None

    try:

        # ====================================================
        # STEP 1
        # Connect to MongoDB
        # ====================================================

        logger.info(
            "Connecting to MongoDB..."
        )

        client, database = connect_to_mongodb(
            MONGO_URI,
            MONGO_DATABASE
        )

        # ====================================================
        # STEP 2
        # INGEST STUDENTS FROM MONGODB
        # ====================================================

        logger.info(
            "Loading students from MongoDB..."
        )

        students_documents = load_collection(
            database,
            STUDENTS_COLLECTION
        )

        # ====================================================
        # STEP 3
        # SAVE RAW STUDENTS
        # ====================================================

        save_raw_json(
            students_documents,
            STUDENTS_RAW_FILE
        )

        # ====================================================
        # STEP 4
        # LOAD RAW STUDENTS INTO PANDAS
        # ====================================================

        students_df = load_json_as_dataframe(
            STUDENTS_RAW_FILE
        )

        print("\nRaw students data:")
        print(students_df)

        # ====================================================
        # STEP 5
        # FLATTEN STUDENTS
        # ====================================================

        logger.info(
            "Flattening student data..."
        )

        students_df = flatten_students(
            students_df
        )

        # ====================================================
        # STEP 6
        # CONVERT TYPES
        # ====================================================

        students_df = convert_student_data_types(
            students_df
        )

        # ====================================================
        # STEP 7
        # CLEAN
        # ====================================================

        logger.info(
            "Cleaning student data..."
        )

        students_df = clean_students(
            students_df
        )

        # ====================================================
        # STEP 8
        # VALIDATE
        # ====================================================

        logger.info(
            "Validating student data..."
        )

        validate_students(
            students_df
        )

        # ====================================================
        # STEP 9
        # REPORT
        # ====================================================

        generate_quality_report(
            students_df,
            "STUDENTS"
        )

        # ====================================================
        # STEP 10
        # SAVE STUDENTS CSV
        # ====================================================

        save_to_csv(
            students_df,
            STUDENTS_OUTPUT
        )

        # ====================================================
        # STEP 11
        # SAVE STUDENTS SQLITE
        # ====================================================

        save_to_sqlite(
            students_df,
            DATABASE_FILE,
            "students"
        )

        # ====================================================
        # COURSES
        # ====================================================

        logger.info(
            "Loading courses from MongoDB..."
        )

        courses_documents = load_collection(
            database,
            COURSE_COLLECTION
        )

        # ====================================================
        # SAVE RAW COURSES
        # ====================================================

        save_raw_json(
            courses_documents,
            COURSES_RAW_FILE
        )

        # ====================================================
        # LOAD RAW COURSES
        # ====================================================

        courses_df = load_json_as_dataframe(
            COURSES_RAW_FILE
        )

        print("\nRaw courses data:")
        print(courses_df)

        # ====================================================
        # CLEAN COURSES
        # ====================================================

        logger.info(
            "Cleaning course data..."
        )

        courses_df = clean_courses(
            courses_df
        )

        # ====================================================
        # VALIDATE COURSES
        # ====================================================

        logger.info(
            "Validating course data..."
        )

        validate_courses(
            courses_df
        )

        # ====================================================
        # COURSE REPORT
        # ====================================================

        generate_quality_report(
            courses_df,
            "COURSES"
        )

        # ====================================================
        # SAVE COURSES CSV
        # ====================================================

        save_to_csv(
            courses_df,
            COURSES_OUTPUT
        )

        # ====================================================
        # SAVE COURSES SQLITE
        # ====================================================

        save_to_sqlite(
            courses_df,
            DATABASE_FILE,
            "courses"
        )

        # ====================================================
        # SUCCESS
        # ====================================================

        logger.info("=" * 60)
        logger.info(
            "Data pipeline completed successfully."
        )
        logger.info("=" * 60)

    except Exception as exc:

        logger.exception(
            "Pipeline failed: %s",
            exc
        )

        raise

    finally:

        if client is not None:

            client.close()

            logger.info(
                "MongoDB connection closed."
            )


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    run_pipeline()