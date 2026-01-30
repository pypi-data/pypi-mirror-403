import builtins
import threading
import logging

from flask import Flask

_original_print = builtins.print

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel(logging.ERROR)

htmlbase = """
<html>
    <head>
    <link rel="stylesheet" href="/style">
    </head>
<body>
<pre>
"""
body = ""
htmlend = """
</pre>
    <scroller></scroller>
</body>
<script>
    var s = document.getElementsByTagName("scroller")[0];
    s.scrollIntoView({ behavior: 'smooth' });
</script>
"""

css = """
body {
    background-color: black;
    font-family: "Courier New", Courier, monospace;
    color: white;
}
"""

@app.route("/")
def browser():
    return htmlbase + body + htmlend

@app.route("/style")
def style():
    return css

def print(*values: object, sep: str=" ", end: str="\n", file=None, flush: bool=False):
    global body
    _original_print(*values, sep=sep, end=end, file=file, flush=flush)
    addition: str = sep.join(str(v) for v in values) + end
    cleaned_addition = (
        addition
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    body += cleaned_addition
    return


def startserver():
    app.run(use_evalex=False, static_files={"style.css": "static"})

threading.Thread(target=startserver, daemon=True).start()