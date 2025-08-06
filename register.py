import streamlit as st
import cv2
import os
import pickle
import face_recognition
import numpy as np
from PIL import Image
import firebase_admin
from firebase_admin import credentials, db
from supabase import create_client, Client

# Firebase setup


if not firebase_admin._apps:
    cred = credentials.Certificate('faceattendencerealtime-e6285-firebase-adminsdk-fbsvc-3658886fa6-serviceaccountKey.json')
    firebase_admin.initialize_app(cred,{
        'databaseURL': "https://faceattendencerealtime-e6285-default-rtdb.firebaseio.com/"

    })

# Supabase setup
url = "https://xwqlpoyihrjoogthsfuu.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh3cWxwb3lpaHJqb29ndGhzZnV1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM3MjIxNjksImV4cCI6MjA2OTI5ODE2OX0.Qvd4xp4YhrFs6GETHc8mwACYzYWqiteu81tjU9i0tBY"  # 🔒 Replace with real key and keep it safe!
supabase: Client = create_client(url, key)

# UI Title
st.title("📸 Student Registration Form")

# Use Streamlit form for better submission handling
with st.form("registration_form"):
    name = st.text_input("Full Name")
    student_id = st.text_input("Student ID (Roll Number)")
    major = st.text_input("Major/Branch")
    year = st.selectbox("Year", ["1", "2", "3", "4"])
    standing = st.selectbox("Standing", ["Good", "Average", "Needs Improvement"])
    starting_year = st.text_input("Starting Year")
    uploaded_file = st.file_uploader("Upload Your Face Image", type=["jpg", "jpeg", "png"])
    submit_button = st.form_submit_button("Register")

# On Submit
if submit_button:
    if not all([name, student_id, major, year, standing, starting_year, uploaded_file]):
        st.error("Please fill in all fields and upload an image.")
    else:
        with st.spinner("Processing..."):

            # Save uploaded image locally
            file_path = os.path.join("Images", f"{student_id}.jpg")
            os.makedirs("Images", exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.read())

            # Load and encode the image
            img = face_recognition.load_image_file(file_path)
            try:
                encode = face_recognition.face_encodings(img)[0]
            except IndexError:
                st.error("No face detected in the uploaded image. Please try another photo.")
                os.remove(file_path)
                st.stop()

            # Save encoding
            encoding_file = os.path.join("EncodeFile.p")
            if os.path.exists(encoding_file):
                with open(encoding_file, 'rb') as f:
                    encodeListKnownWithIds = pickle.load(f)
                encodeListKnown, studentIds = encodeListKnownWithIds
            else:
                encodeListKnown, studentIds = [], []

            encodeListKnown.append(encode)
            studentIds.append(student_id)

            with open(encoding_file, 'wb') as f:
                pickle.dump((encodeListKnown, studentIds), f)

            # Save student info to Firebase
            data = {
                "name": name,
                "major": major,
                "starting_year": starting_year,
                "standing": standing,
                "total_attendance": 0,
                "year": year
            }

            db.reference(f'Students/{student_id}').set(data)

            # Upload image to Supabase bucket
            try:
                with open(file_path, "rb") as f:
                    supabase.storage.from_("attendance-images").upload(
                        f"Images/{student_id}.jpg", f, {"content-type": "image/jpeg"}
                    )
            except Exception as e:
                st.warning(f"Could not upload to Supabase: {e}")

            # Done
            st.success("🎉 Student registered successfully!")
            st.image(file_path, caption="Uploaded Photo", width=300)
