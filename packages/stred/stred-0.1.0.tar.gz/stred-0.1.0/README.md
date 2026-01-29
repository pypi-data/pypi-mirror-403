# STReam EDitor

`stred` processes its intput using a [Python regular expression], and
produces output according to an (optional) replacement string and
command-line flags.

[Python regular expression]: https://docs.python.org/3/library/re.html#regular-expression-syntax

It can be used as a replacement for traditional UNIX tools such as
`grep` and `sed`, offering more advanced functionality.


## Features

- Filter a stream using a regular expression
- Perform search and replace on a stream using a regular expression
- Use the jinja templating language to specify replacement strings


## Installation

```
pipx install stred
```

## Usage: stream filtering

Only print matching lines:

```
stred -g REGEXP
```

Do case-insensitive matching:

```
stred -g -i REGEXP
```

Only print matches, one per line:

```
stred -g -o REGEXP
```

## Usage: replacement

Replace the string `FOO` with `BAR`:

```
stred FOO BAR
```

Use positional groups in the replacement (the two are equivalent):

```
stred -o "http://([^/]+)/([^ ]*)" "\0:\1"
stred -o "http://([^/]+)/([^ ]*)" "\g<0>:\g<1>"
```

Use named groups in the replacement:

```
stred -o "http://(?P<host>[^/]+)/(?P<path>[^ ]*)" "\g<host>:\g<path>"
```

Same thing using jinja templates:

```
stred -o "http://(?P<host>[^/]+)/(?P<path>[^ ]*)" "{{ host }}:{{ path }}"
```
