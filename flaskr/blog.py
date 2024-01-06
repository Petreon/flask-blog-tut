from flask import (Blueprint, flash, g, redirect, render_template, request, url_for)

from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('blog', __name__)

@bp.route('/')
def index():
    #The index will show all of the posts, most recent first. A JOIN is used so that the author information from the user table is available in the result.
    if g.user is None:
        db = get_db()
        #print('AAAAAAAAAAAAA')
        #print(g.user)

        posts = db.execute(""" SELECT p.id, title, body, created, author_id, username FROM post p JOIN user u ON p.author_id = u.id ORDER BY created DESC
""").fetchall() ## return a list key:value map with all post an return it to template to render
        
    else: 
        ## this is temporary because g is not closing the db connection when load_user_logged is called maybe this get-off in the future but now is working
        posts = g.db.execute(""" SELECT p.id, title, body, created, author_id, username FROM post p JOIN user u ON p.author_id = u.id ORDER BY created DESC
""").fetchall()
        #print(posts[0]['title'])
    
    return render_template('blog/index.html', posts = posts)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required'

        if error is not None:
            flash(error)
        else:
            g.db.execute(""" INSERT INTO post (title,body,author_id) VALUES (?,?,?)""",(title,body,g.user['id']))
            g.db.commit()
            return redirect(url_for('blog.index'))
        
    return render_template('blog/create.html')

#Both the update and delete views will need to fetch a post by id and check if the author matches the logged in user. To avoid duplicating code, you can write a function to get the post and call it from each view.

def get_post(id, check_author=True):
    ## if this doestn work change to g.db.execute()
    post = g.db.execute(
        """SELECT p.id, title, body, created, author_id, username
         FROM post p JOIN user u ON p.author_id = u.id
          WHERE p.id = ? """, (id,)
    ).fetchone()

    #abort() will raise a special exception that returns an HTTP status code. It takes an optional message to show with the error, otherwise a default message is used. 404 means “Not Found”, and 403 means “Forbidden”. (401 means “Unauthorized”, but you redirect to the login page instead of returning that status.)

    if post is None:
        abort(404, f"post {id} doesn't exist")
    
    if check_author and post['author_id'] != g.user['id']: ## i think check_autho variable doesnt nedeed i could pass an whitelist to see if the use is an admin
        abort(403)

    return post

    #The check_author argument is defined so that the function can be used to get a post without checking the author. This would be useful if you wrote a view to show an individual post on a page, where the user doesn’t matter because they’re not modifying the post.

@bp.route('/<int:id>/update', methods=('GET','POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title: # has another ways to handle this not is 'easier'
            error = 'Title is required'
        
        if error is not None:
            flash(error)

        else:
            g.db.execute(
                """UPDATE post SET title = ? , body = ?
                WHERE id = ?""", (title,body,id)
            )
            g.db.commit()
            return redirect(url_for('blog.index'))
        
    #Unlike the views you’ve written so far, the update function takes an argument, id. That corresponds to the <int:id> in the route. A real URL will look like /1/update. Flask will capture the 1, ensure it’s an int, and pass it as the id argument. If you don’t specify int: and instead do <id>, it will be a string. To generate a URL to the update page, url_for() needs to be passed the id so it knows what to fill in: url_for('blog.update', id=post['id']). This is also in the index.html file above.


    return render_template('blog/update.html', post=post)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id) ## the get_post method is only usefull to validate if the user can really delete de post if not will raise an error
    #db = get_db() this doesnt working
    g.db.execute('DELETE FROM post WHERE id = ?', (id,))
    g.db.commit()
    return redirect(url_for('blog.index'))