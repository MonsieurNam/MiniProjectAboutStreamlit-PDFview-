import streamlit as st
import fitz  # PyMuPDF
import os
from io import BytesIO

def pymupdf_parse_page(pdf_path: str, page_number: int = 0) -> str:
    """
    Trích xuất văn bản từ một trang cụ thể trong tệp PDF.

    Args:
        pdf_path (str): Đường dẫn đến tệp PDF.
        page_number (int): Số trang để trích xuất văn bản (chỉ số bắt đầu từ 0).

    Returns:
        str: Văn bản đã trích xuất từ trang được chỉ định.
    """
    text = ""
    try:
        with fitz.open(pdf_path) as file:
            if page_number < 0 or page_number >= file.page_count:
                st.error(f"Số trang {page_number + 1} vượt quá phạm vi cho tệp '{pdf_path}'.")
                return ""
            page = file.load_page(page_number)
            text += page.get_text()
    except Exception as e:
        st.error(f"Lỗi mở tệp PDF '{pdf_path}': {e}")
        return ""
    text = text[:230000]  # Giới hạn kích thước văn bản
    return text

def pymupdf_render_page_as_image(pdf_path: str, page_number: int = 0, zoom: float = 1.5) -> bytes:
    """
    Chuyển đổi một trang cụ thể của PDF thành hình ảnh PNG.

    Args:
        pdf_path (str): Đường dẫn đến tệp PDF.
        page_number (int): Số trang để chuyển đổi thành hình ảnh (chỉ số bắt đầu từ 0).
        zoom (float): Hệ số phóng đại để điều chỉnh độ phân giải hình ảnh.

    Returns:
        bytes: Dữ liệu hình ảnh PNG của trang đã chuyển đổi.
    """
    try:
        with fitz.open(pdf_path) as doc:
            if page_number < 0 or page_number >= doc.page_count:
                st.error(f"Số trang {page_number + 1} vượt quá phạm vi cho tệp '{pdf_path}'.")
                return b""
            page = doc.load_page(page_number)
            mat = fitz.Matrix(zoom, zoom)  # Điều chỉnh phóng đại để thay đổi độ phân giải
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes("png")
            return img_bytes
    except Exception as e:
        st.error(f"Lỗi chuyển đổi trang PDF '{pdf_path}': {e}")
        return b""

def parse_data_detail(file_path: str):
    """
    Phân tích tệp data_detail.txt để trích xuất các phần.

    Args:
        file_path (str): Đường dẫn đến tệp data_detail.txt.

    Returns:
        list of dict: Mỗi dict chứa 'start', 'end', và 'name' của một phần.
    """
    sections = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split('#')  # Cập nhật để tách bằng '#'
                if len(parts) < 3:
                    st.warning(f"Bỏ qua dòng không hợp lệ trong data_detail.txt: {line}")
                    continue
                start_page = int(parts[0])
                end_page = int(parts[1])
                name = parts[2].strip()
                sections.append({
                    'start': start_page,
                    'end': end_page,
                    'name': name
                })
    except FileNotFoundError:
        st.error(f"Không tìm thấy tệp '{file_path}'. Vui lòng đảm bảo nó tồn tại.")
    except Exception as e:
        st.error(f"Lỗi đọc tệp '{file_path}': {e}")
    return sections

def get_page_numbers(section):
    """
    Tạo danh sách số trang trong một phần.

    Args:
        section (dict): Một dict chứa 'start' và 'end' của phần.

    Returns:
        list of int: Danh sách số trang.
    """
    return list(range(section['start'], section['end'] + 1))

def initialize_session_state(total_pages=0):
    """
    Khởi tạo các biến trạng thái phiên cho việc điều hướng trang.

    Args:
        total_pages (int): Tổng số trang trong phần đã chọn.
    """
    if 'total_pages' not in st.session_state:
        st.session_state.total_pages = total_pages

