"""
gcshelp = new GCSHelper()

- should accept a way to pub a message to whatever
- should accept upload a file to a bucket (parameter to compress???)
"""


import os
import io
import json
from google.cloud import pubsub_v1
from google.cloud import storage
from google.api_core import exceptions as gcs_exceptions
import datetime
import zlib
import re
from typing import Union, Literal, List, Dict


class GCSHelper:
    def __init__(self, project_id:str, topic_name:str=None, subscription_name:str=None):
        assert project_id is not None, 'project_id must be set'
        self.project_id = project_id
        self.topic_name = topic_name
        self.subscription_name = subscription_name

    def pub_get_messages(self, subscription_name:str=None, batch_size:int=25) -> list:
        """Get a json string from pubsub. Will be a list of json objects.
        if topic is not defined here, we take from the GCSHelper instantiation
        """
        if subscription_name is None:
            subscription_name = self.subscription_name
        assert subscription_name is not None, 'subscription_name must not be none. Either define it here or at GCSHelper() instantiation'

        project_id = self.project_id
        subscriber = pubsub_v1.SubscriberClient()
        sub_path = subscriber.subscription_path(project=project_id, subscription=subscription_name)

        subscription_metadata = subscriber.get_subscription(request={"subscription": sub_path})

        all_msgs = []

        print(f'looking for msgs for {sub_path}')

        pull_time = datetime.datetime.now()
        time_to_live = subscription_metadata.ack_deadline_seconds
        expiration_time = pull_time + datetime.timedelta(seconds=time_to_live)

        payload = subscriber.pull(
            request={
                'subscription': sub_path,
                'max_messages': batch_size,
            } 
        )

        print(f'found {len(payload.received_messages)} msgs for {sub_path}: ')
        for received_message in payload.received_messages:
            # Monkey patch adding these attributes. May help us later.
            received_message.__dict__['pull_time'] = pull_time
            received_message.__dict__['expiration_time'] = expiration_time
            try:
                received_message.__dict__['json_data'] = json.loads(received_message.message.data)
            except json.JSONDecodeError:
                received_message.__dict__['json_data'] = received_message.message.data

            all_msgs.append(received_message)

        return all_msgs

    def pub_pub_message(self, data: Union[List[Dict], Dict], topic_name:str=None) -> int:
        """Pub a dict message to pubsub. Will be converted to json when the request actually gets submitted.
        
        The idea for this is its going to be one file per message.

        if topic is not defined here, we take from the GCSHelper instantiation

        Return:

            the number of messages published
        """
        if topic_name is None:
            topic_name = self.topic_name
        assert topic_name is not None, 'topic_name must not be none. Either define it here or at GCSHelper() instantiation'

        project_id = self.project_id
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(project=project_id, topic=topic_name)
        if type(data) == list:
            for data_line in data:
                d = json.dumps(obj=data_line).encode(encoding='utf-8')
                print(f'pubbing {d} to {topic_name}')
                publisher.publish(topic=topic_path, data=d)
            return len(data)

        else:
            d: bytes = json.dumps(obj=data).encode(encoding='utf-8')
            print(f'pubbing {d} to {topic_name}')
            publisher.publish(topic=topic_path, data=d)
            return 1
        
    def pub_ack_message(self, data: Union[List[object], object], expired_message_action: Literal['warn', 'fail', 'silent']='warn', subscription_name:str=None) -> int:
        """Attempts to Acknolwedge pubsub messages.

        Params:
            subscription_name: The GCS Subscription name as a string. If subscription is not defined here, we take from the GCSHelper instantiation.

            data: list of pubsub google.cloud.pubsub_v1.types.ReceivedMessage messages.

            expired_message_action: Action to preform if we try to acknowledge an expired message. This requires the attribute 
                expiration_time to exist on google.cloud.pubsub_v1.types.ReceivedMessage. 
                (This was a monkey patch and is NOT STANDARD.)

                warn - Print a warning message to console. This is the default behavior.

                fail - Throws an ExpiredMessageException

                silent - Does nothing. if expiration_time does not exist this is selected.

        Returns:
            the number of messages published
        """
        if subscription_name is None:
            subscription_name = self.subscription_name
        assert subscription_name is not None, 'subscription_name must not be none. Either define it here or at GCSHelper() instantiation'

        test_data = data[0] if type(data) == list else data
        if not hasattr(test_data, 'expiration_time'):
            expired_message_action = 'silent'

        project_id = self.project_id
        subscriber = pubsub_v1.SubscriberClient()
        sub_path = subscriber.subscription_path(project=project_id, subscription=subscription_name)

        if type(data) == list:
            print(f'Acknowledging {len(data)} Messages')

            for current_data in data:
                check_message_for_expiration(message=current_data, expired_message_action=expired_message_action)

                subscriber.acknowledge(
                    request={
                    'subscription': sub_path,
                    'ack_ids': [current_data.ack_id],
                    } 
                )

        else:
            print(f'Acknowledging 1 message')
            check_message_for_expiration(message=data, expired_message_action=expired_message_action)
            subscriber.acknowledge(
                request={
                'subscription': sub_path,
                'ack_ids': [data.ack_id],
                } 
            )

    def download_bucket_data_to_bytes(self, gs_blob_url:str, decompress=False) -> bytes:
        """Downloads a file from a GCS bucket. Returns as bytes.

        full_path - Fully qualified path name, in the form of gs://bucket_name/path/to/blob.txt
        """
        blob = self.get_cloud_bucket_object(gs_blob_url=gs_blob_url)

        data: bytes = blob.download_as_bytes()

        if decompress == True:
            data = attempt_to_decompress(data=data)

        data = io.BytesIO(data)

        return data

    def download_bucket_data_to_path(self, gs_blob_url:str, download_path:str, decompress=False) -> str:
        """Downloads a file from a GCS bucket. Downloads to a directory.

        full_path - Fully qualified path name, in the form of gs://bucket_name/path/to/blob.txt
        
        download_path - Full path of download file (inclduing filename)
        """
        blob = self.get_cloud_bucket_object(gs_blob_url=gs_blob_url)
        
        abs_path: str = os.path.abspath(download_path)

        data = blob.download_as_bytes()

        if decompress == True:
            data = attempt_to_decompress(data=data)

        with open(abs_path, 'wb') as f:
            f.write(data)

        return abs_path

    def download_bucket_data_to_str(self, gs_blob_url:str, decompress=False) -> str:
        """Downloads a file from a GCS bucket. Returns as a str

        full_path - Fully qualified path name, in the form of gs://bucket_name/path/to/blob.txt
        
        download_path - Directory where file(s) should be stored.
        """
        blob = self.get_cloud_bucket_object(gs_blob_url=gs_blob_url)

        if decompress == False:
            return blob.download_as_text()

        else:
            data = attempt_to_decompress(blob.download_as_bytes())
            data = data.decode('utf-8', errors='ignore')

            return re.sub(r'&#x1A|&#x00|&#x01', '', data)

    def get_cloud_bucket_object(self, gs_blob_url: str):
        """Get the Google Cloud Blob object"""
        blob_url = parse_gs_string(gs_blob_url)

        client = storage.Client()
        bucket = client.get_bucket(blob_url.get('bucket'))
        blob = bucket.get_blob(blob_url.get('object_path'))
        
        return blob

    def get_new_cloud_bucket_object(self, gs_blob_url: str):
        """Get the Google Cloud Blob object"""
        blob_url = parse_gs_string(gs_blob_url)

        client = storage.Client()
        bucket = client.get_bucket(blob_url.get('bucket'))
        blob = bucket.blob(blob_url.get('object_path'))
        
        return blob

    def upload_bucket_data_from_bytes(self, bytes_data:bytes, gs_blob_url:str, compress:bool=False) -> str:
        """Gets data as a bytes object, then sends it up to GCS"""
        
        blob = self.get_new_cloud_bucket_object(gs_blob_url=gs_blob_url)

        if compress == True:
            bytes_data = zlib.compress(bytes_data)

        blob.upload_from_file(bytes_data)

        return gs_blob_url

    def upload_bucket_data_from_path(self, file_path:str, gs_blob_url:str, compress:bool=False) -> str:
        '''Open a path on the filesystem, the uploads it to GCS.
        
        args:
            file_path (str): Full or relative file path on the filesystem.
        '''
        blob = self.get_new_cloud_bucket_object(gs_blob_url=gs_blob_url)

        with open(file_path, 'rb') as f:
            if compress == True:
                blob.upload_from_file(zlib.compress(f.read()))
            else:
                blob.upload_from_file(f.read())

        return gs_blob_url

    def upload_bucket_data_from_str(self, data:str, gs_blob_url:str, compress:bool=False) -> str:
        """Gets data as a str, then sends it up to GCS as a blob."""

        blob = self.get_new_cloud_bucket_object(gs_blob_url=gs_blob_url)

        if compress == True:
            blob.upload_from_file(zlib.compress(data.encode()))

        blob.upload_from_string(data)

        return gs_blob_url
    
    def list_blobs_using_prefix(self, gs_path_url:str) -> List[str]:
        """Given a specified path in gsutil format, return all the blobs.
        
        Note: This cannot do wildcard-based searches, for that use fnmatch.
        """
        blob_url = parse_gs_string(gs_path_url)

        client = storage.Client()
        bucket = client.get_bucket(blob_url.get('bucket'))

        blobs = bucket.list_blobs(prefix=blob_url.get('object_path'))

        return [get_gsutil_path_from_blob(blob=b) for b in blobs]
    
    def del_blob(self, gs_blob_url: str) -> bool:
        """Deletes a blob from a full gsutil path. Returns True if blob was deleted and False if we cannot."""
        
        try:
            blob_url = parse_gs_string(gs_blob_url)

            client = storage.Client()
            bucket = client.get_bucket(blob_url.get('bucket'))
            blob = bucket.get_blob(blob_url.get('object_path'))
            blob.delete()

            return True
        
        except gcs_exceptions.NotFound:
            print(f'Warning: {gs_blob_url} was not found.')
            return False



