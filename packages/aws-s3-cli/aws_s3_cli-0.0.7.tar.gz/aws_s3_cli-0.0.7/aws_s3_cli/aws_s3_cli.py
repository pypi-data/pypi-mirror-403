# /usr/bin/env python
__author__ = "Sujit Mandal"
# Date :25-06-2023
import os
import boto3


def upload_file(
    BUCKET_NAME, AWS_ACCESS_KEY, AWS_SECRET_ACCESS_KEY, FILE_OBJ, FILE_NAME
):
    """
    Uploads a file to AWS S3 bucket

    Parameters
    ----------
    BUCKET_NAME : str
        Name of the S3 bucket
    AWS_ACCESS_KEY : str
        AWS access key
    AWS_SECRET_ACCESS_KEY : str
        AWS secret access key
    FILE_OBJ : file object
        File object to be uploaded
    FILE_NAME : str
        Name of the file to be uploaded

    Returns
    -------
    dict
        Dictionary containing the status of the upload operation
    """
    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )

    s3.upload_file(FILE_OBJ, BUCKET_NAME, FILE_NAME)

    s3bucket = boto3.resource(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )
    bucket = s3bucket.Bucket(BUCKET_NAME)

    upload_file_info = []
    for obj in bucket.objects.filter(Prefix=FILE_NAME):
        upload_file_bucket_name = obj.bucket_name
        upload_file_name = obj.key
        upload_file_info.append(upload_file_bucket_name)
        upload_file_info.append(upload_file_name)

    status = {}
    if BUCKET_NAME in upload_file_info and FILE_NAME in upload_file_info:
        status["status"] = True
        status["message"] = "File uploaded successfully."

    else:
        status["status"] = False
        status["message"] = "Error in uploading file."

    return status


def download_file(
    BUCKET_NAME, AWS_ACCESS_KEY, AWS_SECRET_ACCESS_KEY, S3_FILE_NAME, FILE_NAME
):
    """
    Downloads a file from AWS S3 bucket

    Parameters
    ----------
    BUCKET_NAME : str
        Name of the S3 bucket
    AWS_ACCESS_KEY : str
        AWS access key
    AWS_SECRET_ACCESS_KEY : str
        AWS secret access key
    S3_FILE_NAME : str
        Name of the file to be downloaded
    FILE_NAME : str
        Name of the file to be saved

    Returns
    -------
    dict
        Dictionary containing the status of the download operation
    """
    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )

    s3bucket = boto3.resource(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )
    bucket = s3bucket.Bucket(BUCKET_NAME)

    upload_file_info = []
    for obj in bucket.objects.filter(Prefix=S3_FILE_NAME):
        upload_file_bucket_name = obj.bucket_name
        upload_file_name = obj.key
        upload_file_info.append(upload_file_bucket_name)
        upload_file_info.append(upload_file_name)

    status = {}
    if BUCKET_NAME in upload_file_info and S3_FILE_NAME in upload_file_info:
        with open(FILE_NAME, "wb") as f:
            s3.download_fileobj(BUCKET_NAME, S3_FILE_NAME, f)
            f.seek(0)

    if os.path.exists(FILE_NAME):
        status["status"] = True
        status["message"] = "File download successfully."

    else:
        status["status"] = False
        status["message"] = "File not found."

    return status


