"""Implements the ve.direct text protocol."""

import enum

import pint

from . import defs

_LF = 0x0A
_CR = 0x0D
_TAB = 0x09
_CHECKSUM = 'Checksum'

# Parses for certain unique field values.
_PARSERS = {
    defs.FW.label: lambda x: '%d.%d' % (int(x) // 100, int(x) % 100),
    defs.LOAD.label: lambda x: 1 if x == 'ON' else 0,
}


class _Source:
    def __init__(self, f):
        self._f = f
        self._ready = b''

    def next(self) -> int:
        while self._ready is None or len(self._ready) == 0:
            self._ready = self._f.read(1000)

        ch, self._ready = self._ready[0], self._ready[1:]
        return ch


def _get_value(label: str, value: bytearray) -> object:
    """Parses the value in a label specific way."""
    if label == _CHECKSUM:
        return value[0]

    value = value.decode()
    try:
        if label not in defs.FIELD_MAP:
            return int(value)
        field = defs.FIELD_MAP[label]
        kind = field.kind()
        if field.label in _PARSERS:
            value = _PARSERS[field.label](value)
        if kind is not None:
            if isinstance(kind, pint.Quantity):
                return int(value) * kind
            elif issubclass(kind, enum.Enum):
                return kind(int(value))
            elif issubclass(kind, str):
                return value
            assert False, 'Unhandled kind %s' % kind
        return int(value)
    except ValueError as ex:
        return value


def _get_line(src):
    label = bytearray()

    while True:
        ch = src.next()
        if ch == _TAB:
            break
        label.append(ch)

    value = bytearray((src.next(), ))

    while True:
        ch = src.next()
        if ch == _CR:
            break
        value += bytes([ch])

    ch = src.next()
    if ch != _LF:
        raise ProtocolError('got a 0x%x, want a LF' % ch)

    label = label.decode()
    return label, _get_value(label, value)


def parse(src):
    src = _Source(src)

    while src.next() != _LF:
        pass

    while True:
        label, value = _get_line(src)
        if label == _CHECKSUM:
            break

    while True:
        fields = {}

        while True:
            label, value = _get_line(src)
            if label == _CHECKSUM:
                # End of a block
                break
            fields[label] = value

        print(fields)
        yield fields
