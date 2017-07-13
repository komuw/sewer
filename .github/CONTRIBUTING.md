Thank you for thinking of contributing to sewer.                    
Every contribution to sewer is important to us.                       
You may not know it, but you are about to contribute towards making the world a more safer and secure place.                         

Contributor offers to license certain software (a “Contribution” or multiple
“Contributions”) to sewer, and sewer agrees to accept said Contributions,
under the terms of the MIT License.
Contributor understands and agrees that sewer shall have the irrevocable and perpetual right to make
and distribute copies of any Contribution, as well as to create and distribute collective works and
derivative works of any Contribution, under the MIT License.


## To contribute:            

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
