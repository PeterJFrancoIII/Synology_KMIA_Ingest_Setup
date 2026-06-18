#!/bin/sh
set -eu

find /volume2/Data \
  -path /volume2/Data/Games -prune -o \
  -path /volume2/Data/docker -prune -o \
  \( \
    -iname "*kalshi*" -o \
    -iname "*kmia*" -o \
    -iname "*madis*" -o \
    -iname "*ndfd*" -o \
    -iname "*synoptic*" -o \
    -iname "*weather*" \
  \) -print
