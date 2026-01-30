from nancal_langchain_base.global_conf.global_config import APP_MODE


def is_prod() -> bool:
    return APP_MODE == "prod"

def get_execute_mode() -> str:
    return "test_run" if not is_prod() else "run"
