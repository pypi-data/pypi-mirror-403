from flask import Flask, request, Response

PORT = 5000
app = Flask(__name__)


@app.route("/")
def hello():
    return "Hello, World!"


@app.route("/my-webhook", methods=["POST"])
def mindkosh():
    print(request.json)
    return Response(status=200)


if __name__ == "__main__":
    app.run(port=PORT,debug=True)
