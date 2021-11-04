# Pyrnalist

An elegant console reporter, a python port of [Yournalist](https://github.com/0x80/yurnalist).

## Introduction

Pretty console output makes developers happy and Yarn is doing a nice job.
Pyrnalist is an incomplete rewrite of Node.js's Yournalist, which in turn
is a public version of Yarn internal console reproter.

Yurnalist can be used to report many different things besides simple messages.

### Features

* log, info, warn, succes, error & command messages
* activity spinners
* emojis
* process steps
* lists
* program header & footer
* progress bars

### Missing features of Yournalist

* object inspection
* trees
* tables
* user question
* user select

## Install

```sh
pip install pyrnalist
```

## How to use

Here is an example showing a combination of different reporter API functions.

```python
from pyrnalist import report
import time

report.header("pyrnalist", version="0.0.2")

report.info("Please wait while I fetch something for you.")
report.warn("It might take a little while though.")

spinner = report.activity()
spinner.tick("I am on it!")
time.sleep(1)
spinner.tick("Still busy...")
time.sleep(1)
spinner.tick("Almost there...")
time.sleep(1)
report.success("Done!")
spinner.end()

steps = 15
tick = report.progress(steps)
report.info('🥚 Wait for it...')
for x in range(steps):
    tick()
    if x % 5 == 0:
        report.warn("Interrupt.")
    time.sleep(0.25)
report.success('🐣 Tjiep!')

report.footer()
```

## Configuration

A normal import gives you a reporter instance configured with defaults for easy
use. If you want something else you can call `create_reporter()` to give
you an instance with different options.

### Options

These are the options of the reporter as defined by Flow:

```python
def create_reporter(
    verbose=True, 
    silent=False, 
    emoji=True
    ):
```

## Credits

Of course ❤️ and credits to all the contributers of [Yournalist](https://github.com/0x80/yurnalist) and [Yarn](https://yarnpkg.com).
The ease with which I was able to port the module to python from their codebase is proving some awesome engineering skills.
