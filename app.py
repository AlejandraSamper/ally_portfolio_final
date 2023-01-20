from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import os
import sys
import re
import feedparser

app = Flask(__name__)

if __name__ == '__main__':
    app.run(debug=True)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
db = SQLAlchemy(app)


class Feeds(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(80), unique=False, nullable=False)
    url = db.Column(db.String(120), unique=False, nullable=False)

    def __init__(self, user, url):
        self.user = user
        self.url = url


db.drop_all()
db.create_all()


#ROUTES THAT RENDER A PAGE FOR THE BROWSER
@app.route('/')
def index():
    urls = ["https://www.giantbomb.com/feeds/reviews"]
    for url in urls:
        feed = feedparser.parse(url)
        article = feed['entries'][0]
        # check for pictures
    try:
        media_url = article.media_content[0]['url']
    except AttributeError:
        media_url = ''
    
    #might actually uncomment and go back to this. Iterate through list of feeds, then serve the whole block as content of a div in index.html???
    # return """<html>
    #    <body>
    #        <div style="display: block; margin-right: auto; margin-left: auto; width: 400px">
    #            <h1>Yahoo News</h1>
    #            <b>{0}</b><br>
    #            <p>{1}</p><br>
    #            <p>{2}</p><br>
    #            <p>{3}</p><br>
#
#            </div>
#        </body>
#        </html>""".format(article.get("title"), article.get("link"), article.get("pubDate"), article.get("source"))
    previewText = article.get("description")[:200] + "..."
    return render_template('index.html', content=previewText, title=article.get("title"), link=article.get("link"), image=media_url)

@app.route('/<username>', methods=['GET'])
def publish_username_feeds(username):
    list_of_feeds = []
    for result in Feeds.query.filter(Feeds.user == username):
        del result.__dict__['_sa_instance_state']
        list_of_feeds.append(result.__dict__.get('url'))
    
    #begin html body
    htmlbody = """
        <html>
            <body style="background-color: blanchedalmond;">
                <div>
                <p style="font-family: sans-serif; margin-top: 40px; text-align: center"><b>Welcome, {0}! Here are the latest updates to your RSS subscriptions</b></p>
                """.format(str(username).capitalize())
    print (list_of_feeds, file=sys.stderr)
    for url in list_of_feeds:
        article = feedparser.parse(url)
        block = article['entries'][0]
        # check for pictures
        try:
            block_media = block.media_content[0]['url']
        except AttributeError:
            block_media = ''
        block_text = block.get("description")[40:200]
        block_text = re.sub(r'\W+\s', '', block_text) + "..."
        block_title = block.get("title")
        block_link = block.get("link")
        
        htmlbody += """
                    <hr style="width: 80%; margin-left: auto; margin-right: auto;">
                    <div style="display: block; margin-right: auto; margin-left: auto; width: 400px; background-color: white; text-align: center;">
                        <b>{0}</b>
                        <p><a href="{1}">{1}</a></p>
                        <p><img src="{2}" alt="preview" height="auto" width="300px" style="margin-right: auto; margin-left: auto;"></p>
                    </div>
        """.format(block_title, block_link, block_media)
    
    htmlbody += """
                </div>
            </body>
        </html>    
    """
    
    return htmlbody

#API ROUTES
@app.route('/feeds/<username>', methods=['GET'])
def get_user_feeds(username):
    result_feeds = []
    for feed in Feeds.query.filter(Feeds.user == username):
        del feed.__dict__['_sa_instance_state']
        result_feeds.append(feed.__dict__)
    return jsonify(result_feeds)


@app.route('/feeds', methods=['GET'])
def get_feeds():
    feeds = []
    for item in db.session.query(Feeds).all():
        del item.__dict__['_sa_instance_state']
        feeds.append(item.__dict__)
    return jsonify(feeds)


@app.route('/feeds', methods=['POST'])
def create_user():
    body = request.get_json()
    db.session.add(Feeds(body['user'], body['url']))
    db.session.commit()
    return "associated feed URL with user " + body['user']
 

@app.route('/feeds/<user>', methods=['DELETE'])
def delete_user(user):
    db.session.query(Feeds).filter_by(user=user).delete()
    db.session.commit()
    return str("user " + user + " deleted")
