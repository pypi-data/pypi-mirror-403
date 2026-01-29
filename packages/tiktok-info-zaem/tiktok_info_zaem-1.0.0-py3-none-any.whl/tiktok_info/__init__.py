import requests

def user(username):
    url = "https://www.tikwm.com/api/user/info"
    r = requests.get(url, params={"unique_id": username}, timeout=20)
    data = r.json()

    user = data["data"]["user"]
    stats = data["data"]["stats"]

    return f"""
USER : {user['uniqueId']}
NAME : {user['nickname']}
ID : {user['id']}
FOLLOWER : {stats['followerCount']}
FOLLOW : {stats['followingCount']}
VERIFIED : {bool(user['verified'])}
""".strip()