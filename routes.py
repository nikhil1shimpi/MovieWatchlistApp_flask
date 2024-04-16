from flask import flash, Blueprint, current_app, url_for, render_template, session, redirect, request
from forms import LoginForm, RegisterForm, MovieForm, ExtendedMovieForm
import uuid
from dataclasses import asdict
from models import Movie, User
import datetime
from passlib.hash import pbkdf2_sha256
import functools
import pickle
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

pages = Blueprint(
    "pages", __name__, template_folder="templates", static_folder="static"
)

def login_required(route):
    @functools.wraps(route)
    def route_wrapper(*args, **kwargs):
        if session.get("email") is None:
            return redirect(url_for(".login"))
        return route(*args, **kwargs)
    return route_wrapper

@pages.route("/")
@login_required
def index():
    user_data = current_app.db.user.find_one({"email": session["email"]})
    user = User(**user_data)

    movie_data = current_app.db.movie.find({"_id": {"$in":user.movies}})
    movies = [Movie(**movie) for movie in movie_data]
    return render_template(
        "index.html",
        title="Movies Watchlist",
        movies_data = movies
    )

@pages.route("/register", methods=["GET","POST"])
def register():
    if session.get("email"):
        return redirect(url_for(".index"))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(_id=uuid.uuid4().hex, email=form.email.data, password=pbkdf2_sha256.hash(form.password.data))
        current_app.db.user.insert_one(asdict(user))
        flash("User registration done successfully.", "Success")
        return redirect(url_for(".login"))
    return render_template("register.html", title="Movies Watchlist - Register", form =form)

@pages.route("/logout")
def logout():
    session.clear()
    return redirect(url_for(".login"))

@pages.route("/login", methods=["GET","POST"])
def login():
    if session.get("email"):
        return redirect(url_for(".index"))
    form = LoginForm()
    if form.validate_on_submit():
        user_data = current_app.db.user.find_one({"email": form.email.data})
        if not user_data:
            flash("Login credential not correct", category="danger")
            return redirect(url_for(".login"))
        user = User(**user_data)
        if user and pbkdf2_sha256.verify(form.password.data, user.password):
            session["user_id"] = user._id
            session["email"] = user.email
            return redirect(url_for('.index'))
        flash("Login credential not correct", category="danger")
    return render_template("login.html", title="Movies Watchlist - Login", form =form)


@pages.route("/add", methods=["GET","POST"])
@login_required
def add_movie():
    form = MovieForm()
    if form.validate_on_submit():
        movie = Movie(_id = uuid.uuid4().hex,
            title= form.title.data,
            director= form.director.data,
            year= form.year.data
        )
        current_app.db.movie.insert_one(asdict(movie))
        current_app.db.user.update_one(
            {"_id": session["user_id"]}, {"$push": {"movies": movie._id}}
        )
        return redirect(url_for(".index"))
    return render_template("new_movie.html", title="Movies watchlist - Add Movie", form=form)

@pages.route("/edit/<string:_id>", methods=["GET","POST"])
@login_required
def edit_movie(_id: str):
    movie_data = current_app.db.movie.find_one({"_id": _id})
    movie = Movie(**movie_data)
    form = ExtendedMovieForm(obj=movie)
    if form.validate_on_submit():
        movie.title= form.title.data
        movie.director= form.director.data
        movie.year= form.year.data
        movie.cast = form.cast.data
        movie.series = form.series.data
        movie.tags = form.tags.data
        movie.description = form.description.data
        movie.video_link = form.video_link.data
        # overview, genre, keywords, cast, crew.
        current_app.db.movie.update_one({"_id": _id}, {"$set":asdict(movie)})
        return redirect(url_for(".movie", _id=movie._id))
    return render_template("movie_form.html", movie=movie, form=form)
    
@pages.get("/movie/<string:_id>")
def movie(_id: str):
    movie_data = current_app.db.movie.find_one({"_id": _id})
    movie = Movie(**movie_data)
    return render_template("movie_details.html", movie=movie)

@pages.get("/movie/<string:_id>/similar_movies")
@login_required
def find_similar_movies(_id):
    new = pd.read_csv("Movie Recomandation\\new_dataset.csv")
    movie_data = current_app.db.movie.find_one({"_id": _id})
    if movie_data["description"]:
        movie_data_list = movie_data["description"] + movie_data["tags"] + movie_data["cast"]
        movie_data_string = ' '.join([str(elem) for elem in movie_data_list])
        # print(type(movie_data_string))
        # print(movie_data_string)
        vectors = pickle.load(open("Movie Recomandation\\vector_file", "rb"))
        new_movie_vector = vectors.transform([movie_data_string])
        # print(new_movie_vector.shape)
        # print(new_movie_vector)
        vectors = pickle.load(open("Movie Recomandation\\vector_file1", "rb"))
        # print(vectors.shape)
        similarity = cosine_similarity(new_movie_vector, vectors)
        # print(type(similarity))
        # print(similarity.shape)
        data_series = pd.Series(similarity[0])
        sorted_series_desc = data_series.sort_values(ascending=False)
        similar_movies = list(new.iloc[sorted_series_desc.head(5).index]["title"])
        # similar_movies = ["A", "B", "C", "D", "E"]
        current_app.db.movie.update_one({"_id": _id}, {"$set":{"similar_movies":similar_movies}})
    movie_data = current_app.db.movie.find_one({"_id": _id})
    movie = Movie(**movie_data)
    return redirect(url_for(".movie", _id=_id))

@pages.get("/movie/<string:_id>/rate")
@login_required
def rate_movie(_id):
    rating = int(request.args.get("rating"))
    current_app.db.movie.update_one({"_id": _id}, {"$set":{"rating": rating}})
    return redirect(url_for(".movie", _id=_id))

@pages.get("/movie/<string:_id>/watch")
@login_required
def watch_today(_id):
    current_app.db.movie.update_one({"_id": _id},{"$set":{"last_watched": datetime.datetime.today()}})
    return redirect(url_for(".movie", _id=_id))

@pages.route("/toggle-theme")
def toggle_theme():
    current_theme =session.get('theme')
    if current_theme == "dark":
        session["theme"] = "light"
    else:
        session["theme"] = "dark"
    return redirect(request.args.get("current_page"))