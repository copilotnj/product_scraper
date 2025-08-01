import streamlit as st
import pandas as pd
import json
import os
import glob

DATA_DIR = "data"

@st.cache_data
def load_latest_products_data(data_dir):
    try:
        list_of_files = glob.glob(os.path.join(data_dir, 'all_products_*.json'))
        if not list_of_files:
            return None
        latest_file = max(list_of_files, key=os.path.getctime)
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"加载数据文件失败: {e}")
        return None

def main():
    st.set_page_config(layout="wide", page_title="A-Premium 产品查看器")
    st.title("A-Premium 产品数据查看器")

    df_products_original = load_latest_products_data(DATA_DIR)
    if df_products_original is None or df_products_original.empty:
        st.warning("未能加载产品数据或数据为空。请确保 'data' 文件夹中有 'all_products_*.json' 文件。")
        return

    df_display = df_products_original.copy()
    st.sidebar.header("筛选和搜索")

    # 分类统计
    category_counts = {}
    if 'category' in df_products_original.columns:
        for cat, cnt in df_products_original['category'].value_counts().items():
            category_counts[cat] = cnt
        total_categories = len(category_counts)
        # 构造下拉选项，带数量
        unique_categories = ["所有分类"] + [
            f"{cat} ({category_counts[cat]})" for cat in sorted(category_counts)
        ]
        # 在下拉框标题后显示分类总数
        st.sidebar.markdown(
            f"<span style='font-weight:bold'>按产品主分类筛选 (Filter by Category)</span> <span style='color:gray'>（共 {total_categories} 类）</span>",
            unsafe_allow_html=True
        )
        selected = st.sidebar.selectbox("", unique_categories)
        # 解析选择
        if selected != "所有分类":
            # 去掉括号及数量
            selected_category = selected.rsplit(' (', 1)[0]
            df_display = df_display[df_display['category'] == selected_category]
    else:
        st.sidebar.text("数据中未找到 'category' 字段用于分类。")

    # 关键词搜索（仅模糊搜索名称）
    search_term = st.sidebar.text_input("名称搜索")
    if search_term and 'name' in df_display.columns:
        mask = df_display['name'].astype(str).str.contains(search_term, case=False, na=False)
        df_display = df_display[mask]

    st.header("产品列表 (Product List)")

    # 计算去重OE号总数
    unique_oe_numbers = set()
    if 'oe_number' in df_display.columns:
        for oe_list in df_display['oe_number']:
            if isinstance(oe_list, list):
                unique_oe_numbers.update(str(oe).strip() for oe in oe_list if oe)
            elif pd.notna(oe_list) and oe_list:
                unique_oe_numbers.add(str(oe_list).strip())
    st.write(f"共找到 {len(df_display)} 条产品记录 (Found {len(df_display)} records)。独立 OE 号总数 (Total Unique OE Numbers): {len(unique_oe_numbers)}")

    column_mapping = {
        'name': 'Name (产品名称)',
        'sku': 'SKU',
        'item_number': 'Item Number (物料号)',
        'price': 'Price (价格)',
        'original_price': 'Original Price (原价)',
        'category': 'Category (分类)',
        'brand': 'Brand (品牌)',
        'availability': 'Availability (库存状态)',
        'sales': 'Sales (销量)',
        'review_count': 'Review Count (评论数)',
        'review_rating': 'Review Rating (评分)',
        'warranty': 'Warranty (质保)',
        'fitment': 'Fitment (适配车型)',
        'oe_number': 'OE Number (OE号)',
        'interchange_number': 'Interchange Number (替换号)',
        'url': 'Product URL (产品链接)',
        'image_url': 'Image URL (图片链接)',
        'material': 'Material (材质)',
        'color': 'Color (颜色)',
        'installation': 'Installation (安装方式)'
    }

    display_columns = [
        'name', 'sku', 'item_number', 'price', 'category', 'brand',
        'availability', 'sales', 'fitment', 'oe_number',
        'material', 'color', 'installation', 'url', 'image_url'
    ]
    display_columns = [col for col in display_columns if col in df_display.columns]
    df_for_table = df_display[display_columns].copy()

    # SKU、Fitment分割为标签
    if 'sku' in df_for_table.columns:
        df_for_table['sku'] = df_for_table['sku'].fillna('').astype(str).apply(
            lambda x: [s.strip() for s in x.split(',') if s.strip()] if x else []
        )
    if 'fitment' in df_for_table.columns:
        df_for_table['fitment'] = df_for_table['fitment'].fillna('').astype(str).apply(
            lambda x: [s.strip() for s in x.split(';')] if x.strip() else []
        )

    df_for_table.rename(columns=column_mapping, inplace=True)

    column_config_dict = {}
    if 'Product URL (产品链接)' in df_for_table.columns:
        column_config_dict['Product URL (产品链接)'] = st.column_config.LinkColumn(
            "产品链接", help="点击打开产品页面", display_text="打开链接"
        )
    if 'Image URL (图片链接)' in df_for_table.columns:
        column_config_dict['Image URL (图片链接)'] = st.column_config.LinkColumn(
            "图片链接", help="点击查看图片", display_text="查看图片"
        )

    if not df_for_table.empty:
        st.dataframe(
            df_for_table,
            column_config=column_config_dict if column_config_dict else None,
            hide_index=True
        )
    else:
        st.info("没有找到符合条件的产品。 (No products found matching your criteria.)")

if __name__ == "__main__":
    main()