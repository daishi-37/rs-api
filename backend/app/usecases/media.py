import os
import uuid
import subprocess
import time
import shutil
from datetime import datetime
from fastapi import UploadFile
from app.schemas import media
from app.core.logger import main_logger
from app.core import settings


MEDIA_DIR = os.path.join(settings.UPLOAD_DIR, "media")  # メディアファイルの保存先ディレクトリ
FILE_RETENTION_PERIOD = 24 * 60 * 60                    # ファイルの保持期間（秒） 


def clean_files() -> None:
    main_logger.info("-------- 定期ファイル削除:開始 -----")
    try:
        if not os.path.exists(MEDIA_DIR):
            return
            
        current_time = time.time()
        cleaned_count = 0
        
        for filename in os.listdir(MEDIA_DIR):
            file_path = os.path.join(MEDIA_DIR, filename)
            
            file_mod_time = os.path.getmtime(file_path)
            
            if current_time - file_mod_time > FILE_RETENTION_PERIOD:
                try:
                    os.remove(file_path)
                    main_logger.info(f"ファイル削除完了 {file_path}")
                    cleaned_count += 1
                except Exception as e:
                    main_logger.error(f"ファイル削除エラー {filename}: {e}")
        
        if cleaned_count > 0:
            main_logger.info(f"{cleaned_count}件の古いメディアファイルを削除しました")
            
    except Exception as e:
        main_logger.error(f"古いファイルのクリーンアップ中にエラーが発生しました: {e}")


def split_by_size(file: UploadFile, size: int = 25) -> media.ResBase:
    main_logger.info("-------- メディアファイル分割処理：開始 -----")
    try:
        now = datetime.now().strftime("%Y%m%d")
        file_id = f"{now}_{uuid.uuid4().hex[:8]}"
        input_filename = f"{file_id}_input{os.path.splitext(file.filename)[1]}"
        input_path = os.path.join(MEDIA_DIR, input_filename)
        
        # ストリームからファイルに直接コピーし、メモリ使用量を削減
        with open(input_path, "wb") as f:
            file.file.seek(0)
            shutil.copyfileobj(file.file, f)
        
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
        output_path = os.path.join(MEDIA_DIR, output_basename)
        
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
            
        split_files = [f for f in os.listdir(MEDIA_DIR) 
                      if f.startswith(file_id) and f != input_filename]
        
        media_urls = []
        for split_file in sorted(split_files):
            # 新しいマウント設定に合わせたURLパス構造
            url = f"{settings.BASE_URL}{settings.BASE_PATH}/uploads/media/{split_file}"
            media_urls.append(url)
            
            # 検証のために各ファイルの存在確認と権限をログに記録
            file_path = os.path.join(MEDIA_DIR, split_file)
            if os.path.exists(file_path):
                file_perms = oct(os.stat(file_path).st_mode)[-3:]
                main_logger.info(f"ファイル確認: {file_path} 存在します。権限: {file_perms}")
            else:
                main_logger.error(f"ファイル確認: {file_path} 存在しません")
            
        os.remove(input_path)
        main_logger.info(f"ファイルを {len(media_urls)} 個に分割しました: {file.filename}")

        return media.ResBase(media_urls=media_urls)
        
    except Exception as e:
        main_logger.error(f"ファイル分割（容量） error: {e}")
        raise Exception(f"ファイル分割（容量）に失敗しました: {str(e)}")
