# app_ubuntu_terminal_final_v9.py
# Jalankan: streamlit run app_ubuntu_terminal_final_v9.py
# Python 3.14 kompatibel - VERSI 3 KATEGORI (Pending → Processed → Confirmed)

import io
import re
import json
import hashlib
import os
import secrets
import string
from datetime import datetime

import pandas as pd
import streamlit as st

# ============================================================================
# CONFIG & STYLING
# ============================================================================

st.set_page_config(page_title="Program Pesanan 3 Tahap (v9)", layout="wide")

CSS = """
<style>
.stApp {
    background: #0d0d0d;
    color: #e5e5e5;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Courier New', monospace;
}
.stButton>button, .stDownloadButton>button {
    background: #dd4814;
    color: white;
    border: none;
    border-radius: 8px;
}
.block-container .stDataEditor {
    border: 1px solid #333;
    border-radius: 8px;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

st.markdown("""
### nariyahsore:~
**Program proses pesanan 3 tahap — v9**
Alur: Upload → Filter → **Belum Diproses** → **Sudah Diproses** → **Konfirmasi** → Download
""")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def make_code(n=4):
    """Generate random uppercase code"""
    return ''.join(secrets.choice(string.ascii_uppercase) for _ in range(n))

def file_fingerprint(b: bytes) -> str:
    """Generate SHA1 hash untuk file tracking"""
    return hashlib.sha1(b).hexdigest()

def smart_read(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Baca CSV/XLSX dengan auto-detect encoding & delimiter"""
    name = filename.lower()
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(file_bytes))

    # Try multiple encodings
    for enc in ["utf-8-sig", "utf-8", "latin-1"]:
        try:
            return pd.read_csv(io.BytesIO(file_bytes), sep=None, engine="python", encoding=enc)
        except Exception:
            continue
    raise RuntimeError("Gagal membaca file CSV/XLSX")

def normalize_cols(cols):
    """Normalize column names untuk matching"""
    return [re.sub(r"\s+", " ", str(c)).strip().lower() for c in cols]

# Synonym lists untuk auto-detect kolom
VAR_SYNS = ["variation", "variations", "variant", "variants", "variasi", "varian",
            "product variant", "sku variant", "nama variasi", "opsi", "option", "options"]
QTY_SYNS = ["qty", "quantity", "jumlah", "kuantitas", "qty ordered", "jumlah beli",
            "order qty", "qty pesanan", "qty order", "jumlah order", "quantity ordered"]
NAME_SYNS = ["product name", "nama produk", "title", "judul", "name", "product_title",
             "sku", "sku id", "nama sku", "deskripsi"]

def find_best_match(df, synonyms, fallback_type="text"):
    """Find best matching column based on synonyms"""
    norm = normalize_cols(df.columns)

    # Exact match
    for syn in synonyms:
        if syn in norm:
            return norm.index(syn)

    # Partial match
    for i, c in enumerate(norm):
        for syn in synonyms:
            if syn in c:
                return i

    # Fallback heuristic
    if fallback_type == "text":
        scores = []
        for i, col in enumerate(df.columns):
            s = df[col].astype(str)
            nonnum = (s.str.replace(r"[0-9\.\-]", "", regex=True).str.strip() != "").mean()
            scores.append((nonnum, i))
        scores.sort(reverse=True)
        return scores[0][1] if scores else 0
    else:  # numeric
        scores = []
        for i, col in enumerate(df.columns):
            s = pd.to_numeric(df[col], errors="coerce")
            scores.append((s.notna().mean(), i))
        scores.sort(reverse=True)
        return scores[0][1] if scores else (0 if len(df.columns) == 1 else 1)

def build_base_df(df, var_col, qty_col, text_col):
    """Build base dataframe dengan kolom standar"""
    out = pd.DataFrame({
        "Variation": df[var_col].astype(str).str.strip(),
        "Qty": pd.to_numeric(df[qty_col], errors="coerce"),
        "TextSource": df[text_col].astype(str),
        "OriginalIndex": range(len(df))
    })

    # Clean Qty
    if not out["Qty"].isna().all():
        out["Qty"] = out["Qty"].fillna(0)
        if (out["Qty"] % 1 == 0).all():
            out["Qty"] = out["Qty"].astype(int)

    return out

def tokenize(text):
    """Extract words from text"""
    return re.findall(r"[\w\-]+", str(text).lower(), flags=re.UNICODE)