def get_all_file_dict(BUCKET_NAME, AWS_ACCESS_KEY, AWS_SECRET_ACCESS_KEY):
    """
    Retrieves all files from an S3 bucket as a dictionary

    Parameters
    ----------
    BUCKET_NAME : str
        Name of the S3 bucket
    AWS_ACCESS_KEY : str
        AWS access key
    AWS_SECRET_ACCESS_KEY : str
        AWS secret access key

    Returns
    -------
    dict
        Dictionary containing the status and a list of file names
    """
    s3bucket = boto3.resource(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )
    bucket = s3bucket.Bucket(BUCKET_NAME)

    upload_file_info = []
    for obj in bucket.objects.all():
        bucket_name = obj.bucket_name
        file_name = obj.key

        upload_file_info.append([bucket_name, file_name])

    file_name_dict = {}
    if len(upload_file_info) != 0:
        file_name_dict_list = []
        for file_name_list in upload_file_info:
            tmp_dict = {}
            tmp_dict["bucket_name"] = file_name_list[0]
            tmp_dict["file_name"] = file_name_list[1]

            file_name_dict_list.append(tmp_dict)

        file_name_dict["status"] = True
        file_name_dict["data"] = file_name_dict_list
    else:
        file_name_dict["status"] = False
        file_name_dict["message"] = "File not found."

    return file_name_dict


def get_all_file_list(BUCKET_NAME, AWS_ACCESS_KEY, AWS_SECRET_ACCESS_KEY):
    """
    Retrieves a list of all files in a given S3 bucket

    Parameters
    ----------
    BUCKET_NAME : str
        Name of the S3 bucket
    AWS_ACCESS_KEY : str
        AWS access key
    AWS_SECRET_ACCESS_KEY : str
        AWS secret access key

    Returns
    -------
    list
        List of file names in the given S3 bucket
    """
    s3bucket = boto3.resource(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )
    bucket = s3bucket.Bucket(BUCKET_NAME)

    upload_file_info = []
    for obj in bucket.objects.all():
        bucket_name = obj.bucket_name
        file_name = obj.key

        upload_file_info.append([bucket_name, file_name])

    file_list = []
    if len(upload_file_info) != 0:
        for file_name_list in upload_file_info:
            bucket_name = file_name_list[0]
            file_name = file_name_list[1]

            file_list.append(file_name)

    return file_list


def check_file_status(BUCKET_NAME, AWS_ACCESS_KEY, AWS_SECRET_ACCESS_KEY, S3_FILE_NAME):
    s3bucket = boto3.resource(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )
    bucket = s3bucket.Bucket(BUCKET_NAME)

    upload_file_info = []
    for obj in bucket.objects.filter(Prefix=S3_FILE_NAME):
        upload_file_bucket_name = obj.bucket_name
        upload_file_name = obj.key
        upload_file_info.append(upload_file_bucket_name)
        upload_file_info.append(upload_file_name)

    status = {}
    if len(upload_file_info) != 0:
        status["status"] = True
        status["data"] = "File available."
    else:
        status["status"] = False
        status["message"] = "File not found."

    return status


def generate_presigned_url(
    BUCKET_NAME, AWS_ACCESS_KEY, AWS_SECRET_ACCESS_KEY, S3_FILE_NAME, EXPIRATION=3600
):
    """
    Generate a presigned URL to download a file from S3

    Parameters
    ----------
    BUCKET_NAME : str
        Name of the S3 bucket
    AWS_ACCESS_KEY : str
        AWS access key
    AWS_SECRET_ACCESS_KEY : str
        AWS secret access key
    S3_FILE_NAME : str
        Name of the file to be downloaded
    EXPIRATION : int, optional
        Time in seconds for the presigned URL to expire. Defaults to 3600.

    Returns
    -------
    dict
        Dictionary containing the status of the download operation and the presigned URL
    """
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )

    try:
        url = s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": BUCKET_NAME, "Key": S3_FILE_NAME},
            ExpiresIn=EXPIRATION,
        )

        return {"status": True, "url": url}

    except Exception as e:
        return {"status": False, "message": str(e)}


