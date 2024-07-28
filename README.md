
# Bankmail Retriever

Playwright script to retrieve bankmail from BOB (Bankwest online banking)


## Authors

- [@hotchie](https://www.github.com/hotchie)


## Run Locally

Clone the project

```bash
  git clone https://github.com/hotchie/bankmail-retriever.git
```

Go to the project directory

```bash
  cd bankmail-retriever
```

(Optionally) Create credentials file

```bash
  touch .env
```

(Optionally) Add your PAN and online banking password to the credentials file

```bash
  echo PAN=<your-pan> >> .env
  echo PASSWORD=<your-online-banking-password> >> .env
```

Or you can open the file and enter them manually so they don't appear in your command line history

The script will prompt for credentials if they can't be found

Run the script with the desired options

```bash
  ./retrieve-bankmail.py -h
usage: retrieve-bankmail.py [-h] [-v] [-d] [-s] [-l LIMIT] [-g LOG_LEVEL]

options:
  -h, --help            show this help message and exit
  -v, --verbose         verbose logging
  -d, --debug           debug logging
  -s, --show-browser    display the browser
  -l LIMIT, --limit LIMIT
                        limit for the amount of mail returned
  -g LOG_LEVEL, --log-level LOG_LEVEL
                        manually set the log level

```
