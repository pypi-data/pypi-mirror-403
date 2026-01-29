# subarashii

[![Publish to PyPI](https://github.com/hzokbe/subarashii/actions/workflows/publish.yml/badge.svg)](https://github.com/hzokbe/subarashii/actions/workflows/publish.yml)

**Subarashii** is a lightweight Python library that provides generic CRUD repository classes built on top of **SQLAlchemy**.

Its goal is to reduce boilerplate by offering reusable, type-safe repository implementations for common database operations.

## Features

- Generic CRUD repository pattern
- Built with SQLAlchemy ORM
- Type-safe using Python Generics
- Simple and extensible design
- Custom exceptions for common error cases

## Requirements

- Python **3.12+**
- SQLAlchemy **2.0+**
- **uv** package manager

## Installing

Run:

```sh
uv add subarashii
```

## Core Concept

Subarashii provides a base `CRUDRepository` class that can be reused for any SQLAlchemy model.

It includes the following operations out of the box:

* `save`
* `get_all`
* `get_by_id`
* `get_by`
* `update`
* `delete`
* `count`
* `exists_by_id`
