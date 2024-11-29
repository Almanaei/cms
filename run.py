from app import create_app, db
from app.models import User, Post, Category

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Post': Post,
        'Category': Category
    }

if __name__ == '__main__':
    app.run(debug=True)