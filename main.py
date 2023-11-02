from google.cloud import logging as google_cloud_logging
import functions_framework
from main_function import main

client = google_cloud_logging.Client()
client.setup_logging()

# Register a CloudEvent function with the Functions Framework
@functions_framework.cloud_event
def run_function(cloud_event):
    main()
