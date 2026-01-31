from blueness.pypi import setup

from bluer_ai import NAME, VERSION, DESCRIPTION, REPO_NAME

setup(
    filename=__file__,
    repo_name=REPO_NAME,
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    packages=[
        NAME,
        f"{NAME}.help",
        f"{NAME}.help.env",
        f"{NAME}.help.web",
        f"{NAME}.modules",
        f"{NAME}.modules.terraform",
        f"{NAME}.plugins",
        f"{NAME}.plugins.git",
        f"{NAME}.plugins.gpu",
        f"{NAME}.plugins.web",
        f"{NAME}.plugins.web.receive",
        f"{NAME}.README",
        f"{NAME}.tests",
    ],
    package_data={
        NAME: [
            "config.env",
            "sample.env",
            ".abcli/**/*.sh",
            "assets/**/*",
        ],
    },
)