def categorize_by_keywords(series, keywords):
    """Kategorisasi berdasarkan keywords"""
    if not keywords:
        return pd.Series([""] * len(series), index=series.index)

    kws = [k.lower() for k in keywords if k.strip()]

    def match_first(text):
        t = str(text).lower()
        toks = set(tokenize(t))

        # Exact token match
        for k in kws:
            if k in toks:
                return k

        # Substring fallback
        for k in kws:
            if k in t:
                return k

        return ""

    return series.apply(match_first)

def infer_brand(text, matched_kw):
    """Infer brand dari text dan keyword"""
    t = str(text).lower()
    toks = tokenize(t)

    if matched_kw:
        try:
            idx = toks.index(matched_kw)
            if idx > 0 and not toks[idx - 1].isdigit():
                return toks[idx - 1]
        except ValueError:
            pass

    # Fallback: ambil token non-digit pertama
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

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if "processed_ids" not in st.session_state:
    st.session_state["processed_ids"] = set()

if "confirmed_ids" not in st.session_state:
    st.session_state["confirmed_ids"] = set()

if "keywords" not in st.session_state:
    st.session_state["keywords"] = []

if "session_id" not in st.session_state:
    st.session_state["session_id"] = ""

# ============================================================================
# SIDEBAR
# ============================================================================

st.sidebar.header("⚙️ Pengaturan")
max_rows_show = st.sidebar.number_input(
    "Tampilkan baris (maks)",
    min_value=100,
    max_value=100000,
    value=5000,
    step=100
)
st.sidebar.caption("Urutan data mengikuti urutan asli file.")

# ============================================================================
# FILE UPLOAD
# ============================================================================

uploaded = st.file_uploader("📂 Unggah file CSV/XLSX pesanan", type=["csv", "xlsx", "xls"])

if not uploaded:
    st.info("Silakan unggah file untuk mulai memproses.")
    st.stop()

# Read file
raw_bytes = uploaded.read()
file_hash = file_fingerprint(raw_bytes)

try:
    raw_df = smart_read(raw_bytes, uploaded.name)
except Exception as e:
    st.error(f"❌ Gagal membaca file: {e}")
    st.stop()

st.success(f"✅ File dimuat: **{uploaded.name}** • {len(raw_df)} baris, {len(raw_df.columns)} kolom")

with st.expander("🧭 Lihat kolom asli"):
    st.write(pd.DataFrame({"Columns": raw_df.columns}))

# ============================================================================
# COLUMN SELECTION
# ============================================================================

var_idx = find_best_match(raw_df, VAR_SYNS, "text") or 0
qty_idx = find_best_match(raw_df, QTY_SYNS, "num") or (0 if len(raw_df.columns) == 1 else 1)
name_idx = find_best_match(raw_df, NAME_SYNS, "text") or var_idx

c1, c2, c3 = st.columns([1, 1, 1])
with c1:
    var_col = st.selectbox(
        "Pilih kolom Variation",
        options=list(raw_df.columns),
        index=min(var_idx, len(raw_df.columns) - 1)
    )
with c2:
    qty_col = st.selectbox(
        "Pilih kolom Qty",
        options=list(raw_df.columns),
        index=min(qty_idx, len(raw_df.columns) - 1)
    )
with c3:
    text_source_col = st.selectbox(
        "Kolom teks sumber (tipe/merk)",
        options=list(raw_df.columns),
        index=min(name_idx, len(raw_df.columns) - 1)
    )

# ============================================================================
# BUILD BASE & FILTER BY KEYWORDS
# ============================================================================

base = build_base_df(raw_df, var_col, qty_col, text_source_col)

st.markdown("### 🔎 Filter berdasarkan **tipe sarung**")
kw_input = st.text_input(
    "Tipe untuk ditampilkan (pisahkan dengan koma/spasi)",
    value="ssl, stk",
    help="Contoh: ssl, stk, doby, songket, rayon. Kosongkan untuk tampilkan semua."
)

# Update keywords
cur_keywords = [k.strip() for k in re.split(r"[\s,]+", kw_input) if k.strip()]
if cur_keywords != st.session_state["keywords"]:
    st.session_state["keywords"] = cur_keywords

keywords = st.session_state["keywords"]
st.caption(f"🏷️ Kata kunci aktif: {', '.join(keywords) if keywords else '(kosong → tampil semua)'}")

# Apply filter
if keywords:
    base["Type"] = categorize_by_keywords(base["TextSource"], keywords)
    filtered = base[base["Type"] != ""].copy()
else:
    base["Type"] = ""
    filtered = base.copy()

