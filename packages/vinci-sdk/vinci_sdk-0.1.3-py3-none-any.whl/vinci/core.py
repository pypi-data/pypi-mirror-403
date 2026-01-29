import functools


# so in other words,
# when writing a decorator i am
# this is a factory decorator function
def compute(profile="standard",min_scale=1):
    def decorator(func):
        print(f"[vinci] Registering {func.__name__} with profile:{profile}" )
        # so this wrapper is the "interceptor of the function"
        # so that i am able to change the behaviorof the function

        @functools.wraps(func)
        def wrapper(*args,**kwargs):
            return func (*args,**kwargs)
        return wrapper
    return decorator