
import pandas as pd
import streamlit as st
from gensim import models, similarities
import pickle

# Tải dữ liệu sản phẩm
try:
    Product = pd.read_csv('./Product_clean.csv', encoding='utf-8')
except FileNotFoundError:
    st.error("Không tìm thấy file 'Product_clean.csv'. Vui lòng kiểm tra đường dẫn và thử lại.")
    st.stop()

# Tải dictionary và mô hình TF-IDF
try:
    with open('./dictionary.pkl', 'rb') as file:
        dictionary = pickle.load(file)
    tfidf = models.TfidfModel.load('./tfidf.tfidfmodel')
    index = similarities.SparseMatrixSimilarity.load('./index.docsim')
except FileNotFoundError:
    st.error("Không tìm thấy các mô hình hoặc dictionary. Vui lòng kiểm tra file và thử lại.")
    st.stop()

# Tùy chỉnh giao diện Streamlit
st.title("Content-Based Filtering - Hệ thống gợi ý sản phẩm")

# Hàm hiển thị sản phẩm
def display_products(products, cols=4):
    num_items = len(products)
    rows = (num_items + cols - 1) // cols
    for row in range(rows):
        cols_instances = st.columns(cols)
        for col_idx in range(cols):
            idx = row * cols + col_idx
            if idx < num_items:
                with cols_instances[col_idx]:
                    st.markdown(f"**{products[idx]['Tên sản phẩm']}**")
                    st.markdown(f"Giá: **{products[idx]['Giá bán']:,}** đ")
                    st.markdown(f"Đánh giá: **{products[idx]['Điểm trung bình']}⭐**")
                    st.markdown(f"Giảm giá: **{products[idx]['Tỷ lệ giảm giá']}%**")
                    # Hiển thị mô tả sản phẩm
                    expander = st.expander("Xem mô tả sản phẩm")
                    expander.write(products[idx]['Mô tả'])

# Hàm gợi ý sản phẩm từ danh sách
def show_similar_products_gensim1(dataframe, index, selected_product_code=None, num_similar=4):
    if selected_product_code is None:
        st.warning("Bạn chưa chọn sản phẩm nào để gợi ý.")
        return pd.DataFrame()

    selected_product = dataframe[dataframe['ma_san_pham'] == selected_product_code]
    if selected_product.empty:
        st.error(f"Không tìm thấy sản phẩm với mã: {selected_product_code}")
        return pd.DataFrame()

    selected_product_content = selected_product.iloc[0]['content']
    kw_vector = dictionary.doc2bow(selected_product_content.lower().split())
    sim = index[tfidf[kw_vector]]

    sorted_sim_indices = sorted(range(len(sim)), key=lambda k: sim[k], reverse=True)
    seen_similarities = {}

    for idx in sorted_sim_indices:
        if dataframe.iloc[idx]['ma_san_pham'] == selected_product_code:
            continue

        similarity = sim[idx]
        similar_product = dataframe.iloc[idx]
        if similar_product['diem_trung_binh'] >= 3:
            seen_similarities[similarity] = {
                "Tên sản phẩm": similar_product['ten_san_pham'],
                "Điểm trung bình": similar_product['diem_trung_binh'],
                "Giá bán": similar_product['gia_ban'],
                "Tỷ lệ giảm giá": f"{similar_product['ty_le_giam_gia'] * 100:.0f}",
                "Mô tả": similar_product['mo_ta']
            }
        if len(seen_similarities) == num_similar:
            break

    return pd.DataFrame(list(seen_similarities.values()))

# Hàm tìm kiếm sản phẩm dựa vào nội dung nhập vào
def show_similar_products_input_gensim2(dataframe, index, input_product_name, num_similar=4):
    input_product_tokens = input_product_name.lower().split()
    kw_vector = dictionary.doc2bow(input_product_tokens)
    sim = index[tfidf[kw_vector]]

    sorted_sim_indices = sorted(range(len(sim)), key=lambda k: sim[k], reverse=True)
    seen_similarities = {}
    for idx in sorted_sim_indices:
        similarity = sim[idx]
        similar_product = dataframe.iloc[idx]
        similar_product_name = similar_product['ten_san_pham']
        similar_product_score = similar_product['diem_trung_binh']
        similar_product_discount = similar_product.get('ty_le_giam_gia', 0) * 100

        if similar_product_name.lower() != input_product_name.lower() and similar_product_score >= 3:
            seen_similarities[similarity] = {
                "Tên sản phẩm": similar_product_name,
                "Điểm trung bình": similar_product_score,
                "Giá bán": similar_product['gia_ban'],
                "Tỷ lệ giảm giá": round(similar_product_discount, 0),
                "Mô tả": similar_product['mo_ta']
            }
        if len(seen_similarities) == num_similar:
            break

    return pd.DataFrame(list(seen_similarities.values()))

