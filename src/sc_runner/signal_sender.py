import logging
import requests

# Configure logging to write to runner.log in the same directory
logging.basicConfig(
    filename="runner.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def send_update(project_id: int, status: str, token: str, backend_url: str) -> None:
    """Sends an update to the backend server with the project status.

    Args:
        project_id (int): Project ID for identification.
        status (str): Status message or any other data to update.
        token (str): Authentication token.
        backend_url (str): Backend URL to send the data to.
    """
    logging.info(f">>>>>>>>>>>>>>>>>>>>>> \n Sending update for project {project_id} with status: {status}\n")
    url = f"{backend_url}/resultupload/{project_id}/"
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }
    data = {
        "status": status
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        logging.info(f"Successfully sent update for project {project_id} with status {response.status_code}")
    except requests.RequestException as e:
        logging.error(f"Error sending update for project {project_id}: {e}")


