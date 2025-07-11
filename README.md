# How to start?

## 1st step: install homebrew by

/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

## 2nd step: install all necessary tools 

brew update

brew install pyenv

brew install ffmpeg

## 3rd step: install Python and venv for py

pyenv install 3.10.13

pyenv virtualenv 3.10.13 myproject-env

## 4th step: activate venv

eval "$(pyenv init -)"

eval "$(pyenv virtualenv-init -)"

pyenv activate myproject-env

cd /path/to/your/project

pyenv local myproject-env

python --version # should be 3.10.13

pip install -r requirements.txt


## to activate website -> uvicorn main:app --reload
