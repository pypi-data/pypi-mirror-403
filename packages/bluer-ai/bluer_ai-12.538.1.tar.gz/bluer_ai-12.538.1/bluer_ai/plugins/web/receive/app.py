from flask import Flask, request, abort
import os
import argparse

from blueness import module
from bluer_options import string
from bluer_objects import file
from bluer_objects import objects

from bluer_ai import env
from bluer_ai import NAME, ICON
from bluer_ai.host import signature

NAME = module.name(__file__, NAME)

app = Flask(__name__)

parser = argparse.ArgumentParser(NAME)
parser.add_argument(
    "--object_name",
    type=str,
)
parser.add_argument(
    "--port_receive",
    type=str,
    default=env.BLUER_AI_WEB_RECEIVE_PORT,
)
parser.add_argument(
    "--port_send",
    type=str,
    default=env.BLUER_AI_WEB_SEND_PORT,
)
args = parser.parse_args()

object_path = objects.object_path(args.object_name)

app.config["UPLOAD_FOLDER"] = object_path


@app.post("/save")
def save():
    note_title = (request.form.get("note_title") or "").strip()
    content = request.form.get("content") or ""

    if not note_title:
        abort(400, "note title is required")

    # basic safety: prevent path traversal like ../../etc/passwd
    if "/" in note_title or "\\" in note_title or ".." in note_title:
        abort(400, "invalid note title")

    if not file.save_text(
        objects.path_of(
            object_name=object_path,
            filename=f"notes/{note_title}.txt",
        ),
        [content],
        log=True,
    ):
        abort(400, "saving content failed.")

    return (
        f'✅ saved to <a href="http://{env.BLUER_AI_IP}:{args.port_send}/notes/{note_title}.txt">{note_title}</a> | <a href="../">go back ...</a>\n',
        200,
    )


@app.route("/")
def upload_form():
    success, html = file.load_text(
        file.absolute(
            "./app.html",
            file.path(__file__),
        )
    )
    if not success:
        return "❗️ app.html not found."

    form = "\n".join(html)

    for this, that in {
        "{icon}": ICON,
        "{IP}": env.BLUER_AI_IP,
        "{logo}": env.BLUER_AI_WEB_LOGO,
        "{note_title}": string.timestamp(),
        "{port_receive}": args.port_receive,
        "{port_send}": args.port_send,
        "{footer}": " | ".join(signature()),
        "{header}": (
            ""
            if args.object_name == "void"
            else " | ".join(
                objects.signature(
                    object_name=args.object_name,
                )
            )
        ),
        "{qrcode}": "https://kamangir-public.s3.ir-thr-at1.arvanstorage.ir/kulej/qrcode.png",
    }.items():
        form = form.replace(this, that)

    return form


@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files["file"]
    if file.filename:
        file.save(
            objects.path_of(
                object_name=args.object_name,
                filename=file.filename,
            ),
        )
        return 'uploaded. ✅ | <a href="../">upload another file ...</a>.'

    return '⚠️ file not found | <a href="../">go back ...</a>.'


app.run(
    host="0.0.0.0",
    port=int(args.port_receive),
)
