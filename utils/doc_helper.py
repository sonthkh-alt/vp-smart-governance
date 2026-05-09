import io
from docx import Document
import PyPDF2

def extract_text_from_pdf(file_stream):
    """
    Trích xuất văn bản từ một luồng file PDF.
    """
    try:
        reader = PyPDF2.PdfReader(file_stream)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Lỗi khi đọc PDF: {str(e)}"

def extract_text_from_docx(file_stream):
    """
    Trích xuất văn bản từ một luồng file DOCX.
    """
    try:
        doc = Document(file_stream)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        return f"Lỗi khi đọc DOCX: {str(e)}"

def create_nd30_document(content_dict):
    """
    Tạo một file Word mới tinh chuẩn thể thức Nghị định 30/2020/NĐ-CP
    """
    try:
        from docx import Document
        from docx.shared import Cm, Pt
        from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
        from docx.enum.table import WD_TABLE_ALIGNMENT
        import io
        import re
        
        doc = Document()
        
        # 1. Khổ giấy và lề A4
        for section in doc.sections:
            section.page_width = Cm(21.0)
            section.page_height = Cm(29.7)
            section.top_margin = Cm(2.0)
            section.bottom_margin = Cm(2.0)
            section.left_margin = Cm(3.0)
            section.right_margin = Cm(2.0)
            
        cq_chu_quan = content_dict.get("co_quan_chu_quan", "")
        cq_ban_hanh = content_dict.get("co_quan_ban_hanh", "")
        so_ky_hieu = content_dict.get("so_ky_hieu", "")
        dia_danh = content_dict.get("dia_danh_ngay_thang", "")
        loai_vb = content_dict.get("loai_van_ban", "")
        trich_yeu = content_dict.get("trich_yeu", "")
        noi_dung = content_dict.get("noi_dung_chinh", "")
        noi_nhan = content_dict.get("noi_nhan", [])
        quyen_han_ky = content_dict.get("quyen_han_ky", "")
        nguoi_ky = content_dict.get("nguoi_ky", "")
        
        # 2. Header Table (Quốc hiệu, Cơ quan)
        table_header = doc.add_table(rows=2, cols=2)
        table_header.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        # Thiết lập lại kích thước cột (tương đối)
        for row in table_header.rows:
            row.cells[0].width = Cm(7.0)
            row.cells[1].width = Cm(9.0)
            
        p_cq1 = table_header.cell(0, 0).paragraphs[0]
        p_cq1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if cq_chu_quan:
            run_cq1 = p_cq1.add_run(cq_chu_quan)
            run_cq1.font.name = 'Times New Roman'
            run_cq1.font.size = Pt(13)
            
        p_cq2 = table_header.cell(1, 0).paragraphs[0]
        p_cq2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cq2.paragraph_format.space_after = Pt(0)
        if cq_ban_hanh:
            run_cq2 = p_cq2.add_run(cq_ban_hanh)
            run_cq2.font.name = 'Times New Roman'
            run_cq2.font.size = Pt(13)
            run_cq2.bold = True
            
            # Đường kẻ ngang đứt/liền dưới cơ quan ban hành (dài khoảng 1/3 - 1/2 chữ)
            p_line1 = table_header.cell(1, 0).add_paragraph()
            p_line1.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_line1.paragraph_format.space_before = Pt(0)
            p_line1.paragraph_format.space_after = Pt(0)
            run_line1 = p_line1.add_run("*" * 15 if len(cq_ban_hanh) > 20 else "*" * 10)
            run_line1.font.name = 'Times New Roman'
            run_line1.font.size = Pt(10)
            
        p_so = table_header.cell(1, 0).add_paragraph()
        p_so.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if so_ky_hieu:
            run_so = p_so.add_run(so_ky_hieu)
            run_so.font.name = 'Times New Roman'
            run_so.font.size = Pt(13)
            
        p_qh1 = table_header.cell(0, 1).paragraphs[0]
        p_qh1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_qh1 = p_qh1.add_run("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM")
        run_qh1.font.name = 'Times New Roman'
        run_qh1.font.size = Pt(13)
        run_qh1.bold = True
        
        p_qh2 = table_header.cell(1, 1).paragraphs[0]
        p_qh2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_qh2.paragraph_format.space_after = Pt(0)
        run_qh2 = p_qh2.add_run("Độc lập - Tự do - Hạnh phúc")
        run_qh2.font.name = 'Times New Roman'
        run_qh2.font.size = Pt(14)
        run_qh2.bold = True
        
        # Đường kẻ ngang liền mạch dưới tiêu ngữ (chiều dài bằng chữ)
        p_line2 = table_header.cell(1, 1).add_paragraph()
        p_line2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_line2.paragraph_format.space_before = Pt(0)
        p_line2.paragraph_format.space_after = Pt(0)
        run_line2 = p_line2.add_run("________________________")
        run_line2.font.name = 'Times New Roman'
        run_line2.font.size = Pt(12)
        
        p_date = table_header.cell(1, 1).add_paragraph()
        p_date.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if dia_danh:
            run_date = p_date.add_run(dia_danh)
            run_date.font.name = 'Times New Roman'
            run_date.font.size = Pt(14)
            run_date.italic = True
            
        doc.add_paragraph() # Khoảng trống
        
        # 3. Tiêu đề văn bản
        if loai_vb:
            p_title = doc.add_paragraph()
            p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run_title = p_title.add_run(loai_vb)
            run_title.font.name = 'Times New Roman'
            run_title.font.size = Pt(14)
            run_title.bold = True
            
        if trich_yeu:
            p_trich = doc.add_paragraph()
            p_trich.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run_trich = p_trich.add_run(trich_yeu)
            run_trich.font.name = 'Times New Roman'
            run_trich.font.size = Pt(14)
            run_trich.bold = True
            if loai_vb == "": # Trường hợp là Công văn
                run_trich.bold = False
            
        doc.add_paragraph() # Khoảng trống
        
        # 4. Nội dung chính (Giữ nguyên chuẩn Justify, 14pt, exactly 19pt, before/after 6pt, indent 1.27cm)
        for line in noi_dung.split('\n'):
            if line.strip() == "":
                continue
                
            new_p = doc.add_paragraph()
            new_p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            new_p.paragraph_format.first_line_indent = Cm(1.27)
            new_p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
            new_p.paragraph_format.line_spacing = Pt(19)
            new_p.paragraph_format.space_before = Pt(6)
            new_p.paragraph_format.space_after = Pt(6)
            
            text_to_process = line.strip()
            
            # Tự động nhận diện dòng "Căn cứ..." để in nghiêng theo quy định
            is_can_cu = text_to_process.lower().startswith("căn cứ")
            
            match = re.match(r'^(\d+(?:\.\d+)*\.)\s+(.*)', text_to_process)
            if match:
                number_part = match.group(1)
                rest_part = match.group(2)
                run_num = new_p.add_run(number_part + " ")
                run_num.bold = True
                run_num.font.name = 'Times New Roman'
                run_num.font.size = Pt(14)
                text_to_process = rest_part
                
            parts = re.split(r'(\*\*.*?\*\*)', text_to_process)
            for part in parts:
                if part.startswith('**') and part.endswith('**'):
                    run = new_p.add_run(part[2:-2])
                    run.bold = True
                else:
                    run = new_p.add_run(part.replace('*', ''))
                    
                if run.text:
                    run.font.name = 'Times New Roman'
                    run.font.size = Pt(14)
                    if is_can_cu:
                        run.italic = True
                    
        doc.add_paragraph() # Khoảng trống
        
        # 5. Footer Table (Nơi nhận, Chữ ký)
        table_footer = doc.add_table(rows=1, cols=2)
        table_footer.alignment = WD_TABLE_ALIGNMENT.CENTER
        table_footer.rows[0].cells[0].width = Cm(7.0)
        table_footer.rows[0].cells[1].width = Cm(9.0)
        
        p_nn_title = table_footer.cell(0, 0).paragraphs[0]
        p_nn_title.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run_nn_title = p_nn_title.add_run("Nơi nhận:")
        run_nn_title.font.name = 'Times New Roman'
        run_nn_title.font.size = Pt(12)
        run_nn_title.bold = True
        run_nn_title.italic = True
        
        if noi_nhan:
            for nn in noi_nhan:
                p_nn = table_footer.cell(0, 0).add_paragraph()
                p_nn.alignment = WD_ALIGN_PARAGRAPH.LEFT
                p_nn.paragraph_format.space_after = Pt(0)
                run_nn = p_nn.add_run(nn)
                run_nn.font.name = 'Times New Roman'
                run_nn.font.size = Pt(11)
                
        p_sign_title = table_footer.cell(0, 1).paragraphs[0]
        p_sign_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if quyen_han_ky:
            for line in quyen_han_ky.split('\n'):
                run_sign_title = p_sign_title.add_run(line + '\n')
                run_sign_title.font.name = 'Times New Roman'
                run_sign_title.font.size = Pt(14)
                run_sign_title.bold = True
            
        p_sign_name = table_footer.cell(0, 1).add_paragraph()
        p_sign_name.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_sign_name.paragraph_format.space_before = Pt(60) # Khoảng trống để ký
        if nguoi_ky:
            run_sign_name = p_sign_name.add_run(nguoi_ky)
            run_sign_name.font.name = 'Times New Roman'
            run_sign_name.font.size = Pt(14)
            run_sign_name.bold = True
            
        output_stream = io.BytesIO()
        doc.save(output_stream)
        output_stream.seek(0)
        return output_stream
        
    except Exception as e:
        print(f"Lỗi khi xử lý template DOCX: {str(e)}")
        return None
