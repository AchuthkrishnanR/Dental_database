PATIENT DATABASE — LOCAL PC EDITION
===================================

This folder is a separate copy of the CareLedger patient registry. It stores
records in a SQLite database file on this PC instead of browser local storage.
The existing C:\project\patient registry.html file is separate and is not
changed by this copy.

START THE APP
-------------
1. Install Python 3 on this PC if it is not already installed.
   This app uses only Python's built-in libraries; no pip packages are needed.
2. Double-click "Run Patient Database.bat".
3. Your browser opens the app at http://127.0.0.1:8765.
4. Keep the black server window open while using the app. Press Ctrl+C in that
   window when you are finished.

The local service listens only on this PC. Other devices cannot connect to it.

WHERE RECORDS ARE STORED
------------------------
Records are stored in:
  data\patient-registry.sqlite3

The database file is created the first time the app runs. The browser is only
the interface; patient records are read from and written to the SQLite file.
The data folder is deliberately excluded from source-control commits.

BACKUPS AND MOVING DATA
----------------------
Use Data & Backups in the app to download a JSON backup. Keep that backup in a
secure location, separate from this folder. To move records to another PC,
copy the SQLite file while the app is stopped, or restore a JSON backup using
the app's Restore from backup control.

Do not put the SQLite database or patient backups in a public GitHub repository.
GitHub stores app code; it does not sync the local database between PCs.

DATA PROTECTION
---------------
The SQLite file is not encrypted by this app. Protect this Windows account with
a strong sign-in, keep device encryption enabled where available, and store
backups securely. Anyone who can access the file can access its patient data.
