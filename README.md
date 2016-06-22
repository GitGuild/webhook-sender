# webhook-sender [![PyPi version](https://img.shields.io/pypi/v/webhook_sender.svg)](https://pypi.python.org/pypi/webhook_sender/) [![Build Status](https://travis-ci.org/GitGuild/webhook-sender.svg?branch=MVP)](https://travis-ci.org/GitGuild/webhook-sender) [![Coverage Status](https://coveralls.io/repos/github/GitGuild/webhook-sender/badge.svg?branch=MVP)](https://coveralls.io/github/GitGuild/webhook-sender?branch=MVP)


A simple program to manage the sending of webhooks registered in an SQL database.

# Installation

This package is registered with pypi, and can be installed with pip.

`pip install webhook_sender`

Additionally, it is recommended to set the `sender.py` script up on a cron job running every minute. This manual execution is currently the only way to run the program.

# Configuration

This package expects a config file in the `.ini` format. See the `example_cfg.py` file for example values. To replace this with a production configuration file, set the `WEBHOOK_SENDER_CONFIG_FILE` environmental variable.
