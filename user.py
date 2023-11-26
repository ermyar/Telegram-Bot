from dataclasses import dataclass


@dataclass
class User:
    user_id: int
    username: str
    name: str
    age: int
    photo: str
    description: str
    place: int
    sex: int
    searching_for: int
 