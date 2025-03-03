from typing import List, Optional, Tuple
import numpy as np
import pandas as pd
import re
import ast

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from scipy.sparse import hstack
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from collections import Counter

print('Loading book data...')
booksFiltered = pd.read_parquet('data/booksCleaned.parquet')
# My parquet files don't store lists properly, so need to convert authors and categories back to lists
booksFiltered["authors"] = booksFiltered["authors"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
booksFiltered["categories"] = booksFiltered["categories"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)


print('Loading rating data...')
ratings = pd.read_parquet('data/ratingsCleanedSmaller.parquet')

v = TfidfVectorizer(stop_words='english')

print(f'Fitting book vectorizer...')
xTitles = v.fit_transform(booksFiltered['combined'])

# Book to index series
book2ind = pd.Series(booksFiltered.index, index=booksFiltered['Title'])

#Function I used to tokenize text
def cleanText(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    text = text.split()
    tokens = set(text)
    tokens = [word for word in tokens if word not in stopwords]  # Remove stopwords
    tokens = [t for t in tokens if not any(c.isdigit() for c in t)]
    return ' '.join(tokens)


print('Creating rating model...')

sia = SentimentIntensityAnalyzer()

ratingsSample = pd.read_pickle('data/ratingsSample.pkl')

stopwords = set(stopwords.words('english'))

reviewVect = TfidfVectorizer(tokenizer=cleanText)

print('Transforming text...')
text = ratingsSample['textSummary']
xText = reviewVect.fit_transform(text)
xSS = np.array(ratingsSample["SS"]).reshape(-1, 1)
reviewX = hstack([xText,xSS])
reviewY = ratingsSample['review/score']

print('Fitting rating model...')
xTrain,xTest,yTrain,yTest = train_test_split(reviewX,reviewY,test_size=0.2,random_state=1)
model = LogisticRegression(max_iter=500)
model.fit(xTrain,yTrain)

groups = ratings.groupby('titleClean')

def getMostFreqScore(numbers: List[int]) -> int:
    """Gets the most frequent store in the list of given values.

    Args:
        numbers (list[int]): A list of numbers to get the most frequent value

    Returns:
        int: Most frequent value in the given list
    """
    counter = Counter(numbers)
    max_freq = max(counter.values())
    most_common_numbers = sorted([num for num, freq in counter.items() if freq == max_freq])
    return most_common_numbers[-1]

def getMostSimilarBook(book: str,n: Optional[int] = 10) -> pd.DataFrame:
    """Gets the `n` most similar books to the given `book` using cosine similarity. \n
    If no books were found or the book name is not valid, returns `None`

    Args:
        book (Str): Name of book to use to find similar books.
        n (int, optional): Number of similar books to get. Defaults to 10.

    Returns:
        DataFrame: A `DataFrame` consisting of the information on the 10 most similar books.
    """
    book = book.strip()
    if book in book2ind.keys():
        idx = book2ind[book]
        scores = cosine_similarity(xTitles,xTitles[idx])
        scores = scores.flatten()

        rec = (-scores).argsort()
        rec = rec[1:n]
        return booksFiltered.iloc[rec]
    return None
    
def predictScore(title: str) -> int:
    """Predicts the rating of the given `title`. \n
    Gets all the ratings on the given book, and predicts the score of the given book \n
    based off the ratings sentiment score and review text.

    Args:
        title (str): Title of the book to predict rating

    Returns:
        int: Predicted score of rating.
    """
    # Get the reviews, get textSummary of review and transform it
    if title not in groups.groups:
        return -1
    reviews = groups.get_group(title).copy()
    
    text = reviews['textSummary']
    xText = reviewVect.transform(text)

    # Get the sentiment scores of each review, create x value sparse matrix with sentiment scores and text matrix
    reviews.loc[:, "SS"] = reviews["textSummary"].fillna("").apply(lambda x: sia.polarity_scores(x)["compound"])
    xSS = np.array(reviews["SS"]).reshape(-1, 1)
    xVals = hstack([xText,xSS])

    # Predict score, get most frequent score
    pred = model.predict(xVals)
    predScore = getMostFreqScore(pred)
    return predScore

def recommendBooks(bookTitle: str) -> Tuple[List[str], pd.DataFrame]:
    """Given a `bookTitle` recommends 9 books that are similar. \n
    Using `getMostSimilarBook` and `predictScore`, gets the most \n
    similar books to the given book and sorts them on their predicted score.

    Args:
        bookTitle (str): Title of book to get recommendations based off of.

    Returns:
        Tuple[List[str], pd.DataFrame]: A `Tuple` of the names of the books as \n
        well as a `DataFrame` with all the information of each book.
    """
    similarBooks = getMostSimilarBook(bookTitle)
    if similarBooks is None or similarBooks.empty:
        return None
    books_and_ratings = {}
    # Get the predicted rating of each book
    for book in similarBooks['Title']:
        book = re.sub(r'[^\w\s]', '', book)
        score = predictScore(book)
        if score > -1:
            books_and_ratings[book] = score
        else:
            books_and_ratings[book] = 0
    # Sort by predicted score
    books = sorted(books_and_ratings, key=books_and_ratings.get)
    return (books,similarBooks.to_dict(orient='records'))

print('Recommender loaded!')