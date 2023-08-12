"""_summary_"""

import typing as tp

import streamlit as st

Generic = tp.TypeVar("Generic")


def selectbox_with_default(
    label: str,
    values: tp.Iterable[Generic],
    default: Generic | None = None,
    default_display: str = "<select>",
) -> Generic | None:
    """_summary_

    Args:
        label: _description_
        values: _description_
        default: _description_. Defaults to None.
        default_display: _description_. Defaults to "<select>".

    Returns:
        _description_
    """
    key = hash(label)
    if key not in st.session_state:
        st.session_state[key] = None
    default = st.session_state[key]
    st.session_state[key] = st.selectbox(
        label=label,
        options=(default, *sorted(values)),  # type: ignore
        format_func=lambda x: default_display if x is None else x,
    )
    if st.session_state[key] is None:
        st.stop()
    return st.session_state[key]
