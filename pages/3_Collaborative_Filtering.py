import streamlit as st
import pandas as pd
import pickle
import os
import random

# Hàm cài đặt gói nếu bị thiếu
def install_missing_packages():
    import subprocess
    import sys
    try:
        import surprise
    except ImportError:
        st.warning("Installing required package 'scikit-surprise'. Please wait...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "scikit-surprise"])
        st.success("Package installed successfully! Please restart the app.")
        st.stop()

install_missing_packages()

from surprise import SVDpp

# Tải dữ liệu
st.title("Hệ thống gợi ý sản phẩm - Collaborative Filtering")

data_test_path = './df_summary_collaborative.csv'
df_products_path = './San_pham.csv'
model_path = './svdpp_model.pkl'

if not os.path.exists(data_test_path) or not os.path.exists(df_products_path):
    st.error("Không tìm thấy dữ liệu đầu vào. Vui lòng kiểm tra đường dẫn và thử lại.")
    st.stop()

data_test = pd.read_csv(data_test_path)
df_products = pd.read_csv(df_products_path)
# st.write("Dữ liệu đã được tải thành công!")

# Tải mô hình SVD++
# st.header("Tải mô hình SVD++")
if not os.path.exists(model_path):
    st.error("Không tìm thấy mô hình SVD++. Vui lòng đảm bảo mô hình đã được lưu tại './svdpp_model.pkl'.")
    st.stop()

with open(model_path, 'rb') as f:
    loaded_svd_pp = pickle.load(f)
# st.write("Mô hình SVD++ đã được tải thành công!")

# Hiệu ứng chào mừng
st.markdown(
    """
    <style>
    @keyframes slide-in {
        0% {
            transform: translateX(-100%);
        }
        100% {
            transform: translateX(0);
        }
    }
    .welcome-text {
        font-style: italic;
        font-size: 20px;
        color: #5271C4;
        animation: slide-in 3s ease-in-out;
        white-space: nowrap;
        overflow: hidden;
    }
    </style>
    <div class="welcome-text">
        Chào mừng các bạn đã ghé thăm hệ thống gợi ý sản phẩm của Hasaki chúng tôi!
    </div>
    """,
    unsafe_allow_html=True
)

# Hàm gợi ý sản phẩm
def recommend_products_with_scores(customer_id, df_products, model, top_n=5, rating=None):
    all_products = df_products['ma_san_pham'].unique()
    rated_products = df_products[df_products['ma_khach_hang'] == customer_id]['ma_san_pham'].unique()
    products_to_predict = [prod for prod in all_products if prod not in rated_products]

    recommendations = []
    for product_id in products_to_predict:
        prediction = model.predict(customer_id, product_id)
        recommendations.append((product_id, prediction.est))

    recommended_products = pd.DataFrame(recommendations, columns=['ma_san_pham', 'predicted_rating'])
    recommended_products = recommended_products.groupby('ma_san_pham', as_index=False).agg({'predicted_rating': 'max'})

    if rating is not None:
        recommended_products = recommended_products[recommended_products['predicted_rating'] >= rating]

    recommended_products = recommended_products.nlargest(top_n, 'predicted_rating')

    recommended_products = recommended_products.merge(
        df_products[['ma_san_pham', 'ten_san_pham', 'gia_ban', 'so_sao', 'mo_ta', 'ty_le_giam_gia']].drop_duplicates(subset=['ma_san_pham']),
        on='ma_san_pham',
        how='left'
    )

    # Làm tròn tỷ lệ giảm giá thành 2 chữ số nguyên
    recommended_products['ty_le_giam_gia'] = round(recommended_products['ty_le_giam_gia'], 0)
    return recommended_products

# Hiển thị danh sách sản phẩm
def display_recommended_products(recommended_products, cols=3):
    for i in range(0, len(recommended_products), cols):
        columns = st.columns(cols)
        for j, col in enumerate(columns):
            if i + j < len(recommended_products):
                product = recommended_products.iloc[i + j]
                with col:
                    # st.image("https://via.placeholder.com/150", use_column_width=True)  # Thêm hình ảnh mẫu
                    st.write(f"### {product['ten_san_pham']}")
                    st.write(f"Giá bán: **{product['gia_ban']:,} đ**")
                    st.write(f"Đánh giá: {'⭐' * int(product['so_sao'])}")
                    st.write(f"Giảm giá: **{product['ty_le_giam_gia']}%**")
                    expander = col.expander("Xem mô tả sản phẩm")
                    expander.write(product['mo_ta'])

# Giao diện nhập mã khách hàng
st.header("Nhập mã khách hàng và nhận gợi ý")
input_customer_id = st.text_input("Nhập mã khách hàng (nếu có):", value="")
customer_ids = data_test['ma_khach_hang'].unique()
random_customer_ids = random.sample(list(customer_ids), min(50, len(customer_ids)))

# Dropdown để chọn mã khách hàng
selected_customer_id_dropdown = st.selectbox(
    "Hoặc chọn mã khách hàng từ danh sách:",
    options=[None] + random_customer_ids,
    format_func=lambda x: f"Mã khách hàng: {x}" if x else "Chưa có thông tin khách hàng"
)

# Xác định mã khách hàng cuối cùng
if input_customer_id.strip():
    try:
        selected_customer_id = int(input_customer_id)
        if selected_customer_id not in customer_ids:
            st.warning("Mã khách hàng bạn nhập không tồn tại trong hệ thống.")
            selected_customer_id = None
    except ValueError:
        st.error("Mã khách hàng không hợp lệ. Vui lòng nhập số nguyên.")
        selected_customer_id = None
else:
    selected_customer_id = selected_customer_id_dropdown

# Tùy chọn số lượng sản phẩm và mức đánh giá tối thiểu
max_products = st.slider("Chọn số sản phẩm tối đa:", 1, 10, 5)
star_icons = ["⭐ trở lên", "⭐⭐ trở lên", "⭐⭐⭐ trở lên", "⭐⭐⭐⭐ trở lên", "⭐⭐⭐⭐⭐"]
selected_min_rating = st.radio("Chọn mức đánh giá tối thiểu:", star_icons)
min_rating = star_icons.index(selected_min_rating) + 1

# Nút gợi ý sản phẩm
if st.button("Gợi ý sản phẩm"):
    try:
        if selected_customer_id:
            recommendations = recommend_products_with_scores(
                customer_id=selected_customer_id,
                df_products=data_test,
                model=loaded_svd_pp,
                top_n=max_products,
                rating=min_rating
            )
        else:
            recommendations = data_test[
                (data_test['so_sao'] >= 4) & (data_test['so_sao'] <= 5)
            ].drop_duplicates(subset='ma_san_pham').nlargest(max_products, 'so_sao')

        if recommendations.empty:
            st.warning("Không có sản phẩm nào phù hợp với tiêu chí lọc.")
        else:
            st.write("Danh sách sản phẩm được gợi ý:")
            display_recommended_products(recommendations)

    except Exception as e:
        st.error(f"Lỗi khi thực hiện gợi ý: {e}")
