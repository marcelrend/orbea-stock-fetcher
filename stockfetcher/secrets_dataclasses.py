import dataclasses


@dataclasses.dataclass
class FtpSecrets:
    host: str
    user: str
    password: str


@dataclasses.dataclass
class ShopifySecrets:
    api_secret: str
    shop_url: str
