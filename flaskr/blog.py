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
    query = '''
            SELECT 
                p.id,
                p.title,
                p.body,
                u.username,
                p.created_time,
                p.author_id,
                COUNT(DISTINCT l.uid) AS like_count,
                COUNT(DISTINCT c.id) AS comment_count
            FROM Post p
            LEFT JOIN User u ON p.author_id = u.id
            LEFT JOIN Like l ON p.id = l.pid
            LEFT JOIN Comment c ON p.id = c.pid
            GROUP BY p.id, u.username
            ORDER BY p.created_time DESC
        '''
    posts = db.execute(query).fetchall()
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
        search_results = get_db().execute(
            '''
            SELECT p.id, title, body, created_time, author_id, username,
                   COUNT(DISTINCT l.uid) AS like_count,
                   COUNT(DISTINCT c.id) AS comment_count
            FROM post p
            JOIN user u ON p.author_id = u.id
            LEFT JOIN Like l ON p.id = l.pid
            LEFT JOIN Comment c ON p.id = c.pid
            WHERE p.title LIKE ?
            GROUP BY p.id, u.username
            ORDER BY p.created_time DESC
            ''',
            (f"%{title}%",)
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


@bp.route('/<int:id>/like', methods=['POST', 'GET'])
@login_required
def like_post(id):
    db = get_db()
    pid = id
    uid = g.user['id']

    like = db.execute(
        'SELECT * FROM Like WHERE pid = ? AND uid = ?',
        (pid, uid)
    ).fetchone()

    if like:
        # cancel like
        db.execute(
            'DELETE FROM Like WHERE pid = ? AND uid = ?',
            (pid, uid)
        )
    else:
        # like
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
        ' WHERE p.id = ?',
        (pid,)
    ).fetchone()
    comments = db.execute(
        'SELECT c.content, c.comment_time, u.username, c.id, c.uid FROM Comment c JOIN user u ON c.uid = u.id WHERE pid = ?',
        (pid,)
    ).fetchall()
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

    return render_template('blog/comment.html', post=post, comments=comments)


@bp.route('/<int:id>/comment_delete', methods=('POST',))
@login_required
def comment_delete(id):
    db = get_db()
    db.execute('DELETE FROM Comment WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))

@bp.route('/tags', methods=('POST','GET'))
@login_required
def show_tags():
    db = get_db()
    tag_name = request.args.get('tag')
    print(tag_name)
    if tag_name:
        # selected tag post
        posts = db.execute(
            '''
            SELECT p.id, p.title, p.body, p.created_time, u.username
            FROM Post p
            JOIN User u ON p.author_id = u.id
            JOIN Post_Tag pt ON p.id = pt.pid
            JOIN Tag t ON pt.tid = t.id
            WHERE t.name = ?
            ORDER BY p.created_time DESC
            ''',
            (tag_name,)
        ).fetchall()
    else:
        # all posts
        posts = db.execute(
            '''
            SELECT p.id, p.title, p.body, p.created_time, u.username
            FROM Post p
            JOIN User u ON p.author_id = u.id
            ORDER BY p.created_time DESC
            '''
        ).fetchall()

    # all tags
    tags = db.execute(
        'SELECT name FROM Tag ORDER BY name ASC'
    ).fetchall()

    return render_template('blog/tag.html', posts=posts, tags=tags, current_tag=tag_name)


@bp.route('/tag_create', methods=('GET', 'POST'))
@login_required
def tag_create():
    if request.method == 'POST':
        db = get_db()
        name = request.form['name']
        description = request.form['description']
        error = None

        if not name:
            error = 'Tag name is required.'
        elif db.execute('SELECT * FROM Tag WHERE name = ?', (name,)).fetchone():
            error = 'Tag name is already taken.'
        if error is not None:
            flash(error)
        else:
            db.execute(
                'INSERT INTO Tag (name, description) VALUES (?, ?)',
                (name, description)
            )
            db.commit()
            return redirect(url_for('blog.show_tags'))

    return render_template('blog/create_tag.html')
