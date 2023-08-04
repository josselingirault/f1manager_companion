import streamlit as st
import typing as tp
from dataclasses import dataclass, field
import src.constants as cst
from pathlib import Path


@dataclass
class TestData:
    name: str


@dataclass
class Buddy:
    testing: tp.Dict[str, TestData] = field(default_factory=dict)


def init_buddy() -> Buddy:
    for var_name in [x for x in vars(cst) if x.startswith("PATH_")]:
        path: Path = getattr(cst, var_name)
        path.mkdir(exist_ok=True)
    if "buddy" not in st.session_state:
        st.session_state.buddy = Buddy()
    return st.session_state.buddy  # type: ignore


def init_sidebar():
    with st.sidebar:
        st.title("JoyA's F1Manager Buddy")
        st.session_state.display_help = st.checkbox("Display help", value=True)
