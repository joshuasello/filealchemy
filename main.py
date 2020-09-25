"""
Title: File Alchemy
Version: 1.0.0
Description:
    Lorem ipsrum
"""
from flaskr import create_app


def main():
    print("Running Web app.")
    # Run the main Flask application
    create_app().run(host='localhost', port=5050, debug=True)


if __name__ == '__main__':
    main()
