import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import sys
import time
import base64
from PIL import Image


# ==========================================
# ⚙️ GITHUB / CLOUD CONFIGURATION
# ==========================================
# ใช้ Relative Path แทน Drive R:
# สมมติว่าคุณเอาไฟล์ Excel/CSV ไว้ที่ root ของ repo หรือโฟลเดอร์ data
DATA_FOLDER = "."  # หรือ "data" หากคุณสร้างโฟลเดอร์ชื่อ data ใน github
RFI_FOLDER = "RFI_PDFs"  # คุณต้องสร้างโฟลเดอร์นี้ใน Github และเอาไฟล์ PDF ใส่เข้าไป
IMG_FOLDER = "profile_images"

# ชื่อไฟล์ (ต้องตรงกับที่อัพโหลดขึ้น Github)
DRAWING_EXCEL = "TR-BKK2-PH1 - Shop Drawing Submission_R0.xlsx"
RFI_EXCEL = "TR-BKK2-PH1 - Request for Information Submission_R1.xlsx"

MASTER_DRAWING_PATH = os.path.join(DATA_FOLDER, DRAWING_EXCEL)
MASTER_RFI_PATH = os.path.join(DATA_FOLDER, RFI_EXCEL)

STATUS_FILE = os.path.join(DATA_FOLDER, "bim_status.csv")
CREDENTIALS_FILE = os.path.join(DATA_FOLDER, "bim_users.csv")
PRIVATE_CHAT_FILE = os.path.join(DATA_FOLDER, "bim_private_chat.csv")
NOTIFY_FILE = os.path.join(DATA_FOLDER, "bim_notifications.csv")
RFI_LINKS_FILE = os.path.join(DATA_FOLDER, "bim_drawing_rfi_links.csv")

# Settings
OFFLINE_TIMEOUT_MINUTES = 5

# Lists
FILE_LIST = ["AR-LV1", "AR-LV2", "AR-Facade", "ST-Foundation", "ST-Framing",
             "ME-HVAC", "ME-Sanitary", "EE-Lighting", "EE-Power",
             "Central-AR", "Central-ST", "Central-MEP", "Coordination", "Meeting"]
LEVEL_LIST = ["-", "B1", "L1", "L2", "L3", "L4", "Roof", "Site"]

SHEET_MAPPING = {
    "AR": "Architectural", "ST": "Structural", "CSD": "Combined Services",
    "ME": "Mechanical", "EL": "Electrical", "HY": "Hydraulics", "FI": "Fire Protection"
}
SHEETS_TO_READ = list(SHEET_MAPPING.keys())


def init_files():
    # สร้างโฟลเดอร์ถ้ายังไม่มี
    if not os.path.exists(DATA_FOLDER) and DATA_FOLDER != ".":
        os.makedirs(DATA_FOLDER)
    if not os.path.exists(IMG_FOLDER):
        os.makedirs(IMG_FOLDER)

    # 🟢 1. กำหนดรายชื่อ User ตามที่คุณต้องการ
    real_team = [
        "Pakapon", "Weera", "Suttipong", "Itsarate", "Kittiphong",
        "Tresa", "Hein", "Emon", "Klui", "Thanes", "Paul",
        "Member_12", "Member_13", "Member_14", "Member_15",
        "Member_16", "Member_17", "Member_18", "Member_19", "Member_20"
    ]

    # 🟢 2. สร้าง/อัพเดทไฟล์ Login (Credentials)
    # ถ้าไฟล์ไม่มี หรือมีชื่อไม่ครบตามลิสต์ใหม่ ให้สร้างใหม่เลย
    need_create_cred = False
    if not os.path.exists(CREDENTIALS_FILE):
        need_create_cred = True
    else:
        # เช็คว่ามีชื่อ Weera หรือยัง (เพื่อดูว่าเป็นไฟล์เวอร์ชั่นเก่าไหม)
        df_cred = pd.read_csv(CREDENTIALS_FILE)
        if "Weera" not in df_cred['Username'].values:
            need_create_cred = True

    if need_create_cred:
        pd.DataFrame({
            "Username": real_team,
            "Password": ["1234"] * len(real_team)
        }).to_csv(CREDENTIALS_FILE, index=False)

    # 🟢 3. สร้าง/อัพเดทไฟล์ Status
    # ถ้าไฟล์ไม่มี หรือยังเป็นชื่อเก่า (Member_1...) ให้รีเซ็ตใหม่ให้ตรงกับชื่อจริง
    need_reset_status = False
    if not os.path.exists(STATUS_FILE):
        need_reset_status = True
    else:
        df_status = pd.read_csv(STATUS_FILE)
        # เช็คว่าชื่อในไฟล์ตรงกับรายชื่อจริงหรือไม่
        existing_names = df_status['Name'].tolist()
        # ถ้าไม่มี "Weera" ในไฟล์ แสดงว่าเป็นไฟล์เก่าที่ต้องแก้
        if "Weera" not in existing_names:
            need_reset_status = True

    if need_reset_status:
        # สร้าง Dataframe ใหม่ที่มีรายชื่อถูกต้องครบถ้วน
        pd.DataFrame({
            "Name": real_team,
            "Current_File": "Idle",
            "Level": "-",
            "Task_Detail": "-",
            "Last_Updated": datetime.now().strftime("%H:%M"),
            "Last_Seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Status": "Offline"
        }).to_csv(STATUS_FILE, index=False)

    if not os.path.exists(PRIVATE_CHAT_FILE):
        pd.DataFrame(columns=["Timestamp", "From_User", "To_User", "Message"]).to_csv(PRIVATE_CHAT_FILE, index=False)

    if not os.path.exists(NOTIFY_FILE):
        pd.DataFrame(columns=["To_User", "From_User", "Type", "Message", "Timestamp"]).to_csv(NOTIFY_FILE, index=False)

    if not os.path.exists(RFI_LINKS_FILE):
        pd.DataFrame(columns=["Drawing_RFAS", "Linked_RFI"]).to_csv(RFI_LINKS_FILE, index=False)


