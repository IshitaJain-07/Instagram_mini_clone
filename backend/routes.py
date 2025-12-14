from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Post, Like, Comment, Follow

api = Blueprint("api", __name__)

# ---------- AUTH ----------
@api.route("/signup", methods=["POST"])
def signup():
    data = request.json

    if User.query.filter_by(email=data["email"]).first():
        return jsonify(message="Email already exists"), 400

    user = User(
        username=data["username"],
        email=data["email"],
        password=generate_password_hash(data["password"])
    )
    db.session.add(user)
    db.session.commit()
    return jsonify(message="User created")


@api.route("/login", methods=["POST"])
def login():
    data = request.json
    user = User.query.filter_by(email=data["email"]).first()

    if not user or not check_password_hash(user.password, data["password"]):
        return jsonify(message="Invalid credentials"), 401

    token = create_access_token(identity=str(user.id))
    return jsonify(token=token)


# ---------- POSTS ----------
@api.route("/post", methods=["POST"])
@jwt_required()
def create_post():
    user_id = int(get_jwt_identity())

    post = Post(
        user_id=user_id,
        image_url=request.json["image_url"],
        caption=request.json["caption"]
    )
    db.session.add(post)
    db.session.commit()
    return jsonify(message="Post created")


@api.route("/feed", methods=["GET"])
@jwt_required()
def feed():
    user_id = int(get_jwt_identity())

    following_ids = [f.following_id for f in Follow.query.filter_by(follower_id=user_id)]
    following_ids.append(user_id)

    posts = Post.query.filter(Post.user_id.in_(following_ids)).order_by(Post.id.desc()).all()

    return jsonify([
        {
            "id": p.id,
            "image_url": p.image_url,
            "caption": p.caption,
            "likes": Like.query.filter_by(post_id=p.id).count(),
            "comments": [{"text": c.text} for c in Comment.query.filter_by(post_id=p.id)]
        } for p in posts
    ])


# ---------- LIKE / COMMENT ----------
@api.route("/post/<int:post_id>/like", methods=["POST"])
@jwt_required()
def like_post(post_id):
    uid = int(get_jwt_identity())

    if not Like.query.filter_by(user_id=uid, post_id=post_id).first():
        db.session.add(Like(user_id=uid, post_id=post_id))
        db.session.commit()

    return jsonify(message="Liked")


@api.route("/post/<int:post_id>/comment", methods=["POST"])
@jwt_required()
def comment_post(post_id):
    db.session.add(Comment(
        user_id=int(get_jwt_identity()),
        post_id=post_id,
        text=request.json["text"]
    ))
    db.session.commit()
    return jsonify(message="Comment added")


# ---------- SEARCH USERS ----------
@api.route("/users/search")
@jwt_required()
def search_users():
    q = request.args.get("q", "")
    current = int(get_jwt_identity())

    users = User.query.filter(User.username.contains(q)).all()

    return jsonify([
        {"username": u.username}
        for u in users if u.id != current
    ])


# ---------- PROFILE ----------
@api.route("/user/<username>")
@jwt_required()
def user_profile(username):
    current = int(get_jwt_identity())
    user = User.query.filter_by(username=username).first_or_404()

    is_following = Follow.query.filter_by(
        follower_id=current,
        following_id=user.id
    ).first() is not None

    return jsonify({
        "id": user.id,
        "username": user.username,
        "is_self": current == user.id,
        "is_following": is_following
    })


# ---------- FOLLOW ----------
@api.route("/follow/<int:user_id>", methods=["POST"])
@jwt_required()
def follow(user_id):
    current = int(get_jwt_identity())

    if current != user_id and not Follow.query.filter_by(
        follower_id=current, following_id=user_id
    ).first():
        db.session.add(Follow(follower_id=current, following_id=user_id))
        db.session.commit()

    return jsonify(message="Followed")


@api.route("/unfollow/<int:user_id>", methods=["POST"])
@jwt_required()
def unfollow(user_id):
    current = int(get_jwt_identity())
    f = Follow.query.filter_by(follower_id=current, following_id=user_id).first()

    if f:
        db.session.delete(f)
        db.session.commit()

    return jsonify(message="Unfollowed")

