# app_ubuntu_terminal_final_v10.py
# Jalankan: streamlit run app_ubuntu_terminal_final_v10.py --server.port 8501 --server.address 0.0.0.0
# Python 3.14 kompatibel - Professional UI with auto-sync

import io
import re
import json
import hashlib
import os
import time
from datetime import datetime

import pandas as pd
import streamlit as st

# ============================================================================
# CONFIG & STYLING
# ============================================================================

st.set_page_config(page_title="Program Pesanan 3 Tahap", layout="wide")

# Professional dark green theme
CSS = """
<style>
:root {
    --primary-green: #2d6e2c;
    --secondary-green: #3d8940;
    --accent-green: #4caf50;
    --dark-bg: #0d0d0d;
    --card-bg: #1a1a1a;
    --border-color: #333;
    --text-primary: #e5e5e5;
    --text-secondary: #b0b0b0;
}

.stApp {
    background: var(--dark-bg);
    color: var(--text-primary);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
}

/* Buttons */
.stButton>button, .stDownloadButton>button {
    background: var(--primary-green);
    color: white;
    border: none;
    border-radius: 6px;
    padding: 0.6rem 1.2rem;
    font-weight: 500;
    transition: all 0.2s ease;
}

.stButton>button:hover, .stDownloadButton>button:hover {
    background: var(--secondary-green);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(45, 110, 44, 0.3);
}

.stButton>button[kind="primary"] {
    background: var(--accent-green);
    font-size: 1rem;
    padding: 0.75rem 2rem;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: var(--card-bg);
    padding: 0.5rem;
    border-radius: 8px;
}

.stTabs [data-baseweb="tab"] {
    background-color: transparent;
    border-radius: 6px;
    padding: 0.6rem 1.5rem;
    color: var(--text-secondary);
    border: 1px solid transparent;
    font-weight: 500;
}

.stTabs [data-baseweb="tab"]:hover {
    background-color: rgba(45, 110, 44, 0.1);
    border-color: var(--primary-green);
}

.stTabs [aria-selected="true"] {
    background-color: var(--primary-green);
    color: white;
    border-color: var(--primary-green);
}

/* Forms */
div[data-testid="stForm"] {
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 1.5rem;
    background: var(--card-bg);
}

/* Login card - clean minimal */
.login-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 70vh;
}

.login-card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 3rem 2.5rem;
    margin: 0 auto;
    max-width: 400px;
    width: 100%;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
}

.login-header {
    text-align: center;
    margin-bottom: 2rem;
}

.login-title {
    font-size: 2.5rem;
    font-weight: 700;
    color: var(--accent-green);
    margin: 0;
    letter-spacing: -0.5px;
}

.login-subtitle {
    color: var(--text-secondary);
    font-size: 0.95rem;
    margin-top: 0.5rem;
}

/* Input fields */
.stTextInput input, .stSelectbox select {
    background: var(--dark-bg);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    color: var(--text-primary);
    padding: 0.75rem;
    font-size: 1rem;
}

.stTextInput input:focus, .stSelectbox select:focus {
    border-color: var(--primary-green);
    box-shadow: 0 0 0 2px rgba(45, 110, 44, 0.2);
}

/* Data editor */
.stDataFrame {
    border: 1px solid var(--border-color);
    border-radius: 8px;
}

/* Info/Warning boxes */
.stInfo {
    background: rgba(45, 110, 44, 0.1);
    border-left: 4px solid var(--primary-green);
}

.stSuccess {
    background: rgba(76, 175, 80, 0.1);
    border-left: 4px solid var(--accent-green);
}

.stWarning {
    background: rgba(255, 152, 0, 0.1);
    border-left: 4px solid #ff9800;
}

/* Expander */
.streamlit-expanderHeader {
    background: var(--card-bg);
    border-radius: 6px;
    border: 1px solid var(--border-color);
}

/* Caption text */
.stCaption {
    color: var(--text-secondary);
    font-size: 0.875rem;
}

/* Headers */
h1, h2, h3 {
    color: var(--text-primary);
    font-weight: 600;
}

/* Divider */
hr {
    border-color: var(--border-color);
    opacity: 0.3;
}

/* Sync indicator */
.sync-indicator {
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: var(--primary-green);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-size: 0.875rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    z-index: 1000;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ============================================================================
# MOBILE DETECTION
# ============================================================================

def is_mobile():
    """Detect if accessing from mobile device"""
    try:
        headers = st.context.headers
        if headers:
            user_agent = headers.get("User-Agent", "").lower()
            mobile_keywords = ["mobile", "android", "iphone", "ipad", "tablet", "phone"]
            return any(keyword in user_agent for keyword in mobile_keywords)
    except:
        pass
    return False

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def make_code(n=4):
    """Generate random lowercase code"""
    import secrets, string
    return ''.join(secrets.choice(string.ascii_lowercase) for _ in range(n))

def file_fingerprint(b: bytes) -> str:
    """Generate SHA1 hash for file tracking"""
    return hashlib.sha1(b).hexdigest()

def smart_read(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Read CSV/XLSX with auto-detect encoding & delimiter"""
    name = filename.lower()
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(file_bytes))

    for enc in ["utf-8-sig", "utf-8", "latin-1"]:
        try:
            return pd.read_csv(io.BytesIO(file_bytes), sep=None, engine="python", encoding=enc)
        except Exception:
            continue
    raise RuntimeError("Failed to read CSV/XLSX file")

