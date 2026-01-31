from abcount.model.common import PKaAttribute


class PKaClassBuilder:
    @classmethod
    def build(cls, **overrides):
        """
        Return a CustomPKaAttribute class with overridden values.
        Any attributes not given in overrides will
        fall back to the parent values.
        """
        return type("CustomPKaAttribute", (PKaAttribute,), overrides)
