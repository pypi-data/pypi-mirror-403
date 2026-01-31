from bluer_options.testing import are_nonempty_strs

from bluer_ai import env


def test_bluer_ai_env():
    assert are_nonempty_strs(
        [
            env.BLUER_AI_WEB_CHECK_URL,
            env.BLUER_AI_STORAGE_CHECK_URL,
            env.BLUER_AI_NATIONAL_INTERNET_INDEX,
            env.BLUER_AI_WEB_RECEIVE_PORT,
            env.BLUER_AI_WEB_SEND_PORT,
            env.BLUER_AI_WEB_OBJECT,
        ]
    )
