#!/bin/bash

alembic upgrade head

sqlite3 vpn/db.db