from tornado.options import define, options
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import mailer, db, ratelimit, config
from email.utils import parseaddr
import os, uuid, socket, struct

# application URLs
_BASE_URL = ('https' if config.SSL_ENABLED else 'http') + '://' + config.HOST + '/'
_REDIRECT_IMG = 'get_cookie.png'
_LANDING_IMG = 'image.png'
_REDIRECT_LINK = 'click'
_LANDING_LINK = 'landing_page'
_COOKIE_NAME = 'uuid'

# command-line argument definitions
define('port', default=(443 if config.SSL_ENABLED else 80), help='server port', type=int)
define('debug', default=False, help='enable debug mode', type=bool)

class Application(tornado.web.Application):
    def __init__(self, debug):
        root = os.path.dirname(__file__)
        static_path = os.path.join(root, 'static')
        template_path = os.path.join(root, 'templates')
        settings = {
            'debug': debug,
            'compress_response': True,
            'template_path': template_path,
        }

        # routes
        handlers = [
            (r'/submit', FormHandler),
            (r'/results/?', ResultsSummaryHandler),
            (r'/results/([0-9a-fA-F-]+)/?', ResultsHandler),
            (r'/tracking/([0-9a-fA-F-]+)/([A-Za-z0-9._-]+)/?', TrackingHandler),
            (r'/unsubscribe/([0-9a-fA-F-]+)/?', BlacklistHandler),
            (r'/privacy/?', PrivacyHandler),
            (r'/', MainHandler),
            (r'/(.*)', StaticHandler, {'path': static_path}),
        ]

        # database instance
        self.db = db.MailerDatabase(config.DB_PATH)

        # rate limiters
        self.global_limiter = ratelimit.Bucket(**config.GLOBAL_RATE_LIMIT)
        self.ip_limiters = {}

        tornado.web.Application.__init__(self, handlers, **settings)

class StaticHandler(tornado.web.StaticFileHandler):
    def set_default_headers(self):
        try:
            del self._headers['Server']
        except:
            pass

    def write_error(self, status_code, *args, **kwargs):
        self.set_status(404)
        self.finish()

class BaseHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        try:
            del self._headers['Server']
        except:
            pass

    def options(self):
        self.set_status(204)
        self.finish()

class MainHandler(BaseHandler):
    def get(self):
        self.render('index.html')

class PrivacyHandler(BaseHandler):
    def get(self):
        self.render('privacy.html')

class ResultsSummaryHandler(BaseHandler):
    def get(self):
        # get user info
        summary = self.application.db.get_user_summary()

        # categorize by platform and client
        data = {}
        for row in summary:
            platform_data = data.setdefault(row['platform'], {})
            client_data = platform_data.setdefault(row['client'], [])
            client_data.append({'id': row['id'], 'timestamp': row['timestamp']})

        # sort data
        sorted_data = []
        for platform, name in (('web', 'Web'), ('desktop', 'Desktop'), ('mobile', 'Mobile')):
            if platform not in data:
                continue

            sorted_clients = []
            platform_data = data[platform]
            for client in sorted(platform_data, key=lambda s: s.lower()):
                client_data = list(reversed(platform_data[client]))
                sorted_clients.append((client, client_data))
            sorted_data.append((name, sorted_clients))

        # render page
        self.render('summary.html', data=sorted_data)

