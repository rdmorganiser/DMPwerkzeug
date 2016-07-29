Setup RDMO on Windows
----------------------------

Install the prerequisites from their webpages:

* `python` (we recommend version 3.4) from https://www.python.org/downloads/windows/
* `git` from https://git-for-windows.github.io/
* `Node.js` (stable version) from https://nodejs.org/en/download/
* `Pandoc` from http://pandoc.org/installing.html
* `pdflatex` (optional, for pdf export) from http://miktex.org/

The open the windows shell `cmd.exe` from  the Start-Menu.

Install `bower` using npm:

```
npm -g install bower
```

Now, clone the repository to a convenient place:

```
git clone https://github.com/rdmorganiser/rdmo
```

Change to the created directory, create a [virtualenv](https://virtualenv.readthedocs.org) and install the required dependecies:

```
cd rdmo
virtualenv env                              # for python 2.7
python -m venv env                          # for python 3.4
call env/Scripts/activate.bat

pip install -r requirements/base.txt
pip install -r requirements/postgres.txt    # for postgres
pip install -r requirements/mysql.txt       # for mysql, does not work with python 3.4
pip install -r requirements/test.txt        # for running tests
```

Install the client side libraries using `bower`:

```
./manage.py bower install
```

Create a new file as `rdmo/settings/local.py`. You can use `rdmo/settings/development.py` or `rdmo/settings/production.py` as template, i.e.:

```
cp rdmo/settings/development.py rdmo/settings/local.py
```

Configure your database connection using the `DATABASES` variable in this file. If no `DATABASE` setting is given `sqlite3` will be used as database backend.

In addition set `DEBUG = True` for the development setup.

Then, setup the application:

```
./manage.py migrate          # initializes the database
./manage.py createsuperuser  # creates the admin user
```
