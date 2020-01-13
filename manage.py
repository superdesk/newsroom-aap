#!/usr/bin/env python

from flask_script import Manager
from newsroom.web import NewsroomWebApp

app = NewsroomWebApp(__name__)
manager = Manager(app)

if __name__ == "__main__":
    manager.run()