def normalize_cols(cols):
    """Normalize column names for matching"""
    return [re.sub(r"\s+", " ", str(c)).strip().lower() for c in cols]

VAR_SYNS = ["variation", "variations", "variant", "variants", "variasi", "varian",
            "product variant", "sku variant", "nama variasi", "opsi", "option", "options"]
QTY_SYNS = ["qty", "quantity", "jumlah", "kuantitas", "qty ordered", "jumlah beli",
            "order qty", "qty pesanan", "qty order", "jumlah order", "quantity ordered"]
NAME_SYNS = ["product name", "nama produk", "title", "judul", "name", "product_title",
             "sku", "sku id", "nama sku", "deskripsi"]

def find_column_by_name(df, search_names):
    """Find column by exact or partial name match (case-insensitive)"""
    norm = normalize_cols(df.columns)
    search_names_lower = [s.lower() for s in search_names]

    # Exact match first
    for search in search_names_lower:
        if search in norm:
            return norm.index(search)

    # Partial match
    for i, col in enumerate(norm):
        for search in search_names_lower:
            if search in col or col in search:
                return i

    return None

def find_best_match(df, synonyms, fallback_type="text"):
    """Find best matching column based on synonyms"""
    norm = normalize_cols(df.columns)

    for syn in synonyms:
        if syn in norm:
            return norm.index(syn)

    for i, c in enumerate(norm):
        for syn in synonyms:
            if syn in c:
                return i

    if fallback_type == "text":
        scores = []
        for i, col in enumerate(df.columns):
            s = df[col].astype(str)
            nonnum = (s.str.replace(r"[0-9\.\-]", "", regex=True).str.strip() != "").mean()
            scores.append((nonnum, i))
        scores.sort(reverse=True)
        return scores[0][1] if scores else 0
    else:
        scores = []
        for i, col in enumerate(df.columns):
            s = pd.to_numeric(df[col], errors="coerce")
            scores.append((s.notna().mean(), i))
        scores.sort(reverse=True)
        return scores[0][1] if scores else (0 if len(df.columns) == 1 else 1)

def build_base_df(df, var_col, qty_col, productname_col, skuid_col, brand_col):
    """Build base dataframe with FIXED column names from user selections"""
    out = pd.DataFrame({
        "Variation": df[var_col].astype(str).str.strip(),
        "Quantity": pd.to_numeric(df[qty_col], errors="coerce"),
        "ProductName": df[productname_col].astype(str).str.strip(),
        "SkuID": df[skuid_col].astype(str).str.strip(),
        "Brand": df[brand_col].astype(str).str.strip(),
        "OriginalIndex": range(len(df))
    })

    if not out["Quantity"].isna().all():
        out["Quantity"] = out["Quantity"].fillna(0)
        if (out["Quantity"] % 1 == 0).all():
            out["Quantity"] = out["Quantity"].astype(int)

    return out

def tokenize(text):
    """Extract words from text"""
    return re.findall(r"[\w\-]+", str(text).lower(), flags=re.UNICODE)

def categorize_by_keywords(series, keywords):
    """Categorize by keywords"""
    if not keywords:
        return pd.Series([""] * len(series), index=series.index)

    kws = [k.lower() for k in keywords if k.strip()]

    def match_first(text):
        t = str(text).lower()
        toks = set(tokenize(t))
        for k in kws:
            if k in toks:
                return k
        for k in kws:
            if k in t:
                return k
        return ""

    return series.apply(match_first)

