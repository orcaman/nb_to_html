import os

from flask import Flask
from flask import request
import nbhtml 

app = Flask(__name__)

@app.route('/nb_to_html')
def nb_to_html_request():
    return nbhtml.execute_notebook(request)

@app.route('/health')
def health():
    return 'OK'

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0',port=int(os.environ.get('PORT', 8080)))