def check_message_for_expiration(message: object, expired_message_action:str='silent') -> None:
    """Checks a pubsub message if it is expired, expired_message_action shows what to do with it. Returns nothing."""
    if not hasattr(message, 'expiration_time') and expired_message_action != 'silent':
        print('Warning, Message has no expiration_time attribute')
        return None

    if expired_message_action == 'warn' and message.expiration_time < datetime.datetime.now():

        print(f'Warning: Google PubSub Message ID {message.message.message_id} expired at {message.expiration_time}, which was {(datetime.datetime.now() - message.expiration_time).total_seconds()} seconds ago.')

    elif expired_message_action == 'fail' and message.expiration_time < datetime.datetime.now():

        # assert False, f'Error: Google PubSub Message ID {message.message.message_id} expired at {message.expiration_time}, which was {(datetime.datetime.now() - message.expiration_time).total_seconds()} seconds ago.'
        raise ExpiredMessageException(pubsub_message=message)

def parse_gs_string(input_str: str) -> dict:
    assert input_str.lower().startswith('gs://'), f"Missing gs:// identifier"
    chunks = input_str[5:].split('/')  # Skipping 'gs://'
    bucket = chunks[0]
    object_path = '/'.join(chunks[1:])
    return {
        'bucket': bucket,
        'object_path': object_path
    }

def to_gs_string(bucket_name: str, list_of_blobs: list) -> list:
    return [f'gs://{bucket_name}/{b}' for b in list_of_blobs]

def get_gsutil_path_from_blob(blob: object) -> str:
    return f"gs://{blob.bucket.name}/{blob.name}"

def attempt_to_decompress(data: bytes) -> bytes:
    """Attempts to use the zlib library to decompress file data."""
    try:
        data = zlib.decompress(data)
    except zlib.error as e:
        print(f'Warning: Could not decompress blob. Returning the raw data. error was: {e}')
    finally:
        return data
    
class ExpiredMessageException(Exception):
    def __init__(self, pubsub_message):
        self.message = pubsub_message

    def __str__(self):
        return f'Google PubSub Message ID {self.message.message.message_id} expired at {self.message.expiration_time}, which was {(datetime.datetime.now() - self.message.expiration_time).total_seconds()} seconds ago.'
