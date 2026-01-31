from cidc_api.telemetry import trace_


def _stripper(x):
    if x and isinstance(x, str):
        return x.strip()
    else:
        return x


@trace_("sheet")
def strip_whitespaces(df, sheet=None):
    if sheet:
        df = df[sheet]

    df.rename(columns=_stripper, inplace=True)
    df = df.map(_stripper)
    df.replace("", None, inplace=True)

    return df
