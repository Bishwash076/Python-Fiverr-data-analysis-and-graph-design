from sentence_transformers import SentenceTransformer
import chromadb
from delta import configure_spark_with_delta_pip
from pyspark.sql import SparkSession
from dotenv import load_dotenv
import os

load_dotenv()

def get_spark():
    builder = SparkSession.builder.appName("Embed") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
        .config("spark.hadoop.fs.s3a.access.key", os.getenv("MINIO_ROOT_USER")) \
        .config("spark.hadoop.fs.s3a.secret.key", os.getenv("MINIO_ROOT_PASSWORD")) \
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
    return configure_spark_with_delta_pip(builder).getOrCreate()

def generate_embeddings():
    model = SentenceTransformer("all-MiniLM-L6-v2")
    client = chromadb.PersistentClient(path="/chroma")
    collection = client.get_or_create_collection("books")
    
    spark = get_spark()
    df = spark.read.format("delta").load("s3a://lake/gold/")
    
    for row in df.collect():
        text = row["text"][:1000]
        embedding = model.encode(text).tolist()
        metadata = {
            "id": row["id"],
            "title": row["title"],
            "author": row["author"],
            "url": row["url"]
        }
        collection.add(documents=[text], metadatas=[metadata], ids=[row["id"]], embeddings=[embedding])

if __name__ == "__main__":
    generate_embeddings()
