"""Algorithm export page."""

from __future__ import annotations

import io
import json
import shutil
import tempfile
from pathlib import Path

import streamlit as st

from fraclab_sdk.algorithm import AlgorithmLibrary
from fraclab_sdk.config import SDKConfig
from fraclab_sdk.snapshot import SnapshotLibrary
from fraclab_sdk.workbench import ui_styles

st.set_page_config(page_title="Export Algorithm", page_icon="📦", layout="wide")
st.title("Export Algorithm")

ui_styles.apply_global_styles()

# --- Page-Specific CSS ---
st.markdown("""
<style>
    /* Status badge styling */
    .status-badge {
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .status-ok { background-color: #d1fae5; color: #065f46; }
    .status-missing { background-color: #fee2e2; color: #991b1b; }
</style>
""", unsafe_allow_html=True)


config = SDKConfig()
algo_lib = AlgorithmLibrary(config)
snap_lib = SnapshotLibrary(config)

algos = algo_lib.list_algorithms()
if not algos:
    st.info("No algorithms imported. Use Snapshots page to import or create one.")
    st.stop()

# ==========================================
# 1. Source Selection
# ==========================================
st.subheader("1. Select Algorithm Source")

with st.container(border=True):
    c1, c2 = st.columns([3, 1])
    with c1:
        algo_options = {f"{a.algorithm_id}:{a.version}": a for a in algos}
        selected_key = st.selectbox(
            "Target Algorithm",
            options=list(algo_options.keys()),
            format_func=lambda k: f"{algo_options[k].algorithm_id} (v{algo_options[k].version})",
            label_visibility="collapsed"
        )
    with c2:
        if selected_key:
            selected_algo = algo_options[selected_key]
            st.caption(f"ID: `{selected_algo.algorithm_id}`")

if not selected_key:
    st.stop()

selected_algo = algo_options[selected_key]
handle = algo_lib.get_algorithm(selected_algo.algorithm_id, selected_algo.version)
algo_dir = handle.directory

# File paths
manifest_path = algo_dir / "manifest.json"
params_schema_path = algo_dir / "dist" / "params.schema.json"
output_contract_path = algo_dir / "dist" / "output_contract.json"
drs_path = algo_dir / "dist" / "drs.json"

# ==========================================
# 2. Package Integrity Check & DRS Source
# ==========================================
st.subheader("2. Package Integrity Check")

def _get_status_html(path: Path, label: str):
    exists = path.exists()
    status_cls = "status-ok" if exists else "status-missing"
    icon = "✅" if exists else "❌"
    text = "Present" if exists else "Missing"
    return f"""
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #f0f2f6;">
        <span style="font-weight: 500;">{label}</span>
        <span class="status-badge {status_cls}">{icon} {text}</span>
    </div>
    """