# Add brand guess
filtered["BrandGuess"] = [
    infer_brand(t, k) for t, k in zip(filtered["TextSource"], filtered["Type"])
]

# Sort
if keywords:
    filtered["Type"] = pd.Categorical(filtered["Type"], categories=keywords, ordered=True)
    filtered = filtered.sort_values(["Type", "OriginalIndex"]).reset_index(drop=True)
else:
    filtered = filtered.sort_values(["OriginalIndex"]).reset_index(drop=True)

# ============================================================================
# CATEGORIZE DATA INTO 3 BUCKETS
# ============================================================================

processed_ids = set(st.session_state["processed_ids"])
confirmed_ids = set(st.session_state["confirmed_ids"])

# Pending: belum di processed dan belum di confirmed
pending_df = filtered[
    ~filtered["OriginalIndex"].isin(processed_ids) &
    ~filtered["OriginalIndex"].isin(confirmed_ids)
].copy()

# Processed: sudah di processed tapi belum di confirmed
processed_df = filtered[
    filtered["OriginalIndex"].isin(processed_ids) &
    ~filtered["OriginalIndex"].isin(confirmed_ids)
].copy()

# Confirmed: sudah di confirmed (final)
confirmed_df = filtered[
    filtered["OriginalIndex"].isin(confirmed_ids)
].copy()

# ============================================================================
# SECTION 1: BELUM DIPROSES
# ============================================================================

st.markdown("---")
st.subheader("📋 1. Belum Diproses")
st.caption(f"Total: {len(pending_df)} item | Ditampilkan: {min(len(pending_df), max_rows_show)}")

