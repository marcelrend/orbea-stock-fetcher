import requests


# Create class to download Orbea stock
class OrbeaStock:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.session = requests.Session()

    def login(self):
        login_url = "https://www.orbea.com/nl-en/kide/login/"
        login_data = {
            "login_email": self.email,
            "login_password": self.password,
            "from": "",
            "login": "",
        }
        orbea_login_response = self.session.post(
            login_url,
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            allow_redirects=True,
        )
        orbea_login_response.raise_for_status()

    def download(self):
        download_url = "https://www.orbea.com/nl-en/kide/available/csv/"
        download_response = self.session.get(
            download_url, headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        if download_response.status_code != 200:
            raise Exception(
                f"Error: csv download returned status code [{download_response.status_code}], expected 200"
            )

        return download_response.content
