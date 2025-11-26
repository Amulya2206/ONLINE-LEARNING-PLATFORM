# Online Learning Platform 

This project is a minimal but complete online learning platform built with Flask,
supporting:
  - User registration and login (hashed passwords, session)
  - Video streaming endpoint with Range support
  - Courses with video lessons
  - Quizzes per lesson
  - Progress tracking

# Folder structure:
  /online_learning_platform
  ├─ app.py
  ├─ requirements.txt
  ├─ init_db.py
  ├─ templates/
  │  ├─ layout.html
  │  ├─ index.html
  │  ├─ register.html
  │  ├─ login.html
  │  ├─ dashboard.html
  │  └─ course.html
  └─ static/
     ├─ css/style.css
     ├─ js/app.js
     └─ videos