with st.form("form_pending"):
    view_pending = pending_df[["Type", "BrandGuess", "Variation", "Qty", "TextSource", "OriginalIndex"]].head(max_rows_show).copy()
    view_pending["✓"] = False

    edited_pending = st.data_editor(
        view_pending.drop(columns=["OriginalIndex"]),
        use_container_width=True,
        height=350,
        num_rows="fixed",
        column_config={
            "✓": st.column_config.CheckboxColumn("✓", help="Centang untuk memilih"),
            "Type": st.column_config.TextColumn("Type", width="small"),
            "BrandGuess": st.column_config.TextColumn("Brand", width="small"),
            "Variation": st.column_config.TextColumn("Variation", width="medium"),
            "Qty": st.column_config.NumberColumn("Qty", width="small"),
            "TextSource": st.column_config.TextColumn("Text Source", width="large"),
        },
        disabled=["Type", "BrandGuess", "Variation", "Qty", "TextSource"],
        key="editor_pending"
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        btn_to_processed = st.form_submit_button("➡️ Pindah ke Sudah Diproses", use_container_width=True)
    with col2:
        btn_to_confirmed = st.form_submit_button("⏭️ Langsung ke Konfirmasi", use_container_width=True)
    with col3:
        btn_all_to_processed = st.form_submit_button("➡️ Semua → Sudah Diproses", use_container_width=True)

    if btn_to_processed or btn_all_to_processed:
        mask = edited_pending["✓"] if btn_to_processed else pd.Series([True] * len(edited_pending))
        selected_ids = view_pending.loc[mask.to_numpy(), "OriginalIndex"].tolist()

        if selected_ids:
            processed_ids.update(selected_ids)
            st.session_state["processed_ids"] = processed_ids
            st.rerun()

    if btn_to_confirmed:
        mask = edited_pending["✓"]
        selected_ids = view_pending.loc[mask.to_numpy(), "OriginalIndex"].tolist()

        if selected_ids:
            confirmed_ids.update(selected_ids)
            st.session_state["confirmed_ids"] = confirmed_ids
            st.rerun()

# ============================================================================
# SECTION 2: SUDAH DIPROSES
# ============================================================================

st.markdown("---")
st.subheader("⚙️ 2. Sudah Diproses")
st.caption(f"Total: {len(processed_df)} item | Ditampilkan: {min(len(processed_df), max_rows_show)}")

with st.form("form_processed"):
    view_processed = processed_df[["Type", "BrandGuess", "Variation", "Qty", "TextSource", "OriginalIndex"]].head(max_rows_show).copy()
    view_processed["✓"] = False

    edited_processed = st.data_editor(
        view_processed.drop(columns=["OriginalIndex"]),
        use_container_width=True,
        height=350,
        num_rows="fixed",
        column_config={
            "✓": st.column_config.CheckboxColumn("✓", help="Centang untuk memilih"),
            "Type": st.column_config.TextColumn("Type", width="small"),
            "BrandGuess": st.column_config.TextColumn("Brand", width="small"),
            "Variation": st.column_config.TextColumn("Variation", width="medium"),
            "Qty": st.column_config.NumberColumn("Qty", width="small"),
            "TextSource": st.column_config.TextColumn("Text Source", width="large"),
        },
        disabled=["Type", "BrandGuess", "Variation", "Qty", "TextSource"],
        key="editor_processed"
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        btn_back_to_pending = st.form_submit_button("⬅️ Balik ke Belum Diproses", use_container_width=True)
    with col2:
        btn_proc_to_confirmed = st.form_submit_button("➡️ Pindah ke Konfirmasi", use_container_width=True)
    with col3:
        btn_all_proc_to_confirmed = st.form_submit_button("➡️ Semua → Konfirmasi", use_container_width=True)

    if btn_back_to_pending:
        mask = edited_processed["✓"]
        selected_ids = view_processed.loc[mask.to_numpy(), "OriginalIndex"].tolist()

        if selected_ids:
            processed_ids.difference_update(selected_ids)
            st.session_state["processed_ids"] = processed_ids
            st.rerun()

    if btn_proc_to_confirmed or btn_all_proc_to_confirmed:
        mask = edited_processed["✓"] if btn_proc_to_confirmed else pd.Series([True] * len(edited_processed))
        selected_ids = view_processed.loc[mask.to_numpy(), "OriginalIndex"].tolist()

        if selected_ids:
            # Pindahkan dari processed ke confirmed
            processed_ids.difference_update(selected_ids)
            confirmed_ids.update(selected_ids)
            st.session_state["processed_ids"] = processed_ids
            st.session_state["confirmed_ids"] = confirmed_ids
            st.rerun()

# ============================================================================
# SECTION 3: KONFIRMASI (FINAL)
# ============================================================================

st.markdown("---")
st.subheader("✅ 3. Konfirmasi (Final)")
st.caption(f"Total: {len(confirmed_df)} item | Ditampilkan: {min(len(confirmed_df), max_rows_show)}")

with st.form("form_confirmed"):
    view_confirmed = confirmed_df[["Type", "BrandGuess", "Variation", "Qty", "TextSource", "OriginalIndex"]].head(max_rows_show).copy()
    view_confirmed["✓"] = False

    edited_confirmed = st.data_editor(
        view_confirmed.drop(columns=["OriginalIndex"]),
        use_container_width=True,
        height=350,
        num_rows="fixed",
        column_config={
            "✓": st.column_config.CheckboxColumn("✓", help="Centang untuk memilih"),
            "Type": st.column_config.TextColumn("Type", width="small"),
            "BrandGuess": st.column_config.TextColumn("Brand", width="small"),
            "Variation": st.column_config.TextColumn("Variation", width="medium"),
            "Qty": st.column_config.NumberColumn("Qty", width="small"),
            "TextSource": st.column_config.TextColumn("Text Source", width="large"),
        },
        disabled=["Type", "BrandGuess", "Variation", "Qty", "TextSource"],
        key="editor_confirmed"
    )

    col1, col2 = st.columns(2)
    with col1:
        btn_back_to_processed = st.form_submit_button("⬅️ Balik ke Sudah Diproses", use_container_width=True)
    with col2:
        btn_back_all = st.form_submit_button("⬅️ Semua → Sudah Diproses", use_container_width=True)

    if btn_back_to_processed or btn_back_all:
        mask = edited_confirmed["✓"] if btn_back_to_processed else pd.Series([True] * len(edited_confirmed))
        selected_ids = view_confirmed.loc[mask.to_numpy(), "OriginalIndex"].tolist()

        if selected_ids:
            # Pindahkan dari confirmed ke processed
            confirmed_ids.difference_update(selected_ids)
            processed_ids.update(selected_ids)
            st.session_state["confirmed_ids"] = confirmed_ids
            st.session_state["processed_ids"] = processed_ids
            st.rerun()

# ============================================================================
# DOWNLOAD SECTION
# ============================================================================

st.markdown("---")
st.markdown("## ⬇️ Download Hasil")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.download_button(
        "📄 Semua (CSV)",
        data=to_csv_bytes(filtered),
        file_name="semua_data.csv",
        mime="text/csv",
        use_container_width=True
    )

with col2:
    st.download_button(
        "⚙️ Sudah Diproses (CSV)",
        data=to_csv_bytes(processed_df),
        file_name="sudah_diproses.csv",
        mime="text/csv",
        use_container_width=True
    )

with col3:
    st.download_button(
        "✅ Konfirmasi (CSV)",
        data=to_csv_bytes(confirmed_df),
        file_name="konfirmasi.csv",
        mime="text/csv",
        use_container_width=True
    )

with col4:
    st.download_button(
        "✅ Konfirmasi (XLSX)",
        data=to_xlsx_bytes(confirmed_df),
        file_name="konfirmasi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

# ============================================================================
# SAVE / LOAD SESSION
# ============================================================================

st.markdown("---")
st.markdown("## 💾 Simpan / Muat Session")
st.caption("Gunakan Session ID 4 huruf untuk save/load progress. Storage lokal di folder `storage/`")

os.makedirs("storage", exist_ok=True)

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    session_id = st.text_input(
        "Session ID (4 huruf A-Z)",
        value=st.session_state["session_id"],
        max_chars=4,
        help="Contoh: ABCD"
    ).upper()
    st.session_state["session_id"] = session_id

with col2:
    if st.button("🎲 Generate ID", use_container_width=True):
        st.session_state["session_id"] = make_code(4)
        st.rerun()

with col3:
    st.write("")  # spacing

# Validasi session ID
invalid_id = len(session_id) != 4 or not session_id.isalpha() or session_id != session_id.upper()

if invalid_id:
    st.warning(f"⚠️ Session ID harus 4 huruf kapital (A-Z). Contoh: {make_code(4)}")

# Save/Load buttons
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("💾 Simpan ke Disk", disabled=invalid_id, use_container_width=True):
        payload = {
            "saved_at": datetime.utcnow().isoformat() + "Z",
            "app_version": "v9",
            "file_name": uploaded.name,
            "file_hash": file_hash,
            "keywords": keywords,
            "processed_ids": sorted(list(processed_ids)),
            "confirmed_ids": sorted(list(confirmed_ids)),
        }
        path = os.path.join("storage", f"{session_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        st.success(f"✅ Tersimpan: storage/{session_id}.json")

with col2:
    payload_download = {
        "saved_at": datetime.utcnow().isoformat() + "Z",
        "app_version": "v9",
        "file_name": uploaded.name,
        "file_hash": file_hash,
        "keywords": keywords,
        "processed_ids": sorted(list(processed_ids)),
        "confirmed_ids": sorted(list(confirmed_ids)),
    }
    st.download_button(
        "⬇️ Download Save",
        data=json.dumps(payload_download, ensure_ascii=False, indent=2).encode("utf-8"),
        file_name=f"{session_id or 'SESSION'}.json",
        mime="application/json",
        disabled=invalid_id,
        use_container_width=True
    )

with col3:
    if st.button("📂 Muat dari Disk", disabled=invalid_id, use_container_width=True):
        path = os.path.join("storage", f"{session_id}.json")
        if not os.path.exists(path):
            st.error("❌ File tidak ditemukan di storage/")
        else:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if data.get("file_hash") != file_hash:
                st.warning("⚠️ File fingerprint berbeda. Pastikan file yang diupload sama dengan saat save.")

            st.session_state["keywords"] = data.get("keywords", [])
            st.session_state["processed_ids"] = set(data.get("processed_ids", []))
            st.session_state["confirmed_ids"] = set(data.get("confirmed_ids", []))
            st.success("✅ Session dimuat dari disk")
            st.rerun()

with col4:
    uploaded_save = st.file_uploader("📤 Upload Save", type=["json"], key="upload_save")
    if uploaded_save:
        try:
            data = json.loads(uploaded_save.read().decode("utf-8"))

            if data.get("file_hash") != file_hash:
                st.warning("⚠️ File fingerprint berbeda. Pastikan file yang diupload sama dengan saat save.")

            st.session_state["keywords"] = data.get("keywords", [])
            st.session_state["processed_ids"] = set(data.get("processed_ids", []))
            st.session_state["confirmed_ids"] = set(data.get("confirmed_ids", []))

            if not st.session_state["session_id"]:
                st.session_state["session_id"] = make_code(4)

            st.success("✅ Session dimuat dari file")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Gagal memuat file: {e}")

# ============================================================================
# FOOTER INFO
# ============================================================================

st.markdown("---")
st.caption(f"📊 Ringkasan: {len(pending_df)} Pending | {len(processed_df)} Processed | {len(confirmed_df)} Confirmed | {len(filtered)} Total (setelah filter)")
