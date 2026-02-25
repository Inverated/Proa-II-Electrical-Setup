import ngrok
import time

import requests

ngrok.set_auth_token("3A9A4WJayeZ9dXQ8w6NPxqhW0zX_5BMUbqdzE4gKJMHQHBi9J") 

def main():
    
    listener = ngrok.forward(5000)

    # Output the public ngrok URL
    print(f"Ingress established at {listener.url()}")

    # Keep the listener alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Closing listener")
        ngrok.disconnect()

if __name__ == "__main__":
    main()