from flask import Flask, render_template, request, redirect, flash, session,Response
from pymongo import MongoClient
from bson import ObjectId
import gridfs

app = Flask(__name__)

# MongoDB setup

client = MongoClient("your connection string")
db = client["user_database"]
users_collection = db["users"]

# GridFS for storing large files

fs = gridfs.GridFS(db)



# main route also login route

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']  
        user_id = request.form['login_id']  
        
        # Searching for the user id from the mongo db data base uisng find_one mehtod (only finding the preticular document from the db)

        user = users_collection.find_one({"name": name, "id": user_id})
        
        if user:
            #using session

            session['user_id'] = str(user['_id'])  # Store the user_id in the session
            flash("Login successful!", "success")
            return redirect('/status') 
        else:
            # If user not found, show error message

            flash("Invalid username or ID. Please try again.", "error")
            return redirect('/login')
    
    return render_template('login.html')



# route for the register 

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form['name']
        user_id = request.form['id']
        course = request.form['course']
        

        picture = request.files['picture']  #taking the picture from the html register 
        
        # Save the image to GridFS (converting the large image to small chuncks )

        picture_id = None
        if picture:
            picture_id = fs.put(picture, filename=picture.filename)

        # Create a new user document

        new_user = {
            "name": name,
            "id": user_id,
            "course": course,
            "picture_id": picture_id  # Store the GridFS ID for the image
        }

        # Insert into MongoDB

        try:
            users_collection.insert_one(new_user)  #insertng one document to the mongo db
            flash("Registration successful!", "success")
            return redirect('/login')
        except Exception as e:
            flash("An error occurred during registration.", "error")
            print(e)
            return redirect('/register')
    
    return render_template('register.html')




#route for the status 

@app.route('/status', methods=['GET', 'POST'])
def status():
    if request.method == 'POST':
        
        course_completed = request.form['course_completed']
        assignment_completed = request.form['assignment_completed']
        exam_completed = request.form['exam_completed']

        # Check if all answers are 'Yes'

        if course_completed == 'Yes' and assignment_completed == 'Yes' and exam_completed == 'Yes':
            return redirect('/certificate')  
        else:
            # If any answer is 'No', redirect back to login page with error message
            flash("You won't receive the certificate. Please complete all tasks.", "error")
            return redirect('/login')  
    
    return render_template('status.html')


#route for the certificate 

@app.route('/certificate', methods=['GET'])
def certificate():
    # Get the user_id from the session
    user_id = session.get('user_id')

    if not user_id:
        flash("You must log in first!", "error")
        return redirect('/login')  
    
    # Fetch user details from the database
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if user:
        # Fetch the image from GridFS
        picture = fs.get(user['picture_id']) if 'picture_id' in user else None

        return render_template('certificate.html', user=user, picture=picture)
    else:
        flash("User not found", "error")
        return redirect('/login')
    

#picture route

@app.route('/picture/<picture_id>')
def picture_route(picture_id):
    image_data = fs.get(ObjectId(picture_id)).read()
    return Response(image_data, mimetype='image/jpeg')






if __name__ == '__main__':
    app.secret_key = 'admin123'
    app.run(debug=True)
