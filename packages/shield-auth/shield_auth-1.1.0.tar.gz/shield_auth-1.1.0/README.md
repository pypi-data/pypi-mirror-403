(Run the site)

1. Create and activate a virtual environment (PowerShell):

	python -m venv venv; .\venv\Scripts\Activate.ps1

2. Install dependencies:

	pip install -r requirements.txt

3. Start the server:

	python main.py

4. Open a browser:

	- Landing page: http://127.0.0.1:8080/ (links to both sites)
	- New site: http://127.0.0.1:8080/dqdemonlist_new/index.html

Notes:
- On Windows, installing bcrypt may require build tools. If pip install bcrypt fails, try installing the "wheel" binary matching your Python version or use the Windows Build Tools.
- The Flask server used here is for development only.

