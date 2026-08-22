from dataclasses import dataclass


@dataclass
class LoginInfo:
    username: str
    password: str