from bluer_options import string
from bluer_options import env


def as_str(
    emoji: bool = True,
    timestamp: bool = False,
) -> str:
    return "{} {}".format(
        (
            "{} -".format(
                string.timestamp(
                    unique_length=0,
                )
            )
            if timestamp
            else "access:"
        ),
        ", ".join(
            [
                "{} {}".format(
                    name,
                    (
                        ("✅" if emoji else "pass")
                        if accessible
                        else ("🛑" if emoji else "fail")
                    ),
                )
                for name, accessible in {
                    "pypi": env.BLUER_AI_PYPI_IS_ACCESSIBLE,
                    "storage": env.BLUER_AI_STORAGE_IS_ACCESSIBLE,
                    "web": env.BLUER_AI_WEB_IS_ACCESSIBLE,
                }.items()
            ]
        ),
    )
