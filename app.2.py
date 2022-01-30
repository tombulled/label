import dataclasses
import types
import typing

from typing import Any

import annotate

'''
Options:
    @repeatable (uses a list)
    @inherited (classes inherit annotations)

@repeatable
@inherited
@annotation
def route(*paths, **kwargs):
    ...

Marker:
    needs: key (overwrites)

Single Value:
    needs: key, value (overwrites)

Multi Value:
    needs: key, value/hook, resolver

Marker -> (key, value)
    value = None

Annotation
    value = hook(*args, **kwargs)

set(key, value)

Interfaces:
@annotate('description', 'foo')
@description('value')


>>> foo._annotations_
{'description': Annotation(key='description', value='An awesome function!', inherited=False, repeatable=False)}
'''

def identity(x):
    return x

def extract_annotations(obj):
    return {
        annotation.key: annotation.value
        for annotation in annotate.get(obj).values()
    }

@dataclasses.dataclass
class Route:
    path: str
    method: str

# TODO: Make this frozen
@dataclasses.dataclass
class Annotation:
    key: str
    value: Any = None

    inherited: bool = False # NOTE: Should this apply to methods?
    repeatable: bool = False

    # TODO: Use a flag (e.g. None/False) to indicate *all* targets
    targets: typing.Tuple[type] = dataclasses.field(default_factory=lambda: (type, object))

    def __call__(self, obj):
        if not isinstance(obj, self.targets):
            raise Exception('obj type not targetted by this annotation')

        if isinstance(obj, type) and not annotate.has(obj):
            orig_init_subclass = obj.__init_subclass__

            def init_subclass(cls, *args, **kwargs):
                orig_init_subclass(*args, **kwargs)

                annotate.init(cls)

                annotations = annotate.get(cls)

                cls._annotations_ = {
                    key: annotation
                    for key, annotation in annotations.items()
                    if annotation.inherited
                }
                
                return cls

            obj = type(
                obj.__name__,
                obj.__bases__,
                {
                    **obj.__dict__,
                    **dict(
                        __init_subclass__ = init_subclass,
                    )
                }
            )

        annotate.init(obj)

        annotations = annotate.get(obj)

        if self.repeatable:
            if self.key not in annotations:
                annotations[self.key] = dataclasses.replace(self, value = [self.value])
            else:
                annotations[self.key].value.append(self.value)
        else:
            annotations[self.key] = self

        return obj

# @dataclasses.dataclass(init=False)
# class Factory:
#     hook: typing.Callable = identity
#     marker: Marker

#     def __init__(self, *args, hook: typing.Callable = identity, **kwargs):
#         self.hook = hook
#         self.marker = Marker(*args, **kwargs)

#     def __call__(self, *args, **kwargs):
#         return dataclasses.replace(self.marker, value=self.hook(*args, **kwargs))

# route = Annotation('route', value_factory=Route, repeatable=True)

# @route('/a', method='GET')
# @route('/b', method='GET')
# def foo(): ...

# print(foo._annotations_)

def description(description: str) -> Annotation:
    return Annotation('description', description, inherited=False, repeatable=True)

@description('awesome!')
@description('cool!')
class Foo:
    def __init_subclass__(cls) -> None:
        print('orgin init subclass called')
        return cls

    def some_method(self): ...

class Bar(Foo):...
class Baz(Bar):...

print(Foo._annotations_)
print(Bar._annotations_)
print(Baz._annotations_)