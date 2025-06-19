# Set a Recurring Server Job

Once deployed on the server and with an established body of knowledge coming from the
published work of KNBS, it is necessary to update this document store.

In order to do this, the `pdf_runner.py` script can be run with the relevant `mode` from
the `main.toml` configuration file. In particular with `mode == UPDATE`.

However, a manual trigger isn't the most convinient.
It is possible to set up the Ubuntu server to run the `pdf_runner.py` script automatically.
The most straightforward method is to use `cron`, the built-in job scheduler in Unix-like systems.

## Step 1: Locate the script

First, it is important to know where the script is relative to the server's home:

```bash
statschat/pdf_runner.py
```

## Step 2: Locate the Virtual Environment

It is also important to locate the virtual environment path.
This will look something like:

```bash
/home/username/my_env/bin/python
```
You’ll use this Python path in the cron job to ensure it uses the correct environment.

## Step 3: Edit the `crontab`

Run:

```bash

crontab -e
```

If it asks for an editor, you can select `nano` for simplicity.

## Step 4: Add a Cron Entry

To run your script at 04:00 (am) every day, add the following line to the crontab:

```bash
0 4 * * * /home/username/my_env/bin/python /home/username/statschat-ke/statschat/pdf_runner.py >> /home/username/my_script/cron.log 2>&1
```

### Explanation

- `0 4 * * *` → Run at minute 0 of hour 4 of every day.
- The `>> ... 2>&1` part logs standard output and errors to `cron.log`, useful for debugging.

Replace paths with the actual script and virtual environment locations.

## Step 5: Save and Exit

If using `nano`, press `CTRL + O` to write, `Enter` to confirm, and `CTRL + X` to exit.

## Step 6: Confirm the Cron Job is Scheduled

Run:

```bash
crontab -l
```

You should see the line you just added.
