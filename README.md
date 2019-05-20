# reimburser

Have you ever gone on a trip with a bunch of your friends, but then been too
lazy to calculate who owes whom what? Well, this is your solution. For you,
this package will figure out a reimbursement scheme and also send all
participants an email detailing the reimbursement information.

## Requirements

This package requires Python 3.7.3 or greater. Technically, probably not, but I
wrote this is Python 3.7.3 and it's good practice to keep up with software
updates so you might as well just update Python to the most recent version.

Currently, this package only supports gmail for sending out the emails. Also,
the gmail account needs to be
[given permission](https://support.google.com/accounts/answer/6010255?hl=en)
else this package won't be able to access said email account.
Let me know if you'd like a different service to be supported and I'll look in
to it.

While I also recommend having Git, that's technically not required since you can
just download the files directly from the repository page. This package is not
on PyPI, and I have no intention of publishing this there for the foreseeable
future.

## Installation

I recommend installing this package in a virtual environment so that it won't
interfere with other, more official packages.

To set up and activate a virtual environment (which I'll call `env`), run the
following in the terminal:

```sh
$ python -m venv env
$ source env/bin/activate
(env) $
```

The easiest way to install this is directly from GitHub using the python package
manager:

```sh
(env) $ pip install https://github.com/emof/reimburser
```

Or, clone or directly download the files from GitHub, go to wherever the 
directory was downloaded, then run:

```sh
(env) $ pip install reimburser
```

To leave the virtual environment, just type `deactivate`. You will know you are
out of the virtual environment when the `(env)` disappears.

## Example

In order to use this package, you need two CSV (comma-separated values) files:
*participants.csv* and *costs.csv*. *participants.csv* should have the
following format:

| participant | email |
| ----------- | ----- |
| Alice | alice@email.com |
| Bob | bob@email.com |
| Carol | carol@email.com |
| Dan | dan@email.com |

For this file, the header is optional (but helpful), and should always preserve
the ("participant", "email") column order.

*costs.csv* should have the following format (and as an example, I've filled it
out):

| reimbursee | cost | currency | reimbursers | notes |
| ---------- | ---: | -------- | ----------- | ----- |
| Dan | 100.00 | | | groceries |
| Bob |  42.98 | | Bob, Carol | also paid for Carol's lunch |
| Alice | 12.34 | | Dan | IOU |
| Carol |  3.00 | | not Alice |

The header is required in this file. The three most important columns here are
"reimbursee", "cost", and "reimbursers". Each row denotes a payment made by the
reimbursee during the trip. The cost is the cost of the payment, to be split
amongst the reimbursers. If the payment needs to be split amongst all
participants, then "reimbursers" row element can be left blank. However, if
only a subset of participants need to reimburse the reimbursee, those
participants should be listed there. In this case, the reimbursee should also
be listed. In the case participants did not take part in the payment, they can
be removed from consideration of the payment by having a "not " prepended to
the name. The previous two cases should not be used together.

If only one currency is used, the "currency" column can be
left out altogether and defaults to USD. If included but not filled, it will be
filled with the whatever currency is specified at the time of execution (and
defaults to USD if unspecified). The "notes" column is completely optional and
is only there if the reimbursee wants to note what the cost was for.

```sh
(env) $ python -m reimburser participants.csv costs.csv
```

You will be prompted to enter your email and password. And that's it.
