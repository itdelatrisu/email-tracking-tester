# Email Tracking Tester
See how your email client protects your privacy (or not).

## Setup
Requires Python. To install dependencies, use pip:
```
$ pip install -r requirements.txt
```

Next, fill out `config.py` with your server/mailer details. You **must** set up
a publicly-reachable server and an [SSL certificate](https://letsencrypt.org/)
for accurate results, but the server will minimally function on `localhost`.

## Usage
Run the server:
```
$ python webserver.py
```

The server supports the following command-line options (displayed with `--help`):
* `--debug`: Enables debug mode.
* `--port=<port_number>`: Uses a non-default port number.

Note that in order to stop the server on Windows, you may need to press
`Ctrl`+`PauseBr` (instead of `Ctrl`+`C`).

## License
**This software is licensed under GNU GPL version 3.**
You can find the full text of the license [here](LICENSE).
