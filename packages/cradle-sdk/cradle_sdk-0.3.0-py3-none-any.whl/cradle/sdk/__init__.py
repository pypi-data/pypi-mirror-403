"""Cradle Platform API SDK

This SDK provides a convenient Python interface for interacting with the Cradle Platform APIs.
It allows you to programmatically access and manage your data, projects, rounds, and tasks within the Cradle platform.

Key Features:
- Seamless OAuth authentication with the Cradle Platform via device flow.
- Easy access to various client interfaces for different API functionalities (Data, Project, Round, Task).
- Simplified data upload and management.

Getting Started:
1.  Installation:
    Install the SDK using pip::

        pip install cradle-sdk

2.  Authentication:
    The SDK uses OAuth device flow for authentication. Simply instantiate the client,
    and it will provide you with a URL to complete authentication in your browser.

3.  Basic Usage:
    Initialize the client and follow the authentication prompt:
    ```python
    from cradle.sdk import Client

    # Initialize the client - this will prompt for authentication
    client = Client(workspace="YOUR_WORKSPACE_NAME")

    # The client will display a message like this:
    # Please click the following URL to complete authentication
    # https://signin.cradle.bio/device?user_code=XXXX-XXXX
    # and verify that the code matches: XXXX-XXXX

    # After authenticating in your browser via SSO or Cradle credentials,
    # the client will be ready to use.

    # Access specific API clients
    data_client = client.data
    project_client = client.project
    round_client = client.round
    task_client = client.task

    # Example: List projects
    projects = project_client.list_projects()
    for project in projects:
        print(project.name)
    ```

For detailed documentation on each module and class, please refer to the respective sections.
"""

from .client import (
    Client as Client,
    DataClient as DataClient,
    DataLoadClient as DataLoadClient,
    ProjectClient as ProjectClient,
    RoundClient as RoundClient,
    TaskClient as TaskClient,
)
from .exceptions import ClientError as ClientError
