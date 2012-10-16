#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Copyright 2012 posativ <info@posativ.org>. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
# The views and conclusions contained in the software and documentation are
# those of the authors and should not be interpreted as representing official
# policies, either expressed or implied, of posativ <info@posativ.org>.
#
# lightweight Disqus alternative

__version__ = '0.1'

import json

from werkzeug.routing import Map, Rule
from werkzeug.serving import run_simple
from werkzeug.wrappers import Request, Response
from werkzeug.exceptions import HTTPException, NotFound, NotImplemented, InternalServerError

from isso import admin, comment, db, utils


_dumps = json.dumps
setattr(json, 'dumps', lambda obj: _dumps(obj, cls=utils.IssoEncoder))


url_map = Map([
    # moderation panel
    Rule('/', endpoint='admin.index', methods=['GET', 'POST']),

    # comments API
    Rule('/comment/<string:path>/', endpoint='comment.get'),
    Rule('/comment/<string:path>/new', endpoint='comment.create', methods=['POST']),
    Rule('/comment/<string:path>/<int:id>', endpoint='comment.get'),
    Rule('/comment/<string:path>/<int:id>', endpoint='comment.modify',
        methods=['PUT', 'DELETE']),
])


class Isso:

    def __init__(self, conf):
        self.conf = conf
        self.db = db.SQLite(conf)

    def dispatch(self, request, start_response):
        adapter = url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            module, function = endpoint.split('.', 1)
            handler = getattr(globals()[module], function)
            return handler(self, request.environ, request, **values)
        except NotFound, e:
            return Response('Not Found', 404)
        except HTTPException, e:
            return e
        except InternalServerError, e:
            return Response(e, 500)

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch(request, start_response)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)


def main():

    app = Isso({'SQLITE': '/tmp/sqlite.db'})
    run_simple('127.0.0.1', 8080, app)