def load_data(file_path):
    if not os.path.exists(file_path): return pd.DataFrame()
    try:
        return pd.read_csv(file_path).fillna("")
    except:
        return pd.DataFrame()


def save_data(df, file_path):
    try:
        df.to_csv(file_path, index=False)
    except:
        pass


def save_rfi_link(drawing_rfas, rfi_string):
    df_links = load_data(RFI_LINKS_FILE)
    if not df_links.empty:
        df_links = df_links[df_links['Drawing_RFAS'] != drawing_rfas]
    new_row = pd.DataFrame([{"Drawing_RFAS": drawing_rfas, "Linked_RFI": rfi_string}])
    df_final = pd.concat([df_links, new_row], ignore_index=True)
    save_data(df_final, RFI_LINKS_FILE)


# Cache Data Loading
@st.cache_data(ttl=60)
def load_rfi_data_global():
    return _read_rfi_excel()


@st.cache_data(ttl=60)
def load_drawing_excel(rfi_status_map):
    return _read_drawing_excel(rfi_status_map)


def _read_rfi_excel():
    if not os.path.exists(MASTER_RFI_PATH): return pd.DataFrame(), {}
    all_data = []
    rfi_map = {}

    for sheet in SHEETS_TO_READ:
        try:
            df = pd.read_excel(MASTER_RFI_PATH, sheet_name=sheet, header=1)

            def get_col(kw):
                for c in df.columns:
                    if any(k in str(c).lower() for k in kw): return c
                return None

            c_doc = get_col(["doc ref", "rfas doc"])
            c_act = get_col(["action"])
            c_desc = get_col(["description", "title"])
            c_stat = get_col(["approved status", "status"])
            c_sub = get_col(["submission date"])

            if c_doc:
                temp = pd.DataFrame()
                temp["Doc Ref No."] = df[c_doc]
                temp["Trade"] = SHEET_MAPPING.get(sheet, sheet)

                temp["Document Description"] = df[c_desc] if c_desc else "-"
                temp["Action By"] = df[c_act] if c_act else "-"
                temp["Approved Status"] = df[c_stat] if c_stat else "-"

                for _, row in temp.iterrows():
                    rfi_map[str(row["Doc Ref No."]).strip()] = str(row["Action By"]).strip().upper()

                if c_sub:
                    temp["Actual Submission Date"] = df[c_sub]
                else:
                    temp["Actual Submission Date"] = "-"

                all_data.append(temp.dropna(subset=["Doc Ref No."]))
        except:
            pass

    if not all_data: return pd.DataFrame(), {}
    final_df = pd.concat(all_data, ignore_index=True)

    def clean_dt(val):
        if pd.isnull(val): return "-"
        if not isinstance(val, (datetime, date)):
            try:
                val = pd.to_datetime(val)
            except:
                return str(val)
        if pd.isna(val): return "-"
        if val.year <= 1900: return "-"
        return val.strftime('%d %b %Y')

    if "Actual Submission Date" in final_df.columns:
        final_df["Actual Submission Date"] = pd.to_datetime(final_df["Actual Submission Date"], errors='coerce').apply(
            clean_dt)

    return final_df.fillna("-"), rfi_map


