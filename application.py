
import csv
from email.mime import application
from flask import Flask, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp

from helpers import apology, get_start

application = Flask(__name__)

application.config["SESSION_FILE_DIR"] = mkdtemp()
application.config["SESSION_PERMANENT"] = False
application.config["SESSION_TYPE"] = "filesystem"
Session(application)

# Create list of regions
REGIONS = [
	"General",
	"Upper Limb",
	"Lower Limb",
	"Thorax",
	"Abdomen",
	"Pelvis",
	"Perineum",
	"Back",
    	"Head",
    	"Neck",
    	"Face",
]


@application.route("/", methods=["GET", "POST"])
def index():

	if request.method == "POST":
		#if "answer" in session: # delete this row
		session.clear()
		# Validate users input
		if not request.form.get("region"):
			return apology("must provide region", 403)
		session["region"] = request.form.get("region")

		if not request.form.get("start"):
			return apology("must provide start", 403)
		
		# Catch value error
		try:
			start = int(request.form.get("start"))
		except ValueError:
			return apology("start must be an int", 403)

		# Open file and read as dictionary to get limit
		file = open(f"answers/{session['region']}.csv")
		reader = csv.DictReader(file)
		session["limit"] = len(list(reader))

		# Check if start from user is valid
		begin = get_start(start)
		if begin <= 0:
			return apology("must be a Valid start", 403)

		# Reject if start num exceeds end of region
		if begin > session["limit"]:
			return apology("start index out of range", 403)

		# Create session for the start
		session["start"] = begin


		# Initialize empty list of answer from marking scheme and users input
		session["answers"] = []
		session["mark_scheme"] = []
		session["Questions"] = []
		session["failures"] = []

		return render_template("questions.html", start=session["start"], limit=session["limit"], region=session["region"])
	
	# Clear old sessions if any
	session.clear()
	return render_template("index.html", regions=REGIONS)

@application.route("/add", methods=["GET", "POST"])
def add():

	if request.method == "POST":

		# Append users answers to list
		for n in range(5):
			if not request.form.get(f"group{n}"):
				session["answers"].append("Z")
			elif request.form.get(f"group{n}"):
				session["answers"].append(request.form.get(f"group{n}"))

		# Current Question numbers
		current_list = []
		for n in range(5):
			current_list.append(str(int(request.form.get("first")) + n))

		# Open file and read as dictionary
		file = open(f"answers/{session['region']}.csv")
		reader = csv.DictReader(file)

		# Append answers to list
		for row in reader:
			if row["Question"] in current_list:
				session["mark_scheme"].append(row["Answer"])
				session["Questions"].append(int(row["Question"]))

		score, med_score, _ = check()

		# Close file
		file.close()

		# Get last question number from frontend
		session["current_num"] = int(request.form.get("last"))

		return render_template("questions.html", start=session["current_num"], current_score=score, current_med_score=med_score, limit=session["limit"], region=session["region"])

@app.route("/undo", methods=["GET", "POST"])
def undo():
	# delete last 5 input from list
	for _ in range(5):
		if session["failures"]:
			session["failures"].pop()
		session["answers"].pop()
		session["Questions"].pop()
		session["mark_scheme"].pop()

	# Call check to update scores
	score, med_score, _ = check()

	# Get first number of previous page
	session["current_num"] = session["current_num"] - 5

	# Return previous page
	return render_template("questions.html", start=session["current_num"], current_score=score, current_med_score=med_score, limit=session["limit"], region=session["region"])
	

@application.route("/end", methods=["GET", "POST"])
def end():

	""" This route will displays users Score and percentage Over a 100% """

	session["current_score"], session["current_medical_score"], failures = check()

	per = session["current_medical_score"] / len(session["answers"]) * 100

	return render_template("end.html", failed=sorted(failures), score=session["current_score"], scoreN=session["current_medical_score"], per=per, totalQ=len(session["answers"]), region=session["region"])

# Get current score
def check():
	user_answer = session["answers"]
	marking_scheme = session["mark_scheme"]
	users_failures = session["Questions"]
	score = 0
	medical = 0

	for n in range(len(user_answer)):

		# Check if user answer is correct
		if user_answer[n] == marking_scheme[n]:
			score += 1
		
		# Check if answer is null
		elif user_answer[n] == "Z":
			if f"{users_failures[n]}. {marking_scheme[n]}" not in session["failures"]:
				session["failures"].append(f"{users_failures[n]}. {marking_scheme[n]}")
		
		# Check if answer is wrong
		else:
			medical += 0.5
			if f"{users_failures[n]}. {marking_scheme[n]}" not in session["failures"]:
				session["failures"].append(f"{users_failures[n]}. {marking_scheme[n]}")


	return score, score-medical, session["failures"]
if __name__ == "__main__":
	application.run()
