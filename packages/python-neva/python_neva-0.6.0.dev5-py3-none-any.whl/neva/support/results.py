"""Implementation of the Option and Result types for functional error handling.

This module provides Rust-inspired Option and Result types for handling optional values
and errors in a functional style. The API is inspired by Rust's standard library but
adapted for Python idioms and use cases.

The Option type represents an optional value (Some or Nothing), while the Result type
represents either a success value (Ok) or an error value (Err). Both types provide
chainable methods for transforming and handling values in a functional manner.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import (
    TypeVar,
    cast,
    override,
)


T = TypeVar("T", covariant=True)
E = TypeVar("E", covariant=True)


class UnwrapError(Exception):
    """Exception raised when unwrapping a Nothing or Err value.

    This exception is raised when attempting to unwrap a value that doesn't exist
    (Nothing) or unwrapping the wrong variant (e.g., calling unwrap on Err).
    """


class OptionProtocol[T](ABC):
    """Protocol defining the Option API.

    Defines the interface for Option types (Some and Nothing), providing
    methods for transforming, filtering, and extracting optional values.
    """

    @abstractmethod
    def and_then[U](self, f: Callable[[T], "Option[U]"]) -> "Option[U]":
        """Chain Option-returning operations.

        Returns Nothing if the option is Nothing, otherwise calls f with the value.

        Args:
            f: Function that takes the contained value and returns an Option.

        Returns:
            The result of f if this is Some, otherwise Nothing.

        """

    @abstractmethod
    def expect(self, msg: str) -> T:
        """Return the contained value or raise an exception with a custom message.

        Args:
            msg: Error message to use if the option is Nothing.

        Returns:
            The contained value.

        Raises:
            UnwrapError: If this is Nothing.

        """

    @abstractmethod
    def filter(self, predicate: Callable[[T], bool]) -> "Option[T]":
        """Filter the option based on a predicate.

        Returns Nothing if the option is Nothing or if the predicate returns False.

        Args:
            predicate: Function to test the contained value.

        Returns:
            Some(value) if predicate returns True, otherwise Nothing.

        """

    @abstractmethod
    def flatten(self) -> "Option[T]":
        """Remove one level of nesting from a nested Option.

        Returns:
            The inner Option if this is Some(Option), otherwise Nothing.

        """

    @property
    @abstractmethod
    def is_nothing(self) -> bool:
        """Check if this Option is Nothing.

        Returns:
            True if this is Nothing, False if this is Some.

        """

    @property
    @abstractmethod
    def is_some(self) -> bool:
        """Check if this Option is Some.

        Returns:
            True if this is Some, False if this is Nothing.

        """

    @abstractmethod
    def map[U](self, f: Callable[[T], U]) -> "Option[U]":
        """Transform the contained value by applying a function.

        Args:
            f: Function to apply to the contained value.

        Returns:
            Some(f(value)) if this is Some, otherwise Nothing.

        """

    @abstractmethod
    def map_or[U](self, default: U, f: Callable[[T], U]) -> U:
        """Transform the contained value or return a default.

        Args:
            default: Default value if this is Nothing.
            f: Function to apply to the contained value.

        Returns:
            f(value) if this is Some, otherwise default.

        """

    @abstractmethod
    def map_or_else[U](self, default: Callable[[], U], f: Callable[[T], U]) -> U:
        """Transform the contained value or compute a default.

        Args:
            default: Function to compute default value if this is Nothing.
            f: Function to apply to the contained value.

        Returns:
            f(value) if this is Some, otherwise default().

        """

    @abstractmethod
    def ok_or[E](self, err: E) -> "Result[T, E]":
        """Transform Option into Result with a fixed error value.

        Args:
            err: Error value to use if this is Nothing.

        Returns:
            Ok(value) if this is Some, otherwise Err(err).

        """

    @abstractmethod
    def ok_or_else[E](self, f: Callable[[], E]) -> "Result[T, E]":
        """Transform Option into Result with a computed error value.

        Args:
            f: Function to compute error value if this is Nothing.

        Returns:
            Ok(value) if this is Some, otherwise Err(f()).

        """

    def unwrap(self) -> T:
        """Return the contained value or raise an exception.

        Returns:
            The contained value.

        Raises: # noqa: DOC501
            UnwrapError: If this is Nothing.

        """
        return self.expect("called `Option.unwrap()` on a `Nothing` value")

    @abstractmethod
    def unwrap_or(self, default: T) -> T:
        """Return the contained value or a default.

        Args:
            default: Default value if this is Nothing.

        Returns:
            The contained value if Some, otherwise default.

        """

    @abstractmethod
    def unwrap_or_else(self, f: Callable[[], T]) -> T:
        """Return the contained value or compute a default.

        Args:
            f: Function to compute default value if this is Nothing.

        Returns:
            The contained value if Some, otherwise f().

        """

    @abstractmethod
    def or_else(self, f: Callable[[], "Option[T]"]) -> "Option[T]":
        """Return this Option or compute an alternative.

        Args:
            f: Function to compute alternative Option if this is Nothing.

        Returns:
            This Option if Some, otherwise f().

        """

    @abstractmethod
    def zip(self, other: "Option[T]") -> "Option[tuple[T, T]]":
        """Combine two Options into a tuple.

        Args:
            other: Another Option to zip with.

        Returns:
            Some((value1, value2)) if both are Some, otherwise Nothing.

        """

    @abstractmethod
    def __contains__(self, item: T) -> bool:
        """Check if the Option contains a specific value.

        Args:
            item: Value to check for.

        Returns:
            True if this is Some and contains the value, False otherwise.

        """


@dataclass(eq=True, frozen=True)
class Some(OptionProtocol[T]):
    """An Option containing a value.

    Represents the presence of a value in an Option type. All transformation
    methods operate on the contained value.

    Attributes:
        value: The contained value.

    """

    value: T

    @override
    def and_then[U](self, f: Callable[[T], "Option[U]"]) -> "Option[U]":
        return f(self.value)

    @override
    def expect(self, msg: str) -> T:
        return self.value

    @override
    def filter(self, predicate: Callable[[T], bool]) -> "Option[T]":
        return self if predicate(self.value) else Nothing()

    @override
    def flatten(self) -> "Option[T]":
        t = self.unwrap()
        if isinstance(t, OptionProtocol):
            return cast("Option[T]", t)
        return self

    @property
    @override
    def is_nothing(self) -> bool:
        return False

    @property
    @override
    def is_some(self) -> bool:
        return True

    @override
    def map[U](self, f: Callable[[T], U]) -> "Option[U]":
        return Some(f(self.value))

    @override
    def map_or[U](self, default: U, f: Callable[[T], U]) -> U:
        return f(self.value)

    @override
    def map_or_else[U](self, default: Callable[[], U], f: Callable[[T], U]) -> U:
        return f(self.value)

    @override
    def ok_or[E](self, err: E) -> "Result[T, E]":
        return Ok(self.value)

    @override
    def ok_or_else[E](self, f: Callable[[], E]) -> "Result[T, E]":
        return Ok(self.value)

    @override
    def unwrap_or(self, default: T) -> T:
        return self.value

    @override
    def unwrap_or_else(self, f: Callable[[], T]) -> T:
        return self.value

    @override
    def or_else(self, f: Callable[[], "Option[T]"]) -> "Option[T]":
        return self

    @override
    def zip(self, other: "Option[T]") -> "Option[tuple[T, T]]":
        return Some((self.unwrap(), other.unwrap())) if other.is_some else Nothing()

    @override
    def __contains__(self, item: T) -> bool:
        return item == self.value


@dataclass(eq=True, frozen=True)
class Nothing(OptionProtocol[T]):
    """An Option containing no value.

    Represents the absence of a value in an Option type. All transformation
    methods return Nothing without executing their function arguments.
    """

    @override
    def and_then[U](self, f: Callable[[T], "Option[U]"]) -> "Option[U]":
        return Nothing()

    @override
    def expect(self, msg: str) -> T:
        raise UnwrapError(msg)

    @override
    def filter(self, predicate: Callable[[T], bool]) -> "Option[T]":
        return self

    @override
    def flatten(self) -> "Option[T]":
        return self

    @property
    @override
    def is_nothing(self) -> bool:
        return True

    @property
    @override
    def is_some(self) -> bool:
        return False

    @override
    def map[U](self, f: Callable[[T], U]) -> "Option[U]":
        return Nothing()

    @override
    def map_or[U](self, default: U, f: Callable[[T], U]) -> U:
        return default

    @override
    def map_or_else[U](self, default: Callable[[], U], f: Callable[[T], U]) -> U:
        return default()

    @override
    def ok_or[E](self, err: E) -> "Result[T, E]":
        return Err(err)

    @override
    def ok_or_else[E](self, f: Callable[[], E]) -> "Result[T, E]":
        return Err(f())

    @override
    def unwrap_or(self, default: T) -> T:
        return default

    @override
    def unwrap_or_else(self, f: Callable[[], T]) -> T:
        return f()

    @override
    def or_else(self, f: Callable[[], "Option[T]"]) -> "Option[T]":
        return f()

    @override
    def zip(self, other: "Option[T]") -> "Option[tuple[T, T]]":
        return Nothing()

    @override
    def __contains__(self, item: T) -> bool:
        return False


Option = Nothing[T] | Some[T]


class ResultProtocol[T, E](ABC):
    """Protocol defining the Result API for error handling.

    Defines the interface for Result types (Ok and Err), providing methods
    for transforming, mapping, and extracting success or error values.
    """

    @abstractmethod
    def and_then[U](self, f: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        """Chain Result-returning operations.

        Args:
            f: Function that takes the success value and returns a Result.

        Returns:
            The result of f if this is Ok, otherwise Err.

        """

    @abstractmethod
    def err(self) -> "Option[E]":
        """Convert Result to Option containing the error value.

        Returns:
            Some(error) if this is Err, otherwise Nothing.

        """

    @abstractmethod
    def expect(self, msg: str) -> T:
        """Return the contained Ok value or raise with a custom message.

        Args:
            msg: Error message to use if this is Err.

        Returns:
            The success value.

        Raises:
            UnwrapError: If this is Err.

        """

    @abstractmethod
    def expect_err(self, msg: str) -> E:
        """Return the contained Err value or raise with a custom message.

        Args:
            msg: Error message to use if this is Ok.

        Returns:
            The error value.

        Raises:
            UnwrapError: If this is Ok.

        """

    @property
    @abstractmethod
    def is_err(self) -> bool:
        """Check if this Result is an Err.

        Returns:
            True if this is Err, False if this is Ok.

        """

    @property
    @abstractmethod
    def is_ok(self) -> bool:
        """Check if this Result is an Ok.

        Returns:
            True if this is Ok, False if this is Err.

        """

    @abstractmethod
    def map[U](self, op: Callable[[T], U]) -> "Result[U, E]":
        """Transform the success value by applying a function.

        Args:
            op: Function to apply to the success value.

        Returns:
            Ok(op(value)) if this is Ok, otherwise Err.

        """

    @abstractmethod
    def map_or[U](self, default: U, f: Callable[[T], U]) -> U:
        """Transform the success value or return a default.

        Args:
            default: Default value if this is Err.
            f: Function to apply to the success value.

        Returns:
            f(value) if this is Ok, otherwise default.

        """

    @abstractmethod
    def map_or_else[U](self, default: Callable[[], U], f: Callable[[T], U]) -> U:
        """Transform the success value or compute a default.

        Args:
            default: Function to compute default value if this is Err.
            f: Function to apply to the success value.

        Returns:
            f(value) if this is Ok, otherwise default().

        """

    @abstractmethod
    def map_err[F](self, op: Callable[[E], F]) -> "Result[T, F]":
        """Transform the error value by applying a function.

        Args:
            op: Function to apply to the error value.

        Returns:
            Err(op(error)) if this is Err, otherwise Ok.

        """

    @abstractmethod
    def ok(self) -> "Option[T]":
        """Convert Result to Option containing the success value.

        Returns:
            Some(value) if this is Ok, otherwise Nothing.

        """

    @abstractmethod
    def unwrap(self) -> T:
        """Return the contained Ok value or raise an exception.

        Returns:
            The success value.

        Raises:
            UnwrapError: If this is Err.

        """

    @abstractmethod
    def unwrap_err(self) -> E:
        """Return the contained Err value or raise an exception.

        Returns:
            The error value.

        Raises:
            UnwrapError: If this is Ok.

        """

    @abstractmethod
    def unwrap_or(self, default: T) -> T:
        """Return the contained Ok value or a default.

        Args:
            default: Default value if this is Err.

        Returns:
            The success value if Ok, otherwise default.

        """

    @abstractmethod
    def unwrap_or_else(self, f: Callable[[], T]) -> T:
        """Return the contained Ok value or compute a default.

        Args:
            f: Function to compute default value if this is Err.

        Returns:
            The success value if Ok, otherwise f().

        """


@dataclass(eq=True, frozen=True)
class Ok(ResultProtocol[T, E]):
    """A Result containing a success value.

    Represents a successful operation in a Result type. All transformation
    methods operate on the contained success value.

    Attributes:
        _value: The contained success value.

    """

    _value: T

    @override
    def and_then[U](self, f: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        return f(self._value)

    @override
    def err(self) -> "Option[E]":
        return Nothing()

    @override
    def expect(self, msg: str) -> T:
        return self._value

    @override
    def expect_err(self, msg: str) -> E:
        raise UnwrapError(msg)

    @property
    @override
    def is_err(self) -> bool:
        return False

    @property
    @override
    def is_ok(self) -> bool:
        return True

    @override
    def map[U](self, op: Callable[[T], U]) -> "Result[U, E]":
        return Ok(op(self._value))

    @override
    def map_or[U](self, default: U, f: Callable[[T], U]) -> U:
        return f(self._value)

    @override
    def map_or_else[U](self, default: Callable[[], U], f: Callable[[T], U]) -> U:
        return f(self._value)

    @override
    def map_err[F](self, op: Callable[[E], F]) -> "Result[T, F]":
        return Ok(self._value)

    @override
    def ok(self) -> "Option[T]":
        return Some(self._value)

    @override
    def unwrap(self) -> T:
        return self._value

    @override
    def unwrap_err(self) -> E:
        return self.expect_err("Called `Result.unwrap_err()` on an `Ok` value")

    @override
    def unwrap_or(self, default: T) -> T:
        return self._value

    @override
    def unwrap_or_else(self, f: Callable[[], T]) -> T:
        return self._value


@dataclass(eq=True, frozen=True)
class Err(ResultProtocol[T, E]):
    """A Result containing an error value.

    Represents a failed operation in a Result type. All transformation methods
    on the success value are bypassed, while error transformations are applied.

    Attributes:
        _err: The contained error value.

    """

    _err: E

    @override
    def and_then[U](self, f: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        return Err(self._err)

    @override
    def err(self) -> "Option[E]":
        return Some(self._err)

    @override
    def expect(self, msg: str) -> T:
        raise UnwrapError(msg)

    @override
    def expect_err(self, msg: str) -> E:
        return self._err

    @property
    @override
    def is_err(self) -> bool:
        return True

    @property
    @override
    def is_ok(self) -> bool:
        return False

    @override
    def map[U](self, op: Callable[[T], U]) -> "Result[U, E]":
        return Err(self._err)

    @override
    def map_or[U](self, default: U, f: Callable[[T], U]) -> U:
        return default

    @override
    def map_or_else[U](self, default: Callable[[], U], f: Callable[[T], U]) -> U:
        return default()

    @override
    def map_err[F](self, op: Callable[[E], F]) -> "Result[T, F]":
        return Err(op(self._err))

    @override
    def ok(self) -> "Option[T]":
        return Nothing()

    @override
    def unwrap(self) -> T:
        return self.expect("Called `Result.unwrap()` on an `Err` value")

    @override
    def unwrap_err(self) -> E:
        return self._err

    @override
    def unwrap_or(self, default: T) -> T:
        return default

    @override
    def unwrap_or_else(self, f: Callable[[], T]) -> T:
        return f()


Result = Ok[T, E] | Err[T, E]


def from_optional[T](opt: T | None) -> Option[T]:
    """Convert an optional value to an Option type.

    Args:
        opt: Optional value that may be None.

    Returns:
        Some(value) if opt is not None, otherwise Nothing.

    """
    return Some(opt) if opt is not None else Nothing()
