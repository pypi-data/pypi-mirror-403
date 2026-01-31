from bluer_options.env import load_config, load_env, get_env

load_env(__name__)
load_config(__name__)


abcli_is_github_workflow = get_env("GITHUB_ACTIONS")

abcli_display_fullscreen = get_env("abcli_display_fullscreen")

BLUER_AI_GIT_SSH_KEY_NAME = get_env("BLUER_AI_GIT_SSH_KEY_NAME")

bluer_ai_gpu_status_cache = get_env("bluer_ai_gpu_status_cache")

abcli_path_abcli = get_env("abcli_path_abcli")

ABCLI_PATH_IGNORE = get_env("ABCLI_PATH_IGNORE")

ABCLI_MLFLOW_STAGES = get_env("ABCLI_MLFLOW_STAGES")

BLUER_AI_GITHUB_TOKEN = get_env("BLUER_AI_GITHUB_TOKEN")

BLUER_AI_STORAGE_CHECK_URL = get_env("BLUER_AI_STORAGE_CHECK_URL")

BLUER_AI_WEB_CHECK_URL = get_env("BLUER_AI_WEB_CHECK_URL")

BLUER_AI_WEB_RECEIVE_PORT = get_env("BLUER_AI_WEB_RECEIVE_PORT")
BLUER_AI_WEB_SEND_PORT = get_env("BLUER_AI_WEB_SEND_PORT")

BLUER_AI_IP = get_env("BLUER_AI_IP")

BLUER_AI_WEB_LOGO = "https://kamangir-public.s3.ir-thr-at1.arvanstorage.ir/2026-01-15-20-36-14-veuhs0/test-00.png"

BLUER_AI_WEB_OBJECT = get_env("BLUER_AI_WEB_OBJECT")

BLUER_AI_NATIONAL_INTERNET_INDEX = get_env("BLUER_AI_NATIONAL_INTERNET_INDEX")
