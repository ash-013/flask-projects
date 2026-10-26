from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.orm import Mapped, mapped_column

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///todo.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Todo(db.Model):
    __tablename__ = "todos"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(nullable=False)
    completed: Mapped[bool] = mapped_column(default=False)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'completed': self.completed
        }

    def __repr__(self) -> str:
        return f"Todo {self.title}"


with app.app_context():
    @event.listens_for(db.engine, "connect")
    def set_sqlite_pragma(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA synchronous=NORMAL")
        cur.close()
    db.create_all()


@app.route('/')
def home():
    return render_template("index.html")


@app.route('/todos', methods=['POST'])
def add_todos():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({
            'message': "Request body must be a JSON object"
        }), 400

    title = data.get('title')

    if not isinstance(title, str) or not title.strip():
        return jsonify({
            'message': "Title is required and must be a non-empty string"
        }), 400
    todo = Todo(title=title.strip())

    db.session.add(todo)
    db.session.commit()
    return jsonify({
        'message': "TODO added successfully",
        'todo': {
            'id': todo.id,
            'title': todo.title,
            'completed': todo.completed
        }
    }), 201


@app.route('/todos/<int:id>', methods=['PUT'])
def update_todo(id):
    todo = db.session.get(Todo, id)
    if not todo:
        return jsonify({
            'message': "Todo not found"
        }), 404

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({
            'message': "Request body must be a JSON object"
        }), 400

    title = data.get("title")

    if title is not None:
        if not isinstance(title, str) or not title.strip():
                return jsonify({
                    'message': "Title must be a non-empty string"
                }), 400
        todo.title = title.strip()

    completed = data.get("completed")
    if completed is not None:
        if not isinstance(completed, bool):
            return jsonify({
                'message': "Completed must be True/False"
            }), 400
        todo.completed = completed

    db.session.commit()
    return jsonify({
        'message': "TODO updated successfully",
        'todo': {
            'id': todo.id,
            'title': todo.title,
            'completed': todo.completed
        }
    }), 200

@app.route('/todos', methods=['GET'])
def get_todos():
    todos = db.session.execute(
        db.select(Todo).order_by(Todo.id.desc())
    ).scalars().all()
    return jsonify({
        'todos': [todo.to_dict() for todo in todos]
    }), 200


@app.route('/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    todo = db.session.get(Todo, todo_id)
    if not todo:
        return jsonify({
            'message': "TODO not found"
        }), 404
    db.session.delete(todo)
    db.session.commit()

    return jsonify({
        'message': "Todo deleted successfully"
    }), 200


if __name__ == '__main__':
    app.run(debug=True, port=5001)
