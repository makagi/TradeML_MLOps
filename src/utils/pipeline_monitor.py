# -*- coding: utf-8 -*-
"""パイプライン監視ユーティリティ"""
import time
from typing import Optional, Dict
from enum import Enum


class PipelineState(Enum):
    """パイプラインの状態"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    UNKNOWN = "UNKNOWN"


def monitor_pipeline_execution(
    job_resource_name: str,
    project_id: str,
    location: str = "us-central1",
    poll_interval: int = 30,
    timeout: int = 3600,
) -> Dict:
    """パイプライン実行を監視
    
    Args:
        job_resource_name: パイプラインジョブのリソース名
        project_id: プロジェクトID
        location: リージョン
        poll_interval: ポーリング間隔（秒）
        timeout: タイムアウト（秒）
    
    Returns:
        実行結果の辞書
    """
    from google.cloud import aiplatform
    
    aiplatform.init(project=project_id, location=location)
    
    print(f"[INFO] Monitoring pipeline: {job_resource_name}")
    print(f"[INFO] Poll interval: {poll_interval}s, Timeout: {timeout}s")
    
    # ジョブを取得
    try:
        job = aiplatform.PipelineJob.get(job_resource_name)
    except Exception as e:
        print(f"[ERROR] Failed to get pipeline job: {e}")
        return {
            "status": "ERROR",
            "message": f"Failed to get job: {e}"
        }
    
    start_time = time.time()
    last_state = None
    
    while True:
        elapsed = time.time() - start_time
        
        # タイムアウトチェック
        if elapsed > timeout:
            print(f"\n[ERROR] Pipeline execution timed out after {timeout}s")
            return {
                "status": "TIMEOUT",
                "state": job.state.name if job.state else "UNKNOWN",
                "elapsed_time": elapsed
            }
        
        # 状態を取得
        try:
            job._sync_gca_resource()  # 最新状態を取得
            current_state = job.state.name if job.state else "UNKNOWN"
        except Exception as e:
            print(f"[WARN] Failed to sync job state: {e}")
            current_state = "UNKNOWN"
        
        # 状態が変わった場合のみ表示
        if current_state != last_state:
            print(f"\n[{time.strftime('%H:%M:%S')}] Pipeline state: {current_state}")
            last_state = current_state
        
        # 終了状態をチェック
        if current_state == "PIPELINE_STATE_SUCCEEDED":
            print(f"\n[SUCCESS] Pipeline completed successfully!")
            print(f"Elapsed time: {elapsed:.1f}s")
            return {
                "status": "SUCCESS",
                "state": current_state,
                "elapsed_time": elapsed,
                "job": job
            }
        
        elif current_state == "PIPELINE_STATE_FAILED":
            print(f"\n[ERROR] Pipeline execution failed!")
            print(f"Elapsed time: {elapsed:.1f}s")
            
            # エラー詳細を取得
            error_message = "Unknown error"
            if job.error:
                error_message = str(job.error)
                print(f"Error details: {error_message}")
            
            return {
                "status": "FAILED",
                "state": current_state,
                "error": error_message,
                "elapsed_time": elapsed,
                "job": job
            }
        
        elif current_state == "PIPELINE_STATE_CANCELLED":
            print(f"\n[WARN] Pipeline was cancelled")
            print(f"Elapsed time: {elapsed:.1f}s")
            return {
                "status": "CANCELLED",
                "state": current_state,
                "elapsed_time": elapsed,
                "job": job
            }
        
        # 進行中の場合は待機
        print(".", end="", flush=True)
        time.sleep(poll_interval)


def wait_for_pipeline_completion(
    job_resource_name: str,
    project_id: str,
    location: str = "us-central1",
    timeout: int = 3600,
) -> bool:
    """パイプライン完了を待つ（簡易版）
    
    Returns:
        成功した場合True、失敗した場合False
    """
    result = monitor_pipeline_execution(
        job_resource_name=job_resource_name,
        project_id=project_id,
        location=location,
        timeout=timeout
    )
    
    return result["status"] == "SUCCESS"


def get_pipeline_logs(job_resource_name: str, project_id: str, location: str = "us-central1"):
    """パイプラインのログを取得（簡易版）
    
    Args:
        job_resource_name: パイプラインジョブのリソース名
        project_id: プロジェクトID
        location: リージョン
    """
    from google.cloud import aiplatform
    
    aiplatform.init(project=project_id, location=location)
    
    try:
        job = aiplatform.PipelineJob.get(job_resource_name)
        
        print(f"\n=== Pipeline Job Details ===")
        print(f"Name: {job.display_name}")
        print(f"State: {job.state.name if job.state else 'UNKNOWN'}")
        print(f"Created: {job.create_time}")
        print(f"Updated: {job.update_time}")
        
        if job.error:
            print(f"\nError: {job.error}")
        
        # タスク詳細を表示
        if hasattr(job, 'task_details') and job.task_details:
            print(f"\n=== Task Details ===")
            for task in job.task_details:
                print(f"\nTask: {task.task_name}")
                print(f"  State: {task.state.name if task.state else 'UNKNOWN'}")
                if task.error:
                    print(f"  Error: {task.error}")
        
    except Exception as e:
        print(f"[ERROR] Failed to get pipeline logs: {e}")
