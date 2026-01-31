# -*- coding: utf-8 -*-
import crossplane


def test_state_directive():
    fname = '/path/to/nginx.conf'

    stmt = {
        'directive': 'state',
        'args': ['/path/to/state/file.conf'],
        'line': 5  # this is arbitrary
    }

    # the state directive should not cause errors if it's in these contexts
    good_contexts = set([
        ('http', 'upstream'),
        ('stream', 'upstream'),
        ('some_third_party_context',)
    ])

    for ctx in good_contexts:
        crossplane.analyzer.analyze(fname, stmt, term=';', ctx=ctx)

    # the state directive should not be in any of these contexts
    bad_contexts = set(crossplane.analyzer.CONTEXTS) - good_contexts

    for ctx in bad_contexts:
        try:
            crossplane.analyzer.analyze(fname, stmt, term=';', ctx=ctx)
            raise Exception("bad context for 'state' passed: " + repr(ctx))
        except crossplane.errors.NgxParserDirectiveContextError:
            continue


def test_flag_directive_args():
    fname = '/path/to/nginx.conf'
    ctx = ('events',)

    # an NGINX_CONF_FLAG directive
    stmt = {
        'directive': 'accept_mutex',
        'line': 2  # this is arbitrary
    }

    good_args = [['on'], ['off'], ['On'], ['Off'], ['ON'], ['OFF']]

    for args in good_args:
        stmt['args'] = args
        crossplane.analyzer.analyze(fname, stmt, term=';', ctx=ctx)

    bad_args = [['1'], ['0'], ['true'], ['okay'], ['']]

    for args in bad_args:
        stmt['args'] = args
        try:
            crossplane.analyzer.analyze(fname, stmt, term=';', ctx=ctx)
            raise Exception('bad args for flag directive: ' + repr(args))
        except crossplane.errors.NgxParserDirectiveArgumentsError as e:
            assert e.strerror.endswith('it must be "on" or "off"')


def test_map_freeform_directives():
    """Test that arbitrary directives are allowed inside map blocks."""
    fname = '/path/to/nginx.conf'
    ctx = ('http', 'map')

    # test various map entries that would fail if treated as regular directives
    freeform_stmts = [
        {'directive': 'default', 'args': ['0'], 'line': 1},
        {'directive': '~^/news', 'args': ['1'], 'line': 2},
        {'directive': '*.example.com', 'args': ['backend1'], 'line': 3},
        {'directive': 'hostnames', 'args': [], 'line': 4},
        {'directive': '/api', 'args': ['api_backend'], 'line': 5},
    ]

    for stmt in freeform_stmts:
        # should not raise any errors even in strict mode
        crossplane.analyzer.analyze(fname, stmt, term=';', ctx=ctx, strict=True)


def test_types_freeform_directives():
    """Test that arbitrary MIME type directives are allowed inside types blocks."""
    fname = '/path/to/nginx.conf'
    ctx = ('http', 'types')

    # test various types entries that would fail if treated as regular directives
    freeform_stmts = [
        {'directive': 'text/html', 'args': ['html', 'htm'], 'line': 1},
        {'directive': 'text/css', 'args': ['css'], 'line': 2},
        {'directive': 'application/javascript', 'args': ['js'], 'line': 3},
        {'directive': 'image/png', 'args': ['png'], 'line': 4},
    ]

    for stmt in freeform_stmts:
        # should not raise any errors even in strict mode
        crossplane.analyzer.analyze(fname, stmt, term=';', ctx=ctx, strict=True)


def test_geo_freeform_directives():
    """Test that arbitrary directives are allowed inside geo blocks."""
    fname = '/path/to/nginx.conf'
    ctx = ('http', 'geo')

    freeform_stmts = [
        {'directive': 'default', 'args': ['0'], 'line': 1},
        {'directive': '127.0.0.1', 'args': ['1'], 'line': 2},
        {'directive': '10.0.0.0/8', 'args': ['internal'], 'line': 3},
    ]

    for stmt in freeform_stmts:
        crossplane.analyzer.analyze(fname, stmt, term=';', ctx=ctx, strict=True)


def test_charset_map_freeform_directives():
    """Test that arbitrary directives are allowed inside charset_map blocks."""
    fname = '/path/to/nginx.conf'
    ctx = ('http', 'charset_map')

    freeform_stmts = [
        {'directive': '2F', 'args': ['/', '%2F'], 'line': 1},  # hex code mappings
    ]

    for stmt in freeform_stmts:
        crossplane.analyzer.analyze(fname, stmt, term=';', ctx=ctx, strict=True)
