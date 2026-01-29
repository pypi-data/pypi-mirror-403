from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/call", methods=["GET","POST","PUT","DELETE","PATCH"])
def webhook():
    print("=== WEBHOOK RECEIVED ===")
    print(request.get_json(silent=True) or request.data.decode())
    print("=======================")
    return jsonify({"status":"received"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
