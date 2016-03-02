# BrawlBracket
A web app to simplify running Brawlhalla tournaments, both for players and tournament operators.


## Setup
BrawlBracket uses Gulp to process web files and make development easier.

First, you'll want to install Node.js: https://nodejs.org/en/

Now run `npm install gulp --global` to install Gulp and add it to your PATH.

In this directory, run `npm install` to install dependencies.

Finally, in this directory, run `gulp`. It'll stay running in the background and automatically update the files in
`dist` (where the Flask app gets its files) whenever you make modifications in `src`. Note that even though it says that
the 'watch' task has finished, this actually just means that the 'watch' task was successfully executed, so it should
still be running.

Alternatively, you can run `gulp all-dev`, which will update the web files without starting the watcher task.


## Testing
First, install the module by running `pip install -e .` in this directory.

Then, run `py.test` to run all available tests.