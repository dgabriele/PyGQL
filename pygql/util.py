class Projectable(object):

    @classmethod
    def project(cls, keys, as_list=True):
        if as_list:
            return [getattr(cls, k) for k in keys]
        else:
            return {k: getattr(cls, k) for k in keys}