def main():
    st.set_page_config(page_title="NHÓM 1", layout="wide")
    st.title("NHÓM 1")

    # Định nghĩa thư mục dữ liệu và đường dẫn đến data_detail.txt
    data_dir = "./data"
    data_detail_path = "data_detail.txt"

    # Phân tích data_detail.txt để lấy các phần
    sections = parse_data_detail(data_detail_path)

    if not sections:
        st.error("Không tìm thấy phần hợp lệ. Vui lòng kiểm tra tệp data_detail.txt của bạn.")
        return

    # Thanh bên để chọn phần chính (I hoặc II)
    st.sidebar.header("Chọn Phần Chính")
    main_sections = [section for section in sections if section['name'].startswith("NHỮNG QUỐC GIA") or section['name'].startswith("XÂY DỰNG")]
    selected_main_section = st.sidebar.selectbox("Chọn một phần chính:", [section['name'] for section in main_sections])

    # Tìm phần chính đã chọn
    selected_main_section_details = next((s for s in sections if s['name'] == selected_main_section), None)

    # Nếu phần chính là phần II, cho phép chọn các phần con
    if selected_main_section.startswith("XÂY DỰNG"):
        st.sidebar.header("Chọn Phần Con")
        sub_sections = [section for section in sections if section['start'] >= selected_main_section_details['start'] and section['start'] <= selected_main_section_details['end']]
        selected_sub_section_name = st.sidebar.selectbox("Chọn một phần con:", [section['name'] for section in sub_sections])
        
        # Tìm chi tiết của phần con đã chọn
        selected_sub_section = next((s for s in sections if s['name'] == selected_sub_section_name), None)
        
        if not selected_sub_section:
            st.error("Không tìm thấy phần đã chọn.")
            return
        
        # Tạo danh sách số trang cho phần đã chọn
        page_numbers = get_page_numbers(selected_sub_section)
    else:
        # Nếu phần chính là phần I, hiển thị nội dung tương ứng
        page_numbers = get_page_numbers(selected_main_section_details)

    total_pages = len(page_numbers)

    # Khởi tạo trạng thái phiên
    initialize_session_state(total_pages=total_pages)

    # Tùy chọn hiển thị văn bản và mức thu phóng
    st.sidebar.header("Tùy Chọn Hiển Thị")
    show_text = st.sidebar.checkbox("Hiển Thị Văn Bản Đã Trích Xuất", value=True)
    zoom_factor = st.sidebar.slider("Mức Thu Phóng", min_value=1.0, max_value=3.0, value=1.5, step=0.1)

    # Màn hình chính: Hiển thị toàn bộ các trang PDF của phần đã chọn
    st.header(f"📄 {selected_sub_section_name if selected_main_section.startswith('XÂY DỰNG') else selected_main_section}")

    for idx, page_num in enumerate(page_numbers, start=1):
        # Xây dựng đường dẫn đến tệp PDF cho trang hiện tại
        pdf_filename = f"page_{page_num:03}.pdf"
        pdf_path = os.path.join(data_dir, pdf_filename)

        if not os.path.isfile(pdf_path):
            st.error(f"Không tìm thấy tệp PDF '{pdf_filename}' trong '{data_dir}'.")
            continue

        # Chuyển đổi và hiển thị trang PDF dưới dạng hình ảnh
        try:
            img_bytes = pymupdf_render_page_as_image(pdf_path, page_number=0, zoom=zoom_factor)
            if img_bytes:
                st.image(img_bytes, caption=f"Trang {page_num}", use_column_width=True)
            else:
                st.error("Không thể hiển thị hình ảnh trang.")
        except Exception as e:
            st.error(f"Lỗi hiển thị trang PDF: {e}")

        st.markdown("---")  # Ngăn cách các trang

    # Sidebar: Phần hiển thị văn bản trích xuất và tải xuống dựa trên từng trang
    st.sidebar.header("Thông Tin Trang")

    for idx, page_num in enumerate(page_numbers, start=1):
        with st.sidebar.expander(f"📄 Trang {page_num}"):
            # Xây dựng đường dẫn đến tệp PDF cho trang hiện tại
            pdf_filename = f"page_{page_num:03}.pdf"
            pdf_path = os.path.join(data_dir, pdf_filename)

            if not os.path.isfile(pdf_path):
                st.error(f"Không tìm thấy tệp PDF '{pdf_filename}' trong '{data_dir}'.")
                continue

            # Trích xuất văn bản từ trang PDF
            page_text = pymupdf_parse_page(pdf_path)

            if show_text:
                st.text_area("Văn Bản Đã Trích Xuất:", value=page_text, height=150)

            # Các tùy chọn tải xuống
            download_col1, download_col2 = st.columns(2)

            # Tải xuống Trang PDF
            with download_col1:
                try:
                    with open(pdf_path, 'rb') as f:
                        pdf_bytes = f.read()
                    st.download_button(
                        label="📥 Tải Xuống Trang PDF",
                        data=pdf_bytes,
                        file_name=pdf_filename,
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"Lỗi chuẩn bị tải xuống PDF: {e}")

            # Tải xuống Văn Bản Đã Trích Xuất
            if show_text:
                with download_col2:
                    try:
                        buffer = BytesIO()
                        buffer.write(page_text.encode('utf-8'))
                        buffer.seek(0)
                        # Thay thế các ký tự không hợp lệ trong tên tệp
                        safe_section_name = "".join(c for c in selected_sub_section_name if c.isalnum() or c in (' ', '_', '-')).rstrip()
                        download_filename = f"{safe_section_name}_Trang_{page_num}.txt"
                        st.download_button(
                            label="📄 Tải Xuống Văn Bản Đã Trích Xuất",
                            data=buffer,
                            file_name=download_filename,
                            mime="text/plain"
                        )
                    except Exception as e:
                        st.error(f"Lỗi chuẩn bị tải xuống văn bản: {e}")

if __name__ == "__main__":
    main()
