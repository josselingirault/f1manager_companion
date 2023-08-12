"""Custom Streamlit components."""

import typing as tp

import streamlit as st

Generic = tp.TypeVar("Generic")


def selectbox_with_default(
    label: str,
    values: tp.Iterable[Generic],
    default: Generic | None = None,
    default_display: str = "<select>",
) -> Generic | None:
    """Add session state management and default value to selectbox.

    Args:
        label: selectbox label
        values: selectbox options
        default: pre-selected option. Defaults to None.
        default_display: pre-selected option display. Defaults to "<select>".

    Returns:
        selectbox selection.
    """
    key = hash(label)
    if key not in st.session_state:
        st.session_state[key] = None
    default = st.session_state[key]
    selected = st.selectbox(
        label=label,
        options=(default, *sorted(values)),  # type: ignore
        format_func=lambda x: default_display if x is None else x,
    )
    st.session_state[key] = selected
    if selected is None:
        st.stop()
    return selected
