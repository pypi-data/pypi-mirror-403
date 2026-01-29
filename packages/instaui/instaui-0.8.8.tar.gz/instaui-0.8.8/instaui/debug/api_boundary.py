def user_api(fn):
    fn.__instaui_user_api__ = True
    return fn
