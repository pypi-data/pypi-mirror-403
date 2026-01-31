def as_functor(f, value=None):
    if value is None:

        def _f(pts, res):
            res[:] = f(pts)

        return _f

    def _f(pts, res):
        res[:] = f(pts)
        res -= value

    return _f