def generate_presigned_upload_url(
    BUCKET_NAME, AWS_ACCESS_KEY, AWS_SECRET_ACCESS_KEY, S3_FILE_NAME, EXPIRATION=3600
):
    """
    Generates a presigned URL for uploading a file to S3

    Parameters
    ----------
    BUCKET_NAME : str
        Name of the S3 bucket
    AWS_ACCESS_KEY : str
        AWS access key
    AWS_SECRET_ACCESS_KEY : str
        AWS secret access key
    S3_FILE_NAME : str
        Name of the file to be uploaded
    EXPIRATION : int, optional
        Expiration time for the presigned URL in seconds, defaults to 3600

    Returns
    -------
    dict
        Dictionary containing the status of the upload operation and the presigned URL
    """
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )

    try:
        url = s3_client.generate_presigned_url(
            ClientMethod="put_object",
            Params={"Bucket": BUCKET_NAME, "Key": S3_FILE_NAME},
            ExpiresIn=EXPIRATION,
        )

        return {"status": True, "url": url}

    except Exception as e:
        return {"status": False, "message": str(e)}


def generate_presigned_post(
    BUCKET_NAME, AWS_ACCESS_KEY, AWS_SECRET_ACCESS_KEY, KEY_PREFIX, EXPIRATION=3600
):
    """
    Generates a presigned POST data for S3 direct upload

    Parameters
    ----------
    BUCKET_NAME : str
        Name of the S3 bucket
    AWS_ACCESS_KEY : str
        AWS access key
    AWS_SECRET_ACCESS_KEY : str
        AWS secret access key
    KEY_PREFIX : str
        Prefix for the key to be uploaded
    EXPIRATION : int, optional
        Expiration time for the presigned URL in seconds, defaults to 3600

    Returns
    -------
    dict
        Dictionary containing the status of the upload operation and the presigned POST data
    """
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name="us-east-1",
    )

    try:
        response = s3_client.generate_presigned_post(
            Bucket=BUCKET_NAME,
            Key=f"{KEY_PREFIX}${{filename}}",
            Fields={"x-amz-algorithm": "AWS4-HMAC-SHA256"},
            Conditions=[
                {"bucket": BUCKET_NAME},
                ["starts-with", "$key", KEY_PREFIX],
                {"x-amz-algorithm": "AWS4-HMAC-SHA256"},
            ],
            ExpiresIn=EXPIRATION,
        )

        return {"status": True, "data": response}

    except Exception as e:
        return {"status": False, "message": str(e)}


if __name__ == "__main__":
    FILE_OBJ = ""
    FILE_NAME = ""
    KEY_PREFIX = ""
    S3_FILE_NAME = ""
    BUCKET_NAME = ""
    AWS_ACCESS_KEY = ""
    AWS_SECRET_ACCESS_KEY = ""

    get_all_file_dict(
      BUCKET_NAME,
      AWS_ACCESS_KEY,
      AWS_SECRET_ACCESS_KEY
    )
    get_all_file_list(
      BUCKET_NAME,
      AWS_ACCESS_KEY,
      AWS_SECRET_ACCESS_KEY
    )
    check_file_status(
      BUCKET_NAME,
      AWS_ACCESS_KEY,
      AWS_SECRET_ACCESS_KEY,
      S3_FILE_NAME
    )
    download_file(
        BUCKET_NAME,
        AWS_ACCESS_KEY,
        AWS_SECRET_ACCESS_KEY,
        S3_FILE_NAME, FILE_NAME
    )
    upload_file(
      BUCKET_NAME,
      AWS_ACCESS_KEY,
      AWS_SECRET_ACCESS_KEY,
      FILE_OBJ, FILE_NAME
    )
    generate_presigned_url(
        BUCKET_NAME,
        AWS_ACCESS_KEY,
        AWS_SECRET_ACCESS_KEY,
        S3_FILE_NAME
    )
    generate_presigned_upload_url(
        BUCKET_NAME,
        AWS_ACCESS_KEY,
        AWS_SECRET_ACCESS_KEY,
        S3_FILE_NAME
    )
    generate_presigned_post(
        BUCKET_NAME,
        AWS_ACCESS_KEY,
        AWS_SECRET_ACCESS_KEY,
        KEY_PREFIX
    )