class ResultsHandler(BaseHandler):
    def __generate_summary(self, id, requests):
        summary = [
            {
                'text': ['Loads Images', 'Blocks Images'],
                'tooltip': [
                    'The email client loaded our tracking images.',
                    'The email client blocked all of our tracking images.'
                ],
                'icon': 'glyphicon-picture',
                'flag': False,
            },
            {
                'text': ['Uses Image Proxy', 'No Image Proxy'],
                'tooltip': [
                    'All tracking images were fetched through a proxy server (improving the user\'s privacy).',
                    'Some tracking images were loaded by the user\'s client directly (not through a proxy server).',
                ],
                'icon': 'glyphicon-random',
                'flag': False,
            },
            {
                'text': ['Sends Cookies', 'No Cookies'],
                'tooltip': [
                    'HTTP cookies were set in an initial tracking request and sent back in another request.',
                    'No HTTP cookies were received from any tracking hits.'
                ],
                'icon': 'glyphicon-record',
                'flag': False,
            },
            {
                'text': ['Sends Referrer', 'No Referrer'],
                'tooltip': [
                    'The email client sent the originating page URL in a tracking request.',
                    'The originating page URL was not sent in any tracking requests.'
                ],
                'icon': 'glyphicon-file',
                'flag': False,
            },
        ]

        # compute the flags above
        expected_cookie = _COOKIE_NAME + '=' + id
        user_agent_img = []
        user_agent_link = set()
        ip_img = []
        ip_link = set()
        for req in requests:
            if req['type'] == 'redirect_image' or req['type'] == 'landing_image':
                summary[0]['flag'] = True
                ip_img.append(req['ip'])
            elif req['type'] == 'link':
                ip_link.add(req['ip'])
            for k, v in req['headers'].iteritems():
                if k == 'User-Agent':
                    if v:
                        if req['type'] == 'redirect_image' or req['type'] == 'landing_image':
                            user_agent_img.append(v)
                        elif req['type'] == 'link':
                            user_agent_link.add(v)
                elif k == 'Cookie':
                    if v == expected_cookie:
                        summary[2]['flag'] = True
                elif k == 'Referer':
                    if v:
                        summary[3]['flag'] = True
        if not summary[0]['flag']:
            # no images loaded, don't show image proxy status
            del summary[1]
        else:
            # check if image proxy used:
            # none of the user-agents and IPs for images match those of links
            if user_agent_img and user_agent_link:
                uses_image_proxy = True
                for img_agent in user_agent_img:
                    if img_agent in user_agent_link:
                        uses_image_proxy = False
                        break
                if uses_image_proxy:
                    for img_ip in ip_img:
                        if img_ip in ip_link:
                            uses_image_proxy = False
                            break
                    if uses_image_proxy:
                        summary[1]['flag'] = True
        return summary

    def get(self, id):
        # get user info
        user = self.application.db.get_user_by_id(id)
        if not user:
            self.set_status(403)
            self.finish()
            return

        user.pop('id', None)
        user.pop('tracking_id', None)

        # get user requests
        requests = self.application.db.get_requests(id)

        # hide email address
        if 'email' in user:
            index = user['email'].rfind('@')
            user['email'] = '********' + user['email'][index:]

        # generate summary
        summary = self.__generate_summary(id, requests)

        # render page
        self.render('results.html', id=id, user=user, requests=requests, summary=summary)

