# CWZ - CMK-Werk-Zeug

This is both a collection of tools and shared libraries created for (but not limited to) Checkmk development
and a 'collector' for other tools located in different repositories.


## What you get

For now you only get `cmk-components` - a tool for listing component/code ownership details of the
`check_mk` repository via Gerrit and the `code-owners` plugin


## Install

You either clone the cwz repository (`ssh://review.lan.tribe29.com:29418/cmk-werk-zeug`) and make it's tools available
via `uv` or you install the pip package:

```
pipx install cmk-werk-zeug
```

For ci_build_metrics you need PostgreSQL installed
```
sudo apt install postgresql postgresql-contrib postgresql-server-dev
```
