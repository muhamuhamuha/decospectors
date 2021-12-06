# def test_class_varparams_property():
#
#     def argskwargs_mock(*args, **kwargs):
#         return args, kwargs
#
#     def just_args_mock(*args):
#         return args
#
#     def just_kwargs_mock(**kwargs):
#         return kwargs
#
#     mock1 = __Decospector(argskwargs_mock, 'hello', farewell=0)
#     mock2 = __Decospector(just_args_mock, 'hello')
#     mock3 = __Decospector(just_kwargs_mock, farewell=0)
#
#     assert 'args' in mock1._varparams and 'kwargs' in mock1._varparams
#     assert 'args' in mock2._varparams and 'kwargs' not in mock2._varparams
#     assert 'kwargs' in mock3._varparams and 'args' not in mock3._varparams

