# Copyright (c) 2004-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import os
import sys
from typing import Any, Callable, TypeVar

T = TypeVar("T")


def decorate_test_methods_with(decorator: Callable[[Any], Any]) -> Callable[[type[T]], type[T]]:
    """Decorator for a TestCase class. Wrap every test method with the `decorator` parameter."""
    def class_decorator(decorated_class: type[T]) -> type[T]:
        for (name, member) in decorated_class.__dict__.items():
            if name.startswith("test_") and callable(member):
                setattr(decorated_class, name, decorator(member))
        return decorated_class
    return class_decorator


class environ:
    """Temporarily replace certain mappings of os.environ."""
    def __init__(self, new_mapping: dict[str, str]) -> None:
        self.old_mapping = {
            key: os.environ.get(key) for (key, _) in new_mapping.items()
        }
        self.new_mapping = new_mapping

    def __enter__(self) -> None:
        for key, value in self.new_mapping.items():
            os.environ[key] = value

    def __exit__(self, _exception_type: Any, _exception_value: Any, _traceback: Any) -> None:
        for key, value in self.old_mapping.items():
            if value is None:
                del os.environ[key]
            else:
                os.environ[key] = value

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: Any, **kwargs: Any) -> T:
            with self:
                return func(*args, **kwargs)
        return wrapper


class sys_argv:
    """Temporarily replace the contents of sys.argv with the given string."""
    def __init__(self, new_argv: str | list[str]) -> None:
        self.new_argv = new_argv.strip().split(" ") if isinstance(new_argv, str) else new_argv

    def __enter__(self) -> None:
        self.old_argv, sys.argv = sys.argv, self.new_argv

    def __exit__(self, _exception_type: Any, _exception_value: Any, _traceback: Any) -> None:
        sys.argv = self.old_argv

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: Any, **kwargs: Any) -> T:
            with self:
                return func(*args, **kwargs)
        return wrapper
