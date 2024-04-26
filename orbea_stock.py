import requests


# Create class to download Orbea stock
class OrbeaStock:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.session = requests.Session()
        self.session.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Sec-Ch-Ua": '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": "Windows",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        }

    def login(self):
        login_url = "https://www.orbea.com/nl-en/kide/login/"
        login_data = {
            "login_email": self.email,
            "login_password": self.password,
            "from": "",
            "login": "",
        }
        test = self.session.get(login_url)
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
