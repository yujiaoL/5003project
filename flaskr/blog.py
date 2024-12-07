from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('blog', __name__)

@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created_time, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created_time DESC'
    ).fetchall()
    return render_template('blog/index.html', posts=posts)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id)'
                ' VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')


@bp.route('/find', methods=('GET', 'POST'))
def find():
    if request.method == 'POST':
        title = request.form['target']

        if not title:
            return render_template('blog/find.html')

        title = title + "%"

        search_results = get_db().execute(
            'SELECT p.id, title, body, created_time, author_id, username'
            ' FROM post p JOIN user u ON p.author_id = u.id'
            ' WHERE p.title like ?',
            (title,)
        ).fetchall()

        print(search_results)

        if not search_results:
            search_results = None

        return render_template('blog/find.html', search_results=search_results)
    else:
        return render_template('blog/find.html')


def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created_time, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))

@bp.route('/<int:id>/like', methods=['POST','GET'])
def like_post(id):
    db = get_db()
    pid = id
    uid = g.user['id']

    like = db.execute(
        'SELECT * FROM Like WHERE pid = ? AND uid = ?',
        (pid, uid)
    ).fetchone()

    if like:
        # 如果点赞记录存在，删除记录（取消点赞）
        db.execute(
            'DELETE FROM Like WHERE pid = ? AND uid = ?',
            (pid, uid)
        )
    else:
        # 如果点赞记录不存在，插入记录（点赞）
        db.execute(
            'INSERT INTO Like (pid, uid) VALUES (?, ?)',
            (pid, uid)
        )
    db.commit()
    return redirect(url_for('blog.index'))

@bp.route('/<int:id>/comment', methods=('GET', 'POST'))
@login_required
def comment_post(id):
    pid = id
    uid = g.user['id']
    db = get_db()
    post = db.execute(
        'SELECT p.id, title, body, created_time, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
    ).fetchone()
    if request.method == 'POST':
        content = request.form['content']
        error = None

        if not content:
            error = 'Content is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO Comment (pid, uid, content) VALUES (?, ?, ?)',
                (pid, uid, content)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/comment.html',post=post)
