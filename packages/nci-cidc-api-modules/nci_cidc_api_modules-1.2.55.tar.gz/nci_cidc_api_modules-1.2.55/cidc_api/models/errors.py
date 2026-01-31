class ValueLocError(ValueError):
    """A special case of ValueError that allows us to carry along the 'loc' location where a pydantic
    validation error occured."""

    def __init__(self, *args, loc: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.loc = (loc,)  # Make a tuple to match pydantic's loc structure