class FormHandler(BaseHandler):
    def __ip_to_long(self, ip):  # https://stackoverflow.com/a/9591005
        packed_ip = socket.inet_aton(ip)
        return struct.unpack("!L", packed_ip)[0]

    def get(self):
        self.set_status(403)
        self.finish()

    def post(self):
        # get form fields
        email = self.get_argument('email')
        client = self.get_argument('client')
        platform = self.get_argument('platform')
        ip = self.request.remote_ip
        print('Sending email to %s [%s: %s]...' % (email, platform, client))

        # validate email address (kind of)
        email_parsed = parseaddr(email)[1]
        if '@' not in email_parsed:
            error = 'The email address <code>' + email + '</code> is invalid.'
            self.render('submit.html', success=False, email=email, error=error, results=None)
            return

        # check if email address is blacklisted
        if self.application.db.is_blacklisted(email_parsed):
            error = 'We aren\'t able to send emails to that address. Sorry!'
            self.render('submit.html', success=False, email=email, error=error, results=None)
            return

        # check per-IP rate limit
        try:
            ip_key = self.__ip_to_long(ip)  # convert to number to save space
        except:
            ip_key = ip
        ip_limiter = self.application.ip_limiters.setdefault(ip_key, ratelimit.Bucket(**config.IP_RATE_LIMIT))
        if not ip_limiter.get():
            error = 'We\'re receiving too many form submissions from your IP address (' + ip + '). Please wait a minute and try again.'
            self.render('submit.html', success=False, email=email, error=error, results=None)
            return

        # check global rate limit
        if not self.application.global_limiter.get():
            error = 'Sorry! We\'ve exceeded our capacity for sending emails. Please try again in a few minutes!'
            self.render('submit.html', success=False, email=email, error=error, results=None)
            return

        # reduce rate limiter tokens
        self.application.global_limiter.reduce(1)
        ip_limiter.reduce(1)

        # create an unused ID
        while True:
            id = str(uuid.uuid4())
            tracking_id = str(uuid.uuid4())
            if self.application.db.add_user(id, tracking_id, email_parsed, client, platform, ip):
                break

        # construct links
        img_url = _BASE_URL + 'tracking/' + tracking_id + '/' + _REDIRECT_IMG
        link_url = _BASE_URL + 'tracking/' + tracking_id + '/' + _REDIRECT_LINK
        results_url = _BASE_URL + 'results/' + id
        unsubscribe_url = _BASE_URL + 'unsubscribe/' + tracking_id

        # send email
        try:
            mailer.Mailer(config.MAILER_SETTINGS).send(email_parsed, img_url, link_url, results_url, unsubscribe_url)
            success = True
        except Exception as e:
            print(e)
            success = False
        self.render('submit.html', success=success, email=email_parsed, error=None)

class BlacklistHandler(BaseHandler):
    def get(self, tracking_id):
        # check if user exists
        user = self.application.db.get_user_by_tracking_id(tracking_id)
        if not user:
            self.set_status(403)
            self.finish()
            return

        # blacklist the user
        self.application.db.add_to_blacklist(user['email'])
        self.render('unsubscribe.html')

class TrackingHandler(BaseHandler):
    def __save_headers(self, id, type):
        list = ['Cookie', 'Referer', 'User-Agent']
        headers = {k:self.request.headers.get(k, None) for k in list}
        ip = self.request.remote_ip
        self.application.db.add_request(id, type, ip, headers)

    def get(self, tracking_id, path):
        # check if user exists
        user = self.application.db.get_user_by_tracking_id(tracking_id)
        if not user:
            self.set_status(403)
            self.finish()
            return

        id = user['id']

        # print headers (debug)
        print("\n----- Request Start ----->")
        for (k,v) in sorted(self.request.headers.get_all()):
            print('%s: %s' % (k,v))
        print("<----- Request End -----\n")

        if path == _REDIRECT_IMG:
            self.__save_headers(id, 'redirect_image')

            # set cookie and redirect
            self.set_status(302)
            self.set_header('Location', '/tracking/' + tracking_id + '/' + _LANDING_IMG)
            self.set_header('Set-Cookie', _COOKIE_NAME + '=' + id)
            self.finish()
        elif path == _LANDING_IMG:
            self.__save_headers(id, 'landing_image')

            # send image
            self.set_status(200)
            self.set_header('Content-Type', 'image/png');
            with open('image.png', 'rb') as f:
                self.write(f.read())
            self.finish()
        elif path == _REDIRECT_LINK:
            self.__save_headers(id, 'link')

            # save click
            self.application.db.save_click(id)

            # redirect
            self.set_status(302)
            self.set_header('Location', '/tracking/' + tracking_id + '/' + _LANDING_LINK)
            self.finish()
        elif path == _LANDING_LINK:
            # show success page
            self.render('click.html')
        else:
            self.set_status(404)
            self.finish()

def main():
    tornado.options.parse_command_line()
    application = Application(options.debug)
    ssl_options = None if not config.SSL_ENABLED else {
        'certfile': config.SSL_CERTFILE,
        'keyfile': config.SSL_KEYFILE,
    }
    http_server = tornado.httpserver.HTTPServer(application, ssl_options=ssl_options)
    http_server.listen(options.port)
    print 'Listening on port %d...' % options.port
    try:
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        tornado.ioloop.IOLoop.instance().stop()

if __name__ == "__main__":
    main()
