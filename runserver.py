import sys
from app import app

def main(argv):
    host = '0.0.0.0'
    port = 9181
    app.run(host=host, port=port)

if __name__ == '__main__':
    main(sys.argv)
