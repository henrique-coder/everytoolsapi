import flask


app = flask.current_app


class APIVersion:
    class Latest:
        def __init__(self):
            self.version = 'v2'