def _read_drawing_excel(rfi_status_map):
    if not os.path.exists(MASTER_DRAWING_PATH): return pd.DataFrame(), "File Not Found"

    df_links = load_data(RFI_LINKS_FILE)
    links_dict = {}
    if not df_links.empty:
        links_dict = dict(zip(df_links['Drawing_RFAS'], df_links['Linked_RFI']))

    all_data = []

    for sheet in SHEETS_TO_READ:
        try:
            df = pd.read_excel(MASTER_DRAWING_PATH, sheet_name=sheet, header=1)

            def find_col(pats, exclude=None):
                for c in df.columns:
                    c_str = str(c).lower()
                    if any(p in c_str for p in pats):
                        if exclude and exclude in c_str:
                            continue
                        return c
                return None

            c_rfas = find_col(["rfas"])
            c_desc = find_col(["description", "title"])
            if not c_desc and len(df.columns) > 3: c_desc = df.columns[3]

            if c_rfas:
                temp = pd.DataFrame()
                temp["RFAS Doc No."] = df[c_rfas]
                temp["Trade"] = SHEET_MAPPING.get(sheet, sheet)
                temp["Document Description"] = df[c_desc] if c_desc else "-"

                c_plan = find_col(["planned"])
                c_sub = find_col(["submission"], exclude="planned")
                c_res = find_col(["respond"])
                c_app = find_col(["approval"])

                temp["Planned Submission"] = df[c_plan] if c_plan else None
                temp["Submission Date"] = df[c_sub] if c_sub else None
                temp["Consultant Respond Date"] = df[c_res] if c_res else None
                temp["Approval Date"] = df[c_app] if c_app else None

                c_rev = find_col(["rev"])
                temp["Revision"] = df[c_rev] if c_rev else "-"
                c_act = find_col(["action"])
                temp["Action"] = df[c_act] if c_act else "-"
                c_stat = find_col(["status"])
                temp["Status"] = df[c_stat] if c_stat else "-"

                link_list = []
                block_list = []
                for _, row in temp.iterrows():
                    rfas = str(row["RFAS Doc No."])
                    l_rfi = links_dict.get(rfas, "")
                    is_blocked = False

                    if l_rfi:
                        rfis = [x.strip() for x in l_rfi.split(',')]
                        for r in rfis:
                            act = rfi_status_map.get(r, "PENDING")
                            if not any(x in act for x in ["CLOSED"]):
                                is_blocked = True

                    link_list.append(l_rfi)
                    block_list.append(is_blocked)

                temp["Linked RFI"] = link_list
                temp["Is_Blocked"] = block_list

                all_data.append(temp.dropna(subset=["RFAS Doc No."]))
        except:
            pass

    if not all_data: return pd.DataFrame(), "No Data"
    final = pd.concat(all_data, ignore_index=True)

    def clean_dt(val):
        if pd.isnull(val): return "-"
        if not isinstance(val, (datetime, date)):
            try:
                val = pd.to_datetime(val)
            except:
                return str(val)
        if pd.isna(val): return "-"
        if val.year <= 1900: return "-"
        return val.strftime('%d %b %Y')

    for c in ["Planned Submission", "Submission Date", "Consultant Respond Date", "Approval Date"]:
        final[c] = pd.to_datetime(final[c], errors='coerce').apply(clean_dt)

    final["Revision"] = final["Revision"].apply(
        lambda x: str(int(float(x))) if str(x).replace('.', '').isdigit() else "-")

    return final.fillna("-"), "OK"


# ------------------------------------------------------------------
# 📂 PDF HANDLING FOR CLOUD (MODIFIED)
# ------------------------------------------------------------------
def open_pdf(doc_no):
    # ตรวจสอบว่ามีโฟลเดอร์ RFI หรือไม่
    if not os.path.exists(RFI_FOLDER):
        st.error(f"Folder not found in Repo: {RFI_FOLDER}")
        return

    # ค้นหาไฟล์ PDF
    target_file = None
    try:
        files = os.listdir(RFI_FOLDER)
        for f in files:
            if f.lower().startswith(str(doc_no).lower()) and f.lower().endswith(".pdf"):
                target_file = os.path.join(RFI_FOLDER, f)
                break

        if target_file:
            # บน Cloud เราใช้ st.download_button หรือแสดง PDF Embed แทน os.startfile
            with open(target_file, "rb") as pdf_file:
                PDFbyte = pdf_file.read()

            st.markdown(f"**Found:** `{os.path.basename(target_file)}`")

            # ปุ่ม Download
            st.download_button(label="⬇️ Download PDF",
                               data=PDFbyte,
                               file_name=os.path.basename(target_file),
                               mime='application/octet-stream')

            # (Optional) แสดง Preview ในเว็บเลย
            # base64_pdf = base64.b64encode(PDFbyte).decode('utf-8')
            # pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
            # st.markdown(pdf_display, unsafe_allow_html=True)

        else:
            st.toast(f"⚠️ File not found in Repo: {doc_no}", icon="❌")

    except Exception as e:
        st.error(f"Error accessing file: {str(e)}")


# ------------------------------------------------------------------

def get_image_base64(username):
    file_path = os.path.join(IMG_FOLDER, f"{username}.png")
    if os.path.exists(file_path):
        with open(file_path, "rb") as f: return base64.b64encode(f.read()).decode()
    return None


def save_uploaded_image(uploaded_file, username):
    try:
        image = Image.open(uploaded_file)
        image = image.resize((150, 150))
        file_path = os.path.join(IMG_FOLDER, f"{username}.png")
        image.save(file_path, "PNG")
        return True
    except:
        return False


