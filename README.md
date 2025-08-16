## Project Setup Guide

#### Create Project Folder and Environment Setup

```

# Create a new project folder
mkdir <project_folder_name>

# Move into the project folder
cd <project_folder_name>

# Open the folder in VS Code
code .

# Create a new Conda environment with Python 3.10
conda create -p <env_name> python=3.10 -y

# Activate the environment (use full path to the environment)
conda activate <path_of_the_env>

# Cloning the repository
git clone https://github.com/Soumadeep555/Project1_Document_Portal.git

# Install dependencies from requirements.txt
pip install -r requirements.txt
```

```
## RUN THE APP:
cd api
uvicorn api.main:app --port 8080 --reload
```

## Minimum Requirements for the Project

1. LLM Models ## Groq (Free), OpenAI (Paid), Gemini (15 Days Free Access), Claude (Paid), Hugging Face (Free), Ollama (Local Setup)

2. Embedding Models ## OpenAI, Hugging Face, Gemini

3. Vector Databases ## In-Memory, On-Disk, Cloud-Based

## GROQ API KEY

## GEMINI API KEY

