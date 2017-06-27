import sqlite3, json, os

class MailerDatabase:
    def __init__(self, path):
        self.__db = sqlite3.connect(path)
        self.__db.execute('CREATE TABLE IF NOT EXISTS `users` (`id` TEXT PRIMARY KEY, `tracking_id` TEXT UNIQUE, `email` TEXT, `client` TEXT, `platform` TEXT, `ip` TEXT, `timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP, `clicked` INTEGER NOT NULL DEFAULT 0)')
        self.__db.execute('CREATE TABLE IF NOT EXISTS `requests` (`id` TEXT, `type` TEXT, `ip` TEXT, `headers` TEXT, `timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
        self.__db.execute('CREATE TABLE IF NOT EXISTS `blacklist` (`email` TEXT PRIMARY KEY, `timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
        self.__db.commit()

    def close(self):
        self.__db.close()

    def add_user(self, id, tracking_id, email, client, platform, ip):
        sql = 'INSERT INTO `users` (`id`, `tracking_id`, `email`, `client`, `platform`, `ip`) VALUES (?, ?, ?, ?, ?, ?)'
        try:
            self.__db.execute(sql, (id, tracking_id, email, client, platform, ip))
            self.__db.commit()
            return True
        except IntegrityError:  # picked a non-unique id
            return False

    def add_request(self, id, type, ip, headers):
        sql = 'INSERT INTO `requests` (`id`, `type`, `ip`, `headers`) VALUES (?, ?, ?, ?)'
        self.__db.execute(sql, (id, type, ip, json.dumps(headers)))
        self.__db.commit()

    def save_click(self, id):
        sql = 'UPDATE `users` SET `clicked` = 1 WHERE `id` = ?'
        self.__db.execute(sql, (id,))
        self.__db.commit()

    def add_to_blacklist(self, email):
        sql = 'INSERT OR IGNORE INTO `blacklist` (`email`) VALUES (?)'
        self.__db.execute(sql, (email,))
        self.__db.commit()

    def get_user_by_id(self, id):
        sql = 'SELECT * FROM `users` WHERE `id` = ?'
        rows = self.__db.execute(sql, (id,)).fetchall()
        return self.__get_user(rows[0]) if rows else {}

    def get_user_by_tracking_id(self, tracking_id):
        sql = 'SELECT * FROM `users` WHERE `tracking_id` = ?'
        rows = self.__db.execute(sql, (tracking_id,)).fetchall()
        return self.__get_user(rows[0]) if rows else {}

    def __get_user(self, r):
        return {'id': r[0], 'tracking_id': r[1], 'email': r[2], 'client': r[3], 'platform': r[4], 'ip': r[5], 'timestamp': r[6], 'clicked': r[7]}

    def get_requests(self, id):
        sql = 'SELECT * FROM `requests` WHERE `id` = ? LIMIT 1000'
        rows = self.__db.execute(sql, (id,)).fetchall()
        return [{'type': r[1], 'ip': r[2], 'headers': json.loads(r[3]), 'timestamp': r[4]} for r in rows] if rows else []

    def get_user_summary(self):
        sql = 'SELECT `id`, `client`, `platform`, `timestamp` FROM `users` WHERE `clicked` = 1'
        rows = self.__db.execute(sql).fetchall()
        return [{'id': r[0], 'client': r[1], 'platform': r[2], 'timestamp': r[3]} for r in rows] if rows else []

    def is_blacklisted(self, email):
        sql = 'SELECT COUNT(1) FROM `blacklist` WHERE `email` = ? LIMIT 1'
        rows = self.__db.execute(sql, (email,)).fetchall()
        return True if rows and rows[0] and rows[0][0] else False
