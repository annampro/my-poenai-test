# Import required libraries
from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
import uuid
import requests
import json
import random
import string
import unicodedata
import os
import datetime

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'


# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Create Category model
class Category(db.Model):
    id = db.Column(db.String, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(100), nullable=False)
    thumbnail = db.Column(db.String(100), nullable=False)

# Create Post model
class Post(db.Model):
    id = db.Column(db.String, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(100), nullable=False)
    created_date = db.Column(db.DateTime, nullable=False)
    thumbnail = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.String, db.ForeignKey('category.id'), nullable=False)

@app.route('/sitemap.xml')
def sitemap():
    posts = get_posts_from_database() # replace with your own function to retrieve posts from the database
    sitemap_xml = render_template('sitemap.xml', posts=posts)
    response = make_response(sitemap_xml)
    response.headers["Content-Type"] = "application/xml"
    return response



# Route for index page
@app.route('/')
def index():
    categories = Category.query.all()
    return render_template('index.html', categories=categories)

# Route for handling form submissions
@app.route('/', methods=['POST'])
def create_post():
    # Get form data
    question = request.form['question']
    category_id = request.form['category']

    # Generate unique ID for post
    post_id = str(uuid.uuid4())

    # Call OpenAI Q&A API
    response = requests.post('https://api.openai.com/v1/engines/text-babbage-001/jobs',
    headers={'Content-Type': 'application/json',
             'Authorization': 'Bearer <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>'},
    data=json.dumps({
        'text': question,
        'max_tokens': 500,
        'temperature': 0.7
    }))

    # Get answer from API response
    answer = response.json()['choices'][0]['text']

    # Create new post
    post = Post(id=post_id, title=question, url='/post/' + post_id, content=answer, created_date=datetime.datetime.now(), thumbnail='', category_id=category_id)
    db.session.add(post)
    db.session.commit()

    return redirect('/post/' + post_id)


def generate_post_id():
    # Generate a random string of characters
    id_chars = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    # Encode the string as a Unicode string
    post_id = unicodedata.normalize('NFKD', id_chars).encode('ascii', 'ignore').decode()
    return post_id

post_id = generate_post_id()

# Route for displaying post
@app.route('/post/<post_id>')
def display_post(post_id):
    post = Post.query.filter_by(id=post_id).first()
    category = Category.query.filter_by(id=post.category_id).first()
    return render_template('post.html', post=post, category=category)

# Route for displaying posts in a category
@app.route('/category/<category_id>')
def display_category(category_id):
    category = Category.query.filter_by(id=category_id).first()
    posts = Post.query.filter_by(category_id=category_id).all()
    return render_template('category.html', category=category, posts=posts)



if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
