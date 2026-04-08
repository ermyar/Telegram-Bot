import random

import db
import constants
from user import User

 
async def get_profile(user_id: int) -> str:
    user = User(*(await db.get_user(user_id))[:-1])
    text = constants.profile_template.format(user.name, user.age, constants.places[user.place], user.description)
    return text


async def find_random_profile(user: User) -> int:
    matching = set(map(lambda row: row[0], await db.get_matching_users(user)))
    watched = set(await db.get_watched(user.user_id))
    pick = list(matching - watched)
    if len(pick) == 0:
        return -1
    return random.choice(pick)
