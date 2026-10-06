import json
import logging
import sqlite3
from pathlib import Path

import pandas as pd
from pymongo import MongoClient


# MongoDB

def connect_to_mongodb(
    uri: str,
    database_name: str
):
   

    logging.info("Connecting to MongoDB...")

    client = MongoClient(uri)

    # Test the connection
    client.admin.command("ping")

    database = client[database_name]

    logging.info("Successfully connected to MongoDB.")

    return client, database


def load_collection(
    database,
    collection_name: str
) -> list[dict]:
   

    logging.info(
        f"Loading {collection_name} from MongoDB..."
    )

    collection = database[collection_name]

    documents = list(collection.find())


    for document in documents:

        if "_id" in document:
            document["_id"] = str(document["_id"])

    logging.info(
        f"Loaded {len(documents)} documents "
        f"from collection '{collection_name}'."
    )

    return documents


# JSON

def save_raw_json(
    documents: list[dict],
    output_file: Path
) -> None:
   

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with output_file.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            documents,
            file,
            ensure_ascii=False,
            indent=4
        )

    logging.info(
        f"Saved raw data to: {output_file}"
    )


def load_json_as_dataframe(
    input_file: Path
) -> pd.DataFrame:
   

    if not input_file.exists():

        raise FileNotFoundError(
            f"JSON file not found: {input_file}"
        )

    with input_file.open(
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    df = pd.DataFrame(data)

    logging.info(
        f"Loaded {len(df)} records "
        f"from {input_file}."
    )

    return df


# STUDENTS

def flatten_students(
    df: pd.DataFrame
) -> pd.DataFrame:
    

    logging.info("Flattening student data...")

    df = df.copy()

    # Extract address fields
    if "address" in df.columns:

        df["city"] = df["address"].apply(
            lambda x: (
                x.get("city")
                if isinstance(x, dict)
                else None
            )
        )

        df["country"] = df["address"].apply(
            lambda x: (
                x.get("country")
                if isinstance(x, dict)
                else None
            )
        )

    else:

        df["city"] = None
        df["country"] = None

    # Extract academic fields
    if "academic" in df.columns:

        df["gpa"] = df["academic"].apply(
            lambda x: (
                x.get("gpa")
                if isinstance(x, dict)
                else None
            )
        )

        df["attendance"] = df["academic"].apply(
            lambda x: (
                x.get("attendance")
                if isinstance(x, dict)
                else None
            )
        )

    else:

        df["gpa"] = None
        df["attendance"] = None

    # Remove nested columns after extraction
    for column in ["address", "academic"]:

        if column in df.columns:

            df = df.drop(
                columns=[column]
            )

    return df


def convert_student_data_types(
    df: pd.DataFrame
) -> pd.DataFrame:
   

    logging.info(
        "Converting student data types..."
    )

    df = df.copy()

    numeric_columns = [
        "student_id",
        "age",
        "gpa",
        "attendance"
    ]

    for column in numeric_columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    return df


def clean_students(
    df: pd.DataFrame
) -> pd.DataFrame:
   

    logging.info("Cleaning student data...")

    df = df.copy()

    # Remove completely empty rows

    df = df.dropna(
        how="all"
    )

    # Check student_id

    if "student_id" in df.columns:

        missing_student_id = df[
            "student_id"
        ].isna()

        number_missing = int(
            missing_student_id.sum()
        )

        if number_missing > 0:

            logging.warning(
                f"Found {number_missing} document(s) "
                f"without student_id inside students collection. "
                f"They will not be included in ML-ready data."
            )

            df = df[
                ~missing_student_id
            ].copy()

    else:

        raise ValueError(
            "Required column 'student_id' "
            "is missing from student data."
        )

    # Remove duplicate students


    df = df.drop_duplicates(
        subset=["student_id"],
        keep="first"
    )

    # Clean text columns

    text_columns = [
        "name",
        "city",
        "country"
    ]

    for column in text_columns:

        if column in df.columns:

            df[column] = (
                df[column]
                .astype("string")
                .str.strip()
                .str.title()
            )

    # Validate age range

    if "age" in df.columns:

        invalid_age = ~df[
            "age"
        ].between(
            16,
            80,
            inclusive="both"
        )

        df.loc[
            invalid_age,
            "age"
        ] = pd.NA

    # Validate GPA range

    if "gpa" in df.columns:

        invalid_gpa = ~df[
            "gpa"
        ].between(
            0,
            4,
            inclusive="both"
        )

        df.loc[
            invalid_gpa,
            "gpa"
        ] = pd.NA

    # Validate attendance range

    if "attendance" in df.columns:

        invalid_attendance = ~df[
            "attendance"
        ].between(
            0,
            100,
            inclusive="both"
        )

        df.loc[
            invalid_attendance,
            "attendance"
        ] = pd.NA

    
    # Fill numeric missing values with median

    numeric_columns = [
        "age",
        "gpa",
        "attendance"
    ]

    for column in numeric_columns:

        if column in df.columns:

            median_value = df[
                column
            ].median()

            if pd.notna(median_value):

                df[column] = df[
                    column
                ].fillna(
                    median_value
                )

    return df

#------------------------------------

def validate_students(
    df: pd.DataFrame
) -> bool:
   

    logging.info(
        "Validating student data..."
    )

    required_columns = [
        "student_id",
        "name",
        "age",
        "city",
        "country",
        "gpa",
        "attendance"
    ]

    # Check DataFrame

    if df.empty:

        raise ValueError(
            "Student DataFrame is empty."
        )

    # Check required columns

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            f"Missing required student columns: "
            f"{missing_columns}"
        )

    # Check student_id

    if df["student_id"].isna().any():

        raise ValueError(
            "Student data contains missing student_id."
        )

    if df["student_id"].duplicated().any():

        raise ValueError(
            "Student data contains duplicate student_id."
        )

    # Check name

    if df["name"].isna().any():

        raise ValueError(
            "Student data contains missing names."
        )

    
    # Check age

    if not df["age"].between(
        16,
        80,
        inclusive="both"
    ).all():

        raise ValueError(
            "Student data contains invalid age values."
        )

    # Check GPA

    if not df["gpa"].between(
        0,
        4,
        inclusive="both"
    ).all():

        raise ValueError(
            "Student data contains invalid GPA values."
        )

    # Check attendance

    if not df["attendance"].between(
        0,
        100,
        inclusive="both"
    ).all():

        raise ValueError(
            "Student data contains invalid attendance values."
        )

    logging.info(
        "Student data validation passed."
    )

    return True


