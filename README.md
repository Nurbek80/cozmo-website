How to start?
brew update
brew install pyenv

pyenv install 3.10.13
pyenv virtualenv 3.10.13 myproject-env
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
pyenv activate myproject-env

cd /path/to/your/project
pyenv local myproject-env
python --version # should be 3.10.13
pip install -r requirements.txt


to activate website -> uvicorn main:app --reload
