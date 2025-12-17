FindMyStuff Your Item Finder System

How to Run the System in VS Code (Any OS)
Follow these simple steps to get the system running on your local machine using VS Code:

1. Open the Project
Open VS Code.

Go to File > Open Folder and select your "FindMyStuff Your Item Finder" folder.

2. Activate the Virtual Environment
Open a new terminal in VS Code (Terminal > New Terminal).

You should see (venv) on the left side of your command line.

If not, type:

Windows: source venv/Scripts/activate

macOS/Linux: source venv/bin/activate

3. Install Dependencies
In the same terminal, type this to install the required libraries (Flask, SQLAlchemy, etc.):

Bash

pip install -r requirements.txt
4. Run the Application
In the terminal, start the server by typing:

Bash

python app.py
5. Access the System
Open your web browser (Chrome, Edge, or Safari).

Go to the following address: http://127.0.0.1:5000