import shutil
from datetime import datetime
from pathlib import Path

import streamlit as st

# ------------------------------------------------------------------
# Page setup
# ------------------------------------------------------------------
st.set_page_config(page_title="Cozy Files", page_icon="🗂️", layout="centered")

BASE = Path("my_space")  # everything lives safely inside this folder
BASE.mkdir(exist_ok=True)

# Warm, friendly palette
CREAM = "#FFF8F0"
TERRACOTTA = "#E07A5F"
NAVY = "#3D405B"
SAGE = "#81B29A"
SAND = "#F2CC8F"

st.markdown(
    f"""
    <style>
    .stApp {{ background-color: {CREAM}; }}
    html, body, [class*="css"] {{ color: {NAVY}; }}
    h1, h2, h3 {{ color: {NAVY} !important; font-family: Georgia, 'Times New Roman', serif; }}

    .hero {{
        background: linear-gradient(135deg, {TERRACOTTA} 0%, {SAND} 100%);
        padding: 28px 30px; border-radius: 22px; color: white;
        box-shadow: 0 8px 24px rgba(224,122,95,.25); margin-bottom: 22px;
    }}
    .hero h1 {{ color: white !important; margin: 0 0 6px 0; font-size: 2rem; }}
    .hero p  {{ margin: 0; font-size: 1.05rem; opacity: .95; }}

    .stat {{
        background: white; border-radius: 18px; padding: 16px 18px; text-align: center;
        border: 1px solid #F0E2D2; box-shadow: 0 3px 10px rgba(61,64,91,.06);
    }}
    .stat .num {{ font-size: 1.8rem; font-weight: 700; color: {TERRACOTTA}; }}
    .stat .lbl {{ font-size: .85rem; color: {NAVY}; opacity: .75; }}

    .item {{
        background: white; border-radius: 14px; padding: 10px 16px; margin-bottom: 8px;
        border-left: 5px solid {SAGE}; display: flex; justify-content: space-between;
        box-shadow: 0 2px 6px rgba(61,64,91,.05);
    }}
    .item.folder {{ border-left-color: {TERRACOTTA}; }}
    .item .meta {{ opacity: .6; font-size: .85rem; }}

    .stButton > button, .stFormSubmitButton > button {{
        background-color: {TERRACOTTA}; color: white; border: none;
        border-radius: 12px; padding: .5rem 1.4rem; font-weight: 600;
    }}
    .stButton > button:hover, .stFormSubmitButton > button:hover {{
        background-color: {NAVY}; color: white;
    }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 8px; }}
    .stTabs [data-baseweb="tab"] {{
        background: white; border-radius: 12px; padding: 8px 16px;
        border: 1px solid #F0E2D2;
    }}
    .stTabs [aria-selected="true"] {{ background: {SAGE}; color: white !important; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def resolve(name: str):
    """Turn a typed name into a path inside BASE (blocks '../' tricks)."""
    name = name.strip().strip("/\\")
    if not name:
        return None
    p = (BASE / name).resolve()
    root = BASE.resolve()
    if p == root or root not in p.parents:
        return None
    return p


def rel(p: Path) -> str:
    return str(p.relative_to(BASE))


def all_items():
    return sorted(BASE.rglob("*"), key=lambda p: rel(p).lower())


def human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def notify(msg: str, icon: str = "✅"):
    st.session_state["flash"] = (msg, icon)
    st.rerun()


def greeting() -> str:
    h = datetime.now().hour
    if h < 12:
        return "Good morning"
    if h < 17:
        return "Good afternoon"
    return "Good evening"


if "flash" in st.session_state:
    msg, icon = st.session_state.pop("flash")
    st.toast(msg, icon=icon)

# ------------------------------------------------------------------
# Header + stats
# ------------------------------------------------------------------
st.markdown(
    f"""
    <div class="hero">
        <h1>🗂️ {greeting()}!</h1>
        <p>Welcome to your cozy little file space. Create, tidy up and
        organise your folders and files, nothing here is scary.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

items = all_items()
folders = [p for p in items if p.is_dir()]
files = [p for p in items if p.is_file()]
total = sum(p.stat().st_size for p in files)

c1, c2, c3 = st.columns(3)
for col, num, lbl in (
    (c1, len(folders), "folders"),
    (c2, len(files), "files"),
    (c3, human_size(total), "stored"),
):
    col.markdown(
        f'<div class="stat"><div class="num">{num}</div><div class="lbl">{lbl}</div></div>',
        unsafe_allow_html=True,
    )

st.write("")
tab_browse, tab_create, tab_edit, tab_delete = st.tabs(
    ["📂 Browse", "➕ Create", "✏️ Edit", "🗑️ Delete"]
)

# ------------------------------------------------------------------
# Browse
# ------------------------------------------------------------------
with tab_browse:
    st.subheader("Everything you have")
    if not items:
        st.info("It's quiet in here. Head over to **Create** to make your first folder or file! 🌱")
    for p in items:
        depth = len(p.relative_to(BASE).parts) - 1
        indent = "&nbsp;" * 6 * depth
        if p.is_dir():
            count = sum(1 for _ in p.iterdir())
            st.markdown(
                f'<div class="item folder"><span>{indent}📁 <b>{p.name}</b></span>'
                f'<span class="meta">{count} item(s)</span></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="item"><span>{indent}📄 {p.name}</span>'
                f'<span class="meta">{human_size(p.stat().st_size)}</span></div>',
                unsafe_allow_html=True,
            )

    if files:
        st.divider()
        st.subheader("Peek inside a file")
        pick = st.selectbox("Choose a file to read", [rel(f) for f in files], key="read_pick")
        try:
            st.code((BASE / pick).read_text(encoding="utf-8") or "(this file is empty)", language=None)
        except UnicodeDecodeError:
            st.warning("This doesn't look like a text file, so I can't show it here.")

# ------------------------------------------------------------------
# Create
# ------------------------------------------------------------------
with tab_create:
    parent_options = ["(main space)"] + [rel(f) for f in folders]

    st.subheader("New folder")
    with st.form("new_folder", clear_on_submit=True):
        parent = st.selectbox("Where should it live?", parent_options, key="fo_parent")
        name = st.text_input("Folder name", placeholder="e.g. holiday-photos")
        if st.form_submit_button("Create folder"):
            full = name if parent == "(main space)" else f"{parent}/{name}"
            p = resolve(full) if name.strip() else None
            if p is None:
                st.error("Please enter a valid folder name.")
            elif p.exists():
                st.warning("Oops, something with that name already exists. Try another one!")
            else:
                p.mkdir(parents=True)
                notify(f"Folder '{name}' is ready!", "📁")

    st.divider()
    st.subheader("New file")
    with st.form("new_file", clear_on_submit=True):
        parent = st.selectbox("Where should it live?", parent_options, key="fi_parent")
        fname = st.text_input("File name (with extension)", placeholder="e.g. notes.txt")
        content = st.text_area("What would you like to write?", height=150)
        if st.form_submit_button("Create file"):
            full = fname if parent == "(main space)" else f"{parent}/{fname}"
            p = resolve(full) if fname.strip() else None
            if p is None:
                st.error("Please enter a valid file name.")
            elif p.exists():
                st.warning("That file already exists. Pick a different name!")
            else:
                p.write_text(content, encoding="utf-8")
                notify(f"'{fname}' created!", "📝")

# ------------------------------------------------------------------
# Edit
# ------------------------------------------------------------------
with tab_edit:
    st.subheader("Rename or change things")
    if not items:
        st.info("Nothing to edit yet. Create something first! 🌱")
    else:
        choice = st.selectbox("What would you like to edit?", [rel(p) for p in items], key="edit_pick")
        target = BASE / choice

        if target.is_dir():
            new_name = st.text_input("New folder name", value=target.name, key=f"rn_{choice}")
            if st.button("Rename folder"):
                if not new_name.strip() or "/" in new_name or "\\" in new_name:
                    st.error("Please use a simple name without slashes.")
                elif (target.parent / new_name).exists():
                    st.warning("That name is already taken.")
                else:
                    target.rename(target.parent / new_name)
                    notify("Folder renamed!", "✏️")
        else:
            mode = st.radio(
                "What do you want to do?",
                ["Rename", "Overwrite content", "Add to the end"],
                horizontal=True,
                key=f"mode_{choice}",
            )
            if mode == "Rename":
                new_name = st.text_input("New file name", value=target.name, key=f"fr_{choice}")
                if st.button("Rename file"):
                    if not new_name.strip() or "/" in new_name or "\\" in new_name:
                        st.error("Please use a simple name without slashes.")
                    elif (target.parent / new_name).exists():
                        st.warning("That name is already taken.")
                    else:
                        target.rename(target.parent / new_name)
                        notify("File renamed!", "✏️")
            elif mode == "Overwrite content":
                try:
                    current = target.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    current = ""
                    st.warning("This isn't a plain text file, so I can't edit it here.")
                text = st.text_area("New content", value=current, height=200, key=f"ow_{choice}")
                if st.button("Save changes"):
                    target.write_text(text, encoding="utf-8")
                    notify("Saved!", "💾")
            else:
                extra = st.text_area("What should I add?", height=150, key=f"ap_{choice}")
                if st.button("Add it"):
                    with open(target, "a", encoding="utf-8") as fs:
                        fs.write(extra)
                    notify("Added to your file!", "➕")

# ------------------------------------------------------------------
# Delete
# ------------------------------------------------------------------
with tab_delete:
    st.subheader("Tidy up")
    if not items:
        st.info("Nothing to delete. It's already tidy! ✨")
    else:
        choice = st.selectbox("What would you like to remove?", [rel(p) for p in items], key="del_pick")
        target = BASE / choice

        confirmed = True
        if target.is_dir():
            inside = [p for p in target.rglob("*")]
            if inside:
                n_files = sum(1 for p in inside if p.is_file())
                st.warning(
                    f"This folder isn't empty, it holds {n_files} file(s). "
                    "Deleting it will remove everything inside too."
                )
                confirmed = st.checkbox("Yes, delete the folder and everything in it", key=f"cf_{choice}")

        if st.button("Delete", disabled=not confirmed):
            if target.is_dir():
                shutil.rmtree(target)  # removes folders even when they contain files
            else:
                target.unlink()
            notify(f"'{target.name}' is gone.", "🧹")

st.write("")
st.caption("Made with care 🧡  ·  everything is stored in the 'my_space' folder next to this app")clea