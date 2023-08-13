"""Custom Streamlit components."""

import typing as tp

import streamlit as st

Generic = tp.TypeVar("Generic")


def selectbox_with_default(
    label: str,
    values: tp.Iterable[Generic],
    default: Generic | None = None,
    default_display: str = "<select>",
) -> Generic:
    """Add session state management and default value to selectbox.

    Args:
        label: selectbox label
        values: selectbox options
        default: pre-selected option. Defaults to None.
        default_display: pre-selected option display. Defaults to "<select>".

    Returns:
        selectbox selection.
    """
    # When changing pages, keys used by components in the first page are cleanup up
    # If you want to keep the state somewhere, you have to store it separately
    key = hash(label)
    key_save = key + 1
    if key not in st.session_state:
        st.session_state[key] = st.session_state.get(key_save)
    default = st.session_state[key]
    display_values = sorted(values)  # type: ignore
    if default in display_values:
        display_values.remove(default)
    selected = st.selectbox(
        label=label,
        options=(default, *display_values),
        format_func=lambda x: default_display if x is None else x,
        key=key,
    )
    st.session_state[key_save] = selected
    if selected is None:
        st.stop()
    return selected
