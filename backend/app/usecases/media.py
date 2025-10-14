import os
import uuid
import subprocess
from datetime import datetime
from fastapi import UploadFile
from app.schemas import media
from app.core.logger import main_logger
from app.core.settings import BASE_URL, BASE_PATH


def split_by_size(file: UploadFile, size: int = 25) -> media.ResBase:
    """
    ファイルをサイズ（MB）ごとに分割し、分割したファイルのURLリストを返す
    
    Args:
        file: 分割対象のファイル
        size: 分割するサイズ（MB単位）
    
    Returns:
        media.ResBase: 分割したファイルのURLリスト
    
    Raises:
        Exception: ファイル分割処理に失敗した場合
    """
    try:
        # 一時ファイルパスの作成
        temp_dir = os.path.join("app", "upload")
        os.makedirs(temp_dir, exist_ok=True)
        
        # ユニークなファイル識別子を生成（日時とUUIDの組み合わせ）
        now = datetime.now().strftime("%Y%m%d%H%M%S")
        file_id = f"{now}_{uuid.uuid4().hex[:8]}"
        
        # 入力ファイル保存
        input_filename = f"{file_id}_input{os.path.splitext(file.filename)[1]}"
        input_path = os.path.join(temp_dir, input_filename)
        
        # ファイル保存
        content = file.file.read()
        with open(input_path, "wb") as f:
            f.write(content)
        
        # FFmpegを使用してファイルサイズに基づいて分割
        # segment_timeは秒単位なので、サイズから時間を概算する必要がある
        # これは推定なので、実際のビットレートに応じて調整が必要
        
        # ファイルの情報を取得
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
        
        # 結果を解析
        output_lines = process.stdout.strip().split('\n')
        if len(output_lines) >= 2:
            duration = float(output_lines[0])  # 秒単位
            file_size_bytes = float(output_lines[1])  # バイト単位
            
            # ビットレート計算（ビット/秒）
            bitrate = file_size_bytes * 8 / duration
            
            # サイズMBから分割時間を計算
            # size MBごとに分割したいので、size MB = (bitrate * segment_time) / 8 / 1024 / 1024
            # よって segment_time = size * 8 * 1024 * 1024 / bitrate
            segment_time = (size * 8 * 1024 * 1024) / bitrate if bitrate > 0 else 60
        else:
            # デフォルト値を使用（60秒ごとに分割）
            segment_time = 60
            
        # 出力ファイルのベース名
        output_basename = f"{file_id}_%03d{os.path.splitext(file.filename)[1]}"
        output_path = os.path.join(temp_dir, output_basename)
        
        # FFmpegでファイル分割
        split_cmd = [
            "ffmpeg",
            "-i", input_path,
            "-c", "copy",  # コーデックをコピー（再エンコードなし）
            "-map", "0",
            "-segment_time", str(segment_time),
            "-f", "segment",
            "-reset_timestamps", "1",
            output_path
        ]
        
        process = subprocess.run(split_cmd, capture_output=True, text=True)
        if process.returncode != 0:
            raise Exception(f"ファイル分割に失敗しました: {process.stderr}")
            
        # 分割されたファイルのリストを取得
        split_files = [f for f in os.listdir(temp_dir) 
                      if f.startswith(file_id) and f != input_filename]
        
        # URLリストを作成
        media_urls = []
        for split_file in sorted(split_files):
            url = f"{BASE_URL}{BASE_PATH}/upload/{split_file}"
            media_urls.append(url)
            
        # 元のファイルを削除（オプション）
        os.remove(input_path)
        
        # 結果を返す
        main_logger.info(f"ファイルを {len(media_urls)} 個に分割しました: {file.filename}")
        return media.ResBase(media_urls=media_urls)
        
    except Exception as e:
        main_logger.error(f"ファイル分割（容量） error: {e}")
        raise Exception(f"ファイル分割（容量）に失敗しました: {str(e)}")
