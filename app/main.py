import os
import logging
import httpx
import json
from app.whatsapp import WhatsApp
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, status

# Initialize FastAPI app
app = FastAPI()

# Load .env file
load_dotenv()
token = os.getenv("TOKEN")
secret_token = os.getenv("APP_SECRET")

whatsapp = WhatsApp(token, phone_number_id=os.getenv("PHONE_NUMBER_ID"))
telegram = None
messenger = None
instagram = None

# Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Verify the callback URL from the dashboard (cloud API side)
@app.get("/facebook")
async def verify_facebook_callback(mode: str, challenge: str, verify_token: str):
    if mode and verify_token:
        if mode == "subscribe" and verify_token == token:
            return Response(content=challenge, status_code=status.HTTP_200_OK)
        else:
            return Response(status_code=status.HTTP_403_FORBIDDEN)

# Webhook will always listen
# If a business sends a message from the dashboard:
#   - call the handle_facebook_post to send the message to the user and add message to database
# If a business sends a message from the Whatsapp app:
#   - call the handle_facebook_post to retrieve the sent message and add message to database
# Status update (read, delivered, sent)
# If the user sends a message to the business:
#   - call the handle_facebook_post to retrieve the sent message and add message to database
@app.post("/facebook")
async def handle_facebook_post(request: Request):
    raw_body = await request.body()
    body_param = json.loads(raw_body.decode("utf-8"))

    print("Request received. Request body:")
    print(body_param)

    if body_param["object"]:
        entry = body_param["entry"][0]
        changes = entry["changes"][0]
        
        if "messages" not in changes:
            pass # Message came from the business
        
        else:

            message = changes["messages"][0]

        if message:
            phone_number_id = changes["value"]["metadata"]["phone_number_id"]
            sender = message["from"]
            msg_body = message.get("text", {}).get("body", "")

            print(f"phone number {phone_number_id}")
            print(f"from {sender}")
            print(f"body param {msg_body}")

            async with httpx.AsyncClient() as client:
                await client.post(
                    f"https://graph.facebook.com/v18.0/{phone_number_id}/messages?access_token={token}",
                    json={
                        "messaging_product": "whatsapp",
                        "to": sender,
                        "text": {"body": f"Hello, I'm Davyn. Your message is {msg_body}"}
                    },
                    headers={"Content-Type": "application/json"}
                )
            
            return Response(status_code=status.HTTP_200_OK)
    return Response(status_code=status.HTTP_404_NOT_FOUND)

@app.post("/wadashboard")
def read_root():
    return {"Hello": "World"}

if __name__ == "__main__":
    app.run(port=5000, debug=False)