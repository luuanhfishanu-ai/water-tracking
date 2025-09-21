import streamlit as st
import pandas as pd
from datetime import date

# ====== Quản lý đăng nhập / đăng ký ======
if "users" not in st.session_state:
    st.session_state["users"] = {"admin": "123"}  # user mẫu
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "current_user" not in st.session_state:
    st.session_state["current_user"] = None
if "warning_threshold" not in st.session_state:
    st.session_state["warning_threshold"] = {}

# ====== Form login/register ======
if not st.session_state["logged_in"]:
    st.title("🔑 Đăng nhập / Đăng ký")

    choice = st.radio("Chọn:", ["Đăng nhập", "Đăng ký"])
    user = st.text_input("Tên đăng nhập")
    pwd = st.text_input("Mật khẩu", type="password")

    if choice == "Đăng nhập":
        if st.button("Đăng nhập"):
            if user in st.session_state["users"] and st.session_state["users"][user] == pwd:
                st.session_state["logged_in"] = True
                st.session_state["current_user"] = user
                if user not in st.session_state["warning_threshold"]:
                    st.session_state["warning_threshold"][user] = 200  # mặc định
                st.success("✅ Đăng nhập thành công")
                st.rerun()
            else:
                st.error("❌ Sai tài khoản hoặc mật khẩu")
    else:  # Đăng ký
        if st.button("Đăng ký"):
            if user in st.session_state["users"]:
                st.error("❌ Tài khoản đã tồn tại")
            else:
                st.session_state["users"][user] = pwd
                st.session_state["warning_threshold"][user] = 200
                st.success("🎉 Đăng ký thành công, hãy đăng nhập lại")
else:
    # ====== Sau khi đăng nhập thì load app ======
    st.sidebar.write(f"👋 Xin chào, {st.session_state['current_user']}")
    if st.sidebar.button("Đăng xuất"):
        st.session_state["logged_in"] = False
        st.session_state["current_user"] = None
        st.rerun()

    # ====== Bảng tham chiếu hoạt động -> lít nước ======
    WATER_USAGE = {
        "Tắm vòi sen (5 phút)": 50,
        "Tắm bồn": 150,
        "Giặt tay (1 lần)": 30,
        "Giặt máy (1 lần)": 90,
        "Đánh răng": 3,
        "Rửa mặt": 3,
        "Rửa chén (tay)": 20,
        "Rửa chén (máy)": 15,
        "Nấu ăn bữa sáng": 12,
        "Nấu ăn trưa (1-2 người)": 25,
        "Nấu ăn trưa (3-4 người)": 35,
        "Nấu ăn tối (4 người)": 45,
        "Bữa tiệc (6-10 người)": 100
    }

    # ====== Load dữ liệu ======
    try:
        df = pd.read_csv("water_usage.csv")
    except:
        df = pd.DataFrame(columns=["Date", "Household_ID", "Activity", "Water_Usage_L"])

    st.set_page_config(page_title="Smart Water Usage Tracker", layout="wide")
    st.title("💧 Smart Water Usage Tracker")

    # ====== Tabs ======
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Dashboard", 
        "➕ Nhập theo hoạt động", 
        "✍️ Nhập thủ công (m³)",
        "⚙️ Cài đặt"
    ])

    # ===================== TAB 1: Dashboard =====================
    with tab1:
        st.header("📊 Dashboard tổng quan")

        # Chỉ lấy dữ liệu của user đang đăng nhập
        user_df = df[df["Household_ID"] == st.session_state["current_user"]]

        if user_df.empty:
            st.info("Bạn chưa có dữ liệu nào, hãy nhập ở các tab bên cạnh 👉")
        else:
            # Tổng hợp theo ngày
            daily = user_df.groupby("Date")["Water_Usage_L"].sum()

            # Tổng quan hôm nay
            today = str(date.today())
            today_usage = daily.get(today, 0)
            daily_avg = daily.mean()
            total_usage = user_df["Water_Usage_L"].sum()

            col1, col2, col3 = st.columns(3)
            col1.metric("Hôm nay", f"{today_usage:.0f} L")
            col2.metric("Trung bình/ngày", f"{daily_avg:.0f} L")
            col3.metric("Tổng cộng", f"{total_usage:.0f} L")

            # ⚠️ Cảnh báo nếu vượt ngưỡng
            threshold = st.session_state["warning_threshold"][st.session_state["current_user"]]
            if today_usage > threshold:
                st.error(f"⚠️ Hôm nay bạn đã dùng {today_usage:.0f} L, vượt ngưỡng {threshold} L!")

            st.subheader("📈 Xu hướng tiêu thụ nước")
            st.line_chart(daily)

            st.subheader("📑 Nhật ký gần đây (có thể xóa)")
            for i, row in user_df.tail(10).iterrows():
                cols = st.columns([3, 2, 2, 2, 1])
                cols[0].write(row["Date"])
                cols[1].write(row["Activity"])
                cols[2].write(f"{row['Water_Usage_L']} L")
                cols[3].write(f"ID: {i}")
                if cols[4].button("❌", key=f"del_{i}"):
                    df = df.drop(i)
                    df.to_csv("water_usage.csv", index=False)
                    st.rerun()

    # ===================== TAB 2: Nhập theo hoạt động =====================
    with tab2:
        st.header("➕ Nhập dữ liệu theo hoạt động")

        with st.form("new_activity"):
            new_date = st.date_input("Ngày", value=date.today())
            new_household = st.text_input("Mã hộ", st.session_state["current_user"])
            activity = st.selectbox("Hoạt động", list(WATER_USAGE.keys()))
            times = st.number_input("Số lần thực hiện", min_value=1, value=1)

            submitted = st.form_submit_button("Thêm dữ liệu")
            if submitted:
                water_used = WATER_USAGE[activity] * times
                new_row = {
                    "Date": str(new_date),
                    "Household_ID": new_household,
                    "Activity": activity,
                    "Water_Usage_L": water_used
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                df.to_csv("water_usage.csv", index=False)
                st.success(f"✅ Đã thêm: {activity} x{times} → {water_used} L")

    # ===================== TAB 3: Nhập thủ công =====================
    with tab3:
        st.header("✍️ Nhập dữ liệu thủ công (theo m³)")

        with st.form("new_manual"):
            new_date = st.date_input("Ngày", value=date.today(), key="manual_date")
            new_household = st.text_input("Mã hộ", st.session_state["current_user"], key="manual_household")
            usage_m3 = st.number_input("Số nước tiêu thụ (m³)", min_value=0.0, step=0.1)
            submitted_manual = st.form_submit_button("Thêm dữ liệu")

            if submitted_manual:
                usage_l = usage_m3 * 1000  # đổi m³ -> L
                new_row = {
                    "Date": str(new_date),
                    "Household_ID": new_household,
                    "Activity": "Thủ công (m³)",
                    "Water_Usage_L": usage_l
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                df.to_csv("water_usage.csv", index=False)
                st.success(f"✅ Đã thêm dữ liệu thủ công: {usage_m3} m³ ({usage_l} L)")

    # ===================== TAB 4: Cài đặt =====================
    with tab4:
        st.header("⚙️ Cài đặt tài khoản")
        current_user = st.session_state["current_user"]

        threshold = st.number_input(
            "Ngưỡng cảnh báo (L/ngày)", 
            min_value=50, 
            max_value=2000, 
            value=st.session_state["warning_threshold"][current_user],
            step=10
        )
        if st.button("Lưu cài đặt"):
            st.session_state["warning_threshold"][current_user] = threshold
            st.success("✅ Đã lưu ngưỡng cảnh báo mới")
