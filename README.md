# Fruit API
This is a Flask app with an API layer. It has the following properties:
1. It has the following relational entities:
    1. Fruit
    2. User
    3. Admin
2. Each user can create a bill to calculate fruit price
3. Admin can edit,update, delete, add new fruit to the database
4. User can view bill

## Installation and Set Up

Install the required packages:
```
pip install -r requirements.txt
```

## Launching the Program
Run ```python run.py```. You may use [Postman](https://chrome.google.com/webstore/detail/postman/fhbjgbiflinjbdggehcddcbncdddomop?hl=en) for Google Chrome to run the API.

## API Endpoints

| Resource URL | Methods | Description | Requires Token |
| -------- | ------------- | --------- |--------------- |
| `/api/v1` | GET  | The index | FALSE |
| `/api/v1/auth/register` | POST  | User registration | FALSE |
|  `/api/v1/auth/login` | POST | User login | FALSE |
| `/api/v1/students` | GET, POST | View all students, add a student | TRUE |
| `/api/v1/students/<string:id>` | GET, PUT, DELETE | View, edit, and delete a single student | TRUE |
| `/api/v1/teachers` | GET, POST | View all teachers, add a teacher | TRUE |
| `/api/v1/teachers/<string:id>` | GET, PUT, DELETE | View, edit, and delete a single teacher | TRUE |
| `/api/v1/subjects` | GET, POST | View all subjects, add a subject | TRUE |
| `/api/v1/subjects/<string:id>` | GET, PUT, DELETE | View, edit, and delete a single subject | TRUE |


## Sample API Requests

Registering and logging in to get a JWT token:
![User Registration](https://github.com/mbithenzomo/flask-student-api/blob/master/screenshots/api_register.png)

![User Login](https://github.com/mbithenzomo/flask-student-api/blob/master/screenshots/api_login.png)

Displaying a paginated list of teachers:
![List of Teachers](https://github.com/mbithenzomo/flask-student-api/blob/master/screenshots/api_list_teachers.png)

Displaying a paginated list of subjects:
![List of Subjects](https://github.com/mbithenzomo/flask-student-api/blob/master/screenshots/api_list_subjects.png)

Updating a student:
![Updating Student](https://github.com/mbithenzomo/flask-student-api/blob/master/screenshots/api_update_student.png)

## Web App

The app has a web-based interface and can be accessed [here](https://flask-school-app.herokuapp.com/). A sample user has already been created with the following credentials:

```
username: testuser
password: testpassword
```

Login:
![User Login](https://github.com/mbithenzomo/flask-student-api/blob/master/screenshots/app_login.png)

Dashboard:
![App Dashboard](https://github.com/mbithenzomo/flask-student-api/blob/master/screenshots/app_dashboard.png)

Displaying all students:
![Students](https://github.com/mbithenzomo/flask-student-api/blob/master/screenshots/app_students.png)

Displaying all teachers:
![Teachers](https://github.com/mbithenzomo/flask-student-api/blob/master/screenshots/app_teachers.png)

Displaying all subjects:
![Subjects](https://github.com/mbithenzomo/flask-student-api/blob/master/screenshots/app_subjects.png)


## Testing
To test, run the following command: ```nose2```

## Built With...
* [Flask](http://flask.pocoo.org/)
* [Flask-RESTful](http://flask-restful-cn.readthedocs.io/en/0.3.4/)
* [Flask-SQLAlchemy](http://flask-sqlalchemy.pocoo.org/2.1/)
