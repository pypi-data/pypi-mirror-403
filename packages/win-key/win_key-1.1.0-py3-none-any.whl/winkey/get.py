from . import public

user32=public.user32

def is_key_down(vk_code:int)->int:
    return user32.GetKeyState(vk_code)