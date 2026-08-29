## Handle some neeted tools
We'll be using Visual Studio Code.


### Virtual Environments
- **Install nothing globally!!!**
- There are many ways to create virtual environment.  
I use the built in one:  
```python -m venv <your virtual env name>```  
(which uses the built-in **venv** module)
- Use ```pip freeze > requirements.txt``` that creates a file with that name.  
  - The file includes everything that was instlled in this env.  
  - file name is 
  - Use ```pip install -r requirements.txt``` to install everything automatically
  - Save **requirements.txt** in your git repository
- I don't create a single venv for the whole repository, so that different libraries can be deleted if needed.


### Jupyter Notebook

- Get to know it (if you haven't already)
- **Install python version 3.13.x (not the last 3.14)**
- **Do not install jupyter lab. install notebook.**  
We'll be using it from VScode, not from the web.
- Know how to choose your environment and your jupyter kernel:  
Ctrl-Shift-P (to open commands)