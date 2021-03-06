"""Various auxillary functions for tsweb Web Application"""

from flask import redirect, render_template
from pygments.lexers import guess_lexer
from pygments.formatters import HtmlFormatter
from pygments import highlight as p_highlight
from BeautifulSoup import BeautifulSoup as bs

from tsweb import testsys

def redirector(url, **kwargs):
    """Render custom redirection (HTTP 302) response, passing *kwargs* to
    'redirect.html'"""
    res = redirect(url)
    res.response = [render_template("redirect.html", **kwargs)]

    return res

def login_error():
    """Return error about missing or expired login data"""
    return render_template("error.html",
        text="Login error: session data missing or expired",
        title="Authentification Error")

def error(msg):
    """Return generaral error using *msg* as it's message"""
    return render_template("error.html", text=msg)

def testsys_error(msg):
    """Return TestSys error, using *msg* as message"""
    return render_template("error.html",
        text="TestSys reports following error: {0}".format(msg) if msg
            else "TestSys reports unknown error",
        title="TestSys error")

def communicate(chan, request=None, check_empty=True):
    """Send request to testsys and get response. It returns tuple (state, answer),
    where *state* can be 'error' or 'ok. If state == 'error', *answer* contains
    formatted error message. If state == 'ok', answer contains tuple (answer, id).
    This function can be used in many ways:
    * providing a symbolic channel name as *channel*, e.g. 'MSG', and dict as
    *request*. This way it will open channel with that name, send request,
    return response and close channel.
    * providing :py:class:`testsys.Channel` as *channel* and dict as *request*.
    This way it will do the same, but on existing channel and will not close it
    at the end.
    * providing :py:class:`testsys.Channel` as *channel* and **None** as
    *request*. This way it will try to recieve something from *channel* and
    return the response.
    Optional *check_empty* arguments specifies whether the response should be
    checked for emptyness"""
    if isinstance(chan, testsys.Channel):
        channel = chan
        need_close = False
    else:
        channel = testsys.get_channel(chan)
        try:
            channel.open(1)
        except testsys.ConnectionFailedException as ex:
            return ('error', error(ex.message))
        need_close = True

    if request:
        try:
            ans_id = channel.send(request)
        except testsys.CommunicationException as ex:
            return ('error', error(ex.message))
    else:
        ans_id = 0
 
    answer = channel.recv()
    if not answer and check_empty:
        return ('error', error("Empty response from testsys"))
    if 'Error' in answer:
        return ('error', testsys_error(answer['Error']))
 
    if need_close:
        channel.close()

    return ('ok', (answer, ans_id))

def highlight(text):
    """Guess language in *text* and return its html highlighted version"""
    lexer = guess_lexer(text)
    return p_highlight(text, lexer, HtmlFormatter(full=True, style='manni'))

def parse_contests(text):
    """Parse raw html contests data in *text* to list of dictionaries with
    following keys:
    * id
    * statements
    * name
    * state
    * startedat
    * teams"""
    soup = bs(text)
    contests = []
    for row in soup('tr'):
        contest = {}
        tds = row('td')
        contest['id'] = tds[0].getText()
        link = tds[1]('a')[0]
        contest['statements'] = link['href']
        contest['name'] = link.getText()
        contest['state'] = tds[2].getText()
        contest['startedat'] = tds[3].getText()
        contest['teams'] = tds[4].getText()
        contests.append(contest)
    return contests
