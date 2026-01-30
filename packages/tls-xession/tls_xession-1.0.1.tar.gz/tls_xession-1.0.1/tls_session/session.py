from curl_cffi import requests
import warnings
from .fingerprints import CHROME_144_JA3, CHROME_144_AKAMAI, CHROME_144_EXTRA_FP

warnings.filterwarnings("ignore")


class Session(requests.Session):
    def __init__(self):
        super().__init__()

        self._fixed_user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/144.0.0.0 Safari/537.36"
        )

        self.headers.update({
            "user-agent": self._fixed_user_agent,
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-US,en;q=0.9",
        })

        self.ja3 = CHROME_144_JA3
        self.akamai = CHROME_144_AKAMAI
        self.extra_fp = CHROME_144_EXTRA_FP

    def request(self, method, url, **kwargs):
        headers = kwargs.get("headers", {})

        if "user-agent" in headers:
            headers.pop("user-agent")

        final_headers = self.headers.copy()
        final_headers.update(headers)
        kwargs["headers"] = final_headers

        return super().request(method, url, **kwargs)
