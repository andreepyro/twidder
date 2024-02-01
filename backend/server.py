from flask import Flask, send_file, jsonify, request
import database_helper 
import bcrypt
import uuid
import json
import base64
app = Flask(__name__, static_folder="../frontend", static_url_path='')

@app.route('/')
@app.route('/home')
@app.route('/browse')
@app.route('/account')
def hello_world():
    return send_file("../frontend/client.html")

if __name__ == '__main__':
    app.run(host="localhost", port=8080, debug=True)

#Lesson 2 examples 
@app.route('/sign_in',methods= ['POST'])
def sign_in():
    body = request.get_json() 
    if "username" not in body: 
        return jsonify({"message": "username is missing"}), 400
    if "password" not in body: 
        return jsonify({"message": "password is missing"}), 400
    username = body["username"]
    password = body["password"]
    user = database_helper.retrieve_user(username)
    #password = str(hash(password))
    password = _hash_password(password)["hashed_password"]
    if user is not None and password==user["password"]:
        token = _create_token(username)
        add_token = database_helper.create_token(token)
        if add_token: 
            resp = Flask.Response(add_token, status=200)
            resp.headers["Authorization"] = token
            return resp
        return jsonify({"Token failed to be created"}), 200
    return jsonify({"Combination of username and password is unsuccessful"}), 401
    
def _hash_password(password: str):
    b_password = str.encode(password)
    salt = bcrypt.gensalt()
    hash_password = bcrypt.hashpw(
    password=b_password,
    salt=salt
)
    print(f"Actual Password: {b_password.decode('utf-8')}")
    print(f"Hashed Password: {hash_password.decode('utf-8')}")
    return {"plaintext": b_password.decode('utf-8'), 
            "hashed_password": hash_password.decode('utf-8')}

def _encode_token(token_plain: dict) -> str:
   token_str = json.dumps(token_plain)
   token_b = bytes(token_str, "utf-8")
   token_b64b = base64.b64encode(token_b)
   return token_b64b.decode("utf-8")

def _decode_token(token: str) -> dict:
   token_str = base64.b64decode(token)
   return json.loads(token_str)

def _create_token(user_email: str) -> str:
   return _encode_token({
       "user": user_email,
       "session_id": uuid.uuid4(),
   })

def _verify_token(user_email: str, token: str) -> bool:
   return database_helper.get_token(token) and _decode_token(token)["user"] == user_email

@app.route("/getcontact/<name>", methods = ['GET'])
def get_contact(name):
    if len(name) >= 4:
        contact = database_helper.retrieve_contact(name)
        return jsonify(contact), 200
    else:
        return "Too short name", 400 #return data in json format for instance jsonify({"message" : "Too short name"})

@app.route("/save_contact/", methods = ['POST'])
def save_contact():
    json_dic = request.get_json() #returns dictionary, not text. 
    if "name" in json_dic and "number" in json_dic:
        if len(json_dic["name"])>4:
            resp = database_helper.create_contact(json_dic["name"],json_dic["number"])
            if resp is False: 
                return jsonify({"message": "creating contact"})   
        else: 
            return jsonify({"message": "name to short"})
    else: 
            return jsonify({"message": "data missing"})

