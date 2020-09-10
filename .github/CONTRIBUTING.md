# Contributing to sewer

Thank you for thinking of contributing to sewer.  Every contribution to
sewer is important to us.  You may not know it, but you are about to
contribute towards making the world a safer and more secure place.

Contributor offers to license certain software (a “Contribution” or multiple
“Contributions”) to sewer, and sewer agrees to accept said Contributions,
under the terms of the MIT License.  Contributor understands and agrees that
sewer shall have the irrevocable and perpetual right to make and distribute
copies of any Contribution, as well as to create and distribute collective
works and derivative works of any Contribution, under the MIT License.

## To contribute:

- fork this repo.

- cd sewer

- open an issue on this repo. In your issue, outline what it is you want to add and why.

- install pre-requiste software:
```shell
pip3 install -e .[dev,test]
```

- python cryptography generally only requires openssl's libraries.  To run
  the full set of tests (make test), you **also need the openssl program**

- make the changes you want on your fork.

- your changes should have backward compatibility in mind unless it is impossible to do so.

- add your name and contact(optional) to CONTRIBUTORS.md

- add tests

- format your code using [black](https://github.com/ambv/black) *NB:*
requires black 19.3.b0 or newer (19.10b0 is used by the CI):
```shell
black -l 100 -t py35 .
```

- run [pylint](https://pypi.python.org/pypi/pylint) on the code and fix any issues:
```shell
pylint --enable=E --disable=W,R,C sewer/
```

- run tests and make sure everything is passing:
```shell
make test
```
- open a pull request on this repo.

NB: I make no commitment of accepting your pull requests.

##Styles

Martin (@mmaney) has a few things to say about what he's looking for aside
from code that works:

- Python is not Java.  There is rarely an excuse for @staticmethod, we can
  use first-class non-member _functions_ when _self_ would just be baggage.

- When fixing things, I approve of trying to identify a minimal change that
  repairs the bug (or adds a feature, etc.).  But be prepared to get
  feedback asking (sometimes sketching) a more intrusive refactoring that
  perhaps incidentally fixes the bug.  It's not that I don't appreciate a
  small, focused patch, but there's a lot of houscleaning going on these days!

- And sometimes your PR (or less often a bug report itself) will get me
  thinking about a piece of work I hadn't focused on yet (or get me thinking
  about it in a more productive way), and all of a sudden I've stolen your
  patch and wrapped it in a larger refactoring.  Don't doubt that your
  contribution was appreciated, you just yodeled and triggered an avalanche
  that you weren't expecting!

- black is the current fad, but its indifference to actual readability in
  favor of slavish consistency to simplistic rules sometimes makes me ill. 
  But for now it's a thing.


## Creating a new release:
To create a new release on [https://pypi.org/project/sewer](https://pypi.org/project/sewer);

- Create a new branch

- Update `sewer/meta.json` with the new version number.
  The version numbers should follow semver.

- Update `docs/CHANGELOG.md` with information about what is changing in the new release.

- Open a pull request and have it go through the normal review process.

- Upon approval of the pull request, squash and merge it.   
  Remember that the squash & merge commit message should ideally be the message that was in the pull request template.   

- Once succesfully merged, run;  
```bash
git checkout master
git pull --tags
# if plain "python" runs Py2, prefix "make ..." with "PYTHON=python3"
# or have it set in your shell environment.
make uploadprod
```
   That should upload the new release on pypi.  You do need to have
   permissions to upload to pypi.  Currently only
   [@komuw](https://github.com/komuw) and
   [@mmaney](https://github.com/mmaney) have pypi permissions, so if you
   need to create a new release, do talk to him to do that.  In the future,
   more contributors may be availed permissions to pypi.
