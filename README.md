# SDSC5003 Group Project
# Content
- [Implement function](#Implement-function)
- [Main technology stack](#Main-technology-stack)
- [Usage](#Usage)
# Implement function
## For user
1. Post Publishing:
   - Users can create and publish posts.
   - Likes: Users can like posts.
2. Bookmarks:
   - Users can bookmark posts to their personal collection.
   - The bookmark collection allows removal of posts.
3. Comments:
   - Users can comment under posts.
   - Users can also reply to existing comments.
4. Tags:
   - When publishing a post, users can create new tags or use previously created ones.
   - Description: Each tag can have a description to explain its use or relevance.
5. Search:
   - The platform supports searching by post title only, not including the content of the posts.

## For Admin
- Admins can view and search posts made by users.
- Admins have the authority to delete any posts or comments made by users.
- Default account:
   - username: `admin`
   - password: `admin5003`

# Main technology stack
1. Python 3.11
2. Flask
3. SQLite3
4. Jinjia

# Usage

Make sure Python is installed on your system; if it is not, follow the official documentation: [Python Official Download Page](https://www.python.org/downloads/)

Run the following command in the root directory

1. Install flask `pip install flask`
2. Initialize database    `flask --app flaskr init-db`
3. Run application      `flask  --app flaskr run --debug`

You can refer to the video [‘Instructions.mov’](Instructions.mov) in this project, for more information about the project's functionality.