def update_heartbeat(username):
    df = load_data(STATUS_FILE)

    # ป้องกันกรณีไฟล์ว่างเปล่า
    if df.empty or 'Name' not in df.columns:
        df = pd.DataFrame(
            columns=["Name", "Current_File", "Level", "Task_Detail", "Last_Updated", "Last_Seen", "Status"])

    idx = df.index[df['Name'] == username].tolist()

    # 🟢 FIX: คำนวณเวลาไทย (UTC + 7)
    thai_now = datetime.utcnow() + timedelta(hours=7)

    # 1. เวลาเต็ม (สำหรับคำนวณ Offline)
    timestamp = thai_now.strftime("%Y-%m-%d %H:%M:%S")

    # 2. เวลาโชว์ (วันที่ย่อ/เดือน + เวลา) เช่น "13/02 11:45"
    time_short = thai_now.strftime("%d/%m %H:%M")

    if idx:
        i = idx[0]
        df.at[i, 'Last_Seen'] = timestamp
        df.at[i, 'Last_Updated'] = time_short  # อัพเดทเวลาโชว์

        # ถ้าสถานะเดิม Offline -> เปลี่ยนเป็น Online
        current_stat = str(df.at[i, 'Status'])
        if "Offline" in current_stat or current_stat == "nan" or current_stat == "":
            df.at[i, 'Status'] = "Online"
    else:
        # User ใหม่
        new_row = pd.DataFrame([{
            "Name": username,
            "Current_File": "Idle",
            "Level": "-",
            "Task_Detail": "-",
            "Last_Updated": time_short,
            "Last_Seen": timestamp,
            "Status": "Online"
        }])
        df = pd.concat([df, new_row], ignore_index=True)

    save_data(df, STATUS_FILE)


def check_auto_offline():
    df = load_data(STATUS_FILE)
    if df.empty: return

    # 🟢 FIX: ใช้เวลาไทยในการเช็ค (UTC + 7)
    thai_now = datetime.utcnow() + timedelta(hours=7)

    changed = False
    for i, row in df.iterrows():
        try:
            last_seen_str = str(row['Last_Seen'])
            status = str(row['Status'])

            # ข้ามคน Offline อยู่แล้ว
            if "Offline" in status: continue
            if last_seen_str == "nan" or last_seen_str == "": continue

            # คำนวณเวลา
            last_seen = datetime.strptime(last_seen_str, "%Y-%m-%d %H:%M:%S")
            diff = (thai_now - last_seen).total_seconds() / 60

            # ถ้าหายไปนานเกินกำหนด (เช่น 5 นาที) -> Offline
            if diff > OFFLINE_TIMEOUT_MINUTES:
                df.at[i, 'Status'] = "⚫ Offline"
                df.at[i, 'Current_File'] = "Idle"
                changed = True
        except:
            pass

    if changed: save_data(df, STATUS_FILE)


def send_private_message(from_user, to_user, message):
    df = load_data(PRIVATE_CHAT_FILE)
    new_msg = pd.DataFrame([{"Timestamp": datetime.now().strftime("%H:%M"), "From_User": from_user, "To_User": to_user,
                             "Message": message}])
    df = pd.concat([df, new_msg], ignore_index=True)
    save_data(df, PRIVATE_CHAT_FILE)


def send_notification(to_user, from_user, msg_type):
    df = load_data(NOTIFY_FILE)
    new_notif = pd.DataFrame(
        [{"To_User": to_user, "From_User": from_user, "Type": msg_type, "Message": f"Action: {msg_type}",
          "Timestamp": datetime.now().strftime("%H:%M")}])
    df = pd.concat([df, new_notif], ignore_index=True)
    save_data(df, NOTIFY_FILE)


def get_my_notifications(my_username):
    df = load_data(NOTIFY_FILE)
    if df.empty: return []
    my_notifs = df[df['To_User'] == my_username]
    if not my_notifs.empty:
        df = df[df['To_User'] != my_username]
        save_data(df, NOTIFY_FILE)
        return my_notifs.to_dict('records')
    return []


def highlight_online_status(row):
    status = str(row['Status'])
    if "Online" in status:
        return ['background-color: #d1e7dd; color: #0f5132; font-weight: 500'] * len(row)
    return [''] * len(row)


def highlight_drawing(row):
    style = [''] * len(row)
    try:
        status = str(row.get('Status', '')).lower()
        approve = str(row.get('Approval Date', ''))
        planned = str(row.get('Planned Submission', ''))
        submit = str(row.get('Submission Date', ''))
        is_blocked = row.get('Is_Blocked', False)

        # 🟢🔴 0. Special Logic: Code C (Green BG / Red Text)
        # เช็คว่ามี 'c' อยู่ในสถานะ แต่ต้องไม่ใช่คำว่า 'closed' (เพราะ closed ก็มีตัว c)
        # และต้องระวังไม่ให้ไปจับคำว่า 'blocked' หรือ 'reject' ถ้าคุณไม่ได้ตั้งใจ
        # แต่นี่คือ Logic ตามที่ขอ: ถ้าเจอ c ให้พื้นเขียว ตัวแดง
        if "c" in status and "closed" not in status:
            return ['background-color: #d4edda; color: #dc3545; font-weight: bold'] * len(row)

        # 🟢 1. Green: Approved/Closed
        is_approved = False
        if approve != "-" and approve != "": is_approved = True
        if any(x in status for x in ["closed", "a", "b"]): is_approved = True

        if is_approved:
            return ['background-color: #d4edda; color: #155724'] * len(row)

        # 🟣 2. Purple: Overdue & Blocked by RFI
        is_overdue = False
        if "overdue" in status or "delayed" in status or "revise" in status: is_overdue = True
        if (submit == "-" or submit == "") and (planned != "-" and planned != ""):
            try:
                if datetime.strptime(planned, '%d %b %Y').date() < date.today(): is_overdue = True
            except:
                pass

        if is_overdue and is_blocked:
            return ['background-color: #e2d9f3; color: #5a3791; font-weight: bold'] * len(row)

        # 🔴 3. Red: Overdue
        if is_overdue:
            return ['background-color: #f8d7da; color: #721c24; font-weight: bold'] * len(row)

        # 🟡 4. Yellow: Pending
        if "pending" in status:
            return ['background-color: #fff3cd; color: #856404; font-weight: bold'] * len(row)

    except:
        pass
    return style


