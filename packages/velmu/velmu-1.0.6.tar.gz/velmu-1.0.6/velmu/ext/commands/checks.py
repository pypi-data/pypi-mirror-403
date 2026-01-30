from .core import Context

def check(predicate):
    def decorator(func):
        if not hasattr(func, 'checks'):
            func.checks = []
        func.checks.append(predicate)
        return func
    return decorator

def has_permissions(**perms):
    def predicate(ctx: Context):
        # TODO: Check actual permissions in ctx.author.permissions_in(ctx.channel)
        # For now, return True or check simple flags if available in User object
        return True 
    return check(predicate)

def is_owner():
    def predicate(ctx: Context):
        # return ctx.author.id == ctx.bot.owner_id
        return True
    return check(predicate)
