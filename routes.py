'''
========================================================================
        ╦ ╦┌─┐┌─┐┌─┐┌─┐┌┬┐  ╔╦╗┌─┐┌─┐┌┬┐┬ ┬  ╔╗ ┌─┐┬  ┌─┐┬ ┬┌─┐
        ╠═╣│ │└─┐└─┐├─┤│││  ║║║├─┤│ ┬ ││└┬┘  ╠╩╗├─┤│  ├─┤├─┤├─┤
        ╩ ╩└─┘└─┘└─┘┴ ┴┴ ┴  ╩ ╩┴ ┴└─┘─┴┘ ┴   ╚═╝┴ ┴┴─┘┴ ┴┴ ┴┴ ┴
========================================================================
# Author: Hossam Magdy Balaha
# Initial Creation Date: Aug 2025
# Last Modification Date: Aug 18th, 2025
# Permissions and Citation: Refer to the README file.
'''

from flask import Blueprint, render_template

webBp = Blueprint("web", __name__)


# Routes for web UI.
@webBp.route("/")
def index():
  return render_template("index.html")


@webBp.route("/text2Video")
def text2Video():
  return render_template("text2Video.html")


@webBp.route("/audioTools")
def audioTools():
  return render_template("audioTools.html")


@webBp.route("/jobs")
def jobsPage():
  return render_template("jobs.html")
