from flask import Flask, render_template, request, redirect
from dotenv import load_dotenv
import os
import boto3
import uuid
from db import get_db_connection, init_db

load_dotenv(override=True)

app = Flask(__name__)

S3_BUCKET = os.getenv("AWS_BUCKET_NAME")
CLOUDFRONT_DOMAIN = os.getenv("CLOUDFRONT_DOMAIN")


s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

init_db()

@app.route("/")
def home():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM posts ORDER BY id DESC")
        posts = cursor.fetchall()
    conn.close()
    return render_template("index.html", posts=posts)

@app.route("/post", methods=["POST"])
def post():
    content = request.form.get("content")
    image = request.files.get("image")

    ext = os.path.splitext(image.filename)[1]  
    filename = f"{uuid.uuid4().hex}{ext}"       

    s3.upload_fileobj(image, S3_BUCKET, filename)
    image_url = f"https://{CLOUDFRONT_DOMAIN}/{filename}"

    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO posts (content, image_url) VALUES (%s, %s)",
            (content, image_url)
        )
    conn.commit()
    conn.close()

    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)