def infer_brand(text, matched_kw):
    """Infer brand from text and keyword"""
    t = str(text).lower()
    toks = tokenize(t)

    if matched_kw:
        try:
            idx = toks.index(matched_kw)
            if idx > 0 and not toks[idx - 1].isdigit():
                return toks[idx - 1]
        except ValueError:
            pass

    for tok in toks:
        if not tok.isdigit():
            return tok
    return ""

def to_csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8-sig")

def to_xlsx_bytes(df):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return buf.getvalue()

def save_session(session_code, state_data, file_bytes=None, file_name=None):
    """Auto-save session to storage (with file data)"""
    os.makedirs("storage", exist_ok=True)

    json_path = os.path.join("storage", f"{session_code}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(state_data, f, ensure_ascii=False, indent=2)

    if file_bytes and file_name:
        file_path = os.path.join("storage", f"{session_code}_data_{file_name}")
        with open(file_path, "wb") as f:
            f.write(file_bytes)

def load_session(session_code):
    """Load session from storage"""
    path = os.path.join("storage", f"{session_code}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def load_session_file(session_code, file_name):
    """Load file data from storage"""
    path = os.path.join("storage", f"{session_code}_data_{file_name}")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    return None

# ============================================================================
# AUTO-SYNC MECHANISM (CRITICAL FIX)
# ============================================================================

def check_for_updates(session_code, current_state):
    """Check if storage has newer updates from other devices"""
    saved = load_session(session_code)
    if not saved:
        return False

    # Check if saved state is newer
    saved_time = saved.get("saved_at", "")
    current_time = current_state.get("last_checked", "")

    if saved_time > current_time:
        # Update state from storage
        st.session_state["processed_ids"] = set(saved.get("processed_ids", []))
        st.session_state["confirmed_ids"] = set(saved.get("confirmed_ids", []))
        st.session_state["keywords"] = saved.get("keywords", [])
        st.session_state["last_checked"] = datetime.utcnow().isoformat() + "Z"
        return True

    return False

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "session_code" not in st.session_state:
    st.session_state["session_code"] = ""

if "processed_ids" not in st.session_state:
    st.session_state["processed_ids"] = set()

if "confirmed_ids" not in st.session_state:
    st.session_state["confirmed_ids"] = set()

if "keywords" not in st.session_state:
    st.session_state["keywords"] = []

if "selected_columns" not in st.session_state:
    st.session_state["selected_columns"] = {}

if "loaded_file_bytes" not in st.session_state:
    st.session_state["loaded_file_bytes"] = None

if "loaded_file_name" not in st.session_state:
    st.session_state["loaded_file_name"] = None

if "text_search" not in st.session_state:
    st.session_state["text_search"] = ""

if "last_checked" not in st.session_state:
    st.session_state["last_checked"] = ""

if "last_sync_check" not in st.session_state:
    st.session_state["last_sync_check"] = 0

# ============================================================================
# LOGIN SCREEN (CLEAN MINIMAL DESIGN)
# ============================================================================

if not st.session_state["logged_in"]:
    mobile_mode = is_mobile()

    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<div class="login-card">', unsafe_allow_html=True)

    st.markdown("""
    <div class="login-header">
        <h1 class="login-title">LOGIN</h1>
        <p class="login-subtitle">Program Pesanan 3 Tahap</p>
    </div>
    """, unsafe_allow_html=True)

    # Generate button ONLY for desktop/server
    if not mobile_mode:
        col_input, col_gen = st.columns([3, 1])
        with col_input:
            input_code = st.text_input(
                "Session Code",
                max_chars=4,
                placeholder="abcd",
                label_visibility="collapsed"
            ).lower()
        with col_gen:
            if st.button("Generate", use_container_width=True, key="gen_btn"):
                new_code = make_code(4)
                st.info(f"**{new_code}**")
                st.caption("Copy this code")
                st.stop()
    else:
        input_code = st.text_input(
            "Session Code",
            max_chars=4,
            placeholder="abcd",
            label_visibility="collapsed"
        ).lower()

    st.write("")  # spacing

    if st.button("Continue", type="primary", use_container_width=True):
        if len(input_code) == 4 and input_code.isalpha() and input_code.islower():
            st.session_state["session_code"] = input_code
            st.session_state["logged_in"] = True

            saved = load_session(input_code)
            if saved:
                st.session_state["keywords"] = saved.get("keywords", [])
                st.session_state["processed_ids"] = set(saved.get("processed_ids", []))
                st.session_state["confirmed_ids"] = set(saved.get("confirmed_ids", []))
                st.session_state["selected_columns"] = saved.get("selected_columns", {})
                st.session_state["last_checked"] = saved.get("saved_at", "")

                file_name = saved.get("file_name")
                if file_name:
                    file_bytes = load_session_file(input_code, file_name)
                    if file_bytes:
                        st.session_state["loaded_file_bytes"] = file_bytes
                        st.session_state["loaded_file_name"] = file_name

            st.rerun()
        else:
            st.error("Code must be 4 lowercase letters (a-z)")

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ============================================================================
# LOGGED IN - HEADER
# ============================================================================

session_code = st.session_state["session_code"]
mobile_mode = is_mobile()

# AUTO-SYNC CHECK (every page load)
current_time = time.time()
if current_time - st.session_state.get("last_sync_check", 0) > 2:  # Check every 2 seconds
    st.session_state["last_sync_check"] = current_time
    current_state = {"last_checked": st.session_state.get("last_checked", "")}
    if check_for_updates(session_code, current_state):
        st.rerun()  # Reload dengan data terbaru

col_header1, col_header2 = st.columns([6, 1])
with col_header1:
    st.markdown(f"""
    ### nariyahsore:~$ session `{session_code}`
    **Program Pesanan 3 Tahap** • Auto-sync • {("Mobile" if mobile_mode else "Desktop")}
    """)
with col_header2:
    st.write("")
    st.write("")
    if st.button("Logout", use_container_width=True):
        st.session_state["logged_in"] = False
        st.session_state["session_code"] = ""
        st.session_state["loaded_file_bytes"] = None
        st.session_state["loaded_file_name"] = None
        st.rerun()

# ============================================================================
# FILE UPLOAD / AUTO-LOAD
# ============================================================================

if st.session_state["loaded_file_bytes"] and st.session_state["loaded_file_name"]:
    uploaded = None
    raw_bytes = st.session_state["loaded_file_bytes"]
    file_name = st.session_state["loaded_file_name"]

    st.info(f"File: **{file_name}** (auto-loaded)")

    if st.button("Upload New File"):
        st.session_state["loaded_file_bytes"] = None
        st.session_state["loaded_file_name"] = None
        st.rerun()
else:
    uploaded = st.file_uploader("Upload CSV/XLSX file", type=["csv", "xlsx", "xls"])

    if not uploaded:
        st.warning("Please upload a file to continue")
        st.stop()

    raw_bytes = uploaded.read()
    file_name = uploaded.name

file_hash = file_fingerprint(raw_bytes)

try:
    raw_df = smart_read(raw_bytes, file_name)
except Exception as e:
    st.error(f"Failed to read file: {e}")
    st.stop()

if uploaded:
    st.success(f"Loaded: **{file_name}** • {len(raw_df)} rows, {len(raw_df.columns)} columns")

    # Save file to session immediately after upload
    timestamp = datetime.utcnow().isoformat() + "Z"
    initial_state = {
        "saved_at": timestamp,
        "app_version": "v10",
        "file_name": file_name,
        "file_hash": file_hash,
        "keywords": st.session_state.get("keywords", []),
        "processed_ids": [],
        "confirmed_ids": [],
        "selected_columns": {}
    }
    save_session(session_code, initial_state, raw_bytes, file_name)
    st.session_state["loaded_file_bytes"] = raw_bytes
    st.session_state["loaded_file_name"] = file_name
    st.session_state["last_checked"] = timestamp

with st.expander("View columns"):
    st.dataframe(pd.DataFrame({"Column": raw_df.columns}), use_container_width=True)

# ============================================================================
# COLUMN SELECTION
# ============================================================================

st.markdown("### Column Settings")
st.caption("Map your file columns to output format (Variation | Quantity | Product Name | SkuID)")

# Auto-detect columns based on actual column names (native detection)
# Order: Variation, Quantity, Product Name, SkuID
var_idx = find_column_by_name(raw_df, ["variation", "variasi", "variant", "kode sarung", "kode"])
if var_idx is None:
    var_idx = find_best_match(raw_df, VAR_SYNS, "text") or 0

qty_idx = find_column_by_name(raw_df, ["quantity", "qty", "jumlah", "kuantitas"])
if qty_idx is None:
    qty_idx = find_best_match(raw_df, QTY_SYNS, "num") or (0 if len(raw_df.columns) == 1 else 1)

productname_idx = find_column_by_name(raw_df, ["product name", "nama produk", "product", "nama", "title", "judul"])
if productname_idx is None:
    productname_idx = find_best_match(raw_df, NAME_SYNS, "text") or 0

skuid_idx = find_column_by_name(raw_df, ["skuid", "sku id", "sku", "product id"])
if skuid_idx is None:
    skuid_idx = find_best_match(raw_df, NAME_SYNS, "text") or 0

brand_idx = find_column_by_name(raw_df, ["brand", "merk", "merek", "brand name"])
if brand_idx is None:
    brand_idx = productname_idx

saved_cols = st.session_state.get("selected_columns", {})
if saved_cols and saved_cols.get("file_hash") == file_hash:
    # Backward compatibility: handle old format
    var_col = saved_cols.get("var_col", raw_df.columns[var_idx])
    qty_col = saved_cols.get("qty_col", raw_df.columns[qty_idx])
    productname_col = saved_cols.get("productname_col", saved_cols.get("type_col", saved_cols.get("text_col", raw_df.columns[productname_idx])))
    skuid_col = saved_cols.get("skuid_col", saved_cols.get("text_col", raw_df.columns[skuid_idx]))
    brand_col = saved_cols.get("brand_col", saved_cols.get("text_col", raw_df.columns[brand_idx]))

    if var_col not in raw_df.columns:
        var_col = raw_df.columns[var_idx]
    if qty_col not in raw_df.columns:
        qty_col = raw_df.columns[qty_idx]
    if productname_col not in raw_df.columns:
        productname_col = raw_df.columns[productname_idx]
    if skuid_col not in raw_df.columns:
        skuid_col = raw_df.columns[skuid_idx]
    if brand_col not in raw_df.columns:
        brand_col = raw_df.columns[brand_idx]
else:
    var_col = raw_df.columns[var_idx]
    qty_col = raw_df.columns[qty_idx]
    productname_col = raw_df.columns[productname_idx]
    skuid_col = raw_df.columns[skuid_idx]
    brand_col = raw_df.columns[brand_idx]

# Layout: compact 2-column grid for both mobile and desktop
# Mobile: smaller dropdowns, Desktop: same layout
c1, c2 = st.columns([1, 1])
with c1:
    var_col = st.selectbox(
        "Variation",
        options=list(raw_df.columns),
        index=list(raw_df.columns).index(var_col),
        key="sel_var"
    )
with c2:
    qty_col = st.selectbox(
        "Quantity",
        options=list(raw_df.columns),
        index=list(raw_df.columns).index(qty_col),
        key="sel_qty"
    )

c3, c4 = st.columns([1, 1])
with c3:
    productname_col = st.selectbox(
        "Product Name",
        options=list(raw_df.columns),
        index=list(raw_df.columns).index(productname_col),
        key="sel_productname"
    )
with c4:
    skuid_col = st.selectbox(
        "SkuID",
        options=list(raw_df.columns),
        index=list(raw_df.columns).index(skuid_col),
        key="sel_skuid"
    )

c5, c6 = st.columns([1, 1])
with c5:
    brand_col = st.selectbox(
        "Brand/Merk",
        options=list(raw_df.columns),
        index=list(raw_df.columns).index(brand_col),
        key="sel_brand"
    )

st.session_state["selected_columns"] = {
    "file_hash": file_hash,
    "var_col": var_col,
    "qty_col": qty_col,
    "productname_col": productname_col,
    "skuid_col": skuid_col,
    "brand_col": brand_col
}

# ============================================================================
# KEYWORD FILTER & TEXT SEARCH (UPDATED)
# ============================================================================

st.markdown("### Filter & Search")

col_filter1, col_filter2 = st.columns([1, 1])

with col_filter1:
    st.markdown("**Tipe**")
    kw_input = st.text_input(
        "Filter tipe",
        value=", ".join(st.session_state["keywords"]) if st.session_state["keywords"] else "",
        placeholder="ssl, stk",
        help="Separate with comma/space. Example: ssl, stk, doby, songket",
        label_visibility="collapsed",
        key="kw_filter"
    )
    cur_keywords = [k.strip() for k in re.split(r"[\s,]+", kw_input) if k.strip()]
    if cur_keywords != st.session_state["keywords"]:
        st.session_state["keywords"] = cur_keywords
    keywords = st.session_state["keywords"]
    st.caption(f"{len(keywords)} type(s) active" if keywords else "All types displayed")

with col_filter2:
    st.markdown("**Kode**")
    text_search = st.text_input(
        "Search code",
        value=st.session_state.get("text_search", ""),
        placeholder="34, 36",
        help="Search by product code or variation",
        label_visibility="collapsed",
        key="text_search_input"
    )
    st.session_state["text_search"] = text_search
    if text_search:
        st.caption(f"Searching: '{text_search}'")
    else:
        st.caption("Type to search code/variation")

# ============================================================================
# BUILD BASE & FILTER
# ============================================================================

base = build_base_df(raw_df, var_col, qty_col, productname_col, skuid_col, brand_col)

# Apply keyword filter if specified
if keywords:
    # Filter by ProductName column containing any of the keywords
    mask_keywords = base["ProductName"].astype(str).str.lower().str.contains(
        '|'.join([re.escape(k.lower()) for k in keywords]),
        na=False,
        regex=True
    )
    filtered = base[mask_keywords].copy()
else:
    filtered = base.copy()

# Apply text search
if text_search:
    search_lower = text_search.lower()
    mask = (
        filtered["Variation"].astype(str).str.lower().str.contains(search_lower, na=False) |
        filtered["SkuID"].astype(str).str.lower().str.contains(search_lower, na=False) |
        filtered["ProductName"].astype(str).str.lower().str.contains(search_lower, na=False)
    )
    filtered = filtered[mask].copy()

# Sort by ProductName and OriginalIndex
if keywords:
    filtered = filtered.sort_values(["ProductName", "OriginalIndex"]).reset_index(drop=True)
else:
    filtered = filtered.sort_values(["OriginalIndex"]).reset_index(drop=True)

# ============================================================================
# CATEGORIZE DATA
# ============================================================================

processed_ids = set(st.session_state["processed_ids"])
confirmed_ids = set(st.session_state["confirmed_ids"])

pending_df = filtered[
    ~filtered["OriginalIndex"].isin(processed_ids) &
    ~filtered["OriginalIndex"].isin(confirmed_ids)
].copy()

processed_df = filtered[
    filtered["OriginalIndex"].isin(processed_ids) &
    ~filtered["OriginalIndex"].isin(confirmed_ids)
].copy()

confirmed_df = filtered[
    filtered["OriginalIndex"].isin(confirmed_ids)
].copy()

# ============================================================================
# AUTO-SAVE HELPER (IMPROVED WITH TIMESTAMP)
# ============================================================================

def auto_save():
    """Auto-save session with timestamp"""
    timestamp = datetime.utcnow().isoformat() + "Z"
    state_data = {
        "saved_at": timestamp,
        "app_version": "v10",
        "file_name": file_name,
        "file_hash": file_hash,
        "keywords": keywords,
        "processed_ids": sorted(list(st.session_state["processed_ids"])),
        "confirmed_ids": sorted(list(st.session_state["confirmed_ids"])),
        "selected_columns": st.session_state["selected_columns"]
    }
    save_session(session_code, state_data, raw_bytes, file_name)
    st.session_state["last_checked"] = timestamp

# ============================================================================
# TABS FOR 3 CATEGORIES
# ============================================================================

st.markdown("---")
st.markdown(f"### Status: {len(pending_df)} Pending • {len(processed_df)} Processed • {len(confirmed_df)} Confirmed")

tab1, tab2, tab3 = st.tabs([
    f"Pending ({len(pending_df)})",
    f"Processed ({len(processed_df)})",
    f"Confirmed ({len(confirmed_df)})"
])

# ============================================================================
# TAB 1: PENDING (FIXED COLUMN HEADERS)
# ============================================================================

with tab1:
    st.caption("Unprocessed items. Select items to move to next stage.")

    if len(pending_df) == 0:
        st.info("No pending items. All processed!")
    else:
        with st.form("form_pending"):
            max_rows = min(len(pending_df), 5000)
            # Output order: Select, Variation, Quantity, ProductName, SkuID
            view_pending = pending_df[["Variation", "Quantity", "ProductName", "SkuID", "OriginalIndex"]].head(max_rows).copy()
            view_pending.insert(0, "Select", False)

            if mobile_mode:
                # Mobile: ultra-compact columns, NO horizontal scroll!
                edited_pending = st.data_editor(
                    view_pending.drop(columns=["OriginalIndex"]),
                    use_container_width=True,
                    height=400,
                    num_rows="fixed",
                    hide_index=True,
                    column_config={
                        "Select": st.column_config.CheckboxColumn("✓", width="small"),
                        "Variation": st.column_config.TextColumn("Var", width="small"),
                        "Quantity": st.column_config.NumberColumn("Qty", width="small"),
                        "ProductName": st.column_config.TextColumn("Product", width="small"),
                        "SkuID": st.column_config.TextColumn("SKU", width="small"),
                    },
                    disabled=["Variation", "Quantity", "ProductName", "SkuID"],
                    key="editor_pending"
                )
            else:
                # Desktop: wider columns
                edited_pending = st.data_editor(
                    view_pending.drop(columns=["OriginalIndex"]),
                    use_container_width=True,
                    height=400,
                    num_rows="fixed",
                    hide_index=True,
                    column_config={
                        "Select": st.column_config.CheckboxColumn("Select", width="small"),
                        "Variation": st.column_config.TextColumn("Variation", width="large"),
                        "Quantity": st.column_config.NumberColumn("Quantity", width="small"),
                        "ProductName": st.column_config.TextColumn("Product Name", width="large"),
                        "SkuID": st.column_config.TextColumn("SkuID", width="large"),
                    },
                    disabled=["Variation", "Quantity", "ProductName", "SkuID"],
                    key="editor_pending"
                )

            col1, col2, col3 = st.columns(3)
            with col1:
                btn_to_processed = st.form_submit_button("To Processed", use_container_width=True)
            with col2:
                btn_to_confirmed = st.form_submit_button("To Confirmed", use_container_width=True)
            with col3:
                btn_all_to_processed = st.form_submit_button("All → Processed", use_container_width=True)

            if btn_to_processed or btn_all_to_processed:
                mask = edited_pending["Select"] if btn_to_processed else pd.Series([True] * len(edited_pending))
                selected_ids = view_pending.loc[mask.to_numpy(), "OriginalIndex"].tolist()
                if selected_ids:
                    st.session_state["processed_ids"].update(selected_ids)
                    auto_save()
                    st.rerun()

            if btn_to_confirmed:
                mask = edited_pending["Select"]
                selected_ids = view_pending.loc[mask.to_numpy(), "OriginalIndex"].tolist()
                if selected_ids:
                    st.session_state["confirmed_ids"].update(selected_ids)
                    auto_save()
                    st.rerun()

# ============================================================================
# TAB 2: PROCESSED (FIXED COLUMN HEADERS)
# ============================================================================

with tab2:
    st.caption("Items being processed. Select to move to another stage.")

    if len(processed_df) == 0:
        st.info("No items in process.")
    else:
        with st.form("form_processed"):
            max_rows = min(len(processed_df), 5000)
            view_processed = processed_df[["Variation", "Quantity", "ProductName", "SkuID", "OriginalIndex"]].head(max_rows).copy()
            view_processed.insert(0, "Select", False)

            if mobile_mode:
                # Mobile: ultra-compact columns, NO horizontal scroll!
                edited_processed = st.data_editor(
                    view_processed.drop(columns=["OriginalIndex"]),
                    use_container_width=True,
                    height=400,
                    num_rows="fixed",
                    hide_index=True,
                    column_config={
                        "Select": st.column_config.CheckboxColumn("✓", width="small"),
                        "Variation": st.column_config.TextColumn("Var", width="small"),
                        "Quantity": st.column_config.NumberColumn("Qty", width="small"),
                        "ProductName": st.column_config.TextColumn("Product", width="small"),
                        "SkuID": st.column_config.TextColumn("SKU", width="small"),
                    },
                    disabled=["Variation", "Quantity", "ProductName", "SkuID"],
                    key="editor_processed"
                )
            else:
                # Desktop: wider columns
                edited_processed = st.data_editor(
                    view_processed.drop(columns=["OriginalIndex"]),
                    use_container_width=True,
                    height=400,
                    num_rows="fixed",
                    hide_index=True,
                    column_config={
                        "Select": st.column_config.CheckboxColumn("Select", width="small"),
                        "Variation": st.column_config.TextColumn("Variation", width="large"),
                        "Quantity": st.column_config.NumberColumn("Quantity", width="small"),
                        "ProductName": st.column_config.TextColumn("Product Name", width="large"),
                        "SkuID": st.column_config.TextColumn("SkuID", width="large"),
                    },
                    disabled=["Variation", "Quantity", "ProductName", "SkuID"],
                    key="editor_processed"
                )

            col1, col2, col3 = st.columns(3)
            with col1:
                btn_back_to_pending = st.form_submit_button("Back to Pending", use_container_width=True)
            with col2:
                btn_proc_to_confirmed = st.form_submit_button("To Confirmed", use_container_width=True)
            with col3:
                btn_all_proc_to_confirmed = st.form_submit_button("All → Confirmed", use_container_width=True)

            if btn_back_to_pending:
                mask = edited_processed["Select"]
                selected_ids = view_processed.loc[mask.to_numpy(), "OriginalIndex"].tolist()
                if selected_ids:
                    st.session_state["processed_ids"].difference_update(selected_ids)
                    auto_save()
                    st.rerun()

            if btn_proc_to_confirmed or btn_all_proc_to_confirmed:
                mask = edited_processed["Select"] if btn_proc_to_confirmed else pd.Series([True] * len(edited_processed))
                selected_ids = view_processed.loc[mask.to_numpy(), "OriginalIndex"].tolist()
                if selected_ids:
                    st.session_state["processed_ids"].difference_update(selected_ids)
                    st.session_state["confirmed_ids"].update(selected_ids)
                    auto_save()
                    st.rerun()

# ============================================================================
# TAB 3: CONFIRMED (FIXED COLUMN HEADERS)
# ============================================================================

with tab3:
    st.caption("Confirmed items (final). Ready for download.")

    if len(confirmed_df) == 0:
        st.info("No confirmed items yet.")
    else:
        with st.form("form_confirmed"):
            max_rows = min(len(confirmed_df), 5000)
            view_confirmed = confirmed_df[["Variation", "Quantity", "ProductName", "SkuID", "OriginalIndex"]].head(max_rows).copy()
            view_confirmed.insert(0, "Select", False)

            if mobile_mode:
                # Mobile: ultra-compact columns, NO horizontal scroll!
                edited_confirmed = st.data_editor(
                    view_confirmed.drop(columns=["OriginalIndex"]),
                    use_container_width=True,
                    height=400,
                    num_rows="fixed",
                    hide_index=True,
                    column_config={
                        "Select": st.column_config.CheckboxColumn("✓", width="small"),
                        "Variation": st.column_config.TextColumn("Var", width="small"),
                        "Quantity": st.column_config.NumberColumn("Qty", width="small"),
                        "ProductName": st.column_config.TextColumn("Product", width="small"),
                        "SkuID": st.column_config.TextColumn("SKU", width="small"),
                    },
                    disabled=["Variation", "Quantity", "ProductName", "SkuID"],
                    key="editor_confirmed"
                )
            else:
                # Desktop: wider columns
                edited_confirmed = st.data_editor(
                    view_confirmed.drop(columns=["OriginalIndex"]),
                    use_container_width=True,
                    height=400,
                    num_rows="fixed",
                    hide_index=True,
                    column_config={
                        "Select": st.column_config.CheckboxColumn("Select", width="small"),
                        "Variation": st.column_config.TextColumn("Variation", width="large"),
                        "Quantity": st.column_config.NumberColumn("Quantity", width="small"),
                        "ProductName": st.column_config.TextColumn("Product Name", width="large"),
                        "SkuID": st.column_config.TextColumn("SkuID", width="large"),
                    },
                    disabled=["Variation", "Quantity", "ProductName", "SkuID"],
                    key="editor_confirmed"
                )

            col1, col2 = st.columns(2)
            with col1:
                btn_back_to_processed = st.form_submit_button("Back to Processed", use_container_width=True)
            with col2:
                btn_back_all = st.form_submit_button("All → Processed", use_container_width=True)

            if btn_back_to_processed or btn_back_all:
                mask = edited_confirmed["Select"] if btn_back_to_processed else pd.Series([True] * len(edited_confirmed))
                selected_ids = view_confirmed.loc[mask.to_numpy(), "OriginalIndex"].tolist()
                if selected_ids:
                    st.session_state["confirmed_ids"].difference_update(selected_ids)
                    st.session_state["processed_ids"].update(selected_ids)
                    auto_save()
                    st.rerun()

# ============================================================================
# DOWNLOAD SECTION
# ============================================================================

st.markdown("---")
st.markdown("## Download")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.download_button(
        "All Data (CSV)",
        data=to_csv_bytes(filtered),
        file_name=f"{session_code}_all.csv",
        mime="text/csv",
        use_container_width=True
    )

with col2:
    st.download_button(
        "Processed (CSV)",
        data=to_csv_bytes(processed_df),
        file_name=f"{session_code}_processed.csv",
        mime="text/csv",
        use_container_width=True,
        disabled=len(processed_df) == 0
    )

with col3:
    st.download_button(
        "Confirmed (CSV)",
        data=to_csv_bytes(confirmed_df),
        file_name=f"{session_code}_confirmed.csv",
        mime="text/csv",
        use_container_width=True,
        disabled=len(confirmed_df) == 0
    )

with col4:
    st.download_button(
        "Confirmed (XLSX)",
        data=to_xlsx_bytes(confirmed_df),
        file_name=f"{session_code}_confirmed.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        disabled=len(confirmed_df) == 0
    )

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.caption(f"Auto-sync: ON • Session: **{session_code}** • File: {file_name} • {len(filtered)} items")