with st.container(border=True):
    col_health, col_preview = st.columns([1, 2])

    with col_health:
        st.markdown("#### File Status")
        st.markdown(_get_status_html(manifest_path, "Manifest"), unsafe_allow_html=True)
        st.markdown(_get_status_html(params_schema_path, "Input Schema"), unsafe_allow_html=True)
        st.markdown(_get_status_html(output_contract_path, "Output Contract"), unsafe_allow_html=True)

        # DRS: Show prompt instead of file check
        st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #f0f2f6;">
            <span style="font-weight: 500;">DRS</span>
            <span style="color: #6b7280; font-size: 0.85rem;">👇 Select below</span>
        </div>
        """, unsafe_allow_html=True)

        # Manifest Metadata Preview
        if manifest_path.exists():
            st.markdown("---")
            try:
                m_data = json.loads(manifest_path.read_text())
                st.caption("Manifest Metadata")
                st.text(f"Code Ver: {m_data.get('codeVersion')}")
                st.text(f"Contract: {m_data.get('contractVersion')}")
            except:
                st.error("Invalid Manifest")

    with col_preview:
        st.markdown("#### File Inspector")
        tab_man, tab_in, tab_out = st.tabs(["Manifest", "Input Spec", "Output Spec"])

        def _show_json_preview(path: Path):
            if path.exists():
                try:
                    data = json.loads(path.read_text())
                    st.code(json.dumps(data, indent=2, ensure_ascii=False), language="json", line_numbers=True)
                except Exception:
                    st.error("Failed to parse JSON")
            else:
                st.info("File not generated yet.")

        with tab_man: _show_json_preview(manifest_path)
        with tab_in: _show_json_preview(params_schema_path)
        with tab_out: _show_json_preview(output_contract_path)

# ==========================================
# 3. DRS Source Selection
# ==========================================
st.subheader("3. Select DRS Source")

snapshots = snap_lib.list_snapshots()
snapshot_map = {s.snapshot_id: s for s in snapshots}

if not snapshots:
    st.warning("No snapshots available. Import a snapshot first to provide DRS for export.")
    st.stop()

with st.container(border=True):
    st.caption("The DRS (Data Requirement Specification) defines dataset requirements. Select a snapshot to use its DRS in the export package.")

    selected_snapshot_id = st.selectbox(
        "Snapshot (DRS Source)",
        options=list(snapshot_map.keys()),
        format_func=lambda x: f"{x} — {snapshot_map[x].bundle_id}",
        label_visibility="collapsed"
    )

if not selected_snapshot_id:
    st.stop()

snapshot_handle = snap_lib.get_snapshot(selected_snapshot_id)

# ==========================================
# 4. Export
# ==========================================
st.divider()
st.subheader("4. Export")

def build_zip() -> bytes:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        # copy installed algorithm content
        shutil.copytree(algo_dir, tmpdir_path / algo_dir.name, dirs_exist_ok=True)
        target_root = tmpdir_path / algo_dir.name
        
        # ensure manifest files paths cover dist outputs if present
        manifest_data = json.loads(manifest_path.read_text())
        files = manifest_data.get("files") or {}
        
        if output_contract_path.exists():
            files["outputContractPath"] = "dist/output_contract.json"
        if params_schema_path.exists():
            files["paramsSchemaPath"] = "dist/params.schema.json"
        if drs_path.exists():
            files["drsPath"] = "dist/drs.json"
        
        if files:
            manifest_data["files"] = files
        
        (target_root / "manifest.json").write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")
        
        # DRS Override Logic
        # Try to find DRS path from manifest, default to dist/drs.json
        drs_rel_path = manifest_data.get("files", {}).get("drsPath", "dist/drs.json")
        target_drs_path = target_root / drs_rel_path
        target_drs_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Read DRS from Snapshot
        snap_drs_path = snapshot_handle.directory / snapshot_handle.manifest.specFiles.drsPath
        
        if snap_drs_path.exists():
            target_drs_path.write_bytes(snap_drs_path.read_bytes())
        else:
            # Fallback if snapshot DRS is missing structure (rare)
            pass 

        # Zip it up
        zip_buf = io.BytesIO()
        shutil.make_archive(base_name=tmpdir_path / "algorithm_export", format="zip", root_dir=tmpdir_path, base_dir=algo_dir.name)
        zip_path = tmpdir_path / "algorithm_export.zip"
        zip_buf.write(zip_path.read_bytes())
        zip_buf.seek(0)
        return zip_buf.read()

_, col_btn = st.columns([3, 1])
with col_btn:
    if st.button("📦 Build & Export", type="primary", width="stretch"):
        try:
            with st.spinner("Packaging..."):
                zip_bytes = build_zip()

            st.download_button(
                label="⬇️ Download Zip",
                data=zip_bytes,
                file_name=f"{selected_algo.algorithm_id}-{selected_algo.version}.zip",
                mime="application/zip",
                width="stretch"
            )
        except Exception as e:
            st.error(f"Export failed: {e}")
