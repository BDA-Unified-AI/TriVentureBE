from src.apis.config.firebase_config import firebase_bucket
import base64
import os
import tempfile


def upload_file_to_storage(file_path, file_name):
    """
    Upload a file to Firebase Storage
    param:
        file_path: str - The path of the file on local machine to be uploaded
    return:
        str - The public URL of the uploaded file
    """
    blob = firebase_bucket.blob(file_name)
    blob.upload_from_filename(file_path)
    blob.make_public()

    return blob.public_url



def delete_file_from_storage(file_name):
    """
    Delete a file from Firebase Storage
    param:
        file_name: str - The name of the file to be deleted
    return:
        bool - True if the file is deleted successfully, False if the file is not found
    """
    try:
        blob = firebase_bucket.blob(file_name)
        blob.delete()
        return True
    except Exception as e:
        print("Error:", e)
        return False


def list_all_files_in_storage():
    """
    View all files in Firebase Storage
    return:
        dict - Dictionary with keys are names and values are url of all files in Firebase Storage
    """
    blobs = firebase_bucket.list_blobs()
    blob_dict = {blob.name: blob.public_url for blob in blobs}
    return blob_dict


def download_file_from_storage(file_name, destination_path):
    """
    Download a file from Firebase Storage
    param:
        file_name: str - The name of the file to be downloaded
        destination_path: str - The path to save the downloaded file
    return:
        bool - True if the file is downloaded successfully, False if the file is not found
    """
    try:
        blob = firebase_bucket.blob(file_name)
        blob.download_to_filename(destination_path)
        print("da tai xun thanh cong")
        return True
    except Exception as e:
        print("Error:", e)
        return False


def upload_base64_image_to_storage(base64_image, file_name):
    """
    Upload a base64 image to Firebase Storage
    param:
        base64_image: str - The base64 encoded image
        file_name: str - The name of the file to be uploaded
    return:
        str - The public URL of the uploaded file
    """
    try:
        # Decode the base64 image
        image_data = base64.b64decode(base64_image)

        # Create a temporary file to save the decoded image
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(image_data)
            temp_file_path = temp_file.name

        # Upload the temporary file to Firebase Storage
        public_url = upload_file_to_storage(temp_file_path, file_name)

        # Remove the temporary file
        os.remove(temp_file_path)

        return public_url
    except Exception as e:
        print("Error:", e)
        return None
