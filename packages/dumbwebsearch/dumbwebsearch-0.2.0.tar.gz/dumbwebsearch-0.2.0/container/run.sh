#!/bin/sh -eu

if [ -n "${INDEX_AT_START:-}" ]
then
	if [ -w "$INDEX_DATABASE" ] || ! [ -f "$INDEX_DATABASE" ]
	then
		python3 -m dumbwebsearch.index --docroot="$INDEX_DIR" --database="$INDEX_DATABASE" index
	fi
fi

exec python3 -m dumbwebsearch.browse
