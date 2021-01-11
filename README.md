# Kattis to moodle

A script for IT University of Copenhagen, Algorithms and Datastructures spring 2021.

Gets a list of usernames and solved problems for all problems in all sessions in a course on kattis.

i.e. all problems related to `<sub_domain>.kattis.com/courses/<course_name>/<course_offering>`

## Requirements

- python3

- A Kattis account with teacher or teaching assistant authentication

## Usage

```powershell
get-session.py [-h] [-c COURSEID] [-f FILE] [-o OUTPUT]
```

Remember to download your config file with auth token from `https://<sub_domain>.kattis.com/download/kattisrc`

### Optional arguments

**help** `-h`,`--help` show a help message and exit

**courseid** `-c COURSEID`,`--courseid COURSEID` Which course to get data from. Overrides default "KSALDAS/2021-Spring"

**file** `-f PATH`,`--file PATH` Used for testing. Parses and prints a local JSON file.

**output** `-o .`,`--output .` Used for testing. Gets and prints course JSON file.

### Example
```powershell
py get-course.py
```

## Limitations

Moodle part not implemented yet.

Doesn't extract emails or ITU initials
