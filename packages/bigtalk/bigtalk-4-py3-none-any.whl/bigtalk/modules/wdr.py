# This file is placed in the Public Domain.


"working directory"


from bigtalk.persist import workdir


def wdr(event):
    event.reply(workdir())
