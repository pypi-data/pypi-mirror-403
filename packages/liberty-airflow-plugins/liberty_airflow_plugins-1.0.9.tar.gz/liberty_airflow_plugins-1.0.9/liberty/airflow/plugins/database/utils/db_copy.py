import logging
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import IntegerType, StringType, DecimalType, LongType
from pyspark.sql.functions import trim, col, regexp_replace
from airflow.models import Variable
from liberty.airflow.plugins.database.utils.db_meta import get_column_lengths, get_column_types, get_connection

logging.basicConfig(level=logging.INFO)

def read_data_from_db(spark: SparkSession, table: str, source_conn: dict, source_schema: str ) -> DataFrame:
    data_df = spark.read \
        .format("jdbc") \
        .option("url", source_conn["url"]) \
        .option("driver", source_conn["driver"]) \
        .option("dbtable", f"{source_schema}.{table}") \
        .option("numPartitions", source_conn["numPartitions"]) \
        .option("fetchsize", source_conn["fetchsize"]) \
        .option("user", source_conn["user"]) \
        .option("password", source_conn["password"]) \
        .load()

    # Cast all numeric columns to IntegerType
    for field in data_df.schema.fields:
        dt = field.dataType

        # Handle decimals properly
        if isinstance(dt, DecimalType):
            # JDE: no decimals, integer semantics
            if dt.scale == 0:
                # SMALL ints → 32-bit
                # int max is 2,147,483,647 (10 digits), but to be safe we use precision <= 9
                if dt.precision <= 9:
                    data_df = data_df.withColumn(field.name, col(field.name).cast(IntegerType()))
                else:
                    data_df = data_df.withColumn(field.name, col(field.name).cast(LongType()))
            else:
                data_df = data_df.withColumn(field.name, col(field.name).cast(LongType()))

        # Handle strings: trim + remove null bytes
        elif isinstance(dt, StringType):
            data_df = data_df.withColumn(field.name, trim(col(field.name)))
            data_df = data_df.withColumn(field.name, regexp_replace(col(field.name), "\x00", ""))
    return data_df

def lowercase_columns(df: DataFrame) -> DataFrame:
    # Rename all columns to lowercase
    new_column_names = [col.lower() for col in df.columns]
    df = df.toDF(*new_column_names)  
    return df


def write_data_to_db(spark: SparkSession, data_df: DataFrame, table: str, source_conn: dict, source_schema: str, target_conn: dict, target_schema: str):
    # Convert column names to lowercase before writing to PostgreSQL
    data_df = lowercase_columns(data_df)
    column_lengths = get_column_lengths(spark, table, source_schema, source_conn)
    column_types = get_column_types(data_df, column_lengths, target_conn)

    data_df.write \
        .format("jdbc") \
        .option("url", target_conn["url"]) \
        .option("dbtable", f"{target_schema}.{table}") \
        .option("user", target_conn["user"]) \
        .option("password", target_conn["password"]) \
        .option("driver", target_conn["driver"]) \
        .option("createTableColumnTypes", column_types) \
        .option("numPartitions", target_conn["numPartitions"]) \
        .option("batchsize", target_conn["batchsize"]) \
        .option("truncate", "true") \
        .option("nullValue", "\u0000") \
        .mode("overwrite") \
        .save()


def create_spark_session() -> SparkSession:
    drivers_directory = Variable.get("drivers_directory", default_var="/opt/spark/jars/")
    log4j_config_path = f"file://{drivers_directory}/log4j2.properties"

    logging.info("Starting Spark session (please ignore Spark's initial stderr warnings)")
    spark_session = SparkSession\
        .builder\
        .appName("LIBERTY") \
        .config("spark.sql.debug.maxToStringFields", "-1") \
        .config("spark.jars", f"{drivers_directory}/ojdbc11.jar,{drivers_directory}/postgresql-42.7.4.jar") \
        .config("spark.driver.extraJavaOptions", f"-Dlog4j.configurationFile={log4j_config_path}") \
        .config("spark.executor.extraJavaOptions", f"-Dlog4j.configurationFile={log4j_config_path}") \
        .config("spark.ui.showConsoleProgress", "false") \
        .getOrCreate()
    logging.info("Spark session created successfully")
    return spark_session

def copy_table(conn_source, conn_target, table_name, source_schema, target_schema):
    # Retrieve the connection details from Airflow Connections
    target_conn = get_connection(conn_target)
    source_conn = get_connection(conn_source)

    # Create Spark session
    spark = create_spark_session()
    df = read_data_from_db(spark, table_name, source_conn, source_schema)
    write_data_to_db(spark, df, table_name, source_conn, source_schema, target_conn, target_schema)

    logging.info(f"Job completed for table: {table_name}, schema: {source_schema}")

