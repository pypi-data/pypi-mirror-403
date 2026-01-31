import sys
sys.path.append(r"E:\codes\PDF2PPT\PDF2PPT")
from notebooklm2ppt.utils.ppt_refiner import refine_ppt
import os



if __name__=="__main__":
    # 重定向输出到log文件
    sys.stdout = open(r"log.txt", "w", encoding="utf-8")
    # (tmp_image_dir, json_file, ppt_file, png_dir, png_files, final_out_ppt_file
    tmp_image_dir = r"E:\codes\PDF2PPT\PDF2PPT\dist\workspace\tmp_images"
    png_dir = r"E:\codes\PDF2PPT\PDF2PPT\dist\workspace\AI_Summit_Strategic_Blueprint_pngs"
    ppt_file = r"E:\codes\PDF2PPT\PDF2PPT\dist\workspace\AI_Summit_Strategic_Blueprint.pptx"
    json_file = r"E:\codes\PDF2PPT\PDF2PPT\dist\workspace\MinerU_AI_Summit_Strategic_Blueprint__20260128120952.json"
    png_files = os.listdir(png_dir)
    png_files = sorted([f for f in png_files if not f.endswith("_bg.png")])
    print(png_files)
    # png_files = ['page_0010.png']
    out_ppt_file = ppt_file.replace(".pptx", "_refined.pptx")
    refine_ppt(tmp_image_dir, json_file, ppt_file, png_dir, png_files, out_ppt_file)
