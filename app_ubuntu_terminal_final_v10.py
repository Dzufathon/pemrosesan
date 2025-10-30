# app_ubuntu_terminal_final_v10.py
# Jalankan: streamlit run app_ubuntu_terminal_final_v10.py --server.port 8501 --server.address 0.0.0.0
# Python 3.14 kompatibel - Professional UI with dark green theme

import io
import re
import json
import hashlib
import os
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

/* Login card */
.login-card {
    background: var(--card-bg);
    border: 2px solid var(--primary-green);
    border-radius: 12px;
    padding: 2.5rem;
    margin: 2rem auto;
    max-width: 500px;
    box-shadow: 0 8px 24px rgba(45, 110, 44, 0.2);
}

/* Input fields */
.stTextInput input, .stSelectbox select {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    color: var(--text-primary);
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
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ============================================================================
# MOBILE DETECTION (FIXED)
# ============================================================================

def is_mobile():
    """Detect if accessing from mobile device"""
    try:
        # Use st.context.headers instead of deprecated _get_websocket_headers
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

def build_base_df(df, var_col, qty_col, text_col):
    """Build base dataframe with standard columns"""
    out = pd.DataFrame({
        "VariationData": df[var_col].astype(str).str.strip(),
        "QtyData": pd.to_numeric(df[qty_col], errors="coerce"),
        "TextSource": df[text_col].astype(str),
        "OriginalIndex": range(len(df))
    })

    if not out["QtyData"].isna().all():
        out["QtyData"] = out["QtyData"].fillna(0)
        if (out["QtyData"] % 1 == 0).all():
            out["QtyData"] = out["QtyData"].astype(int)

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

# ============================================================================
# LOGIN SCREEN
# ============================================================================

if not st.session_state["logged_in"]:
    mobile_mode = is_mobile()
    device_type = "Mobile" if mobile_mode else "Desktop"

    st.markdown("<div style='text-align: center; margin-top: 2rem;'>", unsafe_allow_html=True)
    st.markdown("# Login Session")
    st.markdown(f"### Program Pesanan 3 Tahap • {device_type}")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='login-card'>", unsafe_allow_html=True)

    st.markdown("**Masukkan kode sesi (4 huruf kecil)**")
    st.caption("PC/Laptop dan HP harus pakai kode yang sama untuk sync data")

    # Generate button ONLY for desktop/server
    if not mobile_mode:
        col_input, col_gen = st.columns([3, 1])
        with col_input:
            input_code = st.text_input(
                "Kode Session",
                max_chars=4,
                placeholder="contoh: abcd",
                help="Masukkan 4 huruf kecil (a-z)",
                label_visibility="collapsed"
            ).lower()
        with col_gen:
            st.write("")
            if st.button("Generate", use_container_width=True):
                new_code = make_code(4)
                st.info(f"**Kode baru:** {new_code}")
                st.caption("Salin kode ini untuk login")
                st.stop()
    else:
        input_code = st.text_input(
            "Kode Session",
            max_chars=4,
            placeholder="contoh: abcd",
            help="Masukkan 4 huruf kecil (a-z)",
            label_visibility="collapsed"
        ).lower()
        st.caption("Generate kode hanya tersedia di Server/PC")

    if st.button("Login / Buat Session Baru", type="primary", use_container_width=True):
        if len(input_code) == 4 and input_code.isalpha() and input_code.islower():
            st.session_state["session_code"] = input_code
            st.session_state["logged_in"] = True

            saved = load_session(input_code)
            if saved:
                st.session_state["keywords"] = saved.get("keywords", [])
                st.session_state["processed_ids"] = set(saved.get("processed_ids", []))
                st.session_state["confirmed_ids"] = set(saved.get("confirmed_ids", []))
                st.session_state["selected_columns"] = saved.get("selected_columns", {})

                file_name = saved.get("file_name")
                if file_name:
                    file_bytes = load_session_file(input_code, file_name)
                    if file_bytes:
                        st.session_state["loaded_file_bytes"] = file_bytes
                        st.session_state["loaded_file_name"] = file_name

                st.success(f"Session **{input_code}** loaded successfully")
            else:
                st.success(f"New session **{input_code}** created")

            st.rerun()
        else:
            st.error("Kode harus 4 huruf kecil (a-z). Contoh: abcd")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Cara Penggunaan Multi-Device")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Di PC (Server):**
        1. Jalankan: `streamlit run app.py --server.address 0.0.0.0`
        2. Klik **Generate** untuk buat kode
        3. Login dengan kode tersebut
        4. Upload file pesanan & proses data
        """)
    with col2:
        st.markdown("""
        **Di HP (Client):**
        1. Sambung Wi-Fi yang sama dengan PC
        2. Buka: `http://{IP-PC}:8501`
        3. Input kode yang sama dari PC
        4. File & data otomatis sync
        """)

    st.stop()

# ============================================================================
# LOGGED IN - HEADER
# ============================================================================

session_code = st.session_state["session_code"]
mobile_mode = is_mobile()

col_header1, col_header2 = st.columns([6, 1])
with col_header1:
    st.markdown(f"""
    ### nariyahsore:~$ session `{session_code}`
    **Program Pesanan 3 Tahap** • Auto-save • {("Mobile" if mobile_mode else "Desktop")}
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

    st.info(f"File dari session: **{file_name}** (auto-loaded)")

    if st.button("Upload File Baru"):
        st.session_state["loaded_file_bytes"] = None
        st.session_state["loaded_file_name"] = None
        st.rerun()
else:
    uploaded = st.file_uploader("Unggah file CSV/XLSX pesanan", type=["csv", "xlsx", "xls"])

    if not uploaded:
        st.warning("Silakan unggah file untuk mulai memproses")
        st.stop()

    raw_bytes = uploaded.read()
    file_name = uploaded.name

file_hash = file_fingerprint(raw_bytes)

try:
    raw_df = smart_read(raw_bytes, file_name)
except Exception as e:
    st.error(f"Gagal membaca file: {e}")
    st.stop()

if uploaded:
    st.success(f"File dimuat: **{file_name}** • {len(raw_df)} baris, {len(raw_df.columns)} kolom")

with st.expander("Lihat kolom file"):
    st.dataframe(pd.DataFrame({"Kolom": raw_df.columns}), use_container_width=True)

# ============================================================================
# COLUMN SELECTION
# ============================================================================

st.markdown("### Pengaturan Kolom")

var_idx = find_best_match(raw_df, VAR_SYNS, "text") or 0
qty_idx = find_best_match(raw_df, QTY_SYNS, "num") or (0 if len(raw_df.columns) == 1 else 1)
name_idx = find_best_match(raw_df, NAME_SYNS, "text") or var_idx

saved_cols = st.session_state.get("selected_columns", {})
if saved_cols and saved_cols.get("file_hash") == file_hash:
    var_col = saved_cols.get("var_col", raw_df.columns[var_idx])
    qty_col = saved_cols.get("qty_col", raw_df.columns[qty_idx])
    text_source_col = saved_cols.get("text_col", raw_df.columns[name_idx])
    if var_col not in raw_df.columns:
        var_col = raw_df.columns[var_idx]
    if qty_col not in raw_df.columns:
        qty_col = raw_df.columns[qty_idx]
    if text_source_col not in raw_df.columns:
        text_source_col = raw_df.columns[name_idx]
else:
    var_col = raw_df.columns[var_idx]
    qty_col = raw_df.columns[qty_idx]
    text_source_col = raw_df.columns[name_idx]

c1, c2, c3 = st.columns([1, 1, 1])
with c1:
    var_col = st.selectbox(
        "Kolom Variasi/SKU/Varian",
        options=list(raw_df.columns),
        index=list(raw_df.columns).index(var_col),
        key="sel_var"
    )
with c2:
    qty_col = st.selectbox(
        "Kolom Qty/Jumlah",
        options=list(raw_df.columns),
        index=list(raw_df.columns).index(qty_col),
        key="sel_qty"
    )
with c3:
    text_source_col = st.selectbox(
        "Kolom Teks Sumber (Tipe/Merk)",
        options=list(raw_df.columns),
        index=list(raw_df.columns).index(text_source_col),
        key="sel_text"
    )

st.session_state["selected_columns"] = {
    "file_hash": file_hash,
    "var_col": var_col,
    "qty_col": qty_col,
    "text_col": text_source_col
}

# ============================================================================
# KEYWORD FILTER & TEXT SEARCH
# ============================================================================

st.markdown("### Filter & Pencarian")

col_filter1, col_filter2 = st.columns([1, 1])

with col_filter1:
    st.markdown("**Filter Tipe Produk**")
    kw_input = st.text_input(
        "Kata kunci tipe",
        value=", ".join(st.session_state["keywords"]) if st.session_state["keywords"] else "ssl, stk",
        help="Pisahkan dengan koma/spasi. Contoh: ssl, stk, doby, songket",
        label_visibility="collapsed",
        key="kw_filter"
    )
    cur_keywords = [k.strip() for k in re.split(r"[\s,]+", kw_input) if k.strip()]
    if cur_keywords != st.session_state["keywords"]:
        st.session_state["keywords"] = cur_keywords
    keywords = st.session_state["keywords"]
    st.caption(f"{len(keywords)} tipe aktif" if keywords else "Semua tipe ditampilkan")

with col_filter2:
    st.markdown("**Pencarian Kode/Variasi**")
    text_search = st.text_input(
        "Cari kode/variasi",
        value=st.session_state.get("text_search", ""),
        help="Cari berdasarkan kode produk atau nama variasi",
        placeholder="Contoh: A123, merah, XL",
        label_visibility="collapsed",
        key="text_search_input"
    )
    st.session_state["text_search"] = text_search
    if text_search:
        st.caption(f"Mencari: '{text_search}'")
    else:
        st.caption("Ketik untuk mencari kode/variasi")

# ============================================================================
# BUILD BASE & FILTER
# ============================================================================

base = build_base_df(raw_df, var_col, qty_col, text_source_col)

if keywords:
    base["Type"] = categorize_by_keywords(base["TextSource"], keywords)
    filtered = base[base["Type"] != ""].copy()
else:
    base["Type"] = ""
    filtered = base.copy()

filtered["BrandGuess"] = [
    infer_brand(t, k) for t, k in zip(filtered["TextSource"], filtered["Type"])
]

# Apply text search
if text_search:
    search_lower = text_search.lower()
    mask = (
        filtered["VariationData"].astype(str).str.lower().str.contains(search_lower, na=False) |
        filtered["TextSource"].astype(str).str.lower().str.contains(search_lower, na=False)
    )
    filtered = filtered[mask].copy()

if keywords:
    filtered["Type"] = pd.Categorical(filtered["Type"], categories=keywords, ordered=True)
    filtered = filtered.sort_values(["Type", "OriginalIndex"]).reset_index(drop=True)
else:
    filtered = filtered.sort_values(["OriginalIndex"]).reset_index(drop=True)

filtered = filtered.rename(columns={
    "VariationData": var_col,
    "QtyData": qty_col
})

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
# AUTO-SAVE HELPER
# ============================================================================

def auto_save():
    """Auto-save session with force write"""
    state_data = {
        "saved_at": datetime.utcnow().isoformat() + "Z",
        "app_version": "v10",
        "file_name": file_name,
        "file_hash": file_hash,
        "keywords": keywords,
        "processed_ids": sorted(list(st.session_state["processed_ids"])),
        "confirmed_ids": sorted(list(st.session_state["confirmed_ids"])),
        "selected_columns": st.session_state["selected_columns"]
    }
    save_session(session_code, state_data, raw_bytes, file_name)

    # Force sync state
    processed_ids.clear()
    processed_ids.update(st.session_state["processed_ids"])
    confirmed_ids.clear()
    confirmed_ids.update(st.session_state["confirmed_ids"])

# ============================================================================
# TABS FOR 3 CATEGORIES
# ============================================================================

st.markdown("---")
st.markdown(f"### Status Overview: {len(pending_df)} Pending • {len(processed_df)} Processed • {len(confirmed_df)} Confirmed")

tab1, tab2, tab3 = st.tabs([
    f"Belum Diproses ({len(pending_df)})",
    f"Sudah Diproses ({len(processed_df)})",
    f"Konfirmasi ({len(confirmed_df)})"
])

# ============================================================================
# TAB 1: PENDING
# ============================================================================

with tab1:
    st.caption("Item yang belum diproses. Centang item lalu pindahkan ke tahap berikutnya.")

    if len(pending_df) == 0:
        st.info("Tidak ada item pending. Semua sudah diproses!")
    else:
        with st.form("form_pending"):
            max_rows = min(len(pending_df), 5000)
            view_pending = pending_df[["Type", "BrandGuess", var_col, qty_col, "TextSource", "OriginalIndex"]].head(max_rows).copy()
            view_pending.insert(0, "Select", False)

            edited_pending = st.data_editor(
                view_pending.drop(columns=["OriginalIndex"]),
                use_container_width=True,
                height=400,
                num_rows="fixed",
                hide_index=True,  # HIDE INDEX COLUMN
                column_config={
                    "Select": st.column_config.CheckboxColumn("Select", width="small"),
                    "Type": st.column_config.TextColumn("Type", width="small"),
                    "BrandGuess": st.column_config.TextColumn("Brand", width="small"),
                    var_col: st.column_config.TextColumn(var_col, width="medium"),
                    qty_col: st.column_config.NumberColumn(qty_col, width="small"),
                    "TextSource": st.column_config.TextColumn("Text Source", width="large"),
                },
                disabled=["Type", "BrandGuess", var_col, qty_col, "TextSource"],
                key="editor_pending"
            )

            col1, col2, col3 = st.columns(3)
            with col1:
                btn_to_processed = st.form_submit_button("Ke Sudah Diproses", use_container_width=True)
            with col2:
                btn_to_confirmed = st.form_submit_button("Langsung Konfirmasi", use_container_width=True)
            with col3:
                btn_all_to_processed = st.form_submit_button("Semua → Processed", use_container_width=True)

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
# TAB 2: PROCESSED
# ============================================================================

with tab2:
    st.caption("Item yang sedang diproses. Centang untuk memindahkan ke tahap lain.")

    if len(processed_df) == 0:
        st.info("Tidak ada item dalam proses.")
    else:
        with st.form("form_processed"):
            max_rows = min(len(processed_df), 5000)
            view_processed = processed_df[["Type", "BrandGuess", var_col, qty_col, "TextSource", "OriginalIndex"]].head(max_rows).copy()
            view_processed.insert(0, "Select", False)

            edited_processed = st.data_editor(
                view_processed.drop(columns=["OriginalIndex"]),
                use_container_width=True,
                height=400,
                num_rows="fixed",
                hide_index=True,  # HIDE INDEX COLUMN
                column_config={
                    "Select": st.column_config.CheckboxColumn("Select", width="small"),
                    "Type": st.column_config.TextColumn("Type", width="small"),
                    "BrandGuess": st.column_config.TextColumn("Brand", width="small"),
                    var_col: st.column_config.TextColumn(var_col, width="medium"),
                    qty_col: st.column_config.NumberColumn(qty_col, width="small"),
                    "TextSource": st.column_config.TextColumn("Text Source", width="large"),
                },
                disabled=["Type", "BrandGuess", var_col, qty_col, "TextSource"],
                key="editor_processed"
            )

            col1, col2, col3 = st.columns(3)
            with col1:
                btn_back_to_pending = st.form_submit_button("Balik ke Pending", use_container_width=True)
            with col2:
                btn_proc_to_confirmed = st.form_submit_button("Ke Konfirmasi", use_container_width=True)
            with col3:
                btn_all_proc_to_confirmed = st.form_submit_button("Semua → Konfirmasi", use_container_width=True)

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
# TAB 3: CONFIRMED
# ============================================================================

with tab3:
    st.caption("Item yang sudah dikonfirmasi (final). Siap untuk di-download.")

    if len(confirmed_df) == 0:
        st.info("Belum ada item yang dikonfirmasi.")
    else:
        with st.form("form_confirmed"):
            max_rows = min(len(confirmed_df), 5000)
            view_confirmed = confirmed_df[["Type", "BrandGuess", var_col, qty_col, "TextSource", "OriginalIndex"]].head(max_rows).copy()
            view_confirmed.insert(0, "Select", False)

            edited_confirmed = st.data_editor(
                view_confirmed.drop(columns=["OriginalIndex"]),
                use_container_width=True,
                height=400,
                num_rows="fixed",
                hide_index=True,  # HIDE INDEX COLUMN
                column_config={
                    "Select": st.column_config.CheckboxColumn("Select", width="small"),
                    "Type": st.column_config.TextColumn("Type", width="small"),
                    "BrandGuess": st.column_config.TextColumn("Brand", width="small"),
                    var_col: st.column_config.TextColumn(var_col, width="medium"),
                    qty_col: st.column_config.NumberColumn(qty_col, width="small"),
                    "TextSource": st.column_config.TextColumn("Text Source", width="large"),
                },
                disabled=["Type", "BrandGuess", var_col, qty_col, "TextSource"],
                key="editor_confirmed"
            )

            col1, col2 = st.columns(2)
            with col1:
                btn_back_to_processed = st.form_submit_button("Balik ke Processed", use_container_width=True)
            with col2:
                btn_back_all = st.form_submit_button("Semua → Processed", use_container_width=True)

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
st.markdown("## Download Hasil")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.download_button(
        "Semua Data (CSV)",
        data=to_csv_bytes(filtered),
        file_name=f"{session_code}_semua.csv",
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
        "Konfirmasi (CSV)",
        data=to_csv_bytes(confirmed_df),
        file_name=f"{session_code}_konfirmasi.csv",
        mime="text/csv",
        use_container_width=True,
        disabled=len(confirmed_df) == 0
    )

with col4:
    st.download_button(
        "Konfirmasi (XLSX)",
        data=to_xlsx_bytes(confirmed_df),
        file_name=f"{session_code}_konfirmasi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        disabled=len(confirmed_df) == 0
    )

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.caption(f"Auto-save aktif • Session: **{session_code}** • File: {file_name} • {len(filtered)} items (setelah filter)")
