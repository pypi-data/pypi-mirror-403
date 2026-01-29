import os
import appdirs


def get_app_log_dir(app_name: str, app_family: str = ""):
    """Get the directory to store this app's logs in.

    If an environment variable APP_NAME_LOG_DIR is set, returns that.
    If APP_FAMILY_LOG_DIR is set in env, returns APP_FAMILY_LOG_DIR/APP_NAME.
    Otherwise, returns the standard user log dir (e.g. ~/.local/log/APP_NAME.).
    """
    # check environment variables
    env_app_log_dir = os.environ.get(f"{app_name.upper()}_LOG_DIR", None)
    env_family_log_dir = os.environ.get(f"{app_family.upper()}_LOG_DIR", None)

    # decide which log dir to use
    log_dir = ""
    if env_app_log_dir:
        log_dir = env_app_log_dir
    elif env_family_log_dir and app_family:
        log_dir = os.path.join(env_family_log_dir, app_name)
    else:
        log_dir = os.path.join(appdirs.user_log_dir(), app_name)

    # ensure log dir exists
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    return log_dir
