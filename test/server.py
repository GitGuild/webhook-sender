import flask

def create_app():
    app = flask.Flask(__name__)
    @app.route('/wh', methods=['POST'])
    def wh():
        data = flask.request.get_data()
        if data and data != "badmessage":
            return "", 200
        return "error", 400
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(port=8001)

