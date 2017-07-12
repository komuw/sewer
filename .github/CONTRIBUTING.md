# to contribute:            

- fork this repo.
- open an issue on this repo. In your issue, outline what it is you want to add and why.
- install pre-requiste software:             
`apt-get install pandoc && pip install twine wheel pypandoc coverage yapf flake8`                   
- make the changes you want on your fork.
- your changes should have backward compatibility in mind unless it is impossible to do so.
- add your name and contact(optional) to 
- add tests
- run tests to make sure they are passing
- format your code using [yapf](https://github.com/google/yapf):                      
`yapf --in-place --style "google" -r .`                     
- run [flake8](https://pypi.python.org/pypi/flake8) on the code and fix any issues:                      
`flake8 .`                      
- open a pull request on this repo.               

NB: I make no commitment of accepting your pull requests.
