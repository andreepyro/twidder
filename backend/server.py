from flask import Flask, send_file
 
app = Flask(__name__, static_folder="../frontend", static_url_path='')

@app.route('/')
@app.route('/home')
@app.route('/browse')
@app.route('/account')
def hello_world():
    return send_file("../frontend/client.html")

if __name__ == '__main__':
    app.run(host="localhost", port=8080, debug=True)
