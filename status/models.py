
class StatusEntry(object):

    def __init__(self, name, status, error, errorMsg):
        self.name = name
        self.status = status
        self.error = error
        self.errorMsg = errorMsg


class TransInstanceStatus(object):
    def __init__(self, name, host, port, peer_port, username, downloadPath, error, errorMsg):
        self.name = name
        self.host = host
        self.port = port
        self.peer_port = peer_port
        self.username = username
        self.downloadPath = downloadPath
        self.error = error
        self.errorMsg = errorMsg
