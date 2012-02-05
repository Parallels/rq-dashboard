import sys
from app import app

def main(argv):
    host = '127.0.0.1'
    port = 9181
    app.run(host=host, port=port)

if __name__ == '__main__':
    main(sys.argv)