# Trang tìm kiếm sản phẩm theo từ khóa nhập vào
def search_by_input():
    st.markdown("### Tìm kiếm sản phẩm dựa vào nội dung nhập")

    if "input_product_name" not in st.session_state:
        st.session_state["input_product_name"] = ""

    input_product_name = st.text_area(
        "Nhập tên sản phẩm bạn muốn tìm (hoặc để trống để xem Top 50 sản phẩm):",
        value=st.session_state["input_product_name"],
        key="input_product_name",
        height=100
    )
    num_similar = st.slider("Số lượng sản phẩm gợi ý:", 1, 10, 5)

    if st.button("Tìm kiếm"):
        if not input_product_name.strip():
            view_top_50_products()
        else:
            similar_products_df = show_similar_products_input_gensim2(Product, index, input_product_name, num_similar)
            if not similar_products_df.empty:
                display_products(similar_products_df.to_dict("records"))
            else:
                st.warning("Không tìm thấy sản phẩm nào phù hợp!")

# Trang hiển thị Top 50 sản phẩm có đánh giá cao nhất
def view_top_50_products():
    st.markdown("### Top 50 sản phẩm có đánh giá cao nhất")
    high_rating_products = Product.sort_values(by="diem_trung_binh", ascending=False).head(50)
    high_rating_products['ty_le_giam_gia'] = high_rating_products['ty_le_giam_gia'] * 100
    high_rating_products['ty_le_giam_gia'] = high_rating_products['ty_le_giam_gia'].round(0)
    st.markdown(f"Hiển thị **{len(high_rating_products)}** sản phẩm được đánh giá cao nhất:")
    display_products(
        high_rating_products[["ten_san_pham", "diem_trung_binh", "gia_ban", "ty_le_giam_gia", "mo_ta"]]
        .rename(
            columns={
                "ten_san_pham": "Tên sản phẩm",
                "diem_trung_binh": "Điểm trung bình",
                "gia_ban": "Giá bán",
                "ty_le_giam_gia": "Tỷ lệ giảm giá",
                "mo_ta": "Mô tả"
            }
        )
        .to_dict("records"),
        cols=4,
    )

# Trang gợi ý sản phẩm từ danh sách ngẫu nhiên
def recommend_by_product():
    st.markdown("### Gợi ý sản phẩm từ danh sách các sản phẩm của Hasaki (50 sản phẩm khách hàng xem qua)")
    random_products = Product.sample(50)
    selected_code = st.selectbox(
        "Chọn sản phẩm muốn hệ thống gợi ý:",
        random_products['ma_san_pham'].values,
        format_func=lambda x: Product.loc[Product['ma_san_pham'] == x, 'ten_san_pham'].values[0]
    )
    n = st.slider("Số lượng sản phẩm gợi ý:", 1, 10, 5)
    if st.button("Gợi ý"):
        similar_products_df = show_similar_products_gensim1(Product, index, selected_product_code=selected_code, num_similar=n)
        if not similar_products_df.empty:
            display_products(similar_products_df.to_dict('records'))
        else:
            st.warning("Không tìm thấy sản phẩm phù hợp!")

# Tích hợp giao diện
page_names_to_funcs = {
    "Hiển thị Top 50 sản phẩm đánh giá cao nhất": view_top_50_products,
    "Gợi ý sản phẩm từ danh sách các sản phẩm của Hasaki (50 sản phẩm khách hàng xem qua)": recommend_by_product,
    "Tìm kiếm sản phẩm bằng nội dung nhập": search_by_input,
}

selected_page = st.sidebar.radio("Chọn chế độ gợi ý", page_names_to_funcs.keys())
page_names_to_funcs[selected_page]()
