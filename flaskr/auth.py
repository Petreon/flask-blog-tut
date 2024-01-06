import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

#A Blueprint is a way to organize a group of related views and other code. Rather than registering views and other code directly with an application, they are registered with a blueprint. Then the blueprint is registered with the application when it is available in the factory function.

#its an way to create and comunicate routes in another files to the principal application

from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

#creating the "view" code to handle the registration and putting in the database the route is /auth/register handling if the method of the route is POST, otherwise will render a template

#register view function
@bp.route('register', methods=('GET','POST')) #@bp.route associates the URL /register with the register view function. When Flask receives a request to /auth/register, it will call the register view and use the return value as the response.
def register():
    if request.method == 'POST': #If the user submitted the form, request.method will be 'POST'. In this case, start validating the input.
        #request.form is a special type of dict mapping submitted form keys and values. The user will input their username and password.
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        error = None

        ##handling some errors Validate that username and password are not empty.
        if not username:
            error = 'Username is required'
        elif not password:
            error = 'Password is required'

        #If validation succeeds, insert the new user data into the database.

        if error is None:
            try:
                db.execute(
                    "INSERT INTO user (username, password) VALUES (?, ?)", (username, generate_password_hash(password)),
                )
                #db.execute takes a SQL query with ? placeholders for any user input, and a tuple of values to replace the placeholders with. The database library will take care of escaping the values so you are not vulnerable to a SQL injection attack.
                db.commit()
                #For security, passwords should never be stored in the database directly. Instead, generate_password_hash() is used to securely hash the password, and that hash is stored. Since this query modifies data
                 
                #db.commit() needs to be called afterwards to save the changes.


            except db.IntegrityError: #An sqlite3.IntegrityError will occur if the username already exists, which should be shown to the user as another validation error.
                error = f"User {username} is already registered"
            else:
                return redirect(url_for("auth.login"))
                #After storing the user, they are redirected to the login page. url_for() generates the URL for the login view based on its name. This is preferable to writing the URL directly as it allows you to change the URL later without changing all code that links to it. redirect() generates a redirect response to the generated URL.
        
        flash(error)
        #If validation fails, the error is shown to the user. flash() stores messages that can be retrieved when rendering the template.
    
    return render_template('auth/register.html') #When the user initially navigates to auth/register, or there was a validation error, an HTML page with the registration form should be shown. render_template() will render a template containing the HTML


#using the same register patterns
@bp.route("/login", methods=('GET','POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        error = None


        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()
        #The user is queried first and stored in a variable for later use.

        #fetchone() returns one row from the query. If the query returned no results, it returns None. Later, fetchall() will be used, which returns a list of all results.

        if user is None:
            error = 'Incorrect Username.'

        elif not check_password_hash(user['password'], password): #check_password_hash() hashes the submitted password in the same way as the stored hash and securely compares them. If they match, the password is valid.
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))
            #session is a dict that stores data across requests. When validation succeeds, the user’s id is stored in a new session. The data is stored in a cookie that is sent to the browser, and the browser then sends it back with subsequent requests. Flask securely signs the data so that it can’t be tampered with.
            # a modern way to do this is to use an UUID not the autoincrement ID, this can cause problens of another user trying to access other users data
        
                   
        flash(error)

    return render_template("auth/login.html")


#handling with the session, this verify if the user is already logged in

##Now that the user’s id is stored in the session, it will be available on subsequent requests. At the beginning of each request, if a user is logged in their information should be loaded and made available to other views.

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    #print("User_id: ", user_id)

    if user_id is None:
        g.user = None

    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?',(user_id,)
        ).fetchone()
    #bp.before_app_request() registers a function that runs before the view function, no matter what URL is requested. load_logged_in_user checks if a user id is stored in the session and gets that user’s data from the database, storing it on g.user, which lasts for the length of the request. If there is no user id, or if the id doesn’t exist, g.user will be None.
        
@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


#Require Authentication in Other Views
#Creating, editing, and deleting blog posts will require a user to be logged in. A decorator can be used to check this for each view it’s applied to.

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        
        return view(**kwargs)
    
    return wrapped_view

# When using a blueprint, the name of the blueprint is prepended to the name of the function, so the endpoint for the login function you wrote above is 'auth.login' because you added it to the 'auth' blueprint.
    
    