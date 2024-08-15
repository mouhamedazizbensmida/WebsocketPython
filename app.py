import streamlit as st
from streamlit_notification_center_component import notification_center
from pymongo import MongoClient
from datetime import datetime

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client['your_database']
notifications_collection = db['notifications']
users_collection = db['users']  # Assuming you have a users collection with roles

def get_admin_notifications():
    # Fetch notifications intended for Admin users
    return list(notifications_collection.find({"user_role": "Admin"}))

def add_admin_notification(message):
    # Add a new notification to the database for Admin users
    admin_users = users_collection.find({"role": "Admin"})
    for admin in admin_users:
        notifications_collection.insert_one({
            "user_id": admin["_id"],  # Assuming _id is the unique identifier for users
            "user_role": "Admin",
            "message": message,
            "timestamp": datetime.utcnow(),
            "status": "unread"
        })

# App title
st.title("Admin Notification System")

# Example user role (you can get this from your authentication system)
current_user_role = "Admin"  # Example role; replace with actual user role

# Submit button
if st.button("Submit"):
    # Trigger a notification for Admins only when the button is clicked
    add_admin_notification("A new submission has been made!")
    st.success("Notification sent to Admins!")

# Display notifications only if the current user is an Admin
if current_user_role == "Admin":
    notifications = get_admin_notifications()
    formatted_notifications = [{"title": "Notification", "body": notif["message"]} for notif in notifications]

    notification_center(notifications=formatted_notifications)

    # Optionally, add a "Mark all as read" button
    if st.button("Mark all as read"):
        notifications_collection.update_many({"user_role": "Admin"}, {"$set": {"status": "read"}})
        st.experimental_rerun()
else:
    st.warning("You do not have permission to view these notifications.")
