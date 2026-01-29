import winkey

user32=winkey.user32

def get_key_state(vk_code:int)->int:
    return user32.GetKeyState(vk_code)