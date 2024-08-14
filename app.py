import asyncio
import json
import logging
import websockets
import pymongo
import streamlit as st
logging.basicConfig()

# MongoDB setup
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["student_management_db"]
code_sessions_collection = db["code_sessions"]
users_collection = db["users"]
notifications_collection = db["notifications_collection"]

USERS = {}  # Dictionary to store user IDs and their roles
USER_CONNECTIONS = {}  # Dictionary to store WebSocket connections by user ID
NOTIFICATIONS = ""  # Variable to store the latest notification
STUDENTS = set()
ADMINS = set()  # Set to store connected students

def users_event():
    return json.dumps({"type": "users", "count": len(ADMINS)})

def notifications_event():
    print(NOTIFICATIONS,"this")
    return json.dumps({"type": "notifications", "message": NOTIFICATIONS,"status":"unread"})

def students_event():
    #print("oki")
    return json.dumps({"type": "students", "count": len(STUDENTS)})

async def counter(websocket, path):
    global USERS, NOTIFICATIONS, STUDENTS, USER_CONNECTIONS
    try:
        
        # Register user and their role
        response = await websocket.recv()
        role_info = json.loads(response)
        user_id = role_info.get("user_id")
        role = role_info.get("role", "Student")
        #print(user_id)
        if not user_id:
            await websocket.close(code=4000)  # Close the connection if user_id is not provided
            return

        # Register user connections
        USERS[websocket] = (user_id, role)
        if user_id not in USER_CONNECTIONS:
            USER_CONNECTIONS[user_id] = set()
        USER_CONNECTIONS[user_id].add(websocket)

        # Add to students set if the role is "Student"
        if role == "Student":
            # print("ok")
            STUDENTS.add(user_id)
        
        if role == "Admin":
            # print("ok")
            ADMINS.add(user_id)
        
        # Broadcast the updated user and student count
        websockets.broadcast(USERS.keys(), users_event())
        websockets.broadcast(USERS.keys(), students_event())
                
        # Manage state changes
        async for message in websocket:
            event = json.loads(message)
           
            action = event.get("action", "none")
            print(action)
            if action == "submit":
                print("yup")
                notification = event.get("message", "")
                if notification:  # Only add non-empty notifications
                    NOTIFICATIONS = notification
                    print(NOTIFICATIONS)
                    # Broadcast only to Admins
                    admin_users = [ws for ws, (_, role) in USERS.items() if role == "Admin"]
                    websockets.broadcast(admin_users, notifications_event()) 
            elif action == "mark_read":
                print("ok")
                notifications_collection.update_many(
                    {"user_id": user_id, "status": "unread"},
                    {"$set": {"status": "read"}}
                )           
            else:
                logging.error("Unsupported event:", event)
    finally:
        # Unregister user
        user_id, role = USERS.pop(websocket, (None, None))
        if user_id:
            USER_CONNECTIONS[user_id].discard(websocket)
            if not USER_CONNECTIONS[user_id]:
                del USER_CONNECTIONS[user_id]
                if role == "Student":
                    STUDENTS.discard(user_id)
                if role == "Admin":
                    ADMINS.discard(user_id)
        
        # Broadcast the updated user and student count
        websockets.broadcast(USERS.keys(), users_event())
        websockets.broadcast(USERS.keys(), students_event())

async def main():
    async with websockets.serve(counter, "websocketpython-onywqmaszluv84bopmsxho.streamlit.app", 6789):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
