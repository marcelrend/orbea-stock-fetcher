import functions_framework
from main_function import main

# Register a CloudEvent function with the Functions Framework
@functions_framework.cloud_event
def run_function(cloud_event):
    main()
