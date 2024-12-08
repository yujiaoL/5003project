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
    db = get_db()
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        tag_ids = request.form.getlist('tags')
        new_tag_name = request.form['new_tag'].strip()

        # create new post
        cursor = db.execute(
            'INSERT INTO Post (title, body, author_id) VALUES (?, ?, ?)',
            (title, body, g.user['id'])
        )
        post_id = cursor.lastrowid

        # existing tags
        for tag_id in tag_ids:
            db.execute(
                'INSERT INTO Post_Tag (pid, tid) VALUES (?, ?)',
                (post_id, tag_id)
            )

        # new tags
        if new_tag_name:
            # 检查新标签是否重复
            tag = db.execute('SELECT id FROM Tag WHERE name = ?', (new_tag_name,)).fetchone()
            if tag is None:
                tag_cursor = db.execute(
                    'INSERT INTO Tag (name) VALUES (?)',
                    (new_tag_name,)
                )
                new_tag_id = tag_cursor.lastrowid
            else:
                new_tag_id = tag['id']

            db.execute(
                'INSERT INTO Post_Tag (pid, tid) VALUES (?, ?)',
                (post_id, new_tag_id)
            )

        db.commit()
        return redirect(url_for('blog.index'))

    existing_tags = db.execute('SELECT id, name FROM Tag').fetchall()
    return render_template('blog/create.html', existing_tags=existing_tags)


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
    print(1)
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

@bp.route('/<int:id>/reply', methods=('POST',))
@login_required
def comment_reply(id):
    db = get_db()
    content = request.form['reply_content']
    uid = g.user['id']
    comment = db.execute('SELECT * FROM Comment WHERE id = ?', (id,)).fetchone()
    pid = comment['pid']
    if comment is None:
        abort(404, "Comment does not exist.")

    db.execute(
        'INSERT INTO Comment (parent_id, uid, pid, content) VALUES (?, ?, ?, ?)',
        (id, uid, pid, content)
    )
    db.commit()
    return redirect(url_for('blog.comment_post', id=comment['pid']))



@bp.route('/<int:id>/categories', methods=['GET', 'POST'])
@login_required
def categories(id):
    pid = id
    db = get_db()
    user_id = g.user['id']

    # 查询当前用户所有的分类
    categories = db.execute(
        '''
        SELECT CategoryID, CategoryName
        FROM Categories
        WHERE UserID = ?
        ORDER BY CategoryName ASC
        ''',
        (user_id,)
    ).fetchall()

    # 查询帖子详情
    post = db.execute(
        '''
        SELECT p.id, p.title, p.body, p.created_time, u.username
        FROM Post p
        JOIN User u ON p.author_id = u.id
        WHERE p.id = ?
        ''',
        (pid,)
    ).fetchone()

    if not post:
        # 如果没有找到这个帖子，可以抛出错误或者返回某个页面
        return "Post not found", 404

    # 处理POST请求，用户提交的分类
    if request.method == 'POST':
        # 获取用户选择的分类ID
        selected_categories = request.form.getlist('categories')  # 获取选择的现有分类列表

        # 获取用户输入的新分类
        new_category = request.form.get('new_category').strip()

        if new_category:
            # 检查新分类是否已经存在
            existing_category = db.execute(
                '''
                SELECT CategoryID
                FROM Categories
                WHERE UserID = ? AND CategoryName = ?
                ''',
                (user_id, new_category)
            ).fetchone()

            if existing_category:
                # 如果存在该分类，则返回错误消息
                flash('This category already exists.', 'error')
            else:
                # 如果不存在，插入新分类到 Categories 表
                db.execute(
                    '''
                    INSERT INTO Categories (CategoryName, UserID)
                    VALUES (?, ?)
                    ''',
                    (new_category, user_id)
                )
                db.commit()

                # 获取新插入的分类ID
                new_category_id = db.execute(
                    '''
                    SELECT CategoryID
                    FROM Categories
                    WHERE CategoryName = ? AND UserID = ?
                    ''',
                    (new_category, user_id)
                ).fetchone()['CategoryID']

                # 将帖子与新分类关联
                selected_categories.append(str(new_category_id))

        # 将帖子与所有选中的分类关联
        for category_id in selected_categories:
            db.execute(
                '''
                INSERT INTO PostCategory (PostID, CategoryID)
                VALUES (?, ?)
                ''',
                (pid, category_id)
            )
        db.commit()

        flash('Post updated with selected categories!', 'success')
        return redirect(url_for('blog.categories', id=pid))  # 重定向回当前页面

    return render_template('blog/categories.html', post=post, categories=categories)



@bp.route('/my_favorite', methods=['GET'])
@login_required
def my_favorite():
    db = get_db()
    user_id = g.user['id']  # 获取当前登录用户的 ID

    # 获取用户所有的分类
    categories = db.execute(
        '''
        SELECT c.CategoryID, c.CategoryName
        FROM Categories c
        WHERE c.UserID = ?
        ORDER BY c.CategoryName ASC
        ''',
        (user_id,)
    ).fetchall()

    # 获取每个分类下的收藏帖子
    favorites = {}
    for category in categories:
        category_id = category['CategoryID']
        category_name = category['CategoryName']

        # 获取该分类下所有已收藏的帖子
        posts_in_category = db.execute(
            '''
            SELECT p.id, p.title, p.body, p.created_time, u.username, u.id as author_id
            FROM Post p
            JOIN PostCategory pc ON p.id = pc.PostID
            JOIN User u ON p.author_id = u.id
            WHERE pc.CategoryID = ?
            ORDER BY p.created_time DESC
            ''',
            (category_id,)
        ).fetchall()

        # 将帖子按分类分组
        if posts_in_category:
            favorites[category_name] = {
                'category_id': category_id,
                'posts': posts_in_category
            }

    # 渲染模板并传递数据
    return render_template('blog/my_favorite.html', favorites=favorites)

@bp.route('/remove_from_favorites/<int:post_id>/<int:category_id>', methods=['POST'])
@login_required
def remove_from_favorites(post_id, category_id):
    db = get_db()
    user_id = g.user['id']

    # 1. 删除帖子与分类的关系
    db.execute(
        '''
        DELETE FROM PostCategory
        WHERE PostID = ? AND CategoryID = ? 
        ''',
        (post_id, category_id)
    )
    db.commit()

    # 2. 检查该分类下是否还有其他帖子
    remaining_posts = db.execute(
        '''
        SELECT COUNT(*) 
        FROM PostCategory
        WHERE CategoryID = ?
        ''',
        (category_id,)
    ).fetchone()

    # 如果该分类下没有帖子，删除该分类
    if remaining_posts[0] == 0:
        db.execute(
            '''
            DELETE FROM Categories
            WHERE CategoryID = ?
            ''',
            (category_id,)
        )
        db.commit()

    # 3. 提示用户操作成功
    flash('Post removed from favorites and category deleted if empty!', 'success')
    return redirect(url_for('blog.my_favorite'))