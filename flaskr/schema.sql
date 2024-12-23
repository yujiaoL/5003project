DROP TABLE IF EXISTS User;
DROP TABLE IF EXISTS Post;
DROP TABLE IF EXISTS Tag;
DROP TABLE IF EXISTS Post_Tag;
DROP TABLE IF EXISTS Like;
DROP TABLE IF EXISTS Comment;
DROP TABLE IF EXISTS Categories;
DROP TABLE IF EXISTS PostCategory;



CREATE TABLE User
(
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT        NOT NULL,
    permission INTEGER
);

CREATE TABLE Post
(
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    author_id INTEGER   NOT NULL,
    created_time   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    title     TEXT      NOT NULL,
    body      TEXT      NOT NULL,
    FOREIGN KEY (author_id) REFERENCES User (id)
);

CREATE TABLE Tag
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE Post_Tag
(
    pid INTEGER,
    tid INTEGER,
    PRIMARY KEY(pid,tid),
    FOREIGN KEY (pid) REFERENCES Post (id),
    FOREIGN KEY (tid) REFERENCES Tag (id)
);

CREATE TABLE Like
(
    pid INTEGER,
    uid INTEGER,
    PRIMARY KEY(pid,uid),
    FOREIGN KEY (pid) REFERENCES Post (id),
    FOREIGN KEY (uid) REFERENCES User (id)

);

CREATE TABLE Comment
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pid INTEGER,
    uid INTEGER,
    content TEXT,
    parent_id INTEGER,
    comment_time  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pid) REFERENCES Post (id),
    FOREIGN KEY (uid) REFERENCES User (id),
    FOREIGN KEY (parent_id) REFERENCES Comment (id)
);
CREATE TABLE Categories (
    CategoryID INTEGER PRIMARY KEY AUTOINCREMENT,
    CategoryName VARCHAR(255) NOT NULL,
    UserID INT NOT NULL,
    FOREIGN KEY (UserID) REFERENCES User(id)
);

CREATE TABLE PostCategory (
    PostID INTEGER,
    CategoryID INTEGER,
    PRIMARY KEY (PostID, CategoryID),
    FOREIGN KEY (PostID) REFERENCES Post(id),
    FOREIGN KEY (CategoryID) REFERENCES Categories(CategoryID)
);
