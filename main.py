from flask import Flask, render_template, request
import psycopg2
import re

app = Flask(__name__)
template = """
BEGIN;
{}
{}
ROLLBACK;
""".strip("\n")


@app.route("/", methods=["GET"])
def index():
    """
    Render the client application template.

    :return: server response
    """
    return render_template("index.html")


@app.route("/validate", methods=["POST"])
def validate():
    """
    Validate the input SQL code.

    :return: server response
    """
    data = request.json
    if has_semicolon(data["queryCode"][:-1]):
        return {"success": False, "message": "Unsafe code received"}, 400
    query = template.format(data["tablesCode"], data["queryCode"])

    conn = psycopg2.connect(dbname="query_testing", user="testing_user", password="1234", options="-c statement_timeout=5000")
    cursor = conn.cursor()

    try:
        cursor.execute(query)
    except Exception as e:
        error_offset = len(data["tablesCode"].split("\n")) + 1
        a = str(e).split("\n")
        for i, line in enumerate(a):
            if line.startswith("LINE "):
                x, y = line.split(":", 1)
                new_line = f"{x[:5]}{int(x[5:]) - error_offset}:{y}"
                a[i] = new_line
                a[i+1] = a[i+1][len(line)-len(new_line):]
        result = {
            "success": False,
            "message": "\n".join(a)
        }
    else:
        result = {"success": True, "message": "Validated successfully"}

    cursor.close()
    conn.close()

    return result


def has_semicolon(code):
    """
    Check SQL code for semicolons outside of strings.

    :param code: code string
    :return: boolean
    """
    end_quote = None
    for x in re.findall(r"\$\w*\$|.", code):
        if end_quote is None and x == ";":
            return True
        if end_quote is None and (x == "'" or len(x) > 1):
            end_quote = x
        elif x == end_quote:
            end_quote = None
    return False


if __name__ == "__main__":
    app.run(host="0.0.0.0")
