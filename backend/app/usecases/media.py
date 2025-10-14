import os
import uuid
import subprocess
from datetime import datetime
from fastapi import UploadFile
from app.schemas import media
from app.core.logger import main_logger
from app.core.settings import BASE_URL, BASE_PATH


def split_by_size(file: UploadFile, size: int = 25) -> media.ResBase:
    try:
        temp_dir = os.path.join("app", "upload")
        os.makedirs(temp_dir, exist_ok=True)
        
        now = datetime.now().strftime("%Y%m%d")
        file_id = f"{now}_{uuid.uuid4().hex[:8]}"
        input_filename = f"{file_id}_input{os.path.splitext(file.filename)[1]}"
        input_path = os.path.join(temp_dir, input_filename)
        
        content = file.file.read()
        with open(input_path, "wb") as f:
            f.write(content)
        
        file_info_cmd = [
            "ffprobe", 
            "-v", "error",
            "-show_entries", "format=duration,size",
            "-of", "default=noprint_wrappers=1:nokey=1",
            input_path
        ]
        
        process = subprocess.run(file_info_cmd, capture_output=True, text=True)
        if process.returncode != 0:
            raise Exception(f"FFprobeでファイル情報の取得に失敗しました: {process.stderr}")
        
        output_lines = process.stdout.strip().split('\n')
        if len(output_lines) >= 2:
            bitrate = float(output_lines[1]) * 8 / float(output_lines[0])
            segment_time = (size * 8 * 1024 * 1024) / bitrate if bitrate > 0 else 60
        else:
            segment_time = 60
            
        output_basename = f"{file_id}_%03d{os.path.splitext(file.filename)[1]}"
        output_path = os.path.join(temp_dir, output_basename)
        
        split_cmd = [
            "ffmpeg",
            "-i", input_path,
            "-c", "copy",
            "-map", "0",
            "-segment_time", str(segment_time),
            "-f", "segment",
            "-reset_timestamps", "1",
            output_path
        ]
        
        process = subprocess.run(split_cmd, capture_output=True, text=True)
        if process.returncode != 0:
            raise Exception(f"ファイル分割に失敗しました: {process.stderr}")
            
        split_files = [f for f in os.listdir(temp_dir) 
                      if f.startswith(file_id) and f != input_filename]
        
        media_urls = []
        for split_file in sorted(split_files):
            url = f"{BASE_URL}{BASE_PATH}/upload/{split_file}"
            media_urls.append(url)
            
        os.remove(input_path)
        main_logger.info(f"ファイルを {len(media_urls)} 個に分割しました: {file.filename}")
        
        return media.ResBase(media_urls=media_urls)
        
    except Exception as e:
        main_logger.error(f"ファイル分割（容量） error: {e}")
        raise Exception(f"ファイル分割（容量）に失敗しました: {str(e)}")