def highlight_rfi(row):
    style = [''] * len(row)
    try:
        act = str(row.get('Action By', '')).upper()
        if any(x in act for x in ["AUR", "STT", "CTA"]):
            return ['background-color: #fff3cd; color: #856404'] * len(row)
        if "CLOSED" in act:
            return ['background-color: #d4edda; color: #155724'] * len(row)
    except:
        pass
    return style


def main_app():
    # 1. เอา set_page_config ไว้บรรทัดแรกสุด
    st.set_page_config(page_title="BIM Tracker Pro", layout="wide", page_icon="🏗️")

    # (ลบส่วน Auto Refresh ออกไปแล้ว)

    init_files()
    check_auto_offline()

    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    if 'username' not in st.session_state: st.session_state.username = ""

    # --- ส่วน Login ---
    if not st.session_state.logged_in:
        st.markdown("### 🏗️ BIM Team Tracker")
        st.caption("Mode: GitHub / Cloud")
        st.divider()
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Login", use_container_width=True):
                users = load_data(CREDENTIALS_FILE)
                if not users.empty:
                    if not users[users['Username'] == u].empty:
                        # Login สำเร็จ
                        st.session_state.logged_in = True
                        st.session_state.username = u

                        # ✅ บังคับอัพเดทสถานะเป็น Online ทันทีตรงนี้
                        update_heartbeat(u)

                        st.rerun()
                    else:
                        st.error("Wrong Password")
                else:
                    st.error("No DB found")
        return

    update_heartbeat(st.session_state.username)
    alerts = get_my_notifications(st.session_state.username)
    for alert in alerts: st.toast(f"{alert['From_User']}: {alert['Type']}", icon="🔔")

    st.sidebar.markdown(f"### 👤 {st.session_state.username}")
    img_b64 = get_image_base64(st.session_state.username)
    if img_b64:
        st.sidebar.markdown(
            f'<img src="data:image/png;base64,{img_b64}" style="width:80px; height:80px; border-radius:50%; display:block; margin-bottom:10px;">',
            unsafe_allow_html=True)

    with st.sidebar.expander("⚙️ Profile"):
        up_file = st.file_uploader("Photo", type=['png', 'jpg'])
        if up_file and st.button("Save"):
            save_uploaded_image(up_file, st.session_state.username)
            st.rerun()

    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

    st.sidebar.divider()
    st.sidebar.markdown("##### 🔧 Work Update")

    # Status Load
    df_current = load_data(STATUS_FILE)
    my_idx = df_current.index[df_current['Name'] == st.session_state.username].tolist()
    if not my_idx:
        my_row = {"Current_File": "Idle", "Level": "-", "Task_Detail": "-", "Status": "Offline"}
    else:
        my_row = df_current.iloc[my_idx[0]]

    current_files_str = str(my_row['Current_File'])
    current_files_list = current_files_str.split("|") if current_files_str not in ["Idle", "nan"] else []

    selected_files = st.sidebar.multiselect("Active Files:", FILE_LIST,
                                            default=[f for f in current_files_list if f in FILE_LIST])
    cur_level = st.sidebar.selectbox("Level:", LEVEL_LIST,
                                     index=LEVEL_LIST.index(my_row['Level']) if my_row['Level'] in LEVEL_LIST else 0)
    task_dtl = st.sidebar.text_input("Detail:",
                                     value=str(my_row['Task_Detail']) if str(my_row['Task_Detail']) != "nan" else "")

    status_map = {"Online": 0, "Busy": 1, "Away": 2}
    status_key = "Online"
    for k in status_map:
        if k in str(my_row['Status']): status_key = k

    status_select = st.sidebar.radio("My Status:", ["🟢 Online", "🔴 Busy", "🟡 Away"],
                                     index=status_map.get(status_key, 0))

    if st.sidebar.button("Update Status", use_container_width=True):
        df_save = load_data(STATUS_FILE)
        idx_s = df_save.index[df_save['Name'] == st.session_state.username].tolist()
        if idx_s:
            i = idx_s[0]
            files_to_save = "|".join(selected_files) if selected_files else "Idle"
            df_save.at[i, 'Current_File'] = files_to_save
            df_save.at[i, 'Level'] = cur_level
            df_save.at[i, 'Task_Detail'] = task_dtl
            df_save.at[i, 'Last_Updated'] = datetime.now().strftime("%H:%M")
            clean_stat = "Online"
            if "Busy" in status_select:
                clean_stat = "Busy"
            elif "Away" in status_select:
                clean_stat = "Away"
            df_save.at[i, 'Status'] = clean_stat
            save_data(df_save, STATUS_FILE)
            st.rerun()

    st.sidebar.divider()
    show_members = st.sidebar.toggle("Show Member Panel", value=True)

    if show_members:
        col_main, col_right = st.columns([3, 1])
    else:
        col_main = st.container()
        col_right = None

    # Load Global Data
    df_rfi_global, rfi_status_map = load_rfi_data_global()

    with col_main:
        st.markdown("### 🏗️ BIM Team Tracker")
        selected_tab = st.radio("Select View:", ["👥 Team Status", "📋 Drawing Status", "📩 RFI Status"], horizontal=True,
                                label_visibility="collapsed")
        st.divider()

        # --- VIEW 1: Team Status ---
        if selected_tab == "👥 Team Status":
            df_show = load_data(STATUS_FILE)
            df_show['Current_File'] = df_show['Current_File'].astype(str).replace('nan', 'Idle')
            mask = (df_show['Current_File'] != "Idle") | (df_show['Status'].str.contains("Online|Busy|Away"))
            active_df = df_show[mask].copy()

            if not active_df.empty:
                active_df['Current_File'] = active_df['Current_File'].str.split('|')
                exploded_df = active_df.explode('Current_File')
                all_files_active = sorted(list(set(exploded_df['Current_File'].unique()) - {"Idle"}))
                filter_files = st.multiselect("🔍 Filter by Work / File:", all_files_active)
                if filter_files: exploded_df = exploded_df[exploded_df['Current_File'].isin(filter_files)]

                display_cols = ["Name", "Current_File", "Level", "Task_Detail", "Last_Updated", "Status"]
                final_df = exploded_df[display_cols].reset_index(drop=True)

                st.dataframe(final_df.style.apply(highlight_online_status, axis=1), use_container_width=True,
                             height=500)
            else:
                st.info("No active sessions.")

        # --- VIEW 2: Drawing Board ---
        elif selected_tab == "📋 Drawing Status":
            st.markdown(f"#### 📑 Master Drawing: `{DRAWING_EXCEL}`")
            df_excel, msg = load_drawing_excel(rfi_status_map)

            if not df_excel.empty:
                # 1. Logic
                def get_month_key(val):
                    try:
                        if pd.isna(val) or val == "-" or val == "": return None
                        dt = datetime.strptime(str(val), '%d %b %Y')
                        return dt.strftime('%Y-%m')
                    except:
                        return None

                df_excel['Filter_Month'] = df_excel['Planned Submission'].apply(get_month_key)

                today = date.today()

                def get_color_category(row):
                    status = str(row.get('Status', '')).lower()
                    approve = str(row.get('Approval Date', ''))
                    planned = str(row.get('Planned Submission', ''))
                    submit = str(row.get('Submission Date', ''))
                    is_blocked = row.get('Is_Blocked', False)

                    # 1. Green: Approved/Closed
                    is_approved = False
                    if approve != "-" and approve != "": is_approved = True
                    if any(x in status for x in ["closed", "a", "b"]): is_approved = True
                    if is_approved: return "🟢 Approved/Closed"

                    # Check Overdue Condition
                    is_overdue = False
                    if "overdue" in status or "delayed" in status or "revise" in status: is_overdue = True
                    if (submit == "-" or submit == "") and (planned != "-" and planned != ""):
                        try:
                            if datetime.strptime(planned, '%d %b %Y').date() < today: is_overdue = True
                        except:
                            pass

                    # 2. Purple & Red & Yellow
                    if is_overdue and is_blocked: return "🟣 Overdue & Blocked"
                    if is_overdue: return "🔴 Overdue"
                    if "pending" in status: return "🟡 Pending"
                    return "⚪ Normal"

                df_excel['Status_Color'] = df_excel.apply(get_color_category, axis=1)

                # 2. Filter Controls
                col_f1, col_f2, col_f3 = st.columns([1, 1, 1])

                with col_f1:
                    all_trades = ["ALL"] + sorted(
                        [str(x) for x in df_excel['Trade'].unique() if str(x) not in ["nan", "-"]])
                    sel_trade = st.selectbox("📂 Filter Trade:", all_trades)

                with col_f2:
                    available_months = sorted([x for x in df_excel['Filter_Month'].unique() if x is not None])
                    sel_months = st.multiselect("📅 Planned Month:", available_months)

                with col_f3:
                    color_options = ["🟢 Approved/Closed", "🟣 Overdue & Blocked", "🔴 Overdue", "🟡 Pending", "⚪ Normal"]
                    sel_colors = st.multiselect("🎨 Status Color:", color_options)

                search_query = st.text_input("🔍 Search (Description / RFAS / Level):", "")

                # 3. Apply Filters
                df_display = df_excel.copy()

                if sel_trade != "ALL":
                    df_display = df_display[df_display['Trade'] == sel_trade]

                if sel_months:
                    df_display = df_display[df_display['Filter_Month'].isin(sel_months)]

                if sel_colors:
                    df_display = df_display[df_display['Status_Color'].isin(sel_colors)]

                if search_query:
                    search_query = search_query.lower()
                    mask = (
                            df_display['Document Description'].astype(str).str.lower().str.contains(search_query,
                                                                                                    na=False) |
                            df_display['RFAS Doc No.'].astype(str).str.lower().str.contains(search_query, na=False) |
                            df_display['Trade'].astype(str).str.lower().str.contains(search_query, na=False)
                    )
                    df_display = df_display[mask]

                # 4. Dashboard Metrics
                st.markdown("---")

                total_view = len(df_display)
                submitted_view = len(df_display[df_display['Submission Date'] != "-"])
                approved_view = len(df_display[df_display['Status_Color'] == "🟢 Approved/Closed"])
                overdue_view = len(df_display[df_display['Status_Color'].isin(["🟣 Overdue & Blocked", "🔴 Overdue"])])

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Total Drawings", f"{total_view} Sheets")
                m2.metric("Submitted", f"{submitted_view} Sheets",
                          delta=f"{(submitted_view / total_view * 100):.1f}%" if total_view > 0 else "0%")
                m3.metric("Approved", f"{approved_view} Sheets")
                m4.metric("Overdue / Blocked", f"{overdue_view} Sheets", delta_color="inverse")

                st.markdown("---")

                # 5. Show Data Table
                df_show_table = df_display.drop(columns=['Filter_Month', 'Status_Color'], errors='ignore')

                event = st.dataframe(
                    df_show_table.style.apply(highlight_drawing, axis=1),
                    use_container_width=True,
                    height=600,
                    hide_index=True,
                    on_select="rerun",
                    selection_mode="single-row",
                    column_order=["Trade", "RFAS Doc No.", "Document Description", "Linked RFI",
                                  "Planned Submission", "Submission Date", "Status", "Action", "Revision"]
                )

                # 6. RFI Link Action
                if event.selection.rows:
                    idx = event.selection.rows[0]
                    sel_row = df_display.iloc[idx]
                    rfas_no = str(sel_row["RFAS Doc No."]).strip()
                    current_link = str(sel_row["Linked RFI"])
                    unique_key_suffix = f"{rfas_no}_{idx}"

                    st.divider()

                    if not rfas_no or rfas_no.lower() == "nan" or rfas_no == "-" or rfas_no == "0":
                        st.error("❌ ไม่สามารถแอด RFI ได้เนื่องจากไม่มีเลข RFAS")
                    else:
                        st.markdown(f"#### 🔗 Link RFI to: `{rfas_no}`")

                        rfi_options = sorted(df_rfi_global["Doc Ref No."].astype(
                            str).unique().tolist()) if not df_rfi_global.empty else []
                        default_sel = [x.strip() for x in current_link.split(',') if
                                       x.strip() and x.strip() in rfi_options]

                        selected_rfis = st.multiselect(
                            "เลือก RFI ที่เกี่ยวข้อง:",
                            options=rfi_options,
                            default=default_sel,
                            key=f"rfi_select_{unique_key_suffix}"
                        )

                        if selected_rfis:
                            st.caption("สถานะ RFI (กดปุ่ม 📂 ด้านขวาเพื่อดูไฟล์):")
                            for rfi_item in selected_rfis:
                                rfi_stat = "UNKNOWN"
                                if not df_rfi_global.empty:
                                    match_row = df_rfi_global[df_rfi_global['Doc Ref No.'] == rfi_item]
                                    if not match_row.empty:
                                        rfi_stat = str(match_row.iloc[0]['Action By']).upper()

                                if any(x in rfi_stat for x in ["CLOSED"]):
                                    bg_color, text_color, border_color = "#d4edda", "#155724", "#c3e6cb"
                                elif any(x in rfi_stat for x in ["STT"]):
                                    bg_color, text_color, border_color = "#fff3cd", "#856404", "#ffeeba"
                                else:
                                    bg_color, text_color, border_color = "#f8d7da", "#721c24", "#f5c6cb"

                                c1, c2 = st.columns([0.85, 0.15])
                                with c1:
                                    st.markdown(
                                        f"""<div style="background-color: {bg_color}; color: {text_color}; padding: 5px 10px; border-radius: 6px; border: 1px solid {border_color}; font-size: 13px; font-weight: 600; margin-bottom: 4px;">{rfi_item} ({rfi_stat})</div>""",
                                        unsafe_allow_html=True)
                                with c2:
                                    if st.button("📂", key=f"btn_open_{rfi_item}_{unique_key_suffix}", help="Open PDF"):
                                        open_pdf(rfi_item)

                        if st.button("💾 Save Link", key=f"btn_save_{unique_key_suffix}"):
                            new_link_str = ", ".join(selected_rfis)
                            save_rfi_link(rfas_no, new_link_str)
                            st.success(f"บันทึกข้อมูลเรียบร้อย! (บันทึกชั่วคราวใน Session)")
                            st.cache_data.clear()
                            time.sleep(0.5)
                            st.rerun()

        # --- VIEW 3: RFI Status ---
        elif selected_tab == "📩 RFI Status":
            st.markdown(f"#### 📩 Master RFI: `{RFI_EXCEL}`")
            if not df_rfi_global.empty:
                col_r1, col_r2 = st.columns([1, 2])
                with col_r1:
                    rfi_trades = ["ALL"] + sorted(
                        [str(x) for x in df_rfi_global['Trade'].unique() if str(x) != "nan" and str(x) != "-"])
                    sel_rfi_trade = st.selectbox("📂 Filter Trade:", rfi_trades, key="rfi_trade")

                with col_r2:
                    rfi_search = st.text_input("🔍 Search RFI:", key="rfi_search")

                df_rfi_show = df_rfi_global.copy()
                if sel_rfi_trade != "ALL": df_rfi_show = df_rfi_show[df_rfi_show['Trade'] == sel_rfi_trade]
                if rfi_search:
                    q = rfi_search.lower()
                    mask = (df_rfi_show['Document Description'].astype(str).str.lower().str.contains(q, na=False) |
                            df_rfi_show['Doc Ref No.'].astype(str).str.lower().str.contains(q, na=False))
                    df_rfi_show = df_rfi_show[mask]

                event_r = st.dataframe(
                    df_rfi_show.reset_index(drop=True).style.apply(highlight_rfi, axis=1),
                    use_container_width=True,
                    height=600,
                    hide_index=True,
                    on_select="rerun",
                    selection_mode="single-row",
                    column_order=["Trade", "Doc Ref No.", "Document Description", "Actual Submission Date", "Action By",
                                  "Approved Status"]
                )

                if event_r.selection.rows:
                    idx = event_r.selection.rows[0]
                    selected_row = df_rfi_show.iloc[idx]
                    doc_no = selected_row['Doc Ref No.']
                    action = str(selected_row['Action By']).upper()

                    if any(x in action for x in ["AUR", "STT", "CLOSED"]):
                        st.info(f"Selected: **{doc_no}** (Action: {action})")
                        if st.button("📂 Download/Open PDF", type="primary", use_container_width=True):
                            open_pdf(doc_no)
                    else:
                        st.warning(f"Selected: {doc_no} (Action: {action}) - PDF available only for AUR/STT/Closed.")

                st.caption(f"Total Rows: {len(df_rfi_show)}")
            else:
                st.info("No RFI Data Found.")

    # --- Right Panel ---
    if show_members and col_right:
        with col_right:
            st.subheader("👥 Members")
            member_container = st.container(height=300)
            with member_container:
                df_show = load_data(STATUS_FILE)
                if not df_show.empty:
                    df_show['is_online'] = df_show['Status'].apply(lambda x: 1 if "Online" in str(x) else 0)
                    df_sorted = df_show.sort_values(by=['is_online', 'Name'], ascending=[False, True])

                    for _, row in df_sorted.iterrows():
                        m_name = row['Name']
                        m_status = row['Status']
                        dot_color = "#28a745" if "Online" in m_status else (
                            "#dc3545" if "Busy" in m_status else "#6c757d")
                        img_src = f"data:image/png;base64,{get_image_base64(m_name)}" if get_image_base64(
                            m_name) else f"https://ui-avatars.com/api/?name={m_name}&background=random&size=64"

                        st.markdown(f"""
                        <div style="display: flex; align-items: center; margin-bottom: 6px; padding: 6px; background: #f8f9fa; border-radius: 8px;">
                            <div style="position: relative; margin-right: 10px;">
                                <img src="{img_src}" style="width: 32px; height: 32px; border-radius: 50%;">
                                <span style="position: absolute; bottom: 0; right: 0; width: 8px; height: 8px; bg-color: {dot_color}; border-radius: 50%; background-color: {dot_color}; border: 1.5px solid white;"></span>
                            </div>
                            <div style="line-height: 1.1;">
                                <div style="font-size: 13px; font-weight: 600;">{m_name}</div>
                                <div style="font-size: 11px; color: #666;">{m_status}</div>
                            </div>
                        </div>""", unsafe_allow_html=True)

            st.markdown("---")
            st.subheader("💬 Interaction")
            other_users = df_show[df_show['Name'] != st.session_state.username][
                'Name'].tolist() if not df_show.empty else []
            target_user = st.selectbox("Member:", other_users)

            if target_user:
                t1, t2 = st.tabs(["🔒 Chat", "🔔 Action"])
                with t1:
                    with st.form("private_chat_form", clear_on_submit=True):
                        pm_msg = st.text_input("Msg:")
                        if st.form_submit_button("Send"):
                            send_private_message(st.session_state.username, target_user, pm_msg)
                            st.rerun()
                with t2:
                    if st.button("🔄 Sync", use_container_width=True):
                        send_notification(target_user, st.session_state.username, "SYNC Central")
                        st.toast("Sent!")
                    if st.button("🔓 Relinquish", use_container_width=True):
                        send_notification(target_user, st.session_state.username, "Relinquish All")
                        st.toast("Sent!")

    if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()


# Run main app directly
if __name__ == "__main__":
    main_app()