# COURSES

def clean_courses(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Clean course data.
    """

    logging.info("Cleaning course data...")

    df = df.copy()

    # Remove completely empty rows
    df = df.dropna(
        how="all"
    )

    # Convert course_id to numeric
    if "course_id" in df.columns:

        df["course_id"] = pd.to_numeric(
            df["course_id"],
            errors="coerce"
        )

    else:

        raise ValueError(
            "Required column 'course_id' "
            "is missing from course data."
        )

    # Remove documents without course_id
    df = df[
        df["course_id"].notna()
    ].copy()

    # Remove duplicate courses
    df = df.drop_duplicates(
        subset=["course_id"],
        keep="first"
    )

    # Clean course name
    if "name" in df.columns:

        df["name"] = (
            df["name"]
            .astype("string")
            .str.strip()
            .str.title()
        )

    return df


def validate_courses(
    df: pd.DataFrame
) -> bool:
   

    logging.info(
        "Validating course data..."
    )

    required_columns = [
        "course_id",
        "name"
    ]

    # Check DataFrame

    if df.empty:

        raise ValueError(
            "Course DataFrame is empty."
        )

    # Check required columns

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            f"Missing required course columns: "
            f"{missing_columns}"
        )

    # Check course_id

    if df["course_id"].isna().any():

        raise ValueError(
            "Course data contains missing course_id."
        )

    if df["course_id"].duplicated().any():

        raise ValueError(
            "Course data contains duplicate course_id."
        )

    # Check course name

    if df["name"].isna().any():

        raise ValueError(
            "Course data contains missing course names."
        )

    logging.info(
        "Course data validation passed."
    )

    return True


# CSV

def save_to_csv(
    df: pd.DataFrame,
    output_file: Path
) -> None:
   

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig"
    )

    logging.info(
        f"Saved CSV file to: {output_file}"
    )


# SQLITE

def save_to_sqlite(
    df: pd.DataFrame,
    database_file: Path,
    table_name: str
) -> None:
    

    database_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    sqlite_df = df.copy()

    for column in sqlite_df.columns:

        sqlite_df[column] = sqlite_df[column].apply(
            lambda value: json.dumps(
                value,
                ensure_ascii=False
            )
            if isinstance(value, (list, dict))
            else value
        )

    with sqlite3.connect(
        database_file
    ) as connection:

        sqlite_df.to_sql(
            table_name,
            connection,
            if_exists="replace",
            index=False
        )

    logging.info(
        f"Saved {len(sqlite_df)} rows to SQLite table "
        f"'{table_name}'."
    )



# DATA QUALITY REPORT


def generate_quality_report(
    df: pd.DataFrame,
    dataset_name: str
) -> None:
    

    print()
    print("=" * 60)
    print(
        f"DATA QUALITY REPORT: {dataset_name}"
    )
    print("=" * 60)

    print(
        f"Rows    : {df.shape[0]}"
    )

    print(
        f"Columns : {df.shape[1]}"
    )

    print()
    print("Missing values:")

    print(
        df.isna().sum()
    )

    print()
    print("Data types:")

    print(
        df.dtypes
    )

    print("=" * 60)
    print()



# END OF PIPELINE
