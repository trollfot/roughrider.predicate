from dataclasses import dataclass
from roughrider.predicate.errors import Error, ConstraintsErrors
from roughrider.predicate.validators import Validator, Or, resolve_validators


@dataclass
class Document:
    id: str
    body: str = ''
    content_type: str = 'text/plain'


def non_empty_document(item):
    """Implementation of a validator/predicate
    """
    if not item.body:
        raise Error('Body is empty.')


def must_be_real_document(item):
    """Implementation of a validator/predicate
    """
    if item.id == 'test':
        raise Error('The item must not be a test document.')


class ContentType(Validator):

    def __init__(self, content_type):
        self.ct = content_type

    def __call__(self, item):
        if item.content_type != self.ct:
            raise Error(f'Expected {self.ct} and not {item.content_type}.')


class TestFunctionValidators:

    def test_single_resolution(self):
        document = Document(id='test', body='This is a test.')
        errors = resolve_validators([non_empty_document], document)
        assert errors is None

        document = Document(id='test', body='')
        errors = resolve_validators([non_empty_document], document)
        assert isinstance(errors, ConstraintsErrors)
        assert list(errors) == [Error('Body is empty.')]


    def test_multiple_resolution(self):
        document = Document(id='test', body='This is a test.')
        errors = resolve_validators(
            [non_empty_document, must_be_real_document], document)
        assert list(errors) == [
            Error('The item must not be a test document.')
        ]

        document = Document(id='test')
        errors = resolve_validators(
            [non_empty_document, must_be_real_document], document)
        assert list(errors) == [
            Error('Body is empty.'),
            Error('The item must not be a test document.')
        ]


class TestValidators:

    def test_single_resolution(self):
        document = Document(id='test', body='This is a test.')
        assert document.content_type == 'text/plain'
        errors = resolve_validators([ContentType('text/plain')], document)
        assert errors is None

        errors = resolve_validators([ContentType('text/html')], document)
        assert list(errors) == [
            Error('Expected text/html and not text/plain.')
        ]

    def test_multiple_resolution(self):
        document = Document(id='test', body='This is a test.')
        assert document.content_type == 'text/plain'
        errors = resolve_validators([
            ContentType('text/plain'),
            must_be_real_document
        ], document)
        assert list(errors) == [
            Error('The item must not be a test document.')
        ]

        errors = resolve_validators([
            ContentType('text/html'),
            must_be_real_document
        ], document)
        assert list(errors) == [
            Error('Expected text/html and not text/plain.'),
            Error('The item must not be a test document.')
        ]

        document = Document(
            id='not_test',
            body='<html></html>',
            content_type='text/html'
        )
        errors = resolve_validators([
            ContentType('text/html'),
            must_be_real_document
        ], document)
        assert errors is None


class TestOr:

    def test_basic_usage(self):
        import pytest

        _or = Or((ContentType('text/plain'), ContentType('text/html')))
        assert isinstance(_or, tuple)

        document = Document(id='test')
        assert _or(document) is None

        document = Document(id='test', content_type='application/json')
        with pytest.raises(ConstraintsErrors) as exc:
            _or(document)

        assert list(exc.value) == [
            Error('Expected text/plain and not application/json.'),
            Error('Expected text/html and not application/json.'),
        ]

    def test_stacked_or(self):
        import pytest

        _or = Or((
            ContentType('text/plain'),
            Or((ContentType('text/html'), non_empty_document))
        ))
        document = Document(id='test')
        assert _or(document) is None

        document = Document(id='test', content_type='application/json')
        with pytest.raises(ConstraintsErrors) as exc:
            _or(document)

        assert list(exc.value) == [
            Error('Expected text/plain and not application/json.'),
            Error('Expected text/html and not application/json.'),
            Error('Body is empty.'),
        ]

        _or = Or((
            ContentType('text/plain'),
            Or((
                Or((ContentType('text/html'), must_be_real_document)),
                non_empty_document))
            ))
        document = Document(id='123', content_type='application/json')
        assert _or(document) is None

        document = Document(id='test', content_type='application/json')
        with pytest.raises(ConstraintsErrors) as exc:
            _or(document)

        assert list(exc.value) == [
            Error('Expected text/plain and not application/json.'),
            Error('Expected text/html and not application/json.'),
            Error('The item must not be a test document.'),
            Error('Body is empty.'),
        ]