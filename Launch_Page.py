import streamlit as st
import base64

# Cấu hình trang Streamlit
st.set_page_config(
    page_title="A Recommender System for Hasaki.vn",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Tùy chỉnh giao diện sidebar
def set_sidebar_style():
    sidebar_style = '''
    <style>
    [data-testid="stSidebar"] {
        background: linear-gradient(-225deg, #5271C4 0%, #B19FFF 48%, #ECA1FE 100%);
        color: white;
    }
    </style>
    '''
    st.markdown(sidebar_style, unsafe_allow_html=True)

set_sidebar_style()

# Hàm đặt hình nền
def set_background_image(image_file):
    try:
        with open(image_file, "rb") as file:
            encoded_string = base64.b64encode(file.read()).decode()
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url(data:image/png;base64,{encoded_string});
                background-size: 100% 100%;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    except FileNotFoundError:
        st.error(f"Không tìm thấy file hình nền: {image_file}")

# Đặt hình nền
set_background_image("hasaki_background.jpg")

# Tiêu đề chính và nút điều hướng trên cùng một hàng
st.markdown(
    '''
    <style>
    .header-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .custom-title {
        color: #0047AB; /* Màu xanh đậm */
        font-style: italic; /* Chữ in nghiêng */
        font-size: 30px; /* Kích thước chữ */
        margin-left: 10px; /* Sát với sidebar */
    }
    .custom-link {
        color: #0047AB; /* Màu xanh đậm */
        font-size: 18px; /* Kích thước chữ */
        text-decoration: underline; /* Thêm gạch chân */
        font-style: italic; /* Chữ in nghiêng */
        margin-right: 10px; /* Sát lề phải */
    }
    </style>
    <div class="header-container">
        <h1 class="custom-title">A Recommender System for Hasaki.vn 🛒</h1>
        <a href="https://hasaki.vn" target="_blank" class="custom-link">Hãy tham quan các sản phẩm trên website của chúng tôi tại đây: Hasaki.vn</a>
    </div>
    ''',
    unsafe_allow_html=True
)

# Danh sách thành viên nhóm trong sidebar
def display_team_members_in_sidebar(members):
    st.sidebar.markdown('<h2 style="color:#CCFF00; text-align: left;">Thành viên nhóm:</h2>', unsafe_allow_html=True)
    member_html = '<div style="color:#0047AB; font-size: 18px; text-align: left; font-weight: bold;">' + \
                  '<br>'.join(members) + \
                  '</div>'
    st.sidebar.markdown(member_html, unsafe_allow_html=True)

team_members = ["1. Phan Minh Huệ", "2. Huỳnh Danh Nhân"]
display_team_members_in_sidebar(team_members)
