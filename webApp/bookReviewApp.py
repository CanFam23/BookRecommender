from flask import Flask, render_template,request,jsonify
import pandas as pd
from reviewer import recommendBooks

app = Flask(__name__) 

@app.route("/")  
def home():
    """Render the HTML template for the index page.

    Returns:
        flask.Response: The rendered 'index.html' template.
    """
    return render_template("index.html")

@app.route("/getBooks",methods=["POST"])
def submit():
    """Handle book recommendation requests.

    Extracts the book title from the incoming JSON request, finds recommended books using `recommendBooks`, 
    and returns the results as a JSON response.

    Returns:
        flask.Response: A JSON object containing the recommended books and their data, 
        or a message indicating no matching book was found.
    """
    data = request.json 
    name = data.get('name')
    
    bookList,df = recommendBooks(name)
    if not bookList or not df:
        response_message = {"message":f"No book in dataset title '{name}'"}
        return jsonify(response_message)
    
    return jsonify({"bookList":bookList,"bookData":df})

@app.route("/getBookList", methods=["GET"])
def bookList():
    """Retrieve a list of unique book titles.

    Reads the `uniqueBooks.csv` file and extracts the list of book titles, returning them as a JSON response.

    Returns:
        flask.Response: A JSON object containing a list of unique book titles.
    """
    uniqueBooks = pd.read_csv('data/uniqueBooks.csv')
    return jsonify({"bookTitles": uniqueBooks['Title'].to_list()})

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
