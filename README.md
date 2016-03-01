# BrawlBracket
A web app to simplify running Brawlhalla tournaments, both for players and tournament operators.


## Setup
BrawlBracket uses Gulp to process web files and make development easier.

First, you'll want to install Node.js: https://nodejs.org/en/

Then, in this directory, run `npm install`.

Finally, run `gulp`. It'll stay running in the background and automatically update the files in `dist` (where the
Flask app gets its files) whenever you make modifications in `src`.


## Testing
First, install the module by running `pip install -e .` in this directory.

Then, run `py.test` to run all available